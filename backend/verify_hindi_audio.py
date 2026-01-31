
import sys
import logging
from services.bedrock_service import detect_intent
from services.polly_service import generate_audio_base64

# Configure logging
logging.basicConfig(level=logging.INFO)

# Fake context
context = {
    "driver_name": "Raju",
    "subscription_expiry": "2024-12-31"
}

query = "Battery swap kaise kare?"
print(f"\nQuery: {query}")

try:
    # 1. Detect Intent
    print("Calling Bedrock...")
    result = detect_intent(query, context)
    
    print(f"Detected Intent: {result.get('intent')}")
    print(f"Response (Text): {result.get('response')}")
    
    with open("verification_result.txt", "w", encoding="utf-8") as f:
        f.write(f"Detected Intent: {result['intent']}\n")
        f.write(f"Detected Language: '{result['language']}'\n")
        f.write(f"Response: {result['response']}\n")

    # Check if response contains Devanagari characters (range U+0900 to U+097F)
    has_devanagari = any('\u0900' <= char <= '\u097f' for char in result.get('response', ''))
    print(f"Has Devanagari: {has_devanagari}")
    with open("verification_result.txt", "a", encoding="utf-8") as f:
        f.write(f"Has Devanagari: {has_devanagari}\n")

    # 2. Generate Audio
    print("Generating Audio...")
    audio_b64 = generate_audio_base64(result.get('response'), language=result.get('language'))
    
    if audio_b64:
        print("Audio generated successfully (Base64 length):", len(audio_b64))
        with open("verification_result.txt", "a", encoding="utf-8") as f:
            f.write(f"Audio Generated: Yes, Length: {len(audio_b64)}\n")
            # We can't easily log the log messages from polly_service here unless we configure logging to file too.
            # But we can verify if the output exists.
    else:
        print("Failed to generate audio.")
        with open("verification_result.txt", "a", encoding="utf-8") as f:
            f.write("Audio Generated: No\n")

except Exception as e:
    print(f"Error: {e}")
