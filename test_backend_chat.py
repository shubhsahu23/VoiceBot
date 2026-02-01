
import requests
import json
import sys

url = "http://localhost:8000/chat"
payload = {
    "message": "invoice",
    "driver_id": "test_driver"
}
headers = {'Content-Type': 'application/json'}

try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response Intent: {data.get('intent')}")
        print(f"Has Audio: {'audio' in data}")
    else:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
