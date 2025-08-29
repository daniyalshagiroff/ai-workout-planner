"""
Initialize SQLite database with comprehensive workout tracking schema:
-programs: workout programs
-training_days: days within programs
-exercises: exercise catalog
-day_exercises: exercises in each training day
-sets: sets for each exercise
-reps: individual reps within sets

Run this file directly to (re)create the database schema.
"""

from pathlib import Path
import sqlite3
import os


def get_db_path() -> Path:
    return Path(__file__).resolve().parent / "workout.db"


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.cursor()

        # Включаем контроль внешних ключей
        cur.execute("PRAGMA foreign_keys = ON;")

        # Выполнить миграции из папки migrations в порядке по имени файла
        migrations_dir = Path(__file__).resolve().parent / "migrations"
        files = sorted([p for p in migrations_dir.glob("*.sql")])

        for sql_file in files:
            with open(sql_file, "r", encoding="utf-8") as f:
                sql = f.read()
            cur.executescript(sql)

        conn.commit()


if __name__ == "__main__":
    init_db(get_db_path())
    print(f"Initialized comprehensive workout tracking DB at {get_db_path()}")


