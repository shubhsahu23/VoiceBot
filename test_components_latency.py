
import sys
import os
import time
import logging

sys.path.append(os.path.abspath('backend'))
os.environ['AWS_REGION'] = 'us-west-2'

try:
    from services.bedrock_service import detect_intent
    from services.polly_service import generate_audio_base64
except ImportError as e:
    with open('latency_results.txt', 'w') as f:
        f.write(f"Import failed: {e}")
    sys.exit(1)

def test_latency():
    query = "b vcbgvxszc"
    context = {"driver_id": "DRV006"}
    
    with open('latency_results.txt', 'w') as f:
        f.write(f"Testing Latency for query: '{query}'\n")
        
        # Test Bedrock
        start = time.time()
        f.write("Calling detect_intent...\n")
        print("Calling detect_intent...")
        result = detect_intent(query, context)
        bedrock_time = time.time() - start
        f.write(f"Bedrock Time: {bedrock_time:.2f}s\n")
        f.write(f"Result: {result.get('response', '')[:100]}...\n")

        # Test Polly
        if result.get('response'):
            start = time.time()
            f.write("Calling generate_audio_base64...\n")
            print("Calling generate_audio_base64...")
            generate_audio_base64(result['response'], language=result.get('language', 'English'))
            polly_time = time.time() - start
            f.write(f"Polly Time: {polly_time:.2f}s\n")

if __name__ == "__main__":
    test_latency()
