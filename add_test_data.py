import sqlite3

# Connect to database
conn = sqlite3.connect('database/workout.db')

# Add test user program
conn.execute('INSERT INTO user_program (user_id, program_id, notes) VALUES (1, 3, "Test selection")')

# Commit and close
conn.commit()
conn.close()

print("Test data added successfully!")
