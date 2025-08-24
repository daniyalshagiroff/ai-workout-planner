"""
Pydantic schemas for API responses and data validation.
Defines the structure of all API responses and request models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ProgramInfo(BaseModel):
    """Basic program information."""
    name: str = Field(..., description="Program name")
    days_per_week: int = Field(..., description="Number of training days per week")


class WeekInfo(BaseModel):
    """Week information."""
    week_no: int = Field(..., description="Week number")


class DayExport(BaseModel):
    """Training day export data."""
    label: str = Field(..., description="Day label (e.g., 'Day 1', 'Push')")
    emphasis: str = Field(..., description="Day emphasis (e.g., 'chest', 'back', 'legs')")
    exercises: List[str] = Field(..., description="List of exercise names for this day")


class ProgramExport(BaseModel):
    """
    Complete program export for frontend consumption.
    Used by the /api/programs/{program_name}/export endpoint.
    """
    program: ProgramInfo = Field(..., description="Program information")
    week: WeekInfo = Field(..., description="Week information")
    days: List[DayExport] = Field(..., description="Training days with exercises")


class ProgramSummary(BaseModel):
    """Program summary for listing."""
    id: int = Field(..., description="Program ID")
    name: str = Field(..., description="Program name")
    days_per_week: int = Field(..., description="Number of training days per week")


class CycleInfo(BaseModel):
    """Cycle information."""
    id: int = Field(..., description="Cycle ID")
    cycle_no: int = Field(..., description="Cycle number")
    started_at: str = Field(..., description="Cycle start date (ISO format)")


class ProgramDetail(BaseModel):
    """
    Detailed program information.
    Used by the /api/programs/{program_name} endpoint.
    """
    id: int = Field(..., description="Program ID")
    name: str = Field(..., description="Program name")
    days_per_week: int = Field(..., description="Number of training days per week")
    latest_cycle: Optional[CycleInfo] = Field(None, description="Latest cycle information")


class ExerciseInfo(BaseModel):
    """Exercise information."""
    id: int = Field(..., description="Exercise ID")
    name: str = Field(..., description="Exercise name")
    equipment: str = Field(..., description="Required equipment")
    target_muscle: str = Field(..., description="Target muscle group")


class SetInfo(BaseModel):
    """Set information."""
    id: int = Field(..., description="Set ID")
    day_exercise_id: int = Field(..., description="Day exercise ID")
    set_order: int = Field(..., description="Set order within exercise")
    target_weight: Optional[float] = Field(None, description="Target weight")
    notes: Optional[str] = Field(None, description="Set notes")
    rpe: Optional[float] = Field(None, description="Rate of perceived exertion")
    rep: Optional[int] = Field(None, description="Number of reps")
    weight: Optional[float] = Field(None, description="Actual weight used")


class DayExerciseInfo(BaseModel):
    """Day exercise information with sets."""
    id: int = Field(..., description="Day exercise ID")
    exercise: ExerciseInfo = Field(..., description="Exercise information")
    ex_order: int = Field(..., description="Exercise order within day")
    sets: List[SetInfo] = Field(..., description="Sets for this exercise")


class TrainingDayDetail(BaseModel):
    """Detailed training day information."""
    id: int = Field(..., description="Training day ID")
    name: Optional[str] = Field(None, description="Day name")
    emphasis: Optional[str] = Field(None, description="Day emphasis")
    day_order: int = Field(..., description="Day order within week")
    exercises: List[DayExerciseInfo] = Field(..., description="Exercises for this day")


class WeekDetail(BaseModel):
    """Detailed week information."""
    id: int = Field(..., description="Week ID")
    week_no: int = Field(..., description="Week number")
    days: List[TrainingDayDetail] = Field(..., description="Training days in this week")


class CycleDetail(BaseModel):
    """Detailed cycle information."""
    id: int = Field(..., description="Cycle ID")
    cycle_no: int = Field(..., description="Cycle number")
    started_at: str = Field(..., description="Cycle start date (ISO format)")
    weeks: List[WeekDetail] = Field(..., description="Weeks in this cycle")


class ProgramFullDetail(BaseModel):
    """
    Full program detail with complete hierarchy.
    Used for detailed program views.
    """
    id: int = Field(..., description="Program ID")
    name: str = Field(..., description="Program name")
    days_per_week: int = Field(..., description="Number of training days per week")
    cycles: List[CycleDetail] = Field(..., description="All cycles for this program")


# Request models (for future use)
class CreateProgramRequest(BaseModel):
    """Request model for creating a new program."""
    name: str = Field(..., description="Program name", min_length=1, max_length=100)
    days_per_week: int = Field(..., description="Number of training days per week", ge=1, le=7)


class CreateCycleRequest(BaseModel):
    """Request model for creating a new cycle."""
    program_id: int = Field(..., description="Program ID")
    cycle_no: int = Field(..., description="Cycle number", ge=1)


class CreateWeekRequest(BaseModel):
    """Request model for creating a new week."""
    cycle_id: int = Field(..., description="Cycle ID")
    week_no: int = Field(..., description="Week number", ge=1)


class CreateTrainingDayRequest(BaseModel):
    """Request model for creating a new training day."""
    week_id: int = Field(..., description="Week ID")
    name: Optional[str] = Field(None, description="Day name", max_length=100)
    emphasis: Optional[str] = Field(None, description="Day emphasis", max_length=50)
    day_order: int = Field(..., description="Day order within week", ge=1)


class CreateExerciseRequest(BaseModel):
    """Request model for creating a new exercise."""
    name: str = Field(..., description="Exercise name", min_length=1, max_length=100)
    equipment: str = Field(..., description="Required equipment", min_length=1, max_length=50)
    target_muscle: str = Field(..., description="Target muscle group", min_length=1, max_length=50)


class CreateDayExerciseRequest(BaseModel):
    """Request model for creating a new day exercise."""
    training_day_id: int = Field(..., description="Training day ID")
    exercise_id: int = Field(..., description="Exercise ID")
    ex_order: int = Field(..., description="Exercise order within day", ge=1)
    priority_weight: Optional[float] = Field(None, description="Priority weight for the exercise", ge=0)


class CreateSetRequest(BaseModel):
    """Request model for creating a new set."""
    day_exercise_id: int = Field(..., description="Day exercise ID")
    set_order: int = Field(..., description="Set order", ge=1)
    target_weight: Optional[float] = Field(None, description="Target weight", ge=0)
    notes: Optional[str] = Field(None, description="Set notes", max_length=500)
    rpe: Optional[float] = Field(None, description="Rate of perceived exertion", ge=1, le=10)
    rep: Optional[int] = Field(None, description="Number of reps", ge=1)
    weight: Optional[float] = Field(None, description="Actual weight used", ge=0)


# Additional response models
class TrainingDayInfo(BaseModel):
    """Training day information."""
    id: int = Field(..., description="Training day ID")
    week_id: int = Field(..., description="Week ID")
    name: Optional[str] = Field(None, description="Day name")
    emphasis: Optional[str] = Field(None, description="Day emphasis")
    day_order: int = Field(..., description="Day order within week")


class DayExerciseInfo(BaseModel):
    """Day exercise information."""
    id: int = Field(..., description="Day exercise ID")
    training_day_id: int = Field(..., description="Training day ID")
    exercise_id: int = Field(..., description="Exercise ID")
    ex_order: int = Field(..., description="Exercise order within day")
    priority_weight: Optional[float] = Field(None, description="Priority weight")
    exercise: ExerciseInfo = Field(..., description="Exercise information")
