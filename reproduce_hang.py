
import requests
import json
import time

url = "http://localhost:8000/chat"
payload = {
    "message": "b vcbgvxszc",
    "driver_id": "DRV006"
}
headers = {'Content-Type': 'application/json'}

try:
    print("Sending request...")
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    with open('response_debug.txt', 'w', encoding='utf-8') as f:
        f.write(f"Status: {response.status_code}\n")
        f.write(response.text)
    print("Request completed.")
except Exception as e:
    with open('response_debug.txt', 'w') as f:
        f.write(f"Error: {e}")
    print(f"Request failed: {e}")
