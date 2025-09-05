"""
FastAPI application wired to Program ↔ Workout services and reports (v2 endpoints).
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Response, Request, Form
from fastapi import Body
import uvicorn
from typing import Optional
from typing import Dict, Any, List

from . import services
from . import db as app_db
from .repo import UserRepo
from .security import hash_password, verify_password, sign_token, verify_token
from . import db as app_db
from .ai_client import generate_weekly_program, generate_weekly_program_raw

app = FastAPI(
    title="IRON AI Workout Planner",
    description="AI-powered workout planning and tracking",
    version="2.0.0",
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def root():
    return FileResponse("frontend/index.html")


@app.get("/ai-generated-plan.html")
async def ai_generated_plan():
    return FileResponse("frontend/ai-generated-plan.html")


@app.get("/my-plans.html")
async def my_plans():
    return FileResponse("frontend/my-plans.html")


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
        raise HTTPException(status_code=400, detail=f"{type(e).__name__}: {e}")


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
        
        # Ensure planned sets exist for this day; if none and week_number>1, generate from actuals of previous week
        # Ensure planned sets exist for this day; if none and week_number>1, generate from actuals of previous week
        cur.execute(
            """
            SELECT COUNT(ps.id) as cnt
            FROM program_day_exercise pde
            LEFT JOIN planned_set ps ON ps.program_day_exercise_id = pde.id
            WHERE pde.program_day_id = ?
            """,
            (day["id"],),
        )
        ps_result = cur.fetchone()
        ps_cnt = ps_result["cnt"] if ps_result else 0
        if ps_cnt == 0 and week_number > 1:
            try:
                # Generate planned sets for this week/day from actuals (idempotent)
                services.generate_week_progression_from_actuals(program_id, week_number - 1, week_number, owner_user_id)
            except Exception:
                pass

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


@app.post("/api/v2/programs/{program_id}/weeks/{to_week}/progress")
async def api_progress_week(program_id: int, to_week: int, from_week: int = Query(...)):
    """Generate planned sets for week `to_week` based on `from_week` with progression rules."""
    try:
        result = services.generate_week_progression(program_id, from_week, to_week)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v2/programs/{program_id}/weeks/{to_week}/progress-from-actuals")
async def api_progress_week_from_actuals(request: Request, program_id: int, to_week: int, from_week: int = Query(...)):
    """Generate planned sets for week `to_week` based on user's actuals in `from_week` (fallback to planned)."""
    token = request.cookies.get(COOKIE_NAME)
    auth_user_id = verify_token(token) if token else None
    if not auth_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        result = services.generate_week_progression_from_actuals(program_id, from_week, to_week, auth_user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v2/workouts/{workout_id}/log-set")
async def api_log_set(workout_id: int, position: int, planned_set_id: int, set_number: int, reps: int, weight: Optional[float] = None, rpe: Optional[float] = None, rest_seconds: Optional[int] = None):
    try:
        return services.log_workout_set(workout_id, position, planned_set_id, set_number, reps, weight, rpe, rest_seconds)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v2/workouts/{workout_id}/session")
async def api_get_workout_session(request: Request, workout_id: int):
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
        
        token = request.cookies.get(COOKIE_NAME)
        auth_user_id = verify_token(token) if token else None
        if not auth_user_id or auth_user_id != workout["owner_user_id"]:
            raise HTTPException(status_code=403, detail="Forbidden")

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
    return services.get_programs_list()


# Get program info by ID
@app.get("/api/v2/programs/{program_id}/info")
async def get_program_info(program_id: int):
    try:
        return services.get_program_info(program_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Get program weeks count by ID
@app.get("/api/programs/{program_id}/weeks")
async def get_program_weeks_by_id(program_id: int):
    try:
        return services.get_program_weeks_count(program_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Get program weeks count by name (legacy)
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


# Get specific week data by ID
@app.get("/api/programs/{program_id}/weeks/{week_number}")
async def get_program_week_by_id(program_id: int, week_number: int):
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM program WHERE id = ?", (program_id,))
        prog = cur.fetchone()
        if not prog:
            raise HTTPException(status_code=404, detail="Program not found")
        
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
        print(f"DEBUG: Found {len(days_rows)} days for week {week_number} of program {program_id}")
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
            print(f"DEBUG: Day {d['day_of_week']} has {len(ex_names)} exercises: {ex_names}")
            days_out.append({
                "day_number": d["day_of_week"],
                "exercises": ex_names,
            })

        return {
            "program_id": prog["id"],
            "program_name": prog["title"],
            "week_number": week_number,
            "days": days_out,
        }

# Get specific week data by name (legacy)
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
async def api_get_user_programs(request: Request, user_id: Optional[int] = None):
    """Get all programs selected by the authenticated user. Ignores user_id query param."""
    token = request.cookies.get(COOKIE_NAME)
    auth_user_id = verify_token(token) if token else None
    if not auth_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT up.id, up.user_id, up.program_id, up.started_at, up.is_active, 
                   up.current_week, up.current_day, up.notes, up.created_at,
                   p.title as program_title, p.description as program_description
            FROM user_program up
            JOIN program p ON p.id = up.program_id
            WHERE up.user_id = ?
            ORDER BY up.created_at DESC
            """,
            (auth_user_id,),
        )
        programs = []
        for row in cur.fetchall():
            programs.append(
                {
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
                    "created_at": row["created_at"],
                }
            )
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
async def api_get_day_status(request: Request, program_id: int, week_number: int, day_number: int):
    """Get completion status for a specific day"""
    with app_db.get_connection() as conn:
        cur = conn.cursor()
        token = request.cookies.get(COOKIE_NAME)
        auth_user_id = verify_token(token) if token else None
        if not auth_user_id:
            cur.execute(
                """
                SELECT pd.id
                FROM program_day pd
                JOIN program_week pw ON pw.id = pd.program_week_id
                WHERE pw.program_id = ? AND pw.week_number = ? AND pd.day_of_week = ?
                """,
                (program_id, week_number, day_number),
            )
            day = cur.fetchone()
            if not day:
                raise HTTPException(status_code=404, detail="Day not found")
            return {"completed": False, "total_sets": 0, "completed_sets": 0}
        cur.execute(
            """
            SELECT pd.id
            FROM program_day pd
            JOIN program_week pw ON pw.id = pd.program_week_id
            WHERE pw.program_id = ? AND pw.week_number = ? AND pd.day_of_week = ?
        """,
            (program_id, week_number, day_number),
        )
        day = cur.fetchone()
        if not day:
            raise HTTPException(status_code=404, detail="Day not found")
        cur.execute(
            """
            SELECT ps.id
            FROM planned_set ps
            JOIN program_day_exercise pde ON pde.id = ps.program_day_exercise_id
            WHERE pde.program_day_id = ?
        """,
            (day["id"],),
        )
        planned_sets = cur.fetchall()
        total_sets = len(planned_sets)
        if total_sets == 0:
            return {"completed": False, "total_sets": 0, "completed_sets": 0}
        cur.execute(
            """
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
        """,
            (day["id"], auth_user_id),
        )
        completed_result = cur.fetchone()
        completed_sets = completed_result["completed_count"] if completed_result else 0
        return {
            "completed": completed_sets >= total_sets,
            "total_sets": total_sets,
            "completed_sets": completed_sets,
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


# AI generation endpoint
@app.post("/api/v2/ai/generate-plan")
async def api_ai_generate_plan(payload: Dict[str, Any] = Body(...), raw: Optional[int] = Query(None)):
    """Generate a one-week JSON plan via OpenAI using form selections from ai-plan page.
    If raw=1 is provided, return raw model output (for debugging formatting issues)."""
    try:
        owner_user_id: int = int(payload.get("owner_user_id"))
        
        # Generate unique title based on user parameters and timestamp
        import datetime
        experience = payload.get("experience", "novice")
        days = payload.get("days", 3)
        equipment = payload.get("equipment", [])
        priorities = payload.get("priorities", [])
        
        # Create descriptive title
        exp_map = {"novice": "Beginner", "6_12": "Intermediate", "1_3": "Advanced", "3_plus": "Expert"}
        exp_name = exp_map.get(experience, "Beginner")
        
        priority_text = ""
        if priorities:
            priority_text = f" - {', '.join(priorities[:2])}"
        
        equipment_text = ""
        if equipment:
            equipment_text = f" ({', '.join(equipment[:2])})"
        
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        title: str = f"{exp_name} {days}Day{priority_text}{equipment_text} - {timestamp}"
        
        description: Optional[str] = payload.get("description")
        # Map experience from UI to expected values
        raw_experience: str = str(payload.get("experience") or "novice")
        experience_map = {"novice": "novice", "6_12": "intermediate", "1_3": "intermediate", "3_plus": "advanced"}
        experience = experience_map.get(raw_experience, "novice")
        days_per_week: int = int(payload.get("days") or payload.get("days_per_week") or 3)
        # Normalize equipment (accept list or comma-separated string)
        equipment_raw = payload.get("equipment")
        if isinstance(equipment_raw, str):
            equipment: List[str] = [s.strip() for s in equipment_raw.split(",") if s.strip()]
        else:
            equipment = list(equipment_raw or [])
        # Normalize priorities (accept list or comma-separated string)
        priorities_raw = payload.get("priorities")
        if isinstance(priorities_raw, str):
            priorities_list: List[str] = [s.strip() for s in priorities_raw.split(",") if s.strip()]
        else:
            priorities_list = list(priorities_raw or [])
        priority_joined = ", ".join(priorities_list[:2]) if priorities_list else None

        if raw:
            content = generate_weekly_program_raw(
                owner_user_id=owner_user_id,
                title=title,
                description=description,
                experience=experience,
                days_per_week=days_per_week,
                equipment=equipment,
                priority=priority_joined,
            )
            return {"raw": content}

        result = generate_weekly_program(
            owner_user_id=owner_user_id,
            title=title,
            description=description,
            experience=experience,
            days_per_week=days_per_week,
            equipment=equipment,
            priority=priority_joined,
        )
        
        # Debug: Print the AI-generated result
        print(f"DEBUG: AI generated result:")
        print(f"  Title: {result.get('title')}")
        print(f"  Weeks: {len(result.get('weeks', []))}")
        if result.get('weeks'):
            first_week = result['weeks'][0]
            print(f"  First week days: {len(first_week.get('days', []))}")
            for i, day in enumerate(first_week.get('days', [])):
                print(f"    Day {i+1}: day_of_week={day.get('day_of_week')}, exercises={len(day.get('exercises', []))}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{type(e).__name__}: {e}")


@app.post("/api/v2/ai/save-plan")
async def api_save_ai_plan(request: Request, plan_data: Dict[str, Any] = Body(...)):
    """Save an AI-generated plan to the database."""
    try:
        # Get authenticated user ID from request
        token = request.cookies.get(COOKIE_NAME)
        auth_user_id = verify_token(token) if token else None
        if not auth_user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Use authenticated user ID, not the one from plan data
        owner_user_id: int = auth_user_id
        print(f"DEBUG: Authenticated user_id: {auth_user_id}")
        print(f"DEBUG: Plan data owner_user_id: {plan_data.get('owner_user_id')}")
        print(f"DEBUG: Using owner_user_id: {owner_user_id}")
        
        title: str = str(plan_data.get("title") or "AI Program")
        description: Optional[str] = plan_data.get("description")
        weeks = plan_data.get("weeks", [])
        
        if not weeks:
            raise HTTPException(status_code=400, detail="No weeks data provided")
        
        # Create the program
        program = services.create_program_v2(owner_user_id, title, description)
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
            services.ensure_week(program_id, week_number)
            
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
                services.ensure_day(program_id, week_number, day_of_week)
                
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
                        exercise = services.create_exercise(
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
                        exercises_list = services.list_exercises(owner_user_id)
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
                        result = services.add_day_exercise(
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
                        # Exercise might already be added to this day
                        pass
                    
                    # Add planned sets with progression for weeks 2-8
                    for set_data in planned_sets:
                        set_number = set_data.get("set_number", 1)
                        base_reps = set_data.get("reps", 8)
                        base_weight = set_data.get("weight")
                        rpe = set_data.get("rpe")
                        rest_seconds = set_data.get("rest_seconds")
                        
                        # Apply progression for weeks 2-8
                        if week_number > 1:
                            # Increase reps by 1 every 2 weeks, or increase weight by 2.5% every week
                            if week_number % 2 == 0:
                                reps = base_reps + 1
                                weight = base_weight
                            else:
                                reps = base_reps
                                weight = base_weight * 1.025 if base_weight else None
                        else:
                            reps = base_reps
                            weight = base_weight
                        
                        try:
                            services.add_planned_set(
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
                            # Set might already exist
                            pass
        
        # Auto-attach this new program to the creating user so it shows up in My Plans
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
            # If linkage already exists or insertion fails, continue without blocking
            pass

        return {
            "message": "Plan saved successfully",
            "program_id": program_id,
            "program_title": title
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
