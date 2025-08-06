import requests
import json

def test_session_id():
    url = "http://localhost:8000/api/chat"
    data = {
        "message": "I want to build a signup UI."
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Session ID: {result.get('session_id', 'No session ID')}")
        print(f"Response: {result.get('response', 'No response')[:200]}...")
        
        # Check if session ID is not demo_session
        session_id = result.get('session_id', '')
        if 'demo_session' in session_id:
            print("❌ ERROR: Still using demo_session!")
        else:
            print("✅ SUCCESS: Using proper session ID!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_session_id() 