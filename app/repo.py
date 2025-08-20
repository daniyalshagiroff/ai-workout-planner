"""
Repository layer for database operations.
Contains all SQL queries and data access logic.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from . import db


@dataclass
class Program:
    id: int
    name: str
    days_per_week: int


@dataclass
class ProgramCycle:
    id: int
    program_id: int
    cycle_no: int
    started_at: str


@dataclass
class Week:
    id: int
    cycle_id: int
    week_no: int


@dataclass
class Exercise:
    id: int
    name: str
    equipment: str
    target_muscle: str
    default_target_weight: Optional[float] = None


@dataclass
class TrainingDay:
    id: int
    week_id: int
    name: Optional[str]
    emphasis: Optional[str]
    day_order: int


@dataclass
class DayExercise:
    id: int
    training_day_id: int
    exercise_id: int
    ex_order: int


@dataclass
class Set:
    id: int
    day_exercise_id: int
    set_order: int
    target_weight: Optional[float]
    notes: Optional[str]
    rpe: Optional[float]
    rep: Optional[int]
    weight: Optional[float]


def get_program_by_name(name: str) -> Optional[Program]:
    """Get program by name."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, days_per_week FROM programs WHERE name = ?",
            (name,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return Program(
            id=row["id"],
            name=row["name"],
            days_per_week=row["days_per_week"]
        )


def get_latest_cycle(program_id: int) -> Optional[ProgramCycle]:
    """Get the latest cycle for a program by started_at date."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, program_id, cycle_no, started_at
            FROM program_cycles
            WHERE program_id = ?
            ORDER BY datetime(started_at) DESC
            LIMIT 1
            """,
            (program_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return ProgramCycle(
            id=row["id"],
            program_id=row["program_id"],
            cycle_no=row["cycle_no"],
            started_at=row["started_at"]
        )


def get_week_by_number(cycle_id: int, week_no: int) -> Optional[Week]:
    """Get week by cycle and week number."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, cycle_id, week_no FROM weeks WHERE cycle_id = ? AND week_no = ?",
            (cycle_id, week_no)
        )
        row = cur.fetchone()
        if not row:
            return None
        return Week(
            id=row["id"],
            cycle_id=row["cycle_id"],
            week_no=row["week_no"]
        )


def get_training_days(week_id: int) -> List[TrainingDay]:
    """Get all training days for a week, ordered by day_order."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, week_id, name, emphasis, day_order
            FROM training_days
            WHERE week_id = ?
            ORDER BY day_order ASC
            """,
            (week_id,)
        )
        return [
            TrainingDay(
                id=row["id"],
                week_id=row["week_id"],
                name=row["name"],
                emphasis=row["emphasis"],
                day_order=row["day_order"]
            )
            for row in cur.fetchall()
        ]


def get_day_exercises(training_day_id: int) -> List[Dict[str, Any]]:
    """
    Get exercises for a training day with exercise details.
    Returns list of dicts with exercise info and order.
    """
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                de.id as day_exercise_id,
                de.ex_order,
                e.id as exercise_id,
                e.name as exercise_name,
                e.equipment,
                e.target_muscle
            FROM day_exercises de
            JOIN exercises e ON e.id = de.exercise_id
            WHERE de.training_day_id = ?
            ORDER BY de.ex_order ASC
            """,
            (training_day_id,)
        )
        return [dict(row) for row in cur.fetchall()]


def get_sets_for_day_exercise(day_exercise_id: int) -> List[Set]:
    """Get all sets for a day exercise, ordered by set_order."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, day_exercise_id, set_order, target_weight, notes, rpe, rep, weight
            FROM sets
            WHERE day_exercise_id = ?
            ORDER BY set_order ASC
            """,
            (day_exercise_id,)
        )
        return [
            Set(
                id=row["id"],
                day_exercise_id=row["day_exercise_id"],
                set_order=row["set_order"],
                target_weight=row["target_weight"],
                notes=row["notes"],
                rpe=row["rpe"],
                rep=row["rep"],
                weight=row["weight"]
            )
            for row in cur.fetchall()
        ]


