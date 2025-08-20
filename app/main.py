"""
FastAPI application with workout program routes.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from typing import List, Optional

from . import services
from . import schemas


app = FastAPI(
    title="IRON AI Workout Planner",
    description="AI-powered workout planning and tracking",
    version="1.0.0",
)

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def root():
    """Serve the main landing page."""
    return FileResponse("frontend/index.html")


# === PROGRAMS ===
@app.post("/api/programs", response_model=schemas.ProgramSummary)
async def create_program(request: schemas.CreateProgramRequest):
    """Create a new program."""
    try:
        return await services.create_program(request.name, request.days_per_week)
    except services.ProgramAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/programs/{program_id}", response_model=schemas.ProgramDetail)
async def get_program(program_id: int):
    """Get program by ID."""
    try:
        return await services.get_program_by_id(program_id)
    except services.ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/programs", response_model=List[schemas.ProgramSummary])
async def list_programs():
    """List all programs."""
    return await services.list_programs()


# === CYCLES ===
@app.post("/api/cycles", response_model=schemas.CycleInfo)
async def create_cycle(request: schemas.CreateCycleRequest):
    """Create a new cycle for a program."""
    try:
        return await services.create_cycle(request.program_id, request.cycle_no)
    except services.ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except services.CycleAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/cycles", response_model=List[schemas.CycleInfo])
async def list_cycles(program_id: int = Query(..., description="Program ID")):
    """List all cycles for a program."""
    try:
        return await services.list_cycles(program_id)
    except services.ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# === WEEKS ===
@app.post("/api/weeks", response_model=schemas.WeekInfo)
async def create_week(request: schemas.CreateWeekRequest):
    """Create a new week in a cycle."""
    try:
        return await services.create_week(request.cycle_id, request.week_no)
    except services.CycleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except services.WeekAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/weeks", response_model=List[schemas.WeekInfo])
async def list_weeks(cycle_id: int = Query(..., description="Cycle ID")):
    """List all weeks in a cycle."""
    try:
        return await services.list_weeks(cycle_id)
    except services.CycleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# === TRAINING DAYS ===
@app.post("/api/training-days", response_model=schemas.TrainingDayInfo)
async def create_training_day(request: schemas.CreateTrainingDayRequest):
    """Create a new training day in a week."""
    try:
        return await services.create_training_day(
            request.week_id, 
            request.name, 
            request.emphasis, 
            request.day_order
        )
    except services.WeekNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except services.TrainingDayAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/training-days", response_model=List[schemas.TrainingDayInfo])
async def list_training_days(week_id: int = Query(..., description="Week ID")):
    """List all training days in a week."""
    try:
        return await services.list_training_days(week_id)
    except services.WeekNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# === EXERCISES ===
@app.post("/api/exercises", response_model=schemas.ExerciseInfo)
async def create_exercise(request: schemas.CreateExerciseRequest):
    """Create a new exercise in the catalog."""
    try:
        return await services.create_exercise(request.name, request.equipment, request.target_muscle)
    except services.ExerciseAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/exercises", response_model=List[schemas.ExerciseInfo])
async def list_exercises():
    """List all exercises."""
    return await services.list_exercises()


# === DAY EXERCISES ===
@app.post("/api/day-exercises", response_model=schemas.DayExerciseInfo)
async def create_day_exercise(request: schemas.CreateDayExerciseRequest):
    """Add an exercise to a training day."""
    try:
        return await services.create_day_exercise(
            request.training_day_id,
            request.exercise_id,
            request.ex_order,
            request.priority_weight
        )
    except services.TrainingDayNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except services.ExerciseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except services.DayExerciseAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/day-exercises", response_model=List[schemas.DayExerciseInfo])
async def list_day_exercises(training_day_id: int = Query(..., description="Training Day ID")):
    """List all exercises for a training day."""
    try:
        return await services.list_day_exercises(training_day_id)
    except services.TrainingDayNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# === SETS ===
@app.post("/api/sets", response_model=schemas.SetInfo)
async def create_set(request: schemas.CreateSetRequest):
    """Create a new set for a day exercise."""
    try:
        return await services.create_set(
            request.day_exercise_id,
            request.set_order,
            request.target_weight
        )
    except services.DayExerciseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except services.SetAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sets", response_model=List[schemas.SetInfo])
async def list_sets(day_exercise_id: int = Query(..., description="Day Exercise ID")):
    """List all sets for a day exercise."""
    try:
        return await services.list_sets(day_exercise_id)
    except services.DayExerciseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# === LEGACY EXPORT ENDPOINT ===
@app.get("/api/programs/{program_name}/export")
async def export_program(program_name: str) -> schemas.ProgramExport:
    """
    Export a program's latest cycle data as JSON for frontend consumption.
    
    Args:
        program_name: Name of the program (e.g., "Full Body")
        
    Returns:
        ProgramExport: Structured program data with days and exercises
        
    Raises:
        HTTPException: If program not found or no data available
    """
    try:
        return await services.export_program_json(program_name)
    except services.ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
