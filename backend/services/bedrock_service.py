
import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from datetime import datetime, date
import re
from dateutil import parser as date_parser

# Month names for Marathi and Hindi (simple transliterations in Devanagari)
MONTHS_MR = [
    'जानेवारी','फेब्रुवारी','मार्च','एप्रिल','मे','जून','जुलै','ऑगस्ट','सप्टेंबर','ऑक्टोबर','नोव्हेंबर','डिसेंबर'
]
MONTHS_HI = [
    'जनवरी','फ़रवरी','मार्च','अप्रैल','मई','जून','जुलाई','अगस्त','सितंबर','अक्टूबर','नवंबर','दिसंबर'
]

DEVANAGARI_DIGITS = str.maketrans('0123456789', '०१२३४५६७८९')

def localize_number(s: str, lang_name: str) -> str:
    if lang_name in ('Marathi', 'Hindi'):
        return s.translate(DEVANAGARI_DIGITS)
    return s


def format_date_for_lang(dt: datetime, lang_name: str) -> str:
    """Return a human-friendly localized date string for the language."""
    day = str(dt.day)
    year = str(dt.year)
    month_idx = dt.month - 1
    if lang_name == 'Marathi':
        month = MONTHS_MR[month_idx]
        return f"{localize_number(day, 'Marathi')} {month} {localize_number(year, 'Marathi')}"
    if lang_name == 'Hindi':
        month = MONTHS_HI[month_idx]
        return f"{localize_number(day, 'Hindi')} {month} {localize_number(year, 'Hindi')}"
    # Default English
    return dt.strftime('%d %b %Y')


def localize_dates_in_text(text: str, lang_name: str) -> str:
    """Find ISO-like dates in text and replace with localized formats."""
    if not text:
        return text

    # ISO date YYYY-MM-DD
    def repl_iso(m):
        try:
            dt = date_parser.parse(m.group(0)).date()
            return format_date_for_lang(datetime(dt.year, dt.month, dt.day), lang_name)
        except Exception:
            return m.group(0)

    text = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', repl_iso, text)

    # DD/MM/YYYY or DD-MM-YYYY
    def repl_dmy(m):
        try:
            dt = date_parser.parse(m.group(0), dayfirst=True).date()
            return format_date_for_lang(datetime(dt.year, dt.month, dt.day), lang_name)
        except Exception:
            return m.group(0)

    text = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b', repl_dmy, text)

    return text

# Local language detection
try:
    from langdetect import detect