def list_all_programs() -> List[Program]:
    """Get all programs."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, days_per_week FROM programs ORDER BY name")
        return [
            Program(
                id=row["id"],
                name=row["name"],
                days_per_week=row["days_per_week"]
            )
            for row in cur.fetchall()
        ]


def create_program(name: str, days_per_week: int) -> Program:
    """Create a new program."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO programs(name, days_per_week) VALUES(?, ?)",
            (name, days_per_week)
        )
        program_id = cur.lastrowid
        conn.commit()
        return Program(id=program_id, name=name, days_per_week=days_per_week)


def create_cycle(program_id: int, cycle_no: int, started_at: str) -> ProgramCycle:
    """Create a new program cycle."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO program_cycles(program_id, cycle_no, started_at) VALUES(?, ?, ?)",
            (program_id, cycle_no, started_at)
        )
        cycle_id = cur.lastrowid
        conn.commit()
        return ProgramCycle(
            id=cycle_id,
            program_id=program_id,
            cycle_no=cycle_no,
            started_at=started_at
        )


def create_week(cycle_id: int, week_no: int) -> Week:
    """Create a new week."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO weeks(cycle_id, week_no) VALUES(?, ?)",
            (cycle_id, week_no)
        )
        week_id = cur.lastrowid
        conn.commit()
        return Week(id=week_id, cycle_id=cycle_id, week_no=week_no)


def create_training_day(week_id: int, name: Optional[str], emphasis: Optional[str], day_order: int) -> TrainingDay:
    """Create a new training day."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO training_days(week_id, name, emphasis, day_order) VALUES(?, ?, ?, ?)",
            (week_id, name, emphasis, day_order)
        )
        day_id = cur.lastrowid
        conn.commit()
        return TrainingDay(
            id=day_id,
            week_id=week_id,
            name=name,
            emphasis=emphasis,
            day_order=day_order
        )


def create_exercise(name: str, equipment: str, target_muscle: str) -> Exercise:
    """Create a new exercise."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO exercises(name, equipment, target_muscle) VALUES(?, ?, ?)",
            (name, equipment, target_muscle)
        )
        exercise_id = cur.lastrowid
        conn.commit()
        return Exercise(
            id=exercise_id,
            name=name,
            equipment=equipment,
            target_muscle=target_muscle
        )


def add_exercise_to_day(training_day_id: int, exercise_id: int, ex_order: int) -> DayExercise:
    """Add an exercise to a training day."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO day_exercises(training_day_id, exercise_id, ex_order) VALUES(?, ?, ?)",
            (training_day_id, exercise_id, ex_order)
        )
        day_exercise_id = cur.lastrowid
        conn.commit()
        return DayExercise(
            id=day_exercise_id,
            training_day_id=training_day_id,
            exercise_id=exercise_id,
            ex_order=ex_order
        )


def create_set(day_exercise_id: int, set_order: int, target_weight: Optional[float] = None,
               notes: Optional[str] = None, rpe: Optional[float] = None,
               rep: Optional[int] = None, weight: Optional[float] = None) -> Set:
    """Create a new set."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sets(day_exercise_id, set_order, target_weight, notes, rpe, rep, weight)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (day_exercise_id, set_order, target_weight, notes, rpe, rep, weight)
        )
        set_id = cur.lastrowid
        conn.commit()
        return Set(
            id=set_id,
            day_exercise_id=day_exercise_id,
            set_order=set_order,
            target_weight=target_weight,
            notes=notes,
            rpe=rpe,
            rep=rep,
            weight=weight
        )


def list_all_exercises() -> List[Exercise]:
    """Get all exercises."""
    with db.get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, equipment, target_muscle FROM exercises ORDER BY name")
        return [
            Exercise(
                id=row["id"],
                name=row["name"],
                equipment=row["equipment"],
                target_muscle=row["target_muscle"]
            )
            for row in cur.fetchall()
        ]
