import json
import requests


def test_ai_generate_plan_smoke():
    url = "http://localhost:8001/api/v2/ai/generate-plan"
    payload = {
        "owner_user_id": 1,
        "title": "AI Program",
        "description": "Test Generation",
        "experience": "novice",
        "days": 3,
        "equipment": "dumbbell, barbell",
        "priorities": "chest"
    }

    try:
        resp = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        print("status=", resp.status_code)
        if resp.ok:
            data = resp.json()
            assert isinstance(data, dict)
            assert "weeks" in data
            assert isinstance(data["weeks"], list)
        else:
            print("body=", resp.text)
    except Exception as e:
        print("request error:", e)


