# scripts/test.py
import requests
import json

BASE_URL = "https://ansahfredd-my-ai-space.hf.space/api"

def test_endpoint(endpoint, payload):
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.post(
            url,
            json={"data": [payload]},
            timeout=10
        )
        print(f"\nTesting {endpoint}:")
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error testing {endpoint}: {str(e)}")

# Test cases
if __name__ == "__main__":
    test_endpoint("summarize", {
        "text": "The tax law states that...",
        "max_length": 100
    })
    
    test_endpoint("qa", {
        "question": "What is the deadline?",
        "context": "Tax returns are due April 15"
    })