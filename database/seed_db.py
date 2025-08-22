"""
Seed the SQLite database with an initial Full Body program and related entities.

Data inserted:
- programs: "Full Body" with days_per_week = 3
- program_cycles: cycle_no = 1, started_at = now
- weeks: week_no = 1
- exercises: pulldown, bench press, barbell squat, biceps curls, triceps pushdown
- training_days: 3 days (Full Body) with emphasis chest, back, legs and day_orders 1..3
- day_exercises: all exercises included in each training day in logical order
- sets: 2 sets per exercise with placeholder targets and RPE; rep left NULL
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Dict, List, Tuple


DB_PATH = Path(__file__).resolve().parent / "workout.db"


@dataclass(frozen=True)
class ExerciseSeed:
    name: str
    equipment: str
    target_muscle: str
    default_target_weight: float | None


EXERCISES: List[ExerciseSeed] = [
    ExerciseSeed("pulldown", "cable", "lats", 40.0),
    ExerciseSeed("bench press", "barbell", "chest", 60.0),
    ExerciseSeed("barbell squat", "barbell", "quads", 80.0),
    ExerciseSeed("biceps curls", "dumbbells", "biceps", 12.5),
    ExerciseSeed("triceps pushdown", "cable", "triceps", 25.0),
]


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_or_create_program(conn: sqlite3.Connection, name: str, days_per_week: int) -> int:
    cur = conn.execute("SELECT id FROM programs WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return int(row[0])
    cur = conn.execute(
        "INSERT INTO programs(name, days_per_week) VALUES(?, ?)",
        (name, days_per_week),
    )
    return int(cur.lastrowid)


def get_or_create_cycle(conn: sqlite3.Connection, program_id: int, cycle_no: int, started_at: str) -> int:
    cur = conn.execute(
        "SELECT id FROM program_cycles WHERE program_id = ? AND cycle_no = ?",
        (program_id, cycle_no),
    )
    row = cur.fetchone()
    if row:
        return int(row[0])
    cur = conn.execute(
        "INSERT INTO program_cycles(program_id, cycle_no, started_at) VALUES(?, ?, ?)",
        (program_id, cycle_no, started_at),
    )
    return int(cur.lastrowid)


def get_or_create_week(conn: sqlite3.Connection, cycle_id: int, week_no: int) -> int:
    cur = conn.execute(
        "SELECT id FROM weeks WHERE cycle_id = ? AND week_no = ?",
        (cycle_id, week_no),
    )
    row = cur.fetchone()
    if row:
        return int(row[0])
    cur = conn.execute(
        "INSERT INTO weeks(cycle_id, week_no) VALUES(?, ?)",
        (cycle_id, week_no),
    )
    return int(cur.lastrowid)


def get_or_create_exercises(conn: sqlite3.Connection, seeds: List[ExerciseSeed]) -> Dict[str, int]:
    name_to_id: Dict[str, int] = {}
    for seed in seeds:
        cur = conn.execute("SELECT id FROM exercises WHERE name = ?", (seed.name,))
        row = cur.fetchone()
        if row:
            name_to_id[seed.name] = int(row[0])
            continue
        cur = conn.execute(
            "INSERT INTO exercises(name, equipment, target_muscle) VALUES(?, ?, ?)",
            (seed.name, seed.equipment, seed.target_muscle),
        )
        name_to_id[seed.name] = int(cur.lastrowid)
    return name_to_id


def create_training_day(
    conn: sqlite3.Connection,
    week_id: int,
    name: str,
    emphasis: str,
    day_order: int,
) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO training_days(week_id, name, emphasis, day_order) VALUES(?, ?, ?, ?)",
        (week_id, name, emphasis, day_order),
    )
    if cur.lastrowid:
        return int(cur.lastrowid)
    # fetch existing
    cur = conn.execute(
        "SELECT id FROM training_days WHERE week_id = ? AND day_order = ?",
        (week_id, day_order),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError("Failed to create or fetch training day")
    return int(row[0])


def add_day_exercises(
    conn: sqlite3.Connection,
    training_day_id: int,
    exercise_ids_in_order: List[int],
) -> List[int]:
    day_exercise_ids: List[int] = []
    for order_index, exercise_id in enumerate(exercise_ids_in_order, start=1):
        cur = conn.execute(
            "INSERT OR IGNORE INTO day_exercises(training_day_id, exercise_id, ex_order) VALUES(?, ?, ?)",
            (training_day_id, exercise_id, order_index),
        )
        if cur.lastrowid:
            day_exercise_ids.append(int(cur.lastrowid))
        else:
            cur2 = conn.execute(
                "SELECT id FROM day_exercises WHERE training_day_id = ? AND ex_order = ?",
                (training_day_id, order_index),
            )
            row = cur2.fetchone()
            if row:
                day_exercise_ids.append(int(row[0]))
    return day_exercise_ids


def add_sets_for_day_exercises(
    conn: sqlite3.Connection,
    day_exercise_ids_with_weights: List[Tuple[int, float | None]],
    sets_per_exercise: int = 2,
) -> None:
    for day_ex_id, target_weight in day_exercise_ids_with_weights:
        for set_order in range(1, sets_per_exercise + 1):
            conn.execute(
                """
                INSERT OR IGNORE INTO sets(
                    day_exercise_id, set_order, target_weight, notes, rpe, rep, weight
                ) VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    day_ex_id,
                    set_order,
                    target_weight,
                    "",
                    7.5,
                    None,
                    None,
                ),
            )


