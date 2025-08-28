"""
Business logic for Program ↔ Workout schema, including invariant checks A/B/C and reports.
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from .repo import UserRepo, ExerciseRepo, ProgramRepo, WorkoutRepo
from . import schemas, repo


class DomainError(Exception):
    pass


# Exercises (v2)
def create_exercise_v2(owner_user_id: Optional[int], name: str, muscle_group: str, equipment: Optional[str], is_global: bool) -> Dict[str, Any]:
    ex_id = ExerciseRepo.create(owner_user_id, name, muscle_group, equipment, 1 if is_global else 0)
    ex = ExerciseRepo.get(ex_id)
    return ex


def list_exercises_v2(user_id: Optional[int]) -> List[Dict[str, Any]]:
    return ExerciseRepo.list_for_user(user_id)


# Program building
def create_program_v2(owner_user_id: int, title: str, description: Optional[str]) -> Dict[str, Any]:
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
    return WorkoutRepo.get_workout(workout_id)  # type: ignore


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


async def create_program(name: str, days_per_week: int) -> schemas.ProgramSummary:
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


async def create_exercise(name: str, equipment: str, target_muscle: str) -> schemas.ExerciseInfo:
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


async def list_exercises() -> List[schemas.ExerciseInfo]:
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


def seed_foundational_program() -> None:
    """
    Seed the database with the foundational bodybuilding program.
    Creates program, cycle, week, days, exercises, and sets.
    """
    # Exercise definitions with default weights
    exercises_data = [
        ("pulldown", "cable", "lats", 40.0),
        ("bench press", "barbell", "chest", 60.0),
        ("barbell squat", "barbell", "quads", 80.0),
        ("biceps curls", "dumbbells", "biceps", 12.5),
        ("triceps pushdown", "cable", "triceps", 25.0),
    ]
    
    # Create or get program
    program = repo.get_program_by_name("Full Body")
    if not program:
        program = repo.create_program("Full Body", days_per_week=3)
    
    # Create or get cycle
    cycle = repo.get_latest_cycle(program.id)
    if not cycle:
        cycle = repo.create_cycle(
            program_id=program.id,
            cycle_no=1,
            started_at=datetime.now().isoformat()
        )
    
    # Create exercises if they don't exist
    exercise_map = {}
    for ex_name, equipment, target_muscle, default_weight in exercises_data:
        # Try to find existing exercise
        existing_exercises = repo.list_all_exercises()
        exercise = next((ex for ex in existing_exercises if ex.name == ex_name), None)
        if not exercise:
            exercise = repo.create_exercise(
                name=ex_name,
                equipment=equipment,
                target_muscle=target_muscle
            )
        exercise_map[ex_name] = exercise
    
    # Create training days with emphasis
    emphases = ["chest", "back", "legs"]
    exercise_order = [
        "barbell squat",
        "bench press", 
        "pulldown",
        "biceps curls",
        "triceps pushdown"
    ]
    
    for i, emphasis in enumerate(emphases, start=1):
        # Create training day
        day = repo.create_training_day(
            program_id=program.id,
            cycle_id=cycle.id,
            week_no=1,
            name="Full Body",
            emphasis=emphasis,
            day_order=i
        )
        
        # Add exercises to day
        for ex_order, ex_name in enumerate(exercise_order, start=1):
            exercise = exercise_map[ex_name]
            day_exercise = repo.add_exercise_to_day(
                training_day_id=day.id,
                exercise_id=exercise.id,
                ex_order=ex_order
            )
            
            # Create 2 sets for each exercise
            for set_order in range(1, 3):
                repo.create_set(
                    day_exercise_id=day_exercise.id,
                    set_order=set_order,
                    target_weight=exercise_map[ex_name].default_target_weight or 0.0,
                    notes="",
                    rpe=7.5,
                    rep=None,
                    weight=None,
                    program_id=program.id,
                    week_no=1
                )


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
