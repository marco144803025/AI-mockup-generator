import requests
import json

def test_intent_detection():
    url = "http://localhost:8000/api/chat"
    
    # First message to get questions
    data1 = {
        "message": "I want to build a signup UI."
    }
    
    try:
        print("=== Step 1: Initial request ===")
        response1 = requests.post(url, json=data1)
        result1 = response1.json()
        print(f"Response: {result1.get('response', 'No response')[:200]}...")
        
        # Second message to answer a question
        print("\n=== Step 2: Answering question ===")
        data2 = {
            "message": "I want green accents",
            "session_id": result1.get('session_id')
        }
        
        response2 = requests.post(url, json=data2)
        result2 = response2.json()
        print(f"Response: {result2.get('response', 'No response')[:200]}...")
        print(f"Phase: {result2.get('phase', 'No phase')}")
        
        # Check if it's still in template recommendation phase
        if result2.get('phase') == 'template_recommendation':
            print("✅ SUCCESS: Correctly staying in template recommendation phase")
        else:
            print("❌ ERROR: Incorrectly changed phase")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_intent_detection() 