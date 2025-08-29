"""
SQLite connection helpers and schema integrity utilities for Program ↔ Workout schema.
No destructive actions; only ensure missing indexes and triggers exist.
"""

from pathlib import Path
import sqlite3
from contextlib import contextmanager
from typing import Generator, Iterable


# Database file path
DB_PATH = Path(__file__).resolve().parent.parent / "database" / "workout.db"


def get_db_path() -> Path:
    return DB_PATH


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterable[sqlite3.Cursor]:
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _execute_many(cur: sqlite3.Cursor, statements: Iterable[str]) -> None:
    for stmt in statements:
        if not stmt:
            continue
        cur.execute(stmt)


def ensure_schema_integrity() -> None:
    """
    Ensure required indexes and triggers exist for the Program ↔ Workout schema.
    - Creates idempotent indexes on FK/join columns
    - Creates BEFORE INSERT/UPDATE triggers on workout_set enforcing invariants A/B/C
    """
    with get_connection() as conn, transaction(conn) as cur:
        # Indexes (idempotent)
        _execute_many(cur, [
            # Program hierarchy
            "CREATE INDEX IF NOT EXISTS program_owner_idx ON program(owner_user_id)",
            "CREATE INDEX IF NOT EXISTS program_week_program_idx ON program_week(program_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS program_week_uq ON program_week(program_id, week_number)",
            "CREATE INDEX IF NOT EXISTS program_day_week_idx ON program_day(program_week_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS program_day_uq ON program_day(program_week_id, day_of_week)",
            "CREATE INDEX IF NOT EXISTS program_day_exercise_day_idx ON program_day_exercise(program_day_id)",
            "CREATE INDEX IF NOT EXISTS program_day_exercise_ex_idx ON program_day_exercise(exercise_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS program_day_exercise_uq ON program_day_exercise(program_day_id, position)",
            "CREATE INDEX IF NOT EXISTS planned_set_pde_idx ON planned_set(program_day_exercise_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS planned_set_uq ON planned_set(program_day_exercise_id, set_number)",
            # Workouts
            "CREATE INDEX IF NOT EXISTS workout_owner_idx ON workout(owner_user_id)",
            "CREATE INDEX IF NOT EXISTS workout_program_day_idx ON workout(program_day_id)",
            "CREATE INDEX IF NOT EXISTS workout_exercise_wk_idx ON workout_exercise(workout_id)",
            "CREATE INDEX IF NOT EXISTS workout_exercise_pde_idx ON workout_exercise(program_day_exercise_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS workout_exercise_uq ON workout_exercise(workout_id, position)",
            "CREATE INDEX IF NOT EXISTS workout_set_wex_idx ON workout_set(workout_exercise_id)",
            "CREATE INDEX IF NOT EXISTS workout_set_planned_idx ON workout_set(planned_set_id)",
        ])

        # Triggers: create only if not already present
        cur.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        existing_triggers = {row[0] for row in cur.fetchall()}

        if "trg_workout_set_before_ins" not in existing_triggers:
            cur.executescript(
                """
                CREATE TRIGGER trg_workout_set_before_ins
                BEFORE INSERT ON workout_set
                FOR EACH ROW
                BEGIN
                  -- A) set_number equals planned
                  SELECT CASE
                    WHEN NEW.set_number <> (
                      SELECT ps.set_number FROM planned_set ps WHERE ps.id = NEW.planned_set_id
                    ) THEN RAISE(ABORT, 'workout_set.set_number must equal planned_set.set_number')
                  END;

                  -- B) workout_exercise.program_day_exercise_id equals planned_set.program_day_exercise_id
                  SELECT CASE
                    WHEN (
                      SELECT wex.program_day_exercise_id FROM workout_exercise wex WHERE wex.id = NEW.workout_exercise_id
                    ) <> (
                      SELECT ps.program_day_exercise_id FROM planned_set ps WHERE ps.id = NEW.planned_set_id
                    ) THEN RAISE(ABORT, 'workout_exercise.program_day_exercise_id must equal planned_set.program_day_exercise_id')
                  END;

                  -- C) do not exceed planned sets count
                  SELECT CASE
                    WHEN (
                      (SELECT COUNT(*) FROM workout_set ws WHERE ws.workout_exercise_id = NEW.workout_exercise_id) + 1
                    ) > (
                      SELECT COUNT(*) FROM planned_set ps
                      WHERE ps.program_day_exercise_id = (
                        SELECT wex.program_day_exercise_id FROM workout_exercise wex WHERE wex.id = NEW.workout_exercise_id
                      )
                    ) THEN RAISE(ABORT, 'Actual workout sets cannot exceed planned sets for this exercise instance')
                  END;
                END;
                """
            )

        if "trg_workout_set_before_upd" not in existing_triggers:
            cur.executescript(
                """
                CREATE TRIGGER trg_workout_set_before_upd
                BEFORE UPDATE OF planned_set_id, workout_exercise_id, set_number ON workout_set
                FOR EACH ROW
                BEGIN
                  -- A) set_number equals planned
                  SELECT CASE
                    WHEN NEW.set_number <> (
                      SELECT ps.set_number FROM planned_set ps WHERE ps.id = NEW.planned_set_id
                    ) THEN RAISE(ABORT, 'workout_set.set_number must equal planned_set.set_number')
                  END;

                  -- B) workout_exercise.program_day_exercise_id equals planned_set.program_day_exercise_id
                  SELECT CASE
                    WHEN (
                      SELECT wex.program_day_exercise_id FROM workout_exercise wex WHERE wex.id = NEW.workout_exercise_id
                    ) <> (
                      SELECT ps.program_day_exercise_id FROM planned_set ps WHERE ps.id = NEW.planned_set_id
                    ) THEN RAISE(ABORT, 'workout_exercise.program_day_exercise_id must equal planned_set.program_day_exercise_id')
                  END;

                  -- C) do not exceed planned sets count (exclude OLD row)
                  SELECT CASE
                    WHEN (
                      (SELECT COUNT(*) FROM workout_set ws WHERE ws.workout_exercise_id = NEW.workout_exercise_id AND ws.id <> OLD.id) + 1
                    ) > (
                      SELECT COUNT(*) FROM planned_set ps
                      WHERE ps.program_day_exercise_id = (
                        SELECT wex.program_day_exercise_id FROM workout_exercise wex WHERE wex.id = NEW.workout_exercise_id
                      )
                    ) THEN RAISE(ABORT, 'Actual workout sets cannot exceed planned sets for this exercise instance')
                  END;
                END;
                """
            )


if __name__ == "__main__":
    ensure_schema_integrity()
    print(f"Ensured schema integrity at {DB_PATH}")
