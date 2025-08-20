"""
Business logic layer for workout program operations.
Contains high-level business logic and orchestrates repository calls.
"""

from typing import List, Dict, Any
from datetime import datetime

from . import repo
from . import schemas


class ProgramNotFoundError(Exception):
    """Raised when a program is not found."""
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
    
    # Get week 1
    week = repo.get_week_by_number(cycle.id, week_no=1)
    if not week:
        raise NoWeekError(f"Week 1 not found for cycle {cycle.cycle_no}")
    
    # Get training days
    training_days = repo.get_training_days(week.id)
    
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
        week=schemas.WeekInfo(week_no=week.week_no),
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
    
    # Create or get week
    week = repo.get_week_by_number(cycle.id, week_no=1)
    if not week:
        week = repo.create_week(cycle_id=cycle.id, week_no=1)
    
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
            week_id=week.id,
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
                    weight=None
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
