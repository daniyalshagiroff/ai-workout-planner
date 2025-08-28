BEGIN TRANSACTION;

PRAGMA foreign_keys = ON;

-- Invariant trigger: workout_set.set_number equals planned_set.set_number
-- And workout_exercise.program_day_exercise_id equals planned_set.program_day_exercise_id
-- And do not exceed planned sets count per program_day_exercise for a given workout_exercise

CREATE TRIGGER IF NOT EXISTS trg_workout_set_before_ins
BEFORE INSERT ON workout_set
FOR EACH ROW
BEGIN
  -- 1) match set_number
  SELECT CASE
    WHEN NEW.set_number <> (
      SELECT ps.set_number FROM planned_set ps WHERE ps.id = NEW.planned_set_id
    ) THEN RAISE(ABORT, 'workout_set.set_number must equal planned_set.set_number')
  END;

  -- 2) match program_day_exercise across planned_set and workout_exercise
  SELECT CASE
    WHEN (
      SELECT wex.program_day_exercise_id FROM workout_exercise wex WHERE wex.id = NEW.workout_exercise_id
    ) <> (
      SELECT ps.program_day_exercise_id FROM planned_set ps WHERE ps.id = NEW.planned_set_id
    ) THEN RAISE(ABORT, 'workout_exercise.program_day_exercise_id must equal planned_set.program_day_exercise_id')
  END;

  -- 3) do not exceed planned count for this workout_exercise's program_day_exercise
  SELECT CASE
    WHEN (
      (SELECT COUNT(*) FROM workout_set ws WHERE ws.workout_exercise_id = NEW.workout_exercise_id)
      + 1
    ) > (
      SELECT COUNT(*) FROM planned_set ps
      WHERE ps.program_day_exercise_id = (
        SELECT wex.program_day_exercise_id FROM workout_exercise wex WHERE wex.id = NEW.workout_exercise_id
      )
    ) THEN RAISE(ABORT, 'Actual workout sets cannot exceed planned sets for this exercise instance')
  END;
END;

CREATE TRIGGER IF NOT EXISTS trg_workout_set_before_upd
BEFORE UPDATE OF planned_set_id, workout_exercise_id, set_number ON workout_set
FOR EACH ROW
BEGIN
  -- 1) match set_number
  SELECT CASE
    WHEN NEW.set_number <> (
      SELECT ps.set_number FROM planned_set ps WHERE ps.id = NEW.planned_set_id
    ) THEN RAISE(ABORT, 'workout_set.set_number must equal planned_set.set_number')
  END;

  -- 2) match program_day_exercise across planned_set and workout_exercise
  SELECT CASE
    WHEN (
      SELECT wex.program_day_exercise_id FROM workout_exercise wex WHERE wex.id = NEW.workout_exercise_id
    ) <> (
      SELECT ps.program_day_exercise_id FROM planned_set ps WHERE ps.id = NEW.planned_set_id
    ) THEN RAISE(ABORT, 'workout_exercise.program_day_exercise_id must equal planned_set.program_day_exercise_id')
  END;

  -- 3) do not exceed planned count (only check if the wex changes; safe to always check)
  SELECT CASE
    WHEN (
      (SELECT COUNT(*) FROM workout_set ws WHERE ws.workout_exercise_id = NEW.workout_exercise_id AND ws.id <> OLD.id)
      + 1
    ) > (
      SELECT COUNT(*) FROM planned_set ps
      WHERE ps.program_day_exercise_id = (
        SELECT wex.program_day_exercise_id FROM workout_exercise wex WHERE wex.id = NEW.workout_exercise_id
      )
    ) THEN RAISE(ABORT, 'Actual workout sets cannot exceed planned sets for this exercise instance')
  END;
END;

-- Uniqueness of positions and set numbers already covered by UNIQUE constraints in schema.

COMMIT;


