import json
import sys
import requests


def main() -> None:
    url = "http://localhost:8001/api/v2/ai/generate-plan"
    payload = {
        "owner_user_id": 1,
        "title": "AI Program",
        "description": "My program",
        "experience": "novice",
        "days": 3,
        "equipment": ["dumbbell", "barbell"],
        "priorities": ["chest", "legs"]
    }

    try:
        resp = requests.post(url, json=payload, timeout=120)
    except Exception as e:
        print(f"REQUEST FAILED: {e}")
        sys.exit(1)

    print("status:", resp.status_code)
    ct = resp.headers.get("content-type", "")
    print("content-type:", ct)

    # Always print whatever came back
    text = resp.text or ""
    print("raw:", text)


if __name__ == "__main__":
    main()


