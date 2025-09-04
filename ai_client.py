from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv, find_dotenv
from openai import OpenAI


load_dotenv(find_dotenv())


SYSTEM_PROMPT = (
    "You are a fitness AI coach. Your job is to output STRICT JSON objects only, never prose. "
    "You must follow evidence-based hypertrophy principles while keeping output formatting constraints: "
    "(1) volume drives growth; (2) distribute volume across 2–4 touches per muscle/week; "
    "(3) rep ranges 6–10, 8–15, 12–20+ work if 0–3 RIR; "
    "(4) rest: compounds 120–180s, isolation ≥90s; "
    "(5) full ROM and lengthened-position movements. "
    "Apply these rules implicitly in values, but DO NOT explain them. "
    "Always generate programs that train the whole body through the week, covering chest, back, legs, arms, and shoulders. "
    "Exclude abs unless abs are explicitly set as priority. "
    "Each training day must contain between 4 and 8 exercises: "
    "- if days_per_week = 3 → strictly 7–8 exercises per day; "
    "- if days_per_week = 4 → strictly 6–7 exercises per day; "
    "- if days_per_week = 5 → strictly 5–6 exercises per day; "
    "The number of working sets per exercise must be adapted to the user’s experience level: "
    "novice = lower bound, intermediate = mid, advanced = higher bound. "
    "Output must be valid JSON: no comments, no trailing commas, no code fences, no markdown."
)


SCHEMA_BLOCK = (
    "OUTPUT SCHEMA (EXACT):\n"
    "{\n"
    "  \"owner_user_id\": 123,\n"
    "  \"title\": \"Program Title\",\n"
    "  \"description\": \"Optional description\",\n"
    "  \"weeks\": [\n"
    "    {\n"
    "      \"week_number\": 1,\n"
    "      \"days\": [\n"
    "        {\n"
    "          \"day_of_week\": 1,\n"
    "          \"exercises\": [\n"
    "            {\n"
    "              \"name\": \"exercise name 1\",\n"
    "              \"muscle_group\": \"muscle group\",\n"
    "              \"equipment\": \"equipment or null\",\n"
    "              \"position\": 1,\n"
    "              \"notes\": null,\n"
    "              \"planned_sets\": [\n"
    "                { \"set_number\": 1, \"reps\": 8, \"weight\": null, \"rpe\": null, \"rest_seconds\": 90 },\n"
    "                { \"set_number\": 2, \"reps\": 8, \"weight\": null, \"rpe\": null, \"rest_seconds\": 90 }\n"
    "              ]\n"
    "            }\n"
    "          ]\n"
    "        }\n"
    "      ]\n"
    "    }\n"
    "  ]\n"
    "}\n\n"
    "STRICT RULES: Do not add or reorder keys; do not wrap the JSON in markdown; do not include backticks; return only the JSON object."
)


def build_user_prompt(*, owner_user_id: int, title: str, description: str, experience: str, days_per_week: int, equipment: str, priority: str) -> str:
    header = (
        "Generate a weekly training program and return STRICTLY AND ONLY a valid JSON object matching the SCHEMA and KEY ORDER below. "
        "No markdown, no code fences, no comments, no extra keys, no explanations. Use null where data is missing. Keep exact key names and order. "
        "Always start with '{' and end with '}'.\n\n"
        "USER INPUT:\n"
        f"- owner_user_id: {owner_user_id}\n"
        f"- title: {title}\n"
        f"- description: {description}\n"
        f"- experience: {experience} (novice|intermediate|advanced)\n"
        f"- days_per_week: {days_per_week}\n"
        f"- equipment_available: {equipment}\n"
        f"- priority: {priority}\n\n"
        "CONTENT RULES (apply silently; do NOT mention them):\n"
        "- Weekly volume (hard sets 0–3 RIR): novice 8–12; intermediate 10–16; advanced 12–20; priority muscles +20–30%; per session ≤10 sets.\n"
        "- Frequency: 2–4 touches/wk per priority muscle; align with days_per_week.\n"
        "- Reps: compounds 6–10; hypertrophy 8–15; isolation 12–20+. Rest: compounds 120–180s; isolation ≥90s; Week 1 RPE partially null.\n"
        "- Use concrete muscle_group (chest, shoulders, back, quads, hamstrings, glutes, biceps, triceps, calves, rear delts, etc.).\n"
        "- Use concrete equipment (barbell, dumbbell, machine, cable, bodyweight, smith, etc.) or null.\n"
        "- EXERCISE COUNT STRICT RULE: if days_per_week = 3 → 7–8 exercises/day; if days_per_week = 4 → 6–7; if days_per_week = 5 → 5–6.\n"
        "- Each exercise: 2–5 working sets depending on experience (novice 2–3; intermediate 3–4; advanced 4–5).\n\n"
    )
    return header + SCHEMA_BLOCK





def _parse_json_strict(content: str) -> Dict[str, Any]:
    import json
    # Try direct parse
    try:
        return json.loads(content)
    except Exception:
        pass
    s = content.strip()
    # Strip markdown code fences
    if s.startswith("```") and s.endswith("```"):
        lines = s.splitlines()
        s = "\n".join(lines[1:-1]).strip()
    # Slice between first '{' and last '}'
    if "{" in s and "}" in s:
        try:
            start = s.find("{")
            end = s.rfind("}") + 1
            return json.loads(s[start:end])
        except Exception:
            pass
    # Last resort: strip BOM/whitespace
    try:
        return json.loads(s.lstrip("\ufeff\n\r\t "))
    except Exception as e:
        preview = content
        try:
            preview = content[:500]
        except Exception:
            pass
        raise RuntimeError(f"Failed to parse JSON from OpenAI: {e}; raw: {preview}")


def generate_weekly_program(
    *,
    owner_user_id: int,
    title: str,
    description: Optional[str],
    experience: str,
    days_per_week: int,
    equipment: List[str],
    priority: Optional[str],
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)

    user_prompt = build_user_prompt(
        owner_user_id=owner_user_id,
        title=title,
        description=description or "",
        experience=experience,
        days_per_week=days_per_week,
        equipment=", ".join(equipment) if equipment else "none",
        priority=priority or "none",
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        max_tokens=7000,
    )

    content = response.choices[0].message.content or ""
    return _parse_json_strict(content)


def generate_weekly_program_raw(
    *,
    owner_user_id: int,
    title: str,
    description: Optional[str],
    experience: str,
    days_per_week: int,
    equipment: List[str],
    priority: Optional[str],
    model: str = "gpt-4o-mini",
) -> str:
    """Return raw string content from the model without parsing to JSON."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)

    user_prompt = build_user_prompt(
        owner_user_id=owner_user_id,
        title=title,
        description=description or "",
        experience=experience,
        days_per_week=days_per_week,
        equipment=", ".join(equipment) if equipment else "none",
        priority=priority or "none",
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        max_tokens=7000,
    )

    content = response.choices[0].message.content or ""
    return content


