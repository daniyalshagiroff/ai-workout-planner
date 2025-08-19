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
                [EXERCISE] TEXT NOT NULL,
                [SETS] INTEGER,
                [REPS] INTEGER
            )
            """
        )
        conn.commit()


if __name__ == "__main__":
    init_db(get_db_path())
    print(f"Initialized DB at {get_db_path()}")


