import requests
import json

# Test getting user plans
url = "http://localhost:8000/api/v2/user-programs?user_id=1"

try:
    print("Getting user plans...")
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ User plans retrieved successfully!")
        try:
            result = response.json()
            print(f"Number of plans: {len(result)}")
            for plan in result:
                print(f"- {plan['program_title']} (ID: {plan['id']})")
        except:
            print("Could not parse JSON response")
    else:
        print("❌ Failed to get user plans")
        
except Exception as e:
    print(f"Error: {e}")
