"""
Repository layer for the Program ↔ Workout schema. CRUD only, no business logic.
Classes: UserRepo, ExerciseRepo, ProgramRepo, WorkoutRepo
"""

from typing import Optional, List, Dict, Any, Tuple
from . import db


class UserRepo:
    @staticmethod
    def create(email: str, password_hash: str) -> int:
        with db.get_connection() as conn, db.transaction(conn) as cur:
            cur.execute(
                "INSERT INTO users(email, password_hash) VALUES(?, ?)",
                (email, password_hash),
            )
            return cur.lastrowid

    @staticmethod
    def get_by_email(email: str) -> Optional[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None


class ExerciseRepo:
    @staticmethod
    def create(owner_user_id: Optional[int], name: str, muscle_group: str, equipment: Optional[str], is_global: int) -> int:
        with db.get_connection() as conn, db.transaction(conn) as cur:
            cur.execute(
                """
                INSERT INTO exercise(owner_user_id, name, muscle_group, equipment, is_global)
                VALUES(?, ?, ?, ?, ?)
                """,
                (owner_user_id, name, muscle_group, equipment, is_global),
            )
            return cur.lastrowid

    @staticmethod
    def get(exercise_id: int) -> Optional[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM exercise WHERE id = ?", (exercise_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_for_user(user_id: Optional[int]) -> List[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            if user_id is None:
                cur.execute("SELECT * FROM exercise WHERE is_global = 1 ORDER BY name")
            else:
                cur.execute(
                    "SELECT * FROM exercise WHERE is_global = 1 OR owner_user_id = ? ORDER BY name",
                    (user_id,),
                )
            return [dict(r) for r in cur.fetchall()]


class ProgramRepo:
    @staticmethod
    def create(owner_user_id: int, title: str, description: Optional[str]) -> int:
        with db.get_connection() as conn, db.transaction(conn) as cur:
            cur.execute(
                "INSERT INTO program(owner_user_id, title, description) VALUES(?, ?, ?)",
                (owner_user_id, title, description),
            )
            return cur.lastrowid

    @staticmethod
    def get(program_id: int) -> Optional[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM program WHERE id = ?", (program_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def create_week(program_id: int, week_number: int) -> int:
        with db.get_connection() as conn, db.transaction(conn) as cur:
            cur.execute(
                "INSERT INTO program_week(program_id, week_number) VALUES(?, ?)",
                (program_id, week_number),
            )
            return cur.lastrowid

    @staticmethod
    def create_day(program_week_id: int, day_of_week: int) -> int:
        with db.get_connection() as conn, db.transaction(conn) as cur:
            cur.execute(
                "INSERT INTO program_day(program_week_id, day_of_week) VALUES(?, ?)",
                (program_week_id, day_of_week),
            )
            return cur.lastrowid

    @staticmethod
    def add_day_exercise(program_day_id: int, exercise_id: int, position: int, notes: Optional[str]) -> int:
        with db.get_connection() as conn, db.transaction(conn) as cur:
            cur.execute(
                """
                INSERT INTO program_day_exercise(program_day_id, exercise_id, position, notes)
                VALUES(?, ?, ?, ?)
                """,
                (program_day_id, exercise_id, position, notes),
            )
            return cur.lastrowid

    @staticmethod
    def add_planned_set(program_day_exercise_id: int, set_number: int, reps: int, weight: Optional[float], rpe: Optional[float], rest_seconds: Optional[int]) -> int:
        with db.get_connection() as conn, db.transaction(conn) as cur:
            cur.execute(
                """
                INSERT INTO planned_set(program_day_exercise_id, set_number, reps, weight, rpe, rest_seconds)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (program_day_exercise_id, set_number, reps, weight, rpe, rest_seconds),
            )
            return cur.lastrowid

    @staticmethod
    def get_week(program_id: int, week_number: int) -> Optional[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM program_week WHERE program_id = ? AND week_number = ?",
                (program_id, week_number),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_day(program_week_id: int, day_of_week: int) -> Optional[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM program_day WHERE program_week_id = ? AND day_of_week = ?",
                (program_week_id, day_of_week),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_day_exercise(program_day_id: int, position: int) -> Optional[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM program_day_exercise WHERE program_day_id = ? AND position = ?",
                (program_day_id, position),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_day_exercises(program_day_id: int) -> List[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM program_day_exercise WHERE program_day_id = ? ORDER BY position",
                (program_day_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def list_planned_sets(program_day_exercise_id: int) -> List[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM planned_set WHERE program_day_exercise_id = ? ORDER BY set_number",
                (program_day_exercise_id,),
            )
            return [dict(r) for r in cur.fetchall()]


class WorkoutRepo:
    @staticmethod
    def start(owner_user_id: int, program_day_id: int, started_at: Optional[str]) -> int:
        with db.get_connection() as conn, db.transaction(conn) as cur:
            cur.execute(
                "INSERT INTO workout(owner_user_id, program_day_id, started_at) VALUES(?, ?, COALESCE(?, CURRENT_TIMESTAMP))",
                (owner_user_id, program_day_id, started_at),
            )
            return cur.lastrowid

    @staticmethod
    def finish(workout_id: int, finished_at: Optional[str], notes: Optional[str]) -> None:
        with db.get_connection() as conn, db.transaction(conn) as cur:
            cur.execute(
                "UPDATE workout SET finished_at = COALESCE(?, CURRENT_TIMESTAMP), notes = COALESCE(?, notes) WHERE id = ?",
                (finished_at, notes, workout_id),
            )

    @staticmethod
    def ensure_workout_exercise(workout_id: int, program_day_exercise_id: int, position: int) -> int:
        with db.get_connection() as conn, db.transaction(conn) as cur:
            cur.execute(
                "SELECT id FROM workout_exercise WHERE workout_id = ? AND program_day_exercise_id = ?",
                (workout_id, program_day_exercise_id),
            )
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute(
                "INSERT INTO workout_exercise(workout_id, program_day_exercise_id, position) VALUES(?, ?, ?)",
                (workout_id, program_day_exercise_id, position),
            )
            return cur.lastrowid

    @staticmethod
    def add_workout_set(workout_exercise_id: int, planned_set_id: int, set_number: int, reps: int, weight: Optional[float], rpe: Optional[float], rest_seconds: Optional[int]) -> int:
        with db.get_connection() as conn, db.transaction(conn) as cur:
            cur.execute(
                """
                INSERT INTO workout_set(workout_exercise_id, planned_set_id, set_number, reps, weight, rpe, rest_seconds)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (workout_exercise_id, planned_set_id, set_number, reps, weight, rpe, rest_seconds),
            )
            return cur.lastrowid

    @staticmethod
    def get_workout(workout_id: int) -> Optional[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM workout WHERE id = ?", (workout_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def count_actual_sets_for_wex(workout_exercise_id: int) -> int:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM workout_set WHERE workout_exercise_id = ?", (workout_exercise_id,))
            return int(cur.fetchone()[0])

    @staticmethod
    def planned_count_for_pde(program_day_exercise_id: int) -> int:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM planned_set WHERE program_day_exercise_id = ?", (program_day_exercise_id,))
            return int(cur.fetchone()[0])

    @staticmethod
    def get_planned_set(planned_set_id: int) -> Optional[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM planned_set WHERE id = ?", (planned_set_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_workout_exercise(wex_id: int) -> Optional[Dict[str, Any]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM workout_exercise WHERE id = ?", (wex_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    # Reports (SQL only)
    @staticmethod
    def report_planned_sets_for_week(program_id: int, week_number: int) -> int:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(ps.id)
                FROM program_week pw
                JOIN program_day pd ON pd.program_week_id = pw.id
                JOIN program_day_exercise pde ON pde.program_day_id = pd.id
                JOIN planned_set ps ON ps.program_day_exercise_id = pde.id
                WHERE pw.program_id = ? AND pw.week_number = ?
                """,
                (program_id, week_number),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0

    @staticmethod
    def report_actual_sets_for_week(program_id: int, week_number: int) -> int:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(ws.id)
                FROM program_week pw
                JOIN program_day pd ON pd.program_week_id = pw.id
                JOIN workout w ON w.program_day_id = pd.id
                LEFT JOIN workout_exercise wex ON wex.workout_id = w.id
                LEFT JOIN workout_set ws ON ws.workout_exercise_id = wex.id
                WHERE pw.program_id = ? AND pw.week_number = ?
                """,
                (program_id, week_number),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0

    @staticmethod
    def report_sets_by_muscle_group(program_id: int, week_number: int) -> List[Tuple[str, int]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT e.muscle_group, COUNT(ws.id) AS cnt
                FROM program_week pw
                JOIN program_day pd ON pd.program_week_id = pw.id
                JOIN program_day_exercise pde ON pde.program_day_id = pd.id
                JOIN exercise e ON e.id = pde.exercise_id
                JOIN workout w ON w.program_day_id = pd.id
                JOIN workout_exercise wex ON wex.program_day_exercise_id = pde.id
                JOIN workout_set ws ON ws.workout_exercise_id = wex.id
                WHERE pw.program_id = ? AND pw.week_number = ?
                GROUP BY e.muscle_group
                ORDER BY e.muscle_group
                """,
                (program_id, week_number),
            )
            return [(row[0], int(row[1])) for row in cur.fetchall()]

    @staticmethod
    def report_progress_for_exercise(program_id: int, exercise_id: int) -> List[Tuple[int, float, float]]:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT pw.week_number, AVG(ws.weight) AS avg_weight, AVG(ws.reps) AS avg_reps
                FROM program_day_exercise pde
                JOIN program_day pd ON pd.id = pde.program_day_id
                JOIN program_week pw ON pw.id = pd.program_week_id
                JOIN workout_exercise wex ON wex.program_day_exercise_id = pde.id
                JOIN workout_set ws ON ws.workout_exercise_id = wex.id
                WHERE pde.exercise_id = ? AND pw.program_id = ?
                GROUP BY pw.week_number
                ORDER BY pw.week_number
                """,
                (exercise_id, program_id),
            )
            return [(int(row[0]), float(row[1]) if row[1] is not None else 0.0, float(row[2]) if row[2] is not None else 0.0) for row in cur.fetchall()]

