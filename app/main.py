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
async def api_start_workout(
    owner_user_id: int = Form(...),
    program_id: int = Form(...),
    week_number: int = Form(...),
    day_of_week: int = Form(...)
):
    """Start a new workout session"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        
        # Check if program exists
        cur.execute("SELECT id, title FROM program WHERE id = ?", (program_id,))
        program = cur.fetchone()
        if not program:
            raise HTTPException(status_code=404, detail="Program not found")
        
        # Check if week exists
        cur.execute("SELECT id FROM program_week WHERE program_id = ? AND week_number = ?", (program_id, week_number))
        week = cur.fetchone()
        if not week:
            raise HTTPException(status_code=404, detail="Week not found")
        
        # Check if day exists
        cur.execute("SELECT id FROM program_day WHERE program_week_id = ? AND day_of_week = ?", (week["id"], day_of_week))
        day = cur.fetchone()
        if not day:
            raise HTTPException(status_code=404, detail="Day not found")
        
        # Check if workout already exists for this day
        cur.execute("SELECT id FROM workout WHERE owner_user_id = ? AND program_day_id = ?", 
                   (owner_user_id, day["id"]))
        existing = cur.fetchone()
        if existing:
            # Return existing workout
            return {"workout_id": existing["id"], "message": "Workout already exists"}
        
        # Get exercises for this day first
        cur.execute("""
            SELECT pde.id, pde.exercise_id, pde.position
            FROM program_day_exercise pde
            WHERE pde.program_day_id = ?
            ORDER BY pde.position
        """, (day["id"],))
        
        exercises = cur.fetchall()
        
        # Create new workout with transaction
        with app_db.transaction(conn) as cur:
            # Create workout
            cur.execute("""
                INSERT INTO workout (owner_user_id, program_day_id, started_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (owner_user_id, day["id"]))
            workout_id = cur.lastrowid
            
            # Create workout exercises
            for exercise in exercises:
                cur.execute("""
                    INSERT INTO workout_exercise (workout_id, program_day_exercise_id, position)
                    VALUES (?, ?, ?)
                """, (workout_id, exercise["id"], exercise["position"]))
        
        return {"workout_id": workout_id, "message": "Workout started successfully"}


@app.post("/api/v2/workouts/{workout_id}/log-set")
async def api_log_set(workout_id: int, position: int, planned_set_id: int, set_number: int, reps: int, weight: Optional[float] = None, rpe: Optional[float] = None, rest_seconds: Optional[int] = None):
    try:
        return services.log_workout_set(workout_id, position, planned_set_id, set_number, reps, weight, rpe, rest_seconds)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v2/workouts/{workout_id}/session")
