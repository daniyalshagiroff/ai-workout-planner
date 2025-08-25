"""
Business logic layer for workout program operations.
Contains high-level business logic and orchestrates repository calls.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from . import repo
from . import schemas


class ProgramNotFoundError(Exception):
    """Raised when a program is not found."""
    pass


class ProgramAlreadyExistsError(Exception):
    """Raised when a program already exists."""
    pass


class CycleNotFoundError(Exception):
    """Raised when a cycle is not found."""
    pass


class CycleAlreadyExistsError(Exception):
    """Raised when a cycle already exists."""
    pass


class WeekNotFoundError(Exception):
    """Raised when a week is not found."""
    pass


class WeekAlreadyExistsError(Exception):
    """Raised when a week already exists."""
    pass


class TrainingDayNotFoundError(Exception):
    """Raised when a training day is not found."""
    pass


class TrainingDayAlreadyExistsError(Exception):
    """Raised when a training day already exists."""
    pass


class ExerciseNotFoundError(Exception):
    """Raised when an exercise is not found."""
    pass


class ExerciseAlreadyExistsError(Exception):
    """Raised when an exercise already exists."""
    pass


class DayExerciseNotFoundError(Exception):
    """Raised when a day exercise is not found."""
    pass


class DayExerciseAlreadyExistsError(Exception):
    """Raised when a day exercise already exists."""
    pass


class SetNotFoundError(Exception):
    """Raised when a set is not found."""
    pass


class SetAlreadyExistsError(Exception):
    """Raised when a set already exists."""
    pass


class NoCycleError(Exception):
    """Raised when no cycle exists for a program."""
    pass


class NoWeekError(Exception):
    """Raised when no week exists for a cycle."""
    pass


async def export_program_json(program_name: str) -> schemas.ProgramExport:
    """
    Export a program's latest cycle data as structured JSON.
    
    Args:
        program_name: Name of the program to export
        
    Returns:
        ProgramExport: Structured program data with days and exercises
        
    Raises:
        ProgramNotFoundError: If program doesn't exist
        NoCycleError: If no cycle exists for the program
        NoWeekError: If no week exists for the cycle
    """
    # Get program
    program = repo.get_program_by_name(program_name)
    if not program:
        raise ProgramNotFoundError(f"Program '{program_name}' not found")
    
    # Get latest cycle
    cycle = repo.get_latest_cycle(program.id)
    if not cycle:
        raise NoCycleError(f"No cycle found for program '{program_name}'")
    
    # Get training days for week 1
    training_days = repo.get_training_days(program.id, cycle.id, week_no=1)
    if not training_days:
        raise NoWeekError(f"Week 1 not found for cycle {cycle.cycle_no}")
    
    # Build days output
    days_output = []
    for day in training_days:
        # Get exercises for this day
        day_exercises = repo.get_day_exercises(day.id)
        exercises = [ex["exercise_name"] for ex in day_exercises]
        
        days_output.append(schemas.DayExport(
            label=day.name or f"Day {day.day_order}",
            emphasis=day.emphasis or "",
            exercises=exercises
        ))
    
    return schemas.ProgramExport(
        program=schemas.ProgramInfo(
            name=program.name,
            days_per_week=program.days_per_week
        ),
        week=schemas.WeekInfo(week_no=1),
        days=days_output
    )


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
