"""
Export the latest (by started_at) "Full Body" program, its first week days and exercises to a JSON
file that the frontend can consume (frontend/program-foundational.json).
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "workout.db"
FRONTEND_JSON = Path(__file__).resolve().parent.parent / "frontend" / "program-foundational.json"


def main() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON;")

        # Find Full Body program
        cur.execute("SELECT id, name, days_per_week FROM programs WHERE name = ?", ("Full Body",))
        program = cur.fetchone()
        if not program:
            raise SystemExit("Program 'Full Body' not found. Seed the DB first.")

        # Latest cycle by started_at (text ISO format)
        cur.execute(
            """
            SELECT id, started_at FROM program_cycles
            WHERE program_id = ?
            ORDER BY datetime(started_at) DESC
            LIMIT 1
            """,
            (program["id"],),
        )
        cycle = cur.fetchone()
        if not cycle:
            raise SystemExit("No cycle found for program.")

        # Week 1 in that cycle
        cur.execute(
            "SELECT id, week_no FROM weeks WHERE cycle_id = ? AND week_no = 1",
            (cycle["id"],),
        )
        week = cur.fetchone()
        if not week:
            raise SystemExit("Week 1 not found. Seed the DB first.")

        # Days for week ordered
        cur.execute(
            """
            SELECT id, name, COALESCE(emphasis, '') AS emphasis, day_order
            FROM training_days
            WHERE week_id = ?
            ORDER BY day_order ASC
            """,
            (week["id"],),
        )
        days_rows = cur.fetchall()

        days_output = []
        for d in days_rows:
            # Fetch exercises in order
            cur.execute(
                """
                SELECT e.name
                FROM day_exercises de
                JOIN exercises e ON e.id = de.exercise_id
                WHERE de.training_day_id = ?
                ORDER BY de.ex_order ASC
                """,
                (d["id"],),
            )
            ex_rows = cur.fetchall()
            days_output.append({
                "label": d["name"] or f"Day {d['day_order']}",
                "emphasis": d["emphasis"],
                "exercises": [r["name"] for r in ex_rows],
            })

        payload = {
            "program": {"name": program["name"], "days_per_week": program["days_per_week"]},
            "week": {"week_no": 1},
            "days": days_output,
        }

        FRONTEND_JSON.parent.mkdir(parents=True, exist_ok=True)
        with FRONTEND_JSON.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        print(f"Exported to {FRONTEND_JSON}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