async def api_get_workout_session(workout_id: int):
    """Get workout session data with exercises and planned sets"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        
        # Get workout info
        cur.execute("""
            SELECT w.id, w.owner_user_id, w.program_day_id, w.started_at,
                   p.title as program_title, pw.week_number, pd.day_of_week
            FROM workout w
            JOIN program_day pd ON pd.id = w.program_day_id
            JOIN program_week pw ON pw.id = pd.program_week_id
            JOIN program p ON p.id = pw.program_id
            WHERE w.id = ?
        """, (workout_id,))
        
        workout = cur.fetchone()
        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")
        
        # Get exercises with their planned sets
        cur.execute("""
            SELECT we.id, we.position, e.name as exercise_name,
                   pde.id as program_day_exercise_id
            FROM workout_exercise we
            JOIN program_day_exercise pde ON pde.id = we.program_day_exercise_id
            JOIN exercise e ON e.id = pde.exercise_id
            WHERE we.workout_id = ?
            ORDER BY we.position
        """, (workout_id,))
        
        exercises = []
        for exercise_row in cur.fetchall():
            # Get planned sets for this exercise
            cur.execute("""
                SELECT ps.id, ps.set_number, ps.reps as planned_reps, ps.weight as planned_weight
                FROM planned_set ps
                WHERE ps.program_day_exercise_id = ?
                ORDER BY ps.set_number
            """, (exercise_row["program_day_exercise_id"],))
            
            sets = []
            for set_row in cur.fetchall():
                # Check if this set has been logged
                cur.execute("""
                    SELECT ws.reps as actual_reps, ws.weight as actual_weight
                    FROM workout_set ws
                    WHERE ws.planned_set_id = ?
                """, (set_row["id"],))
                
                actual_set = cur.fetchone()
                
                sets.append({
                    "id": set_row["id"],
                    "set_number": set_row["set_number"],
                    "planned_reps": set_row["planned_reps"],
                    "planned_weight": set_row["planned_weight"],
                    "actual_reps": actual_set["actual_reps"] if actual_set else None,
                    "actual_weight": actual_set["actual_weight"] if actual_set else None
                })
            
            exercises.append({
                "id": exercise_row["id"],
                "position": exercise_row["position"],
                "exercise_name": exercise_row["exercise_name"],
                "sets": sets
            })
        
        return {
            "workout": dict(workout),
            "exercises": exercises
        }


@app.post("/api/v2/workouts/{workout_id}/sets/{planned_set_id}")
async def api_log_set(
    workout_id: int, 
    planned_set_id: int,
    reps: int = Form(...),
    weight: Optional[float] = Form(None)
):
    """Log a workout set"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        
        # Verify workout exists
        cur.execute("SELECT id FROM workout WHERE id = ?", (workout_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Workout not found")
        
        # Verify planned set exists
        cur.execute("SELECT id FROM planned_set WHERE id = ?", (planned_set_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Planned set not found")
        
        # Get workout_exercise_id for this planned_set_id
        cur.execute("""
            SELECT we.id as workout_exercise_id, ps.set_number
            FROM workout_exercise we
            JOIN program_day_exercise pde ON pde.id = we.program_day_exercise_id
            JOIN planned_set ps ON ps.program_day_exercise_id = pde.id
            WHERE we.workout_id = ? AND ps.id = ?
        """, (workout_id, planned_set_id))
        
        workout_exercise = cur.fetchone()
        if not workout_exercise:
            raise HTTPException(status_code=404, detail="Workout exercise not found for this planned set")
        
        # Check if set already logged
        cur.execute("SELECT id FROM workout_set WHERE planned_set_id = ?", (planned_set_id,))
        existing = cur.fetchone()
        
        if existing:
            # Update existing set
            with app_db.transaction(conn) as cur:
                cur.execute("""
                    UPDATE workout_set 
                    SET reps = ?, weight = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE planned_set_id = ?
                """, (reps, weight, planned_set_id))
        else:
            # Create new set
            with app_db.transaction(conn) as cur:
                cur.execute("""
                    INSERT INTO workout_set (workout_exercise_id, planned_set_id, set_number, reps, weight)
                    VALUES (?, ?, ?, ?, ?)
                """, (workout_exercise["workout_exercise_id"], planned_set_id, workout_exercise["set_number"], reps, weight))
        
        return {"message": "Set logged successfully"}


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


# Get program weeks count
@app.get("/api/programs/{program_name}/weeks")
async def get_program_weeks(program_name: str):
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        # Find program by title (case-insensitive search)
        cur.execute("SELECT id, title FROM program WHERE UPPER(title) = UPPER(?)", (program_name,))
        prog = cur.fetchone()
        if not prog:
            # Try to find similar programs for debugging
            cur.execute("SELECT title FROM program")
            all_programs = [row["title"] for row in cur.fetchall()]
            raise HTTPException(
                status_code=404, 
                detail=f"Program '{program_name}' not found. Available programs: {all_programs}"
            )
        program_id = prog["id"]

        # Get weeks count
        cur.execute("SELECT COUNT(*) as weeks_count FROM program_week WHERE program_id = ?", (program_id,))
        weeks_count = cur.fetchone()["weeks_count"]
        
        return {"program_name": prog["title"], "weeks_count": weeks_count}


# Get specific week data
@app.get("/api/programs/{program_name}/weeks/{week_number}")
async def get_program_week(program_name: str, week_number: int):
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        # Find program by title (case-insensitive search)
        cur.execute("SELECT id, title FROM program WHERE UPPER(title) = UPPER(?)", (program_name,))
        prog = cur.fetchone()
        if not prog:
            # Try to find similar programs for debugging
            cur.execute("SELECT title FROM program")
            all_programs = [row["title"] for row in cur.fetchall()]
            raise HTTPException(
                status_code=404, 
                detail=f"Program '{program_name}' not found. Available programs: {all_programs}"
            )
        program_id = prog["id"]

        # Get specific week
        cur.execute("SELECT id FROM program_week WHERE program_id = ? AND week_number = ?", (program_id, week_number))
        week = cur.fetchone()
        if not week:
            raise HTTPException(status_code=404, detail=f"Week {week_number} not found for this program")
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
            days_out.append({
                "day_number": d["day_of_week"],
                "exercises": ex_names,
            })

        return {
            "program_name": prog["title"],
            "week_number": week_number,
            "days": days_out,
        }


# User program management
@app.post("/api/v2/user-programs")
async def api_select_program(
    user_id: int = Form(...),
    program_id: int = Form(...),
    notes: Optional[str] = Form(None)
):
    """Select a program for a user"""
    with app_db.get_connection() as conn:
        # Check if program exists
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM program WHERE id = ?", (program_id,))
        program = cur.fetchone()
        if not program:
            raise HTTPException(status_code=404, detail="Program not found")
        
        # Check if user already has this program
        cur.execute("SELECT id FROM user_program WHERE user_id = ? AND program_id = ?", (user_id, program_id))
        existing = cur.fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="User already has this program selected")
        
        # Insert new user program with transaction
        with app_db.transaction(conn) as cur:
            cur.execute(
                "INSERT INTO user_program (user_id, program_id, notes) VALUES (?, ?, ?)",
                (user_id, program_id, notes)
            )
            user_program_id = cur.lastrowid
        
        return {
            "id": user_program_id,
            "user_id": user_id,
            "program_id": program_id,
            "program_title": program["title"],
            "started_at": "CURRENT_TIMESTAMP",
            "is_active": True,
            "current_week": 1,
            "current_day": 1
        }


@app.get("/api/v2/user-programs")
async def api_get_user_programs(user_id: int):
    """Get all programs selected by a user"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT up.id, up.user_id, up.program_id, up.started_at, up.is_active, 
                   up.current_week, up.current_day, up.notes, up.created_at,
                   p.title as program_title, p.description as program_description
            FROM user_program up
            JOIN program p ON p.id = up.program_id
            WHERE up.user_id = ?
            ORDER BY up.created_at DESC
        """, (user_id,))
        
        programs = []
        for row in cur.fetchall():
            programs.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "program_id": row["program_id"],
                "program_title": row["program_title"],
                "program_description": row["program_description"],
                "started_at": row["started_at"],
                "is_active": bool(row["is_active"]),
                "current_week": row["current_week"],
                "current_day": row["current_day"],
                "notes": row["notes"],
                "created_at": row["created_at"]
            })
        
        return programs


