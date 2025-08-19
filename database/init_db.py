"""
Initialize SQLite database with comprehensive workout tracking schema:
- programs: workout programs
- training_days: days within programs
- exercises: exercise catalog
- day_exercises: exercises in each training day
- sets: sets for each exercise
- reps: individual reps within sets

Run this file directly to (re)create the database schema.
"""

from pathlib import Path
import sqlite3


def get_db_path() -> Path:
    return Path(__file__).resolve().parent / "workout.db"


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.cursor()

        # Включаем контроль внешних ключей
        cur.execute("PRAGMA foreign_keys = ON;")

        # Drop existing tables if they exist (for clean recreation)
        cur.executescript("""
        DROP TABLE IF EXISTS reps;
        DROP TABLE IF EXISTS sets;
        DROP TABLE IF EXISTS day_exercises;
        DROP TABLE IF EXISTS training_days;
        DROP TABLE IF EXISTS weeks;
        DROP TABLE IF EXISTS program_cycles;
        DROP TABLE IF EXISTS exercises;
        DROP TABLE IF EXISTS programs;
        """)

        # ===== Справочники / верхний уровень =====
        cur.execute("""
        CREATE TABLE programs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            days_per_week  INTEGER NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE program_cycles (
            id         INTEGER PRIMARY KEY,
            program_id INTEGER NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
            cycle_no   INTEGER NOT NULL,                  -- 1,2,3...
            started_at TEXT,
            UNIQUE(program_id, cycle_no)                  -- одна программа: уникальный номер цикла
        );
        """)

        cur.execute("""
        CREATE TABLE weeks (
            id        INTEGER PRIMARY KEY,
            cycle_id  INTEGER NOT NULL REFERENCES program_cycles(id) ON DELETE CASCADE,
            week_no   INTEGER NOT NULL,                   -- 1..N
            UNIQUE(cycle_id, week_no)                     -- Week 1 может повторяться в новом цикле
        );
        """)

        cur.execute("""
        CREATE TABLE exercises (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            equipment   TEXT NOT NULL,
            target_muscle TEXT NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE training_days (
            id        INTEGER PRIMARY KEY,
            week_id   INTEGER NOT NULL REFERENCES weeks(id) ON DELETE CASCADE,
            name      TEXT,
            day_order INTEGER NOT NULL,
            UNIQUE(week_id, day_order)
        );
        """)

        # Связка: какие упражнения входят в конкретный тренировочный день
        cur.execute("""
        CREATE TABLE day_exercises (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            training_day_id INTEGER NOT NULL REFERENCES training_days(id) ON DELETE CASCADE,
            exercise_id     INTEGER NOT NULL REFERENCES exercises(id),
            ex_order        INTEGER NOT NULL,
            UNIQUE(training_day_id, ex_order)
        );
        """)

        # ===== Низкий уровень: SETS -> REPS =====
        cur.execute("""
        CREATE TABLE sets (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            day_exercise_id INTEGER NOT NULL REFERENCES day_exercises(id) ON DELETE CASCADE,
            set_order       INTEGER NOT NULL,
            target_weight   REAL, 
            notes           TEXT,
            rpe             REAL, 
            rep             INTEGER,
            weight          REAL,
            UNIQUE(day_exercise_id, set_order)
        );
        """)

        # ===== Индексы под частые запросы =====
        cur.executescript("""
        CREATE INDEX idx_cycles_program ON program_cycles(program_id);
        CREATE INDEX idx_weeks_cycle    ON weeks(cycle_id);
        CREATE INDEX idx_days_week      ON training_days(week_id);
        CREATE INDEX idx_dayex_day      ON day_exercises(training_day_id);
        CREATE INDEX idx_sets_dayex     ON sets(day_exercise_id);
        """)

        conn.commit()


if __name__ == "__main__":
    init_db(get_db_path())
    print(f"Initialized comprehensive workout tracking DB at {get_db_path()}")


