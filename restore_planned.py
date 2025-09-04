import sqlite3
cur_db = r'database/workout.db'
bak_db = r'database/workout_backup_before_delete.db'
conn = sqlite3.connect(cur_db)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("ATTACH DATABASE ? AS bak", (bak_db,))
cur.execute("SELECT COUNT(*) AS c FROM bak.planned_set WHERE id >= 17")
print('candidates:', cur.fetchone()['c'])
# Insert missing by id; reps and weight set to NULL
cur.execute("BEGIN")
cur.execute(
    """
    INSERT INTO planned_set (id, program_day_exercise_id, set_number, reps, weight, rpe, rest_seconds)
    SELECT b.id, b.program_day_exercise_id, b.set_number, NULL, NULL, b.rpe, b.rest_seconds
    FROM bak.planned_set b
    WHERE b.id >= 17 AND NOT EXISTS (
      SELECT 1 FROM planned_set p WHERE p.id = b.id
    )
    """
)
ins_by_id = conn.total_changes
# Also insert any remaining missing combos by (program_day_exercise_id,set_number) to ensure plan exists
cur.execute(
    """
    INSERT INTO planned_set (program_day_exercise_id, set_number, reps, weight, rpe, rest_seconds)
    SELECT b.program_day_exercise_id, b.set_number, NULL, NULL, b.rpe, b.rest_seconds
    FROM bak.planned_set b
    WHERE b.id >= 17 AND NOT EXISTS (
      SELECT 1 FROM planned_set p 
      WHERE p.program_day_exercise_id = b.program_day_exercise_id AND p.set_number = b.set_number
    )
    """
)
conn.commit()
print('inserted_by_id_or_combo:', conn.total_changes - ins_by_id)
cur.execute("DETACH DATABASE bak")
conn.close()
print('done')