def main() -> None:
    conn = connect(DB_PATH)
    try:
        # Program → Cycle → Week
        program_id = get_or_create_program(conn, "Full Body", days_per_week=3)
        cycle_id = get_or_create_cycle(conn, program_id, cycle_no=1, started_at=datetime.now().isoformat())
        week_id = get_or_create_week(conn, cycle_id, week_no=1)

        # Exercises
        name_to_ex_id = get_or_create_exercises(conn, EXERCISES)

        # Define exercise orders for different emphases
        exercise_orders = {
            "chest": [
                name_to_ex_id["bench press"],      # 1. Chest first
                name_to_ex_id["barbell squat"],    # 2. Legs
                name_to_ex_id["pulldown"],         # 3. Back
                name_to_ex_id["triceps pushdown"], # 4. Triceps (chest accessory)
                name_to_ex_id["biceps curls"],     # 5. Biceps
            ],
            "back": [
                name_to_ex_id["pulldown"],         # 1. Back first
                name_to_ex_id["barbell squat"],    # 2. Legs
                name_to_ex_id["bench press"],      # 3. Chest
                name_to_ex_id["biceps curls"],     # 4. Biceps (back accessory)
                name_to_ex_id["triceps pushdown"], # 5. Triceps
            ],
            "legs": [
                name_to_ex_id["barbell squat"],    # 1. Legs first
                name_to_ex_id["bench press"],      # 2. Chest
                name_to_ex_id["pulldown"],         # 3. Back
                name_to_ex_id["biceps curls"],     # 4. Biceps
                name_to_ex_id["triceps pushdown"], # 5. Triceps
            ]
        }
        
        default_weights_map = {
            name_to_ex_id["barbell squat"]: 80.0,
            name_to_ex_id["bench press"]: 60.0,
            name_to_ex_id["pulldown"]: 40.0,
            name_to_ex_id["biceps curls"]: 12.5,
            name_to_ex_id["triceps pushdown"]: 25.0,
        }

        # Training days: 3 days with emphasis
        emphases = ["chest", "back", "legs"]

        for i, emphasis in enumerate(emphases, start=1):
            day_id = create_training_day(conn, week_id, name="Full Body", emphasis=emphasis, day_order=i)
            
            # Use the appropriate exercise order for this emphasis
            exercise_order = exercise_orders[emphasis]
            
            day_ex_ids = add_day_exercises(conn, day_id, exercise_order)
            day_ex_ids_with_weights = [(dx_id, default_weights_map.get(ex_id)) for dx_id, ex_id in zip(day_ex_ids, exercise_order)]
            add_sets_for_day_exercises(conn, day_ex_ids_with_weights, sets_per_exercise=2)

        conn.commit()
        print("Seed completed successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