@app.put("/api/v2/user-programs/{user_program_id}/activate")
async def api_activate_program(user_program_id: int):
    """Activate a user program (deactivate others)"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        
        # Get user_id for this program
        cur.execute("SELECT user_id FROM user_program WHERE id = ?", (user_program_id,))
        user_program = cur.fetchone()
        if not user_program:
            raise HTTPException(status_code=404, detail="User program not found")
        
        user_id = user_program["user_id"]
        
        # Update with transaction
        with app_db.transaction(conn) as cur:
            # Deactivate all other programs for this user
            cur.execute("UPDATE user_program SET is_active = 0 WHERE user_id = ?", (user_id,))
            
            # Activate the selected program
            cur.execute("UPDATE user_program SET is_active = 1 WHERE id = ?", (user_program_id,))
        
        return {"message": "Program activated successfully"}


@app.delete("/api/v2/user-programs/{user_program_id}")
async def api_remove_user_program(user_program_id: int):
    """Remove a program from user's selected programs"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        
        # Check if user program exists
        cur.execute("SELECT id FROM user_program WHERE id = ?", (user_program_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User program not found")
        
        # Delete the user program with transaction
        with app_db.transaction(conn) as cur:
            cur.execute("DELETE FROM user_program WHERE id = ?", (user_program_id,))
        
        return {"message": "Program removed successfully"}


@app.get("/api/v2/programs/{program_id}/weeks/{week_number}/days/{day_number}/status")
async def api_get_day_status(program_id: int, week_number: int, day_number: int, user_id: int = 1):
    """Get completion status for a specific day"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        
        # Find the program day
        cur.execute("""
            SELECT pd.id
            FROM program_day pd
            JOIN program_week pw ON pw.id = pd.program_week_id
            WHERE pw.program_id = ? AND pw.week_number = ? AND pd.day_of_week = ?
        """, (program_id, week_number, day_number))
        
        day = cur.fetchone()
        if not day:
            raise HTTPException(status_code=404, detail="Day not found")
        
        # Get all planned sets for this day
        cur.execute("""
            SELECT ps.id
            FROM planned_set ps
            JOIN program_day_exercise pde ON pde.id = ps.program_day_exercise_id
            WHERE pde.program_day_id = ?
        """, (day["id"],))
        
        planned_sets = cur.fetchall()
        total_sets = len(planned_sets)
        
        if total_sets == 0:
            return {"completed": True, "total_sets": 0, "completed_sets": 0}
        
        # Get completed sets for this day
        cur.execute("""
            SELECT COUNT(*) as completed_count
            FROM workout_set ws
            JOIN planned_set ps ON ps.id = ws.planned_set_id
            JOIN program_day_exercise pde ON pde.id = ps.program_day_exercise_id
            JOIN workout w ON w.id = (
                SELECT we.workout_id 
                FROM workout_exercise we 
                WHERE we.program_day_exercise_id = pde.id
                LIMIT 1
            )
            WHERE pde.program_day_id = ? AND w.owner_user_id = ?
        """, (day["id"], user_id))
        
        completed_result = cur.fetchone()
        completed_sets = completed_result["completed_count"] if completed_result else 0
        
        return {
            "completed": completed_sets >= total_sets,
            "total_sets": total_sets,
            "completed_sets": completed_sets
        }


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
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
