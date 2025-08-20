"""
Database connection and setup for SQLite workout tracking.
"""

from pathlib import Path
import sqlite3
from contextlib import contextmanager
from typing import Generator


# Database file path
DB_PATH = Path(__file__).resolve().parent.parent / "database" / "workout.db"


def get_db_path() -> Path:
    """Get the database file path."""
    return DB_PATH


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.
    
    Yields:
        sqlite3.Connection: Configured database connection
        
    Example:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM programs")
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    conn.execute("PRAGMA foreign_keys = ON;")
    
    try:
        yield conn
    finally:
        conn.close()


def init_database() -> None:
    """
    Initialize the database schema.
    Creates all tables if they don't exist.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with get_db_connection() as conn:
        cur = conn.cursor()

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

        # Create tables
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
            cycle_no   INTEGER NOT NULL,
            started_at TEXT,
            UNIQUE(program_id, cycle_no)
        );
        """)

        cur.execute("""
        CREATE TABLE weeks (
            id        INTEGER PRIMARY KEY,
            cycle_id  INTEGER NOT NULL REFERENCES program_cycles(id) ON DELETE CASCADE,
            week_no   INTEGER NOT NULL,
            UNIQUE(cycle_id, week_no)
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
            emphasis  TEXT,
            day_order INTEGER NOT NULL,
            UNIQUE(week_id, day_order)
        );
        """)

        cur.execute("""
        CREATE TABLE day_exercises (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            training_day_id INTEGER NOT NULL REFERENCES training_days(id) ON DELETE CASCADE,
            exercise_id     INTEGER NOT NULL REFERENCES exercises(id),
            ex_order        INTEGER NOT NULL,
            UNIQUE(training_day_id, ex_order)
        );
        """)

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

        # Create indexes
        cur.executescript("""
        CREATE INDEX idx_cycles_program ON program_cycles(program_id);
        CREATE INDEX idx_weeks_cycle    ON weeks(cycle_id);
        CREATE INDEX idx_days_week      ON training_days(week_id);
        CREATE INDEX idx_dayex_day      ON day_exercises(training_day_id);
        CREATE INDEX idx_sets_dayex     ON sets(day_exercise_id);
        """)

        conn.commit()


if __name__ == "__main__":
    init_database()
    print(f"Database initialized at {DB_PATH}")
