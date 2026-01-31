
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health Check Failed: {e}")

def test_driver_validation():
    print("\n--- Testing Driver Validation ---")
    # Valid driver
    try:
        res = requests.post(f"{BASE_URL}/validate-driver", json={"driver_id": "D123"})
        print(f"Valid Driver (D123): {res.status_code} - {res.json()}")
    except Exception as e: print(f"Valid Driver Test Failed: {e}")

    # Invalid driver
    try:
        res = requests.post(f"{BASE_URL}/validate-driver", json={"driver_id": "INVALID_ID"})
        print(f"Invalid Driver (INVALID_ID): {res.status_code} - {res.json()}")
    except Exception as e: print(f"Invalid Driver Test Failed: {e}")

def test_chat_intent():
    print("\n--- Testing Chat Intent ---")
    queries = [
        "Where is the nearest station?",
        "I want to swap my battery",
        "How many leave days do I have?",
        "Can I upgrade my subscription?",
        "What is the capital of France?" # Should escalate or be unrelated
    ]
    
    for q in queries:
        try:
            res = requests.post(f"{BASE_URL}/chat", json={"message": q})
            print(f"Query: '{q}'\nResponse: {res.json()}\n")
        except Exception as e:
            print(f"Chat Test Failed for '{q}': {e}")

def test_context_aware_chat():
    print("\n--- Testing Context-Aware Chat ---")
    # DRV001 has Premium subscription expiring 2026-03-31
    queries = [
        {"msg": "What is my subscription type?", "id": "DRV003"},
        {"msg": "When does my subscription expire?", "id": "DRV003"},
        {"msg": "Show me my last invoice amount", "id": "DRV003"},
        {"msg": "Who am I?", "id": "DRV002"} # Suresh Yadav
    ]
    
    for item in queries:
        try:
            payload = {"message": item['msg'], "driver_id": item['id']}
            res = requests.post(f"{BASE_URL}/chat", json=payload)
            print(f"Query: '{item['msg']}' (Driver: {item['id']})\nResponse: {res.json()}\n")
        except Exception as e:
            print(f"Context Test Failed for '{item['msg']}': {e}")

def test_emergency_escalation():
    print("\n--- Testing Emergency Escalation ---")
    queries = [
        "My battery exploded!",
        "There is fire coming from the battery",
        "Help, smoke is detecting"
    ]
    
    for q in queries:
        try:
            payload = {"message": q, "driver_id": "DRV003"}
            res = requests.post(f"{BASE_URL}/chat", json=payload)
            data = res.json()
            print(f"Query: '{q}'\nIntent: {data.get('intent')}, Escalate: {data.get('escalate')}\n")
        except Exception as e:
            print(f"Emergency Test Failed for '{q}': {e}")

def test_unrelated_escalation():
    print("\n--- Testing Unrelated Escalation ---")
    queries = [
        "Who won the cricket match?",
        "What is the capital of France?",
        "How to bake a cake?"
    ]
    
    for q in queries:
        try:
            payload = {"message": q, "driver_id": "DRV003"}
            res = requests.post(f"{BASE_URL}/chat", json=payload)
            data = res.json()
            print(f"Query: '{q}'\nIntent: {data.get('intent')}, Escalate: {data.get('escalate')}\n")
        except Exception as e:
            print(f"Unrelated Test Failed for '{q}': {e}")

if __name__ == "__main__":
    print("Waiting for server to start...")
    time.sleep(3) # Wait for server
    test_health()
    test_context_aware_chat()
    test_emergency_escalation()
    test_unrelated_escalation()
