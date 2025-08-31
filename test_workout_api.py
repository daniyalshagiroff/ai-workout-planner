import requests
import json

def test_start_workout():
    print("=== Testing Start Workout ===")
    
    url = "http://localhost:8000/api/v2/workouts/start"
    data = {
        'owner_user_id': 1,
        'program_id': 3,
        'week_number': 1,
        'day_of_week': 3
    }
    
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            workout_id = result['workout_id']
            print(f"✅ Workout started! ID: {workout_id}")
            return workout_id
        else:
            print("❌ Failed to start workout")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_log_set(workout_id, planned_set_id):
    print(f"\n=== Testing Log Set (Workout: {workout_id}, Set: {planned_set_id}) ===")
    
    url = f"http://localhost:8000/api/v2/workouts/{workout_id}/sets/{planned_set_id}"
    data = {
        'reps': 10,
        'weight': 50.0
    }
    
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Set logged successfully!")
            return True
        else:
            print("❌ Failed to log set")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    workout_id = test_start_workout()
    
    if workout_id:
        # Test logging a set (using planned_set_id = 1)
        test_log_set(workout_id, 1)
