"""
Initialize SQLite database with a single table `workouts` containing three columns:
- упражнение (TEXT, NOT NULL)
- сеты (INTEGER)
- подходы (INTEGER)

Run this file directly to (re)create the table if it does not exist.
"""

from pathlib import Path
import sqlite3


def get_db_path() -> Path:
    return Path(__file__).resolve().parent / "workout.db"


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workouts (
                [упражнение] TEXT NOT NULL,
                [сеты] INTEGER,
                [подходы] INTEGER
            )
            """
        )
        conn.commit()


if __name__ == "__main__":
    init_db(get_db_path())
    print(f"Initialized DB at {get_db_path()}")


