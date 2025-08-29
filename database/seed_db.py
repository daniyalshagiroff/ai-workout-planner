"""
Seed the database with initial data for testing and development.
"""

import sys
from pathlib import Path

# Add the parent directory to the Python path so we can import from app
sys.path.append(str(Path(__file__).parent.parent))

from app import services


def main():
    """Seed the database with foundational program data."""
    print("Seeding database with foundational program...")
    
    try:
        services.seed_foundational_program()
        print("✅ Database seeded successfully!")
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        raise


if __name__ == "__main__":
    main()


