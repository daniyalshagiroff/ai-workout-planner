BEGIN TRANSACTION;

PRAGMA foreign_keys = ON;

-- Drop old tables if present (fresh rebuild)
DROP TABLE IF EXISTS workout_set;
DROP TABLE IF EXISTS workout_exercise;
DROP TABLE IF EXISTS workout;
DROP TABLE IF EXISTS planned_set;
DROP TABLE IF EXISTS program_day_exercise;
DROP TABLE IF EXISTS program_day;
DROP TABLE IF EXISTS program_week;
DROP TABLE IF EXISTS program;
DROP TABLE IF EXISTS exercise;
DROP TABLE IF EXISTS users;

-- Users
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

-- Exercise catalog (global and user-specific)
CREATE TABLE exercise (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_user_id INTEGER NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  muscle_group TEXT NOT NULL,
  equipment TEXT,
  is_global INTEGER NOT NULL DEFAULT 0, -- 0/1 boolean
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  CHECK ((is_global = 1 AND owner_user_id IS NULL) OR (is_global = 0 AND owner_user_id IS NOT NULL))
);
-- Unique name per owner; and unique among globals
CREATE UNIQUE INDEX IF NOT EXISTS exercise_owner_name_uq
  ON exercise(owner_user_id, lower(name))
  WHERE owner_user_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS exercise_global_name_uq
  ON exercise(lower(name))
  WHERE owner_user_id IS NULL AND is_global = 1;

-- Program hierarchy
CREATE TABLE program (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);
CREATE INDEX IF NOT EXISTS program_owner_idx ON program(owner_user_id);

CREATE TABLE program_week (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  program_id INTEGER NOT NULL REFERENCES program(id) ON DELETE CASCADE,
  week_number INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  CHECK (week_number >= 1),
  UNIQUE(program_id, week_number)
);
CREATE INDEX IF NOT EXISTS program_week_program_idx ON program_week(program_id);

CREATE TABLE program_day (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  program_week_id INTEGER NOT NULL REFERENCES program_week(id) ON DELETE CASCADE,
  day_of_week INTEGER NOT NULL, -- 1..7
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  CHECK (day_of_week BETWEEN 1 AND 7),
  UNIQUE(program_week_id, day_of_week)
);
CREATE INDEX IF NOT EXISTS program_day_week_idx ON program_day(program_week_id);

CREATE TABLE program_day_exercise (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  program_day_id INTEGER NOT NULL REFERENCES program_day(id) ON DELETE CASCADE,
  exercise_id INTEGER NOT NULL REFERENCES exercise(id) ON DELETE RESTRICT,
  position INTEGER NOT NULL,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  CHECK (position >= 1),
  UNIQUE(program_day_id, position)
);
CREATE INDEX IF NOT EXISTS program_day_exercise_day_idx ON program_day_exercise(program_day_id);
CREATE INDEX IF NOT EXISTS program_day_exercise_ex_idx ON program_day_exercise(exercise_id);

CREATE TABLE planned_set (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  program_day_exercise_id INTEGER NOT NULL REFERENCES program_day_exercise(id) ON DELETE CASCADE,
  set_number INTEGER NOT NULL,
  reps INTEGER NOT NULL CHECK (reps >= 0),
  weight REAL CHECK (weight >= 0),
  rpe REAL CHECK (rpe IS NULL OR (rpe >= 0 AND rpe <= 10)),
  rest_seconds INTEGER CHECK (rest_seconds IS NULL OR rest_seconds >= 0),
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  CHECK (set_number >= 1),
  UNIQUE(program_day_exercise_id, set_number)
);
CREATE INDEX IF NOT EXISTS planned_set_pde_idx ON planned_set(program_day_exercise_id);

-- Workouts (actuals)
CREATE TABLE workout (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  program_day_id INTEGER NOT NULL REFERENCES program_day(id) ON DELETE RESTRICT,
  started_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  finished_at TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);
CREATE INDEX IF NOT EXISTS workout_owner_idx ON workout(owner_user_id);
CREATE INDEX IF NOT EXISTS workout_program_day_idx ON workout(program_day_id);

CREATE TABLE workout_exercise (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workout_id INTEGER NOT NULL REFERENCES workout(id) ON DELETE CASCADE,
  program_day_exercise_id INTEGER NOT NULL REFERENCES program_day_exercise(id) ON DELETE RESTRICT,
  position INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  CHECK (position >= 1),
  UNIQUE(workout_id, position)
);
CREATE INDEX IF NOT EXISTS workout_exercise_wk_idx ON workout_exercise(workout_id);
CREATE INDEX IF NOT EXISTS workout_exercise_pde_idx ON workout_exercise(program_day_exercise_id);

CREATE TABLE workout_set (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workout_exercise_id INTEGER NOT NULL REFERENCES workout_exercise(id) ON DELETE CASCADE,
  planned_set_id INTEGER NOT NULL REFERENCES planned_set(id) ON DELETE RESTRICT,
  set_number INTEGER NOT NULL,
  reps INTEGER NOT NULL CHECK (reps >= 0),
  weight REAL CHECK (weight >= 0),
  rpe REAL CHECK (rpe IS NULL OR (rpe >= 0 AND rpe <= 10)),
  rest_seconds INTEGER CHECK (rest_seconds IS NULL OR rest_seconds >= 0),
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  CHECK (set_number >= 1)
);
CREATE INDEX IF NOT EXISTS workout_set_wex_idx ON workout_set(workout_exercise_id);
CREATE INDEX IF NOT EXISTS workout_set_planned_idx ON workout_set(planned_set_id);

-- updated_at auto update triggers (per table)
CREATE TRIGGER IF NOT EXISTS trg_users_updated_at
AFTER UPDATE ON users FOR EACH ROW
BEGIN
  UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_exercise_updated_at
AFTER UPDATE ON exercise FOR EACH ROW
BEGIN
  UPDATE exercise SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_program_updated_at
AFTER UPDATE ON program FOR EACH ROW
BEGIN
  UPDATE program SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_program_week_updated_at
AFTER UPDATE ON program_week FOR EACH ROW
BEGIN
  UPDATE program_week SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_program_day_updated_at
AFTER UPDATE ON program_day FOR EACH ROW
BEGIN
  UPDATE program_day SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_program_day_exercise_updated_at
AFTER UPDATE ON program_day_exercise FOR EACH ROW
BEGIN
  UPDATE program_day_exercise SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_planned_set_updated_at
AFTER UPDATE ON planned_set FOR EACH ROW
BEGIN
  UPDATE planned_set SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_workout_updated_at
AFTER UPDATE ON workout FOR EACH ROW
BEGIN
  UPDATE workout SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_workout_exercise_updated_at
AFTER UPDATE ON workout_exercise FOR EACH ROW
BEGIN
  UPDATE workout_exercise SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_workout_set_updated_at
AFTER UPDATE ON workout_set FOR EACH ROW
BEGIN
  UPDATE workout_set SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

COMMIT;


