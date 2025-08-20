#!/usr/bin/env python3
"""
Initialize database, seed with data, and run the FastAPI application.
"""

import uvicorn
from app.db import init_database
from app.services import seed_foundational_program

def main():
    print("🚀 Initializing IRON AI Workout Planner...")
    
    # Initialize database
    print("📊 Creating database schema...")
    init_database()
    print("✅ Database schema created")
    
    # Seed with foundational program
    print("🌱 Seeding foundational program...")
    seed_foundational_program()
    print("✅ Foundational program seeded")
    
    # Run the application
    print("🌐 Starting FastAPI server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop the server")
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
