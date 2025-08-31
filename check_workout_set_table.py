import sqlite3

conn = sqlite3.connect('database/workout.db')
cur = conn.cursor()

print("=== Workout Set Table Schema ===")
cur.execute("PRAGMA table_info(workout_set)")
columns = cur.fetchall()
for col in columns:
    print(f"Column: {col[1]} ({col[2]})")

print("\n=== Workout Set Table Data ===")
cur.execute("SELECT * FROM workout_set")
sets = cur.fetchall()
for row in sets:
    print(f"Row: {row}")

conn.close()
