-- Key analytical queries examples

-- 1) Planned total sets count per week
-- :program_id, :week_number
SELECT pw.program_id,
       pw.week_number,
       COUNT(ps.id) AS planned_sets_count
FROM program_week pw
JOIN program_day pd ON pd.program_week_id = pw.id
JOIN program_day_exercise pde ON pde.program_day_id = pd.id
JOIN planned_set ps ON ps.program_day_exercise_id = pde.id
WHERE pw.program_id = :program_id
  AND pw.week_number = :week_number
GROUP BY pw.program_id, pw.week_number;

-- 2) Actual sets count per week
-- :program_id, :week_number
SELECT pw.program_id,
       pw.week_number,
       COUNT(ws.id) AS actual_sets_count
FROM program_week pw
JOIN program_day pd ON pd.program_week_id = pw.id
JOIN workout w ON w.program_day_id = pd.id
LEFT JOIN workout_exercise wex ON wex.workout_id = w.id
LEFT JOIN workout_set ws ON ws.workout_exercise_id = wex.id
WHERE pw.program_id = :program_id
  AND pw.week_number = :week_number
GROUP BY pw.program_id, pw.week_number;

-- 3) Actual sets by muscle group per week
-- :program_id, :week_number
SELECT e.muscle_group,
       COUNT(ws.id) AS actual_sets
FROM program_week pw
JOIN program_day pd ON pd.program_week_id = pw.id
JOIN program_day_exercise pde ON pde.program_day_id = pd.id
JOIN exercise e ON e.id = pde.exercise_id
JOIN workout w ON w.program_day_id = pd.id
JOIN workout_exercise wex ON wex.program_day_exercise_id = pde.id
JOIN workout_set ws ON ws.workout_exercise_id = wex.id
WHERE pw.program_id = :program_id
  AND pw.week_number = :week_number
GROUP BY e.muscle_group
ORDER BY e.muscle_group;

-- 4) Progress line: average weight/reps by week for an exercise
-- :exercise_id, :program_id
SELECT pw.week_number,
       AVG(ws.weight) AS avg_weight,
       AVG(ws.reps)   AS avg_reps
FROM program_day_exercise pde
JOIN program_day pd ON pd.id = pde.program_day_id
JOIN program_week pw ON pw.id = pd.program_week_id
JOIN workout_exercise wex ON wex.program_day_exercise_id = pde.id
JOIN workout_set ws ON ws.workout_exercise_id = wex.id
WHERE pde.exercise_id = :exercise_id
  AND pw.program_id = :program_id
GROUP BY pw.week_number
ORDER BY pw.week_number;

-- 5) Diagnostic: verify plan vs actual set numbers alignment for a workout_exercise
-- :workout_exercise_id
SELECT ws.id AS workout_set_id,
       ws.set_number AS actual_set_number,
       ps.set_number AS planned_set_number,
       (ws.set_number = ps.set_number) AS set_number_match
FROM workout_set ws
JOIN planned_set ps ON ps.id = ws.planned_set_id
WHERE ws.workout_exercise_id = :workout_exercise_id;


