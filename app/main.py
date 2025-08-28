"""
FastAPI application wired to Program ↔ Workout services and reports (v2 endpoints).
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Response, Request, Form
import uvicorn
from typing import Optional

from . import services
from . import db as app_db
from .repo import UserRepo
from .security import hash_password, verify_password, sign_token, verify_token
from . import db as app_db

app = FastAPI(
    title="IRON AI Workout Planner",
    description="AI-powered workout planning and tracking",
    version="2.0.0",
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def root():
    return FileResponse("frontend/index.html")


# Auth endpoints (cookie-based)
COOKIE_NAME = "auth_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7


@app.post("/api/v2/auth/register")
async def api_register(email: str = Form(...), password: str = Form(...)):
    existing = UserRepo.get_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    pwd_hash = hash_password(password)
    user_id = UserRepo.create(email, pwd_hash)
    return {"id": user_id, "email": email}


@app.post("/api/v2/auth/login")
async def api_login(response: Response, email: str = Form(...), password: str = Form(...)):
    user = UserRepo.get_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = sign_token(user["id"])  # type: ignore
    response.set_cookie(COOKIE_NAME, token, max_age=COOKIE_MAX_AGE, httponly=True, samesite="lax")
    return {"ok": True}


@app.post("/api/v2/auth/logout")
async def api_logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@app.get("/api/v2/auth/me")
async def api_me(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return {"authenticated": False}
    user_id = verify_token(token)
    if not user_id:
        return {"authenticated": False}
    user = UserRepo.get_by_id(user_id)
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": {"id": user["id"], "email": user["email"]}}


# v2 EXERCISES
@app.post("/api/v2/exercises")
async def api_create_exercise(
    name: str = Form(...),
    muscle_group: str = Form(...),
    equipment: Optional[str] = Form(None),
    is_global: bool = Form(False),
    owner_user_id: Optional[int] = Form(None),
):
    try:
        # Normalize according to DB CHECK constraint:
        # (is_global=1 AND owner_user_id IS NULL) OR (is_global=0 AND owner_user_id IS NOT NULL)
        if is_global:
            owner_user_id = None
        else:
            if owner_user_id is None:
                raise HTTPException(status_code=400, detail="owner_user_id is required for user-scoped exercise")
        return services.create_exercise_v2(owner_user_id, name, muscle_group, equipment, is_global)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v2/exercises")
async def api_list_exercises(owner_user_id: Optional[int] = None):
    return services.list_exercises_v2(owner_user_id)


# v2 PROGRAM BUILDING
@app.post("/api/v2/programs")
async def api_create_program(
    owner_user_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
):
    try:
        return services.create_program_v2(owner_user_id, title, description)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v2/programs/{program_id}/weeks/{week_number}")
async def api_ensure_week(program_id: int, week_number: int):
    try:
        return services.ensure_week(program_id, week_number)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v2/programs/{program_id}/weeks/{week_number}/days/{day_of_week}")
async def api_ensure_day(program_id: int, week_number: int, day_of_week: int):
    try:
        return services.ensure_day(program_id, week_number, day_of_week)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v2/programs/{program_id}/weeks/{week_number}/days/{day_of_week}/exercises")
async def api_add_day_exercise(
    program_id: int,
    week_number: int,
    day_of_week: int,
    exercise_id: int = Form(...),
    position: int = Form(...),
    notes: Optional[str] = Form(None),
):
    try:
        return services.add_day_exercise(program_id, week_number, day_of_week, exercise_id, position, notes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v2/programs/{program_id}/weeks/{week_number}/days/{day_of_week}/exercises/{position}/planned-sets")
async def api_add_planned_set(
    program_id: int,
    week_number: int,
    day_of_week: int,
    position: int,
    set_number: int = Form(...),
    reps: int = Form(...),
    weight: Optional[float] = Form(None),
    rpe: Optional[float] = Form(None),
    rest_seconds: Optional[int] = Form(None),
):
    try:
        return services.add_planned_set(program_id, week_number, day_of_week, position, set_number, reps, weight, rpe, rest_seconds)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# v2 WORKOUTS
@app.post("/api/v2/workouts/start")
async def api_start_workout(owner_user_id: int, program_id: int, week_number: int, day_of_week: int):
    try:
        return services.start_workout(owner_user_id, program_id, week_number, day_of_week)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v2/workouts/{workout_id}/log-set")
async def api_log_set(workout_id: int, position: int, planned_set_id: int, set_number: int, reps: int, weight: Optional[float] = None, rpe: Optional[float] = None, rest_seconds: Optional[int] = None):
    try:
        return services.log_workout_set(workout_id, position, planned_set_id, set_number, reps, weight, rpe, rest_seconds)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v2/workouts/{workout_id}/finish")
async def api_finish_workout(workout_id: int, notes: Optional[str] = None):
    try:
        return services.finish_workout(workout_id, notes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# v2 REPORTS
@app.get("/api/v2/reports/planned-sets")
async def api_report_planned_sets(program_id: int, week_number: int):
    return services.report_total_planned_sets(program_id, week_number)


@app.get("/api/v2/reports/actual-sets")
async def api_report_actual_sets(program_id: int, week_number: int):
    return services.report_total_actual_sets(program_id, week_number)


@app.get("/api/v2/reports/sets-by-muscle-group")
async def api_report_sets_by_muscle_group(program_id: int, week_number: int):
    return services.report_sets_by_muscle_group(program_id, week_number)


@app.get("/api/v2/reports/progress")
async def api_report_progress(program_id: int, exercise_id: int):
    return services.report_progress_for_exercise(program_id, exercise_id)


# Read-only: list programs (for ready-made plans)
@app.get("/api/v2/programs/list")
async def api_programs_list():
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, title, description FROM program ORDER BY title")
        return [dict(row) for row in cur.fetchall()]


# Legacy export endpoint (used by program-view.html)
@app.get("/api/programs/{program_name}/export")
async def export_program(program_name: str):
    # Build a lightweight export from current DB schema (week 1 by default)
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        # Find program by title
        cur.execute("SELECT id, title FROM program WHERE title = ?", (program_name,))
        prog = cur.fetchone()
        if not prog:
            raise HTTPException(status_code=404, detail=f"Program '{program_name}' not found")
        program_id = prog["id"]

        # Get week 1
        cur.execute("SELECT id FROM program_week WHERE program_id = ? AND week_number = 1", (program_id,))
        week = cur.fetchone()
        if not week:
            raise HTTPException(status_code=404, detail="Week 1 not found for this program")
        week_id = week["id"]

        # Days and exercises
        cur.execute(
            "SELECT id, day_of_week FROM program_day WHERE program_week_id = ? ORDER BY day_of_week",
            (week_id,),
        )
        days_rows = cur.fetchall()
        days_out = []
        for d in days_rows:
            cur.execute(
                """
                SELECT e.name
                FROM program_day_exercise pde
                JOIN exercise e ON e.id = pde.exercise_id
                WHERE pde.program_day_id = ?
                ORDER BY pde.position
                """,
                (d["id"],),
            )
            ex_names = [r[0] for r in cur.fetchall()]
            # Legacy export expects label/emphasis fields
            days_out.append({
                "label": f"Day {d['day_of_week']}",
                "emphasis": "",
                "exercises": ex_names,
            })

        export = {
            "program": {"name": prog["title"], "days_per_week": len(days_out)},
            "week": {"week_no": 1},
            "days": days_out,
        }
        return export


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
