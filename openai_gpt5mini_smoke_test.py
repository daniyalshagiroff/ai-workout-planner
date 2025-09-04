import os
import sys
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI


SYSTEM_PROMPT = (
    "You are a fitness AI coach who designs weekly training programs based on the latest scientific principles of hypertrophy. "
    "Return only JSON when asked to output a plan."
)


def main() -> None:
    load_dotenv()
    api_key: Optional[str] = os.getenv("OPENAI_GRP5NINI") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_GRP5NINI/OPENAI_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # Mimic ai_client prompt style but shorter, and print raw output
    owner_user_id = 1
    title = "AI Program"
    description = "Test generation"
    experience = "novice"
    days_per_week = 3
    equipment = ["barbell", "dumbbell", "machine"]
    priority = "chest, back"

    user_prompt = f"""
Generate a weekly training program and return STRICTLY AND ONLY JSON in the following SCHEMA AND KEY ORDER. Do not add any other keys, comments, or text. Use null where data is missing. Keep exact key names and order.

USER INPUT:
- owner_user_id: {owner_user_id}
- title: {title}
- description: {description}
- experience: {experience} (novice|intermediate|advanced)
- days_per_week: {days_per_week}
- equipment_available: {equipment}
- priority: {priority}

OUTPUT MUST MATCH THIS SCHEMA EXACTLY (NO CHANGES):
{{
  "owner_user_id": 123,
  "title": "Program Title",
  "description": "Optional description",
  "weeks": [
    {{
      "week_number": 1,
      "days": [
        {{
          "day_of_week": 1,
          "exercises": [
            {{
              "name": "exercise name 1",
              "muscle_group": "muscle group",
              "equipment": "equipment or null",
              "position": 1,
              "notes": null,
              "planned_sets": [
                {{ "set_number": 1, "reps": 8, "weight": null, "rpe": null, "rest_seconds": 90 }},
                {{ "set_number": 2, "reps": 8, "weight": null, "rpe": null, "rest_seconds": 90 }}
              ]
            }}
          ]
        }}
      ]
    }}
  ]
}}
""".strip()

    try:
        resp = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"}
        )
        print(f"id: {resp.id}")
        print(f"model: {resp.model}")
        try:
            usage = getattr(resp, 'usage', None)
            if usage:
                print(f"usage: {usage}")
        except Exception:
            pass
        if not resp.choices:
            print("EMPTY: no choices returned")
            return
        msg = resp.choices[0].message
        content = msg.content if msg else ""
        if content and content.strip():
            print(content.strip())
        else:
            print("EMPTY: message.content is empty")
            print(f"raw message: {msg}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()


