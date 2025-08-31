import sqlite3

conn = sqlite3.connect('database/workout.db')
cur = conn.cursor()

print("=== Week 1, Day 3 Data ===")
cur.execute('''
    SELECT pd.id, pd.program_week_id, pd.day_of_week, pw.program_id, pw.week_number
    FROM program_day pd
    JOIN program_week pw ON pw.id = pd.program_week_id
    WHERE pw.week_number = 1 AND pd.day_of_week = 3
''')
week1_day3 = cur.fetchall()
for row in week1_day3:
    print(f"Day ID: {row[0]}, Week ID: {row[1]}, Day: {row[2]}, Program: {row[3]}, Week: {row[4]}")

print("\n=== Exercises for Week 1, Day 3 ===")
if week1_day3:
    day_id = week1_day3[0][0]
    cur.execute('''
        SELECT pde.id, pde.exercise_id, pde.position, e.name
        FROM program_day_exercise pde
        JOIN exercise e ON e.id = pde.exercise_id
        WHERE pde.program_day_id = ?
        ORDER BY pde.position
    ''', (day_id,))
    
    exercises = cur.fetchall()
    for row in exercises:
        print(f"Exercise ID: {row[0]}, Exercise: {row[1]}, Position: {row[2]}, Name: {row[3]}")
        
        # Get planned sets for this exercise
        cur.execute('''
            SELECT id, set_number, reps, weight
            FROM planned_set
            WHERE program_day_exercise_id = ?
            ORDER BY set_number
        ''', (row[0],))
        
        sets = cur.fetchall()
        for set_row in sets:
            print(f"  Set {set_row[1]}: {set_row[2]} reps, {set_row[3] or 'N/A'} kg (ID: {set_row[0]})")

conn.close()
