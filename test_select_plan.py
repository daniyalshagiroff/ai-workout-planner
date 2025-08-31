import requests
import json

# Test selecting a plan
url = "http://localhost:8000/api/v2/user-programs"
data = {
    'user_id': 1,
    'program_id': 3
}

try:
    print("Sending request...")
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Plan selected successfully!")
        # Try to parse JSON response
        try:
            result = response.json()
            print(f"Parsed response: {json.dumps(result, indent=2)}")
        except:
            print("Could not parse JSON response")
    else:
        print("❌ Failed to select plan")
        
except Exception as e:
    print(f"Error: {e}")
