#!/usr/bin/env python3
"""
Check exercise order in the database for each training day.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("database/workout.db")

def check_exercise_order():
    conn = sqlite3.connect(DB_PATH)
    try:
        # Get all training days with their emphasis
        cur = conn.execute("""
            SELECT td.id, td.name, td.emphasis, td.day_order
            FROM training_days td
            ORDER BY td.day_order
        """)
        training_days = cur.fetchall()
        
        print("=== EXERCISE ORDER BY TRAINING DAY ===\n")
        
        for day_id, day_name, emphasis, day_order in training_days:
            print(f"DAY {day_order} - {emphasis.upper()} EMPHASIS:")
            print("-" * 40)
            
            # Get exercises for this day in order
            cur = conn.execute("""
                SELECT de.ex_order, e.name, e.target_muscle
                FROM day_exercises de
                JOIN exercises e ON de.exercise_id = e.id
                WHERE de.training_day_id = ?
                ORDER BY de.ex_order
            """, (day_id,))
            
            exercises = cur.fetchall()
            for ex_order, ex_name, target_muscle in exercises:
                print(f"  {ex_order}. {ex_name.title()} ({target_muscle})")
            
            print()
        
    finally:
        conn.close()

if __name__ == "__main__":
    check_exercise_order()
