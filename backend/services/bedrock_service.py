
import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
MODEL_ID = os.getenv("LLM_MODEL_ID", "meta.llama3-1-8b-instruct-v1:0")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN")
    )
    logger.info("Bedrock client initialized")
except Exception as e:
    logger.error(f"Failed to initialize Bedrock client: {e}")
    bedrock_client = None

def detect_intent(user_query, context=None):
    """
    Detects the intent of the user query using Bedrock Llama 3 model.
    :param user_query: The user's question.
    :param context: Optional dictionary containing driver details (e.g. name, plan).
    """
    if not bedrock_client:
        return {"intent": "error", "confidence": 0, "response": "Backend service unavailable.", "escalate": True}

    context_str = ""
    if context:
        # datetime serialization handler
        def json_serial(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        context_str = f"Context Information:\n{json.dumps(context, indent=2, default=str)}\nUse this context to answer specific questions about the driver (e.g., subscription expiry, last swap)."

    # Llama 3 Prompt Style
    prompt_config = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are a helpful AI assistant for a battery swapping service.

    {context_str}

    Your task is to classify the user's intent into one of the following categories:
    - leave (related to checking leave balance, applying for leave)
    - subscription (related to plan details, renewal, upgrade)
    - nearest station (finding a battery station)
    - battery swap (process of swapping, issues with swapping)
    - invoice (related to last bill, amount, payment history)
    - emergency (critical safety issues like fire, blast, smoke, accident, injury)
    - unrelated (anything else)

    CRITICAL RULES:
    - If the intent is 'emergency', you MUST set "escalate": true.
    - If the intent is 'unrelated', you MUST set "escalate": true.
    - If the user mentions fire, smoke, explosion, or immediate danger, classify as 'emergency'.
    - PRIORITY: If the user asks for an invoice, bill, or receipt (e.g., "battery swap invoice"), classify as 'invoice', even if 'battery swap' is mentioned.
    - DETECT the language of the user query.
    - Your "response" MUST be in the SAME language as the user query.
    - If the user speaks Hindi, answer in Hindi using Devanagari script (NOT Hinglish).
    - If the user speaks English, answer in English.

    Provide your response in strictly JSON format.
    Do NOT include any explanation, preamble, or postscript.
    Do NOT use markdown code blocks.
    Just output the raw JSON object.

    Example Format:
    {{
        "intent": "DETECTED_INTENT",
        "confidence": 0.95,
        "response": "GENERATED_RESPONSE",
        "language": "DETECTED_LANGUAGE",
        "escalate": false
    }}<|eot_id|><|start_header_id|>user<|end_header_id|>
    {user_query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    body = json.dumps({
        "prompt": prompt_config,
        "max_gen_len": 512,
        "temperature": 0.1,
        "top_p": 0.9
    })

    try:
        response = bedrock_client.invoke_model(
            body=body,
            modelId=MODEL_ID,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        completion = response_body.get('generation', '')
        
        
        logger.info(f"Raw model response: {completion}")

        # specific cleanup for Llama 3 which might output markdown
        cleaned_completion = completion.strip()


        if cleaned_completion.startswith("```json"):
            cleaned_completion = cleaned_completion[7:]

        # Robust extraction: find the first { and the *matching* }
        start_idx = cleaned_completion.find('{')
        if start_idx != -1:
            brace_count = 0
            json_str = ""
            found_end = False
            for i in range(start_idx, len(cleaned_completion)):
                char = cleaned_completion[i]
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                
                if brace_count == 0:
                    json_str = cleaned_completion[start_idx:i+1]
                    found_end = True
                    break
            
            if found_end:
                try:
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError as json_err:
                     logger.error(f"JSON extract failed on: {json_str}. Error: {json_err}")
                     # Fallback to simple slice if strict counting failed (e.g. malformed)
                     pass

        # Fallback: simple heuristic
        start_idx = cleaned_completion.find('{')
        end_idx = cleaned_completion.rfind('}')
        if start_idx != -1 and end_idx != -1:
             try:
                return json.loads(cleaned_completion[start_idx:end_idx+1])
             except:
                pass
                
        logger.warning("Could not find valid JSON in response")
        return {"intent": "unknown", "confidence": 0, "response": completion, "escalate": True}

    except ClientError as e:
        logger.error(f"Bedrock invocation failed: {e}")
        return {"intent": "error", "confidence": 0, "response": "AI service error", "escalate": True}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return {"intent": "error", "confidence": 0, "response": "Error processing AI response", "escalate": True}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"intent": "error", "confidence": 0, "response": "Unexpected error", "escalate": True}