except Exception:
    # fallback if not installed or detection fails
    def detect(text):
        return None

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

    # Local language detection (best-effort) to prefer Marathi when present
    detected_code = None
    detected_lang_name = None
    try:
        detected_code = detect(user_query) or None
    except Exception:
        detected_code = None

    if detected_code:
        if detected_code.startswith('hi'):
            detected_lang_name = 'Hindi'
        elif detected_code.startswith('mr'):
            detected_lang_name = 'Marathi'
        elif detected_code.startswith('en'):
            detected_lang_name = 'English'
        else:
            detected_lang_name = 'English'
    else:
        detected_lang_name = 'English'

    # Heuristic: if input contains Devanagari script and Marathi-specific tokens, prefer Marathi
    try:
        if re.search(r'[\u0900-\u097F]', user_query):
            marathi_tokens = ['आहे','मला','कृपया','सदस्यत्व','शेवट','शेवटचा','ड्रायव्हर','नाव','स्वॅप','कधी','नवीन']
            if any(tok in user_query for tok in marathi_tokens):
                detected_lang_name = 'Marathi'
    except Exception:
        pass

    context_str = ""
    marathi_context_str = ""
    if context:
        # datetime serialization handler
        def json_serial(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        context_str = f"Context Information:\n{json.dumps(context, indent=2, default=str)}\nUse this context to answer specific questions about the driver (e.g., subscription expiry, last swap)."

        # Build a simple Marathi summary of known fields so the model can reuse DB values directly
        try:
            parts = []
            if 'driver_id' in context:
                parts.append(f"ड्रायव्हर आयडी: {context.get('driver_id')}")
            if 'driverId' in context and not context.get('driver_id'):
                parts.append(f"ड्रायव्हर आयडी: {context.get('driverId')}")
            if 'name' in context:
                parts.append(f"नाव: {context.get('name')}")
            if 'subscription' in context:
                parts.append(f"सदस्यत्व: {context.get('subscription')}")
            if 'subscription_expiry' in context:
                # Localize the expiry date for Marathi context summary if possible
                try:
                    dt = date_parser.parse(str(context.get('subscription_expiry')))
                    parts.append(f"सदस्यत्व समाप्ती: {format_date_for_lang(dt, 'Marathi')}")
                except Exception:
                    parts.append(f"सदस्यत्व समाप्ती: {context.get('subscription_expiry')}")
            if 'last_swap' in context:
                parts.append(f"शेवटचा स्वॅप: {context.get('last_swap')}")
            if parts:
                marathi_context_str = "डाटाबेस संदर्भ: " + "; ".join(parts)
        except Exception:
            marathi_context_str = ""

    # Add explicit language hint to the model to reduce confusion between Hindi and Marathi
    language_hint = f"Detected language: {detected_lang_name}."
    # Make instructions more explicit to avoid confusion between Hindi and Marathi
    language_hint += " If detected language is Marathi, answer in Marathi using Devanagari script and set the 'language' field to 'Marathi'."
    language_hint += " Use Marathi-specific phrases and grammar (examples: 'आहे', 'मला', 'कृपया', 'तुमची', 'तुम्ही', 'सदस्यत्व', 'शेवटचे') and avoid Hindi-only words like 'आपकी' or 'आपका'."
    language_hint += " If detected language is Hindi, answer in Hindi (Devanagari). If detected language is English, answer in English."

    # If we have Marathi DB context, instruct the model to use those DB values verbatim in Marathi
    if marathi_context_str:
        language_hint += f" Use these database facts in Marathi when relevant: {marathi_context_str}. Ensure you reference these values directly in your response when answering the user in Marathi."    # Llama 3 Prompt Style
    prompt_config = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are a helpful AI assistant for a battery swapping service.

    {context_str}

    {language_hint}

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

    Provide your response in strictly JSON format.
    Do NOT include any explanation, preamble, or postscript.
    Do NOT use markdown code blocks.
    Just output the raw JSON object. Make sure the "language" field is present and set to one of: "English", "Hindi", or "Marathi".
    
    If the user input is gibberish, random characters, or meaningless, immediately return:
    {{ "intent": "unrelated", "confidence": 1.0, "response": "I didn't understand that.", "language": "English", "escalate": true }}

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

        # Helper: translation fallback for Marathi when model didn't return Marathi
        def translate_to_marathi(text):
            try:
                t_prompt = f"Translate the following text into natural Marathi (Devanagari script) preserving meaning and tone. Output only the translated text.\n\nText:\n{text}"
                t_body = json.dumps({
                    "prompt": t_prompt,
                    "max_gen_len": 256,
                    "temperature": 0.0
                })
                t_resp = bedrock_client.invoke_model(
                    body=t_body,
                    modelId=MODEL_ID,
                    accept='application/json',
                    contentType='application/json'
                )
                t_resp_body = json.loads(t_resp.get('body').read())
                t_gen = t_resp_body.get('generation', '')
                return t_gen.strip()
            except Exception as e:
                logger.error(f"Marathi translation fallback failed: {e}")
                return text

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
                    # Ensure language field exists; if model didn't set it, use our detected language
                    if 'language' not in result or not result['language']:
                        result['language'] = detected_lang_name

                    # If we detected Marathi but model returned a different language, translate response to Marathi
                    if detected_lang_name == 'Marathi' and result.get('language', '').lower() != 'marathi':
                        translated = translate_to_marathi(result.get('response', ''))
                        result['response'] = translated
                        result['language'] = 'Marathi'

                    # Localize dates in the final response according to detected language
                    try:
                        result['response'] = localize_dates_in_text(result.get('response', ''), detected_lang_name)
                    except Exception:
                        pass

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
                fallback = json.loads(cleaned_completion[start_idx:end_idx+1])
                if 'language' not in fallback or not fallback.get('language'):
                    fallback['language'] = detected_lang_name
                # If Marathi was detected but model didn't return Marathi, translate response
                if detected_lang_name == 'Marathi' and fallback.get('language', '').lower() != 'marathi':
                    fallback['response'] = translate_to_marathi(fallback.get('response', ''))
                    fallback['language'] = 'Marathi'

                # Localize dates in fallback
                try:
                    fallback['response'] = localize_dates_in_text(fallback.get('response', ''), detected_lang_name)
                except Exception:
                    pass
                return fallback
             except:
                pass
                
        logger.warning("Could not find valid JSON in response")
        # Ensure we return the detected language even if model failed to produce structured JSON
        resp = {"intent": "unknown", "confidence": 0, "response": completion, "escalate": True, "language": detected_lang_name}
        if detected_lang_name == 'Marathi' and resp.get('language', '').lower() != 'marathi':
            resp['response'] = translate_to_marathi(resp.get('response', ''))
            resp['language'] = 'Marathi'
        return resp

    except ClientError as e:
        logger.error(f"Bedrock invocation failed: {e}")
        return {"intent": "error", "confidence": 0, "response": "AI service error", "escalate": True}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return {"intent": "error", "confidence": 0, "response": "Error processing AI response", "escalate": True}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"intent": "error", "confidence": 0, "response": "Unexpected error", "escalate": True}
