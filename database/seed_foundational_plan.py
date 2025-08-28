"""
Seed a 6-week FOUNDATIONAL PLAN into the SQLite DB without modifying app code.

Usage:
  python database/seed_foundational_plan.py
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure we can import from app
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from app import db  # type: ignore
from app.repo import ExerciseRepo, ProgramRepo, UserRepo  # type: ignore
from app.security import hash_password  # type: ignore


def ensure_schema() -> None:
    try:
        from app.db import ensure_schema_integrity  # type: ignore
        ensure_schema_integrity()
    except Exception:
        # If not available for any reason, continue; tables should already exist via migrations
        pass


def find_global_exercise_by_name(name: str) -> Optional[Dict[str, Any]]:
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM exercise WHERE lower(name) = lower(?) AND is_global = 1",
            (name,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def ensure_global_exercise(name: str, muscle_group: str, equipment: Optional[str]) -> Dict[str, Any]:
    existing = find_global_exercise_by_name(name)
    if existing:
        return existing
    ex_id = ExerciseRepo.create(None, name, muscle_group, equipment, 1)
    ex = ExerciseRepo.get(ex_id)
    if not ex:
        raise RuntimeError(f"Failed to create exercise: {name}")
    return ex


def find_program_by_title(title: str) -> Optional[Dict[str, Any]]:
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM program WHERE title = ?", (title,))
        row = cur.fetchone()
        return dict(row) if row else None


def seed_foundational_plan() -> Dict[str, Any]:
    ensure_schema()

    # Ensure owner user for the program (FK required)
    owner_email = "foundational@local"
    user = UserRepo.get_by_email(owner_email)
    if not user:
        user_id = UserRepo.create(owner_email, hash_password("foundation"))
        user = UserRepo.get_by_id(user_id)
    owner_user_id = user["id"]

    # Ensure foundational global exercises
    exercises = {
        "barbell squat": ensure_global_exercise("barbell squat", "quads", "barbell"),
        "bench press": ensure_global_exercise("bench press", "chest", "barbell"),
        "deadlift": ensure_global_exercise("deadlift", "back", "barbell"),
        "overhead press": ensure_global_exercise("overhead press", "shoulders", "barbell"),
        "barbell row": ensure_global_exercise("barbell row", "back", "barbell"),
        "lat pulldown": ensure_global_exercise("lat pulldown", "lats", "machine"),
        "dumbbell curl": ensure_global_exercise("dumbbell curl", "arms", "dumbbell"),
        "triceps pushdown": ensure_global_exercise("triceps pushdown", "triceps", "machine"),
        "plank": ensure_global_exercise("plank", "core", "bodyweight"),
    }

    # Create program with valid owner_user_id (FK)
    title = "FOUNDATIONAL PLAN"
    description = "6-week foundational strength/hypertrophy base"
    program = find_program_by_title(title)
    if not program:
        prog_id = ProgramRepo.create(owner_user_id=owner_user_id, title=title, description=description)
        program = ProgramRepo.get(prog_id)
    if not program:
        raise RuntimeError("Failed to create or load foundational program")

    def add_day(week_number: int, day_of_week: int, day_plan: List[Dict[str, Any]]):
        week = ProgramRepo.get_week(program["id"], week_number)
        if not week:
            ProgramRepo.create_week(program["id"], week_number)
            week = ProgramRepo.get_week(program["id"], week_number)
        day = ProgramRepo.get_day(week["id"], day_of_week)
        if not day:
            ProgramRepo.create_day(week["id"], day_of_week)
            day = ProgramRepo.get_day(week["id"], day_of_week)
        # Add exercises in order and planned sets if not present
        existing = { de["position"]: de for de in ProgramRepo.list_day_exercises(day["id"]) }
        for pos, item in enumerate(day_plan, start=1):
            ex = exercises[item["name"]]
            pde = existing.get(pos)
            if not pde:
                pde_id = ProgramRepo.add_day_exercise(day["id"], ex["id"], pos, None)
            else:
                pde_id = pde["id"]
            # planned sets
            planned = ProgramRepo.list_planned_sets(pde_id)
            if not planned:
                total_sets = item["sets"]
                reps = item["reps"]
                weight = item.get("weight")
                for setn in range(1, total_sets + 1):
                    ProgramRepo.add_planned_set(pde_id, setn, reps, weight, None, item.get("rest"))

    day1 = [
        {"name": "barbell squat", "sets": 5, "reps": 5, "weight": None, "rest": 120},
        {"name": "bench press", "sets": 5, "reps": 5, "weight": None, "rest": 120},
        {"name": "barbell row", "sets": 3, "reps": 8, "weight": None, "rest": 90},
        {"name": "dumbbell curl", "sets": 3, "reps": 10, "weight": None, "rest": 60},
    ]
    day2 = [
        {"name": "deadlift", "sets": 3, "reps": 5, "weight": None, "rest": 150},
        {"name": "overhead press", "sets": 5, "reps": 5, "weight": None, "rest": 120},
        {"name": "lat pulldown", "sets": 3, "reps": 10, "weight": None, "rest": 90},
        {"name": "triceps pushdown", "sets": 3, "reps": 12, "weight": None, "rest": 60},
    ]
    day3 = [
        {"name": "barbell squat", "sets": 3, "reps": 5, "weight": None, "rest": 120},
        {"name": "bench press", "sets": 3, "reps": 5, "weight": None, "rest": 120},
        {"name": "lat pulldown", "sets": 3, "reps": 10, "weight": None, "rest": 90},
        {"name": "plank", "sets": 3, "reps": 40, "weight": None, "rest": 60},
    ]

    for wk in range(1, 7):
        add_day(wk, 1, day1)
        add_day(wk, 3, day2)
        add_day(wk, 5, day3)

    return {"program_id": program["id"], "title": program["title"], "weeks": 6}


if __name__ == "__main__":
    result = seed_foundational_plan()
    print(f"Seeded: {result}")


