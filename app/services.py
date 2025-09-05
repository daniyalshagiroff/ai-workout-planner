"""
Business logic for Program ↔ Workout schema, including invariant checks A/B/C and reports.
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from .repo import UserRepo, ExerciseRepo, ProgramRepo, WorkoutRepo
from . import db as app_db
from . import schemas, repo


class DomainError(Exception):
    pass


# Exercises
def create_exercise(owner_user_id: Optional[int], name: str, muscle_group: str, equipment: Optional[str], is_global: bool) -> Dict[str, Any]:
    ex_id = ExerciseRepo.create(owner_user_id, name, muscle_group, equipment, 1 if is_global else 0)
    ex = ExerciseRepo.get(ex_id)
    return ex


def list_exercises(user_id: Optional[int]) -> List[Dict[str, Any]]:
    return ExerciseRepo.list_for_user(user_id)


# V2 aliases for API compatibility
def create_exercise_v2(owner_user_id: Optional[int], name: str, muscle_group: str, equipment: Optional[str], is_global: bool) -> Dict[str, Any]:
    return create_exercise(owner_user_id, name, muscle_group, equipment, is_global)


def list_exercises_v2(user_id: Optional[int]) -> List[Dict[str, Any]]:
    return list_exercises(user_id)


def create_program_v2(owner_user_id: int, title: str, description: Optional[str]) -> Dict[str, Any]:
    return create_program(owner_user_id, title, description)


# Program building
def create_program(owner_user_id: int, title: str, description: Optional[str]) -> Dict[str, Any]:
    pid = ProgramRepo.create(owner_user_id, title, description)
    return ProgramRepo.get(pid)


def ensure_week(program_id: int, week_number: int) -> Dict[str, Any]:
    week = ProgramRepo.get_week(program_id, week_number)
    if week:
        return week
    ProgramRepo.create_week(program_id, week_number)
    return ProgramRepo.get_week(program_id, week_number)  # type: ignore


def ensure_day(program_id: int, week_number: int, day_of_week: int) -> Dict[str, Any]:
    week = ensure_week(program_id, week_number)
    day = ProgramRepo.get_day(week["id"], day_of_week)
    if day:
        return day
    ProgramRepo.create_day(week["id"], day_of_week)
    return ProgramRepo.get_day(week["id"], day_of_week)  # type: ignore


def add_day_exercise(program_id: int, week_number: int, day_of_week: int, exercise_id: int, position: int, notes: Optional[str]) -> Dict[str, Any]:
    day = ensure_day(program_id, week_number, day_of_week)
    pde_id = ProgramRepo.add_day_exercise(day["id"], exercise_id, position, notes)
    return {"id": pde_id, "program_day_id": day["id"], "exercise_id": exercise_id, "position": position, "notes": notes}


def add_planned_set(program_id: int, week_number: int, day_of_week: int, position: int, set_number: int, reps: int, weight: Optional[float], rpe: Optional[float], rest_seconds: Optional[int]) -> Dict[str, Any]:
    day = ensure_day(program_id, week_number, day_of_week)
    pde = ProgramRepo.get_day_exercise(day["id"], position)
    if not pde:
        raise DomainError("program_day_exercise not found for given position")
    ps_id = ProgramRepo.add_planned_set(pde["id"], set_number, reps, weight, rpe, rest_seconds)
    return {"id": ps_id, "program_day_exercise_id": pde["id"], "set_number": set_number, "reps": reps, "weight": weight, "rpe": rpe, "rest_seconds": rest_seconds}


# Workouts
def start_workout(owner_user_id: int, program_id: int, week_number: int, day_of_week: int) -> Dict[str, Any]:
    day = ensure_day(program_id, week_number, day_of_week)
    wid = WorkoutRepo.start(owner_user_id, day["id"], None)
    return WorkoutRepo.get_workout(wid)  # type: ignore


def _ensure_invariants_A_B_C(planned_set_id: int, workout_exercise_id: int, set_number: int) -> None:
    ps = WorkoutRepo.get_planned_set(planned_set_id)
    if not ps:
        raise DomainError("planned_set not found")
    wex = WorkoutRepo.get_workout_exercise(workout_exercise_id)
    if not wex:
        raise DomainError("workout_exercise not found")
    if set_number != ps["set_number"]:
        raise DomainError("Invariant A failed: set_number must equal planned_set.set_number")
    if wex["program_day_exercise_id"] != ps["program_day_exercise_id"]:
        raise DomainError("Invariant B failed: workout_exercise.program_day_exercise_id must equal planned_set.program_day_exercise_id")
    actual = WorkoutRepo.count_actual_sets_for_wex(workout_exercise_id)
    planned = WorkoutRepo.planned_count_for_pde(ps["program_day_exercise_id"])  # type: ignore
    if actual + 1 > planned:
        raise DomainError("Invariant C failed: actual workout sets cannot exceed planned sets")


def log_workout_set(workout_id: int, position: int, planned_set_id: int, set_number: int, reps: int, weight: Optional[float], rpe: Optional[float], rest_seconds: Optional[int]) -> Dict[str, Any]:
    w = WorkoutRepo.get_workout(workout_id)
    if not w:
        raise DomainError("workout not found")
    day_id = w["program_day_id"]
    pdes = ProgramRepo.list_day_exercises(day_id)
    target = next((d for d in pdes if d["position"] == position), None)
    if not target:
        raise DomainError("program_day_exercise (by position) not found")
    wex_id = WorkoutRepo.ensure_workout_exercise(workout_id, target["id"], position)
    _ensure_invariants_A_B_C(planned_set_id, wex_id, set_number)
    ws_id = WorkoutRepo.add_workout_set(wex_id, planned_set_id, set_number, reps, weight, rpe, rest_seconds)
    return {"id": ws_id, "workout_exercise_id": wex_id, "planned_set_id": planned_set_id, "set_number": set_number, "reps": reps, "weight": weight, "rpe": rpe, "rest_seconds": rest_seconds}


def finish_workout(workout_id: int, notes: Optional[str]) -> Dict[str, Any]:
    WorkoutRepo.finish(workout_id, None, notes)
    # After finishing a workout, apply next-week progression from actuals (+1 reps)
    try:
        _apply_next_week_progression_from_actuals(workout_id)
    except Exception:
        # Best-effort; do not break finish if progression fails
        pass
    return WorkoutRepo.get_workout(workout_id)  # type: ignore


def _apply_next_week_progression_from_actuals(workout_id: int) -> None:
    """Populate next week's planned_set for the same day using actuals from this workout.

    Rules:
    - Only proceed if ALL planned sets for this day have actuals logged in this workout.
    - Copy weight as-is (can be NULL). Copy reps as actual_reps + 1 (min 1).
    - For next week same day and same exercise position/set_number:
        - If planned_set exists: update reps/weight.
        - If not: insert planned_set.
    Idempotent: running multiple times will keep the same resulting values.
    """
    with app_db.get_connection() as conn:
        cur = conn.cursor()

        # 1) Gather workout → program/week/day info
        cur.execute(
            """
            SELECT w.id AS workout_id, w.program_day_id,
                   pw.program_id, pw.week_number, pd.day_of_week
            FROM workout w
            JOIN program_day pd ON pd.id = w.program_day_id
            JOIN program_week pw ON pw.id = pd.program_week_id
            WHERE w.id = ?
            """,
            (workout_id,),
        )
        wrow = cur.fetchone()
        if not wrow:
            return

        program_id = wrow[2]
        week_number = wrow[3]
        day_of_week = wrow[4]

        # 2) Collect planned sets and actuals for this workout/day
        cur.execute(
            """
            SELECT ps.id AS planned_set_id,
                   ps.set_number,
                   pde.position,
                   ws.reps AS actual_reps,
                   ws.weight AS actual_weight
            FROM program_day pd
            JOIN program_day_exercise pde ON pde.program_day_id = pd.id
            JOIN planned_set ps ON ps.program_day_exercise_id = pde.id
            LEFT JOIN workout_exercise we
                ON we.program_day_exercise_id = pde.id AND we.workout_id = ?
            LEFT JOIN workout_set ws
                ON ws.workout_exercise_id = we.id AND ws.planned_set_id = ps.id
            WHERE pd.id = ?
            ORDER BY pde.position, ps.set_number
            """,
            (workout_id, wrow[1]),
        )
        rows = cur.fetchall()
        if not rows:
            return

        total_planned = len(rows)
        completed = sum(1 for r in rows if r[3] is not None)
        if completed < total_planned:
            # Day not fully completed; skip progression
            return

        next_week = week_number + 1

        # 3) Ensure next week/day exists
        next_day = ensure_day(program_id, next_week, day_of_week)
        next_day_id = next_day["id"]

        # 4) Upsert planned sets for next week based on actuals
        with app_db.transaction(conn) as tcur:
            for planned_set_id, set_number, position, actual_reps, actual_weight in rows:
                # Safety: if somehow actual is missing, skip (should not happen due to check above)
                if actual_reps is None:
                    continue

                new_reps = max(1, int(actual_reps) + 1)
                new_weight = actual_weight  # can be None

                # Find matching exercise (same position) in next week's same day
                tcur.execute(
                    """
                    SELECT id FROM program_day_exercise
                    WHERE program_day_id = ? AND position = ?
                    """,
                    (next_day_id, position),
                )
                pde_next = tcur.fetchone()
                if not pde_next:
                    # No matching exercise in next week/day → skip
                    continue

                pde_next_id = pde_next[0]

                # Check if next planned_set exists
                tcur.execute(
                    """
                    SELECT id FROM planned_set
                    WHERE program_day_exercise_id = ? AND set_number = ?
                    """,
                    (pde_next_id, set_number),
                )
                ps_next = tcur.fetchone()
                if ps_next:
                    # Update
                    tcur.execute(
                        "UPDATE planned_set SET reps = ?, weight = ? WHERE id = ?",
                        (new_reps, new_weight, ps_next[0]),
                    )
                else:
                    # Insert
                    tcur.execute(
                        """
                        INSERT INTO planned_set (program_day_exercise_id, set_number, reps, weight)
                        VALUES (?, ?, ?, ?)
                        """,
                        (pde_next_id, set_number, new_reps, new_weight),
                    )


# Reports
def report_total_planned_sets(program_id: int, week_number: int) -> Dict[str, int]:
    return {"planned_sets": WorkoutRepo.report_planned_sets_for_week(program_id, week_number)}


def report_total_actual_sets(program_id: int, week_number: int) -> Dict[str, int]:
    return {"actual_sets": WorkoutRepo.report_actual_sets_for_week(program_id, week_number)}


def report_sets_by_muscle_group(program_id: int, week_number: int) -> List[Dict[str, Any]]:
    rows = WorkoutRepo.report_sets_by_muscle_group(program_id, week_number)
    return [{"muscle_group": mg, "sets": cnt} for mg, cnt in rows]


def report_progress_for_exercise(program_id: int, exercise_id: int) -> List[Dict[str, Any]]:
    rows = WorkoutRepo.report_progress_for_exercise(program_id, exercise_id)
    return [{"week_number": w, "avg_weight": aw, "avg_reps": ar} for (w, aw, ar) in rows]


async def list_programs() -> List[schemas.ProgramSummary]:
    """List all available programs."""
    programs = repo.list_all_programs()
    return [
        schemas.ProgramSummary(
            id=program.id,
            name=program.name,
            days_per_week=program.days_per_week
        )
        for program in programs
    ]


async def get_program_detail(program_name: str) -> schemas.ProgramDetail:
    """
    Get detailed program information including latest cycle.
    
    Args:
        program_name: Name of the program
        
    Returns:
        ProgramDetail: Complete program information
        
    Raises:
        ProgramNotFoundError: If program doesn't exist
    """
    program = repo.get_program_by_name(program_name)
    if not program:
        raise ProgramNotFoundError(f"Program '{program_name}' not found")
    
    cycle = repo.get_latest_cycle(program.id)
    
    return schemas.ProgramDetail(
        id=program.id,
        name=program.name,
        days_per_week=program.days_per_week,
        latest_cycle=schemas.CycleInfo(
            id=cycle.id,
            cycle_no=cycle.cycle_no,
            started_at=cycle.started_at
        ) if cycle else None
    )


async def create_program_async(name: str, days_per_week: int) -> schemas.ProgramSummary:
    """Create a new program."""
    # Check if program already exists
    existing = repo.get_program_by_name(name)
    if existing:
        raise ProgramAlreadyExistsError(f"Program '{name}' already exists")
    
    program = repo.create_program(name, days_per_week)
    return schemas.ProgramSummary(
        id=program.id,
        name=program.name,
        days_per_week=program.days_per_week
    )


async def get_program_by_id(program_id: int) -> schemas.ProgramDetail:
    """Get program by ID."""
    program = repo.get_program_by_id(program_id)
    if not program:
        raise ProgramNotFoundError(f"Program with ID {program_id} not found")
    
    cycle = repo.get_latest_cycle(program.id)
    return schemas.ProgramDetail(
        id=program.id,
        name=program.name,
        days_per_week=program.days_per_week,
        latest_cycle=schemas.CycleInfo(
            id=cycle.id,
            cycle_no=cycle.cycle_no,
            started_at=cycle.started_at
        ) if cycle else None
    )


async def create_cycle(program_id: int, cycle_no: int) -> schemas.CycleInfo:
    """Create a new cycle for a program."""
    # Check if program exists
    program = repo.get_program_by_id(program_id)
    if not program:
        raise ProgramNotFoundError(f"Program with ID {program_id} not found")
    
    # Check if cycle already exists
    existing_cycles = repo.list_cycles_by_program(program_id)
    if any(c.cycle_no == cycle_no for c in existing_cycles):
        raise CycleAlreadyExistsError(f"Cycle {cycle_no} already exists for program {program_id}")
    
    cycle = repo.create_cycle(program_id, cycle_no, datetime.now().isoformat())
    return schemas.CycleInfo(
        id=cycle.id,
        cycle_no=cycle.cycle_no,
        started_at=cycle.started_at
    )


async def list_cycles(program_id: int) -> List[schemas.CycleInfo]:
    """List all cycles for a program."""
    # Check if program exists
    program = repo.get_program_by_id(program_id)
    if not program:
        raise ProgramNotFoundError(f"Program with ID {program_id} not found")
    
    cycles = repo.list_cycles_by_program(program_id)
    return [
        schemas.CycleInfo(
            id=cycle.id,
            cycle_no=cycle.cycle_no,
            started_at=cycle.started_at
        )
        for cycle in cycles
    ]


async def create_training_day(program_id: int, cycle_id: int, week_no: int, name: Optional[str], emphasis: Optional[str], day_order: int) -> schemas.TrainingDayInfo:
    """Create a new training day in a cycle."""
    # Check if cycle exists
    cycle = repo.get_cycle_by_id(cycle_id)
    if not cycle:
        raise CycleNotFoundError(f"Cycle with ID {cycle_id} not found")
    
    # Check if day already exists
    existing_days = repo.list_training_days_by_cycle(cycle_id)
    if any(d.day_order == day_order and d.week_no == week_no for d in existing_days):
        raise TrainingDayAlreadyExistsError(f"Day {day_order} already exists for week {week_no} in cycle {cycle_id}")
    
    day = repo.create_training_day(program_id, cycle_id, week_no, name, emphasis, day_order)
    return schemas.TrainingDayInfo(
        id=day.id,
        program_id=day.program_id,
        cycle_id=day.cycle_id,
        week_no=day.week_no,
        name=day.name,
        emphasis=day.emphasis,
        day_order=day.day_order
    )


async def list_training_days(cycle_id: int) -> List[schemas.TrainingDayInfo]:
    """List all training days in a cycle."""
    # Check if cycle exists
    cycle = repo.get_cycle_by_id(cycle_id)
    if not cycle:
        raise CycleNotFoundError(f"Cycle with ID {cycle_id} not found")
    
    days = repo.list_training_days_by_cycle(cycle_id)
    return [
        schemas.TrainingDayInfo(
            id=day.id,
            program_id=day.program_id,
            cycle_id=day.cycle_id,
            week_no=day.week_no,
            name=day.name,
            emphasis=day.emphasis,
            day_order=day.day_order
        )
        for day in days
    ]


# Program operations
def get_programs_list() -> List[Dict[str, Any]]:
    """Get list of programs with owner_user_id = 1"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, title, description FROM program WHERE owner_user_id = 1 ORDER BY title")
        return [dict(row) for row in cur.fetchall()]


