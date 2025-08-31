import sqlite3

conn = sqlite3.connect('database/workout.db')
cur = conn.cursor()

print("=== User Programs ===")
cur.execute('SELECT * FROM user_program')
user_programs = cur.fetchall()
for row in user_programs:
    print(f"ID: {row[0]}, User: {row[1]}, Program: {row[2]}, Started: {row[3]}, Active: {row[4]}")

print("\n=== Available Programs ===")
cur.execute('SELECT id, title FROM program')
programs = cur.fetchall()
for row in programs:
    print(f"ID: {row[0]}, Title: {row[1]}")

conn.close()
