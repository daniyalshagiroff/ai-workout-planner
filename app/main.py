"""
FastAPI application with workout program routes.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from . import services
from . import schemas


app = FastAPI(
    title="IRON AI Workout Planner",
    description="AI-powered workout planning and tracking",
    version="1.0.0",
)

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="../frontend"), name="static")


@app.get("/")
async def root():
    """Serve the main landing page."""
    return FileResponse("../frontend/index.html")


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


@app.get("/api/programs")
async def list_programs() -> list[schemas.ProgramSummary]:
    """List all available programs."""
    return await services.list_programs()


@app.get("/api/programs/{program_name}")
async def get_program(program_name: str) -> schemas.ProgramDetail:
    """
    Get detailed program information including latest cycle.
    
    Args:
        program_name: Name of the program
        
    Returns:
        ProgramDetail: Complete program information
    """
    try:
        return await services.get_program_detail(program_name)
    except services.ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