def get_program_info(program_id: int) -> Dict[str, Any]:
    """Get program info by ID"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, title, description FROM program WHERE id = ?", (program_id,))
        program = cur.fetchone()
        if not program:
            raise ValueError("Program not found")
        return dict(program)


def get_program_weeks_count(program_id: int) -> Dict[str, Any]:
    """Get program weeks count by ID"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM program WHERE id = ?", (program_id,))
        prog = cur.fetchone()
        if not prog:
            raise ValueError("Program not found")
        cur.execute("SELECT COUNT(*) as weeks_count FROM program_week WHERE program_id = ?", (program_id,))
        weeks_count = cur.fetchone()["weeks_count"]
        return {"program_id": prog["id"], "program_name": prog["title"], "weeks_count": weeks_count}


def get_program_week_data(program_id: int, week_number: int) -> Dict[str, Any]:
    """Get program week data by ID and week number"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM program WHERE id = ?", (program_id,))
        prog = cur.fetchone()
        if not prog:
            raise ValueError("Program not found")
        cur.execute("SELECT id FROM program_week WHERE program_id = ? AND week_number = ?", (program_id, week_number))
        week = cur.fetchone()
        if not week:
            raise ValueError(f"Week {week_number} not found for this program")
        week_id = week["id"]
        cur.execute("SELECT id, day_of_week FROM program_day WHERE program_week_id = ? ORDER BY day_of_week", (week_id,))
        days_rows = cur.fetchall()
        print(f"DEBUG: Found {len(days_rows)} days for week {week_number} of program {program_id}")
        days_out = []
        for d in days_rows:
            cur.execute("""
                SELECT e.name
                FROM program_day_exercise pde
                JOIN exercise e ON e.id = pde.exercise_id
                WHERE pde.program_day_id = ?
                ORDER BY pde.position
                """, (d["id"],))
            ex_names = [r[0] for r in cur.fetchall()]
            print(f"DEBUG: Day {d['day_of_week']} has {len(ex_names)} exercises: {ex_names}")
            days_out.append({"day_number": d["day_of_week"], "exercises": ex_names})
        return {"program_id": prog["id"], "program_name": prog["title"], "week_number": week_number, "days": days_out}


# Workout operations
def start_workout(program_id: int, week_number: int, day_number: int, user_id: int) -> Dict[str, Any]:
    """Start a new workout session"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        
        # Check if program exists
        cur.execute("SELECT id, title FROM program WHERE id = ?", (program_id,))
        program = cur.fetchone()
        if not program:
            raise ValueError("Program not found")
        
        # Get program day ID
        cur.execute("""
            SELECT pd.id FROM program_day pd
            JOIN program_week pw ON pd.program_week_id = pw.id
            WHERE pw.program_id = ? AND pw.week_number = ? AND pd.day_of_week = ?
        """, (program_id, week_number, day_number))
        program_day = cur.fetchone()
        if not program_day:
            raise ValueError(f"Day {day_number} not found for week {week_number}")
        
        program_day_id = program_day["id"]
        
        # Create workout
        cur.execute("""
            INSERT INTO workout (owner_user_id, program_day_id, started_at)
            VALUES (?, ?, datetime('now'))
        """, (user_id, program_day_id))
        workout_id = cur.lastrowid
        
        # Get planned sets count for this day
        cur.execute("""
            SELECT COUNT(*) as cnt FROM planned_set ps
            JOIN program_day_exercise pde ON ps.program_day_exercise_id = pde.id
            WHERE pde.program_day_id = ?
        """, (program_day_id,))
        ps_result = cur.fetchone()
        ps_cnt = ps_result["cnt"] if ps_result else 0
        
        return {
            "workout_id": workout_id,
            "program_id": program_id,
            "program_title": program["title"],
            "week_number": week_number,
            "day_number": day_number,
            "planned_sets_count": ps_cnt
        }


