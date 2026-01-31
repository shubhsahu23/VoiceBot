
import os
import sys
from services.bedrock_service import detect_intent

# Fake context
context = {
    "driver_name": "Raju",
    "subscription_expiry": "2024-12-31"
}

queries = [
    "Battery swap kaise kare?",
    "Mera bill kitna hai?",
    "Namaste",
    "How do I swap battery?"
]

print("--- Testing Language Response ---")
for q in queries:
    print(f"\nQuery: {q}")
    try:
        result = detect_intent(q, context)
        print(f"Full Result: {result}")
        print(f"Detected Intent: {result.get('intent')}")
        print(f"Detected Language: {result.get('language')}")
        print(f"Response: {result.get('response')}")
    except Exception as e:
        print(f"Error: {e}")