def get_workout_session(workout_id: int, user_id: int) -> Dict[str, Any]:
    """Get workout session data with exercises and planned sets"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        
        # Get workout info
        cur.execute("""
            SELECT w.id, w.owner_user_id, w.program_day_id, w.started_at,
                   pw.program_id, pw.week_number, pd.day_of_week,
                   p.title as program_title
            FROM workout w
            JOIN program_day pd ON w.program_day_id = pd.id
            JOIN program_week pw ON pd.program_week_id = pw.id
            JOIN program p ON pw.program_id = p.id
            WHERE w.id = ? AND w.owner_user_id = ?
        """, (workout_id, user_id))
        workout = cur.fetchone()
        if not workout:
            raise ValueError("Workout not found")
        
        # Get exercises and sets
        cur.execute("""
            SELECT e.name as exercise_name, e.muscle_group, e.equipment,
                   pde.position, pde.notes,
                   ps.id as set_id, ps.set_number, ps.reps, ps.weight, ps.rpe, ps.rest_seconds,
                   ws.id as workout_set_id, ws.reps as actual_reps, ws.weight as actual_weight,
                   ws.rpe as actual_rpe, ws.rest_seconds as actual_rest
            FROM program_day_exercise pde
            JOIN exercise e ON pde.exercise_id = e.id
            LEFT JOIN planned_set ps ON ps.program_day_exercise_id = pde.id
            LEFT JOIN workout_set ws ON ws.planned_set_id = ps.id AND ws.workout_id = ?
            WHERE pde.program_day_id = ?
            ORDER BY pde.position, ps.set_number
        """, (workout_id, workout["program_day_id"]))
        
        exercises_data = cur.fetchall()
        
        # Group by exercise
        exercises = {}
        for row in exercises_data:
            exercise_name = row["exercise_name"]
            if exercise_name not in exercises:
                exercises[exercise_name] = {
                    "name": exercise_name,
                    "muscle_group": row["muscle_group"],
                    "equipment": row["equipment"],
                    "position": row["position"],
                    "notes": row["notes"],
                    "sets": []
                }
            
            if row["set_id"]:  # If there's a planned set
                exercises[exercise_name]["sets"].append({
                    "set_id": row["set_id"],
                    "set_number": row["set_number"],
                    "planned_reps": row["reps"],
                    "planned_weight": row["weight"],
                    "planned_rpe": row["rpe"],
                    "planned_rest": row["rest_seconds"],
                    "workout_set_id": row["workout_set_id"],
                    "actual_reps": row["actual_reps"],
                    "actual_weight": row["actual_weight"],
                    "actual_rpe": row["actual_rpe"],
                    "actual_rest": row["actual_rest"]
                })
        
        return {
            "workout_id": workout["id"],
            "program_id": workout["program_id"],
            "program_title": workout["program_title"],
            "week_number": workout["week_number"],
            "day_number": workout["day_of_week"],
            "started_at": workout["started_at"],
            "exercises": list(exercises.values())
        }


def log_workout_set(workout_id: int, set_id: int, reps: int, weight: float, rpe: float, rest_seconds: int, user_id: int) -> Dict[str, Any]:
    """Log a workout set"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        
        # Verify workout exists
        cur.execute("SELECT id FROM workout WHERE id = ?", (workout_id,))
        if not cur.fetchone():
            raise ValueError("Workout not found")
        
        # Check if set already logged
        cur.execute("SELECT id FROM workout_set WHERE planned_set_id = ? AND workout_id = ?", (set_id, workout_id))
        existing_set = cur.fetchone()
        
        if existing_set:
            # Update existing set
            cur.execute("""
                UPDATE workout_set 
                SET reps = ?, weight = ?, rpe = ?, rest_seconds = ?
                WHERE planned_set_id = ? AND workout_id = ?
            """, (reps, weight, rpe, rest_seconds, set_id, workout_id))
            workout_set_id = existing_set["id"]
        else:
            # Create new set
            cur.execute("""
                INSERT INTO workout_set (workout_id, planned_set_id, reps, weight, rpe, rest_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (workout_id, set_id, reps, weight, rpe, rest_seconds))
            workout_set_id = cur.lastrowid
        
        return {"workout_set_id": workout_set_id, "message": "Set logged successfully"}


# User program operations
def select_program_for_user(program_id: int, user_id: int) -> Dict[str, Any]:
    """Select a program for a user"""
    with app_db.get_connection() as conn:
        # Check if program exists
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM program WHERE id = ?", (program_id,))
        program = cur.fetchone()
        if not program:
            raise ValueError("Program not found")
        
        # Check if user already has this program
        cur.execute("SELECT id FROM user_program WHERE user_id = ? AND program_id = ?", (user_id, program_id))
        if cur.fetchone():
            raise ValueError("Program already selected")
        
        # Add program to user
        cur.execute("""
            INSERT INTO user_program (user_id, program_id, started_at, is_active, current_week, current_day)
            VALUES (?, ?, datetime('now'), 0, 1, 1)
        """, (user_id, program_id))
        
        return {"message": "Program selected successfully", "program_id": program_id, "program_title": program["title"]}


def get_user_programs(user_id: int) -> List[Dict[str, Any]]:
    """Get user's selected programs"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT up.id, up.user_id, up.program_id, up.started_at, up.is_active, 
                   up.current_week, up.current_day, up.notes, up.created_at,
                   p.title as program_title, p.description as program_description
            FROM user_program up
            JOIN program p ON up.program_id = p.id
            WHERE up.user_id = ?
            ORDER BY up.created_at DESC
            """,
            (user_id,)
        )
        return [dict(row) for row in cur.fetchall()]


def activate_user_program(user_program_id: int, user_id: int) -> Dict[str, Any]:
    """Activate a user program (deactivate others)"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        
        # Get user_id for this program
        cur.execute("SELECT user_id FROM user_program WHERE id = ?", (user_program_id,))
        user_program = cur.fetchone()
        if not user_program:
            raise ValueError("User program not found")
        
        if user_program["user_id"] != user_id:
            raise ValueError("Unauthorized")
        
        # Deactivate all other programs for this user
        cur.execute("UPDATE user_program SET is_active = 0 WHERE user_id = ?", (user_id,))
        
        # Activate this program
        cur.execute("UPDATE user_program SET is_active = 1 WHERE id = ?", (user_program_id,))
        
        return {"message": "Program activated successfully"}


def remove_user_program(user_program_id: int, user_id: int) -> Dict[str, Any]:
    """Remove a program from user's selected programs"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        
        # Check if user program exists
        cur.execute("SELECT id FROM user_program WHERE id = ?", (user_program_id,))
        if not cur.fetchone():
            raise ValueError("User program not found")
        
        # Remove the program
        cur.execute("DELETE FROM user_program WHERE id = ?", (user_program_id,))
        
        return {"message": "Program removed successfully"}


def get_day_status(program_id: int, week_number: int, day_number: int, user_id: int) -> Dict[str, Any]:
    """Get completion status for a specific day"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT pd.id as program_day_id
            FROM program_day pd
            JOIN program_week pw ON pd.program_week_id = pw.id
            WHERE pw.program_id = ? AND pw.week_number = ? AND pd.day_of_week = ?
            """,
            (program_id, week_number, day_number)
        )
        program_day = cur.fetchone()
        if not program_day:
            raise ValueError("Day not found")
        
        program_day_id = program_day["program_day_id"]
        
        # Get planned sets count
        cur.execute(
            """
            SELECT COUNT(*) as planned_count
            FROM planned_set ps
            JOIN program_day_exercise pde ON ps.program_day_exercise_id = pde.id
            WHERE pde.program_day_id = ?
            """,
            (program_day_id,)
        )
        planned_count = cur.fetchone()["planned_count"]
        
        # Get completed sets count
        cur.execute(
            """
            SELECT COUNT(*) as completed_count
            FROM workout_set ws
            JOIN workout w ON ws.workout_id = w.id
            JOIN planned_set ps ON ws.planned_set_id = ps.id
            JOIN program_day_exercise pde ON ps.program_day_exercise_id = pde.id
            WHERE pde.program_day_id = ? AND w.owner_user_id = ?
            """,
            (program_day_id, user_id)
        )
        completed_count = cur.fetchone()["completed_count"]
        
        # Check if workout exists
        cur.execute(
            """
            SELECT id, started_at FROM workout
            WHERE program_day_id = ? AND owner_user_id = ?
            ORDER BY started_at DESC LIMIT 1
            """,
            (program_day_id, user_id)
        )
        workout = cur.fetchone()
        
        return {
            "program_id": program_id,
            "week_number": week_number,
            "day_number": day_number,
            "planned_sets": planned_count,
            "completed_sets": completed_count,
            "completion_percentage": (completed_count / planned_count * 100) if planned_count > 0 else 0,
            "workout_id": workout["id"] if workout else None,
            "workout_started_at": workout["started_at"] if workout else None
        }


def save_ai_plan(owner_user_id: int, plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save AI-generated plan to database with 8 weeks progression"""
    title: str = str(plan_data.get("title") or "AI Program")
    description: Optional[str] = plan_data.get("description")
    weeks = plan_data.get("weeks", [])
    
    if not weeks:
        raise ValueError("No weeks data provided")
    
    # Create the program
    program = create_program_v2(owner_user_id, title, description)
    program_id = program["id"]
    
    # Get the first week data (AI generates only 1 week)
    first_week = weeks[0] if weeks else {}
    first_week_days = first_week.get("days", [])
    print(f"DEBUG: First week has {len(first_week_days)} days")
    for i, day in enumerate(first_week_days):
        exercises = day.get('exercises', [])
        print(f"DEBUG: Day {i+1}: day_of_week={day.get('day_of_week')} with {len(exercises)} exercises")
        for j, exercise in enumerate(exercises):
            print(f"  Exercise {j+1}: {exercise.get('name')} ({exercise.get('muscle_group')})")
    
    # Generate 8 weeks based on the first week
    for week_number in range(1, 9):
        # Ensure week exists
        ensure_week(program_id, week_number)
        
        # For week 1, use the original data; for other weeks, copy the structure
        if week_number == 1:
            days_to_process = first_week_days
        else:
            # Copy the structure from week 1 for weeks 2-8
            days_to_process = first_week_days
        
        # Process each day
        for day_data in days_to_process:
            day_of_week = day_data.get("day_of_week")
            exercises = day_data.get("exercises", [])
            
            print(f"DEBUG: Processing week {week_number}, day {day_of_week} with {len(exercises)} exercises")
            
            if not day_of_week or not exercises:
                print(f"DEBUG: Skipping day {day_of_week} - no day_of_week or no exercises")
                continue
            
            # Ensure day exists
            ensure_day(program_id, week_number, day_of_week)
            
            # Process each exercise
            for exercise_data in exercises:
                exercise_name = exercise_data.get("name")
                muscle_group = exercise_data.get("muscle_group")
                equipment = exercise_data.get("equipment")
                position = exercise_data.get("position", 1)
                notes = exercise_data.get("notes")
                planned_sets = exercise_data.get("planned_sets", [])
                
                if not exercise_name or not muscle_group:
                    continue
                
                # Create or get exercise
                try:
                    # Use the correct create_exercise function directly from services module
                    exercise = create_exercise(
                        owner_user_id,
                        exercise_name,
                        muscle_group,
                        equipment,
                        False
                    )
                    exercise_id = exercise["id"]
                    print(f"DEBUG: Created new exercise {exercise_name} with ID {exercise_id}")
                except Exception as e:
                    print(f"DEBUG: Failed to create exercise {exercise_name}: {e}")
                    # Exercise might already exist, try to find it
                    exercises_list = list_exercises(owner_user_id)
                    existing_exercise = next(
                        (ex for ex in exercises_list if ex["name"] == exercise_name), 
                        None
                    )
                    if existing_exercise:
                        exercise_id = existing_exercise["id"]
                        print(f"DEBUG: Found existing exercise {exercise_name} with ID {exercise_id}")
                    else:
                        print(f"DEBUG: Exercise {exercise_name} not found, skipping...")
                        continue
                
                # Add exercise to day
                try:
                    result = add_day_exercise(
                        program_id=program_id,
                        week_number=week_number,
                        day_of_week=day_of_week,
                        exercise_id=exercise_id,
                        position=position,
                        notes=notes
                    )
                    print(f"DEBUG: Added exercise {exercise_name} to week {week_number}, day {day_of_week}, position {position}")
                except Exception as e:
                    print(f"DEBUG: Error adding exercise {exercise_name} to day: {e}")
                    pass
                
                # Add planned sets
                for set_data in planned_sets:
                    set_number = set_data.get("set_number", 1)
                    base_reps = set_data.get("reps", 8)
                    base_weight = set_data.get("weight")
                    rpe = set_data.get("rpe")
                    rest_seconds = set_data.get("rest_seconds")
                    
                    # Apply progression for weeks 2-8
                    if week_number > 1:
                        if week_number % 2 == 0:
                            # Even weeks: +1 rep
                            reps = base_reps + 1
                            weight = base_weight
                        else:
                            # Odd weeks: +2.5% weight
                            reps = base_reps
                            weight = base_weight * 1.025 if base_weight else None
                    else:
                        reps = base_reps
                        weight = base_weight
                    
                    try:
                        add_planned_set(
                            program_id=program_id,
                            week_number=week_number,
                            day_of_week=day_of_week,
                            position=position,
                            set_number=set_number,
                            reps=reps,
                            weight=weight,
                            rpe=rpe,
                            rest_seconds=rest_seconds
                        )
                    except Exception:
                        pass
    
    # Create user_program relationship
    try:
        print(f"DEBUG: Creating user_program with user_id: {owner_user_id}, program_id: {program_id}")
        with app_db.get_connection() as conn:
            with app_db.transaction(conn) as cur:
                cur.execute(
                    "INSERT INTO user_program (user_id, program_id) VALUES (?, ?)",
                    (owner_user_id, program_id),
                )
        print(f"DEBUG: Successfully created user_program")
    except Exception as e:
        print(f"DEBUG: Error creating user_program: {e}")
        pass
    
    return {"message": "Plan saved successfully", "program_id": program_id, "program_title": title}


def export_program_data(program_name: str) -> Dict[str, Any]:
    """Export program data for frontend"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        # Find program by title
        cur.execute("SELECT id, title FROM program WHERE title = ?", (program_name,))
        prog = cur.fetchone()
        if not prog:
            raise ValueError("Program not found")
        
        program_id = prog["id"]
        program_title = prog["title"]
        
        # Get weeks
        cur.execute("SELECT week_number FROM program_week WHERE program_id = ? ORDER BY week_number", (program_id,))
        weeks = [row["week_number"] for row in cur.fetchall()]
        
        # Get days for week 1 (default)
        week_1_id = None
        if weeks:
            cur.execute("SELECT id FROM program_week WHERE program_id = ? AND week_number = 1", (program_id,))
            week_1 = cur.fetchone()
            if week_1:
                week_1_id = week_1["id"]
        
        days = []
        if week_1_id:
            cur.execute("SELECT day_of_week FROM program_day WHERE program_week_id = ? ORDER BY day_of_week", (week_1_id,))
            days = [row["day_of_week"] for row in cur.fetchall()]
        
        return {
            "program_id": program_id,
            "program_name": program_title,
            "weeks": weeks,
            "days": days
        }


async def create_exercise_catalog(name: str, equipment: str, target_muscle: str) -> schemas.ExerciseInfo:
    """Create a new exercise in the catalog."""
    # Check if exercise already exists
    existing = repo.get_exercise_by_name(name)
    if existing:
        raise ExerciseAlreadyExistsError(f"Exercise '{name}' already exists")
    
    exercise = repo.create_exercise(name, equipment, target_muscle)
    return schemas.ExerciseInfo(
        id=exercise.id,
        name=exercise.name,
        equipment=exercise.equipment,
        target_muscle=exercise.target_muscle
    )


async def list_exercises_async() -> List[schemas.ExerciseInfo]:
    """List all exercises."""
    exercises = repo.list_all_exercises()
    return [
        schemas.ExerciseInfo(
            id=exercise.id,
            name=exercise.name,
            equipment=exercise.equipment,
            target_muscle=exercise.target_muscle
        )
        for exercise in exercises
    ]


async def create_day_exercise(training_day_id: int, exercise_id: int, ex_order: int, priority_weight: Optional[float] = None) -> schemas.DayExerciseInfo:
    """Add an exercise to a training day."""
    # Check if training day exists
    day = repo.get_training_day_by_id(training_day_id)
    if not day:
        raise TrainingDayNotFoundError(f"Training day with ID {training_day_id} not found")
    
    # Check if exercise exists
    exercise = repo.get_exercise_by_id(exercise_id)
    if not exercise:
        raise ExerciseNotFoundError(f"Exercise with ID {exercise_id} not found")
    
    # Check if day exercise already exists
    existing_exercises = repo.list_day_exercises_by_training_day(training_day_id)
    if any(de.ex_order == ex_order for de in existing_exercises):
        raise DayExerciseAlreadyExistsError(f"Exercise order {ex_order} already exists for training day {training_day_id}")
    
    day_exercise = repo.add_exercise_to_day(training_day_id, exercise_id, ex_order)
    return schemas.DayExerciseInfo(
        id=day_exercise.id,
        training_day_id=day_exercise.training_day_id,
        exercise_id=day_exercise.exercise_id,
        ex_order=day_exercise.ex_order,
        priority_weight=priority_weight,
        exercise=schemas.ExerciseInfo(
            id=exercise.id,
            name=exercise.name,
            equipment=exercise.equipment,
            target_muscle=exercise.target_muscle
        )
    )


async def list_day_exercises(training_day_id: int) -> List[schemas.DayExerciseInfo]:
    """List all exercises for a training day."""
    # Check if training day exists
    day = repo.get_training_day_by_id(training_day_id)
    if not day:
        raise TrainingDayNotFoundError(f"Training day with ID {training_day_id} not found")
    
    day_exercises = repo.list_day_exercises_by_training_day(training_day_id)
    result = []
    for de in day_exercises:
        exercise = repo.get_exercise_by_id(de.exercise_id)
        result.append(schemas.DayExerciseInfo(
            id=de.id,
            training_day_id=de.training_day_id,
            exercise_id=de.exercise_id,
            ex_order=de.ex_order,
            priority_weight=None,  # Not stored in DB yet
            exercise=schemas.ExerciseInfo(
                id=exercise.id,
                name=exercise.name,
                equipment=exercise.equipment,
                target_muscle=exercise.target_muscle
            )
        ))
    return result


async def create_set(day_exercise_id: int, set_order: int, rep: int, weight: int, week_no: int, target_weight: Optional[float] = None) -> schemas.SetInfo:
    """Create a new set for a day exercise."""
    # Check if day exercise exists
    day_exercise = repo.get_day_exercise_by_id(day_exercise_id)
    if not day_exercise:
        raise DayExerciseNotFoundError(f"Day exercise with ID {day_exercise_id} not found")
    
    # Get training day to get program_id
    training_day = repo.get_training_day_by_id(day_exercise.training_day_id)
    if not training_day:
        raise TrainingDayNotFoundError(f"Training day with ID {day_exercise.training_day_id} not found")
    
    program_id = training_day.program_id

    # Check if set already exists for this specific week
    existing_sets = repo.list_sets_by_day_exercise(day_exercise_id)
    existing_set = next((s for s in existing_sets if s.set_order == set_order and s.week_no == week_no), None)
    
    if existing_set:
        # Duplicate found: inform caller instead of overwriting
        raise SetAlreadyExistsError("сет уже записано")
    
    # Create new set
    set_obj = repo.create_set(day_exercise_id, set_order, rep, weight, program_id, week_no, target_weight)
    
    return schemas.SetInfo(
        id=set_obj.id,
        day_exercise_id=set_obj.day_exercise_id,
        week_no=set_obj.week_no,
        set_order=set_obj.set_order,
        target_weight=set_obj.target_weight,
        notes=set_obj.notes,
        rpe=set_obj.rpe,
        rep=set_obj.rep,
        weight=set_obj.weight
    )


async def list_sets(day_exercise_id: int) -> List[schemas.SetInfo]:
    """List all sets for a day exercise."""
    # Check if day exercise exists
    day_exercise = repo.get_day_exercise_by_id(day_exercise_id)
    if not day_exercise:
        raise DayExerciseNotFoundError(f"Day exercise with ID {day_exercise_id} not found")
    
    sets = repo.list_sets_by_day_exercise(day_exercise_id)
    return [
        schemas.SetInfo(
            id=set_obj.id,
            day_exercise_id=set_obj.day_exercise_id,
            week_no=set_obj.week_no,
            set_order=set_obj.set_order,
            target_weight=set_obj.target_weight,
            notes=set_obj.notes,
            rpe=set_obj.rpe,
            rep=set_obj.rep,
            weight=set_obj.weight
        )
        for set_obj in sets
    ]


def get_latest_cycle(program_name: str) -> schemas.CycleInfo:
    """
    Get the latest cycle for a program.
    
    Args:
        program_name: Name of the program
        
    Returns:
        CycleInfo: Latest cycle information
        
    Raises:
        ProgramNotFoundError: If program doesn't exist
        NoCycleError: If no cycle exists
    """
    program = repo.get_program_by_name(program_name)
    if not program:
        raise ProgramNotFoundError(f"Program '{program_name}' not found")
    
    cycle = repo.get_latest_cycle(program.id)
    if not cycle:
        raise NoCycleError(f"No cycle found for program '{program_name}'")
    
    return schemas.CycleInfo(
        id=cycle.id,
        cycle_no=cycle.cycle_no,
        started_at=cycle.started_at
    )
