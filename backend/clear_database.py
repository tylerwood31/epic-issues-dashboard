"""
Clear all issues from the database
Run this on production to reset the database before full refresh
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def clear_database():
    """Clear all issues from the database"""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return

    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    print(f"Connecting to database...")
    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Count before delete
        result = conn.execute(text("SELECT COUNT(*) FROM issues"))
        count_before = result.fetchone()[0]
        print(f"Found {count_before} issues in database")

        # Delete all issues
        print("Deleting all issues...")
        conn.execute(text("DELETE FROM issues"))
        conn.commit()

        # Count after delete
        result = conn.execute(text("SELECT COUNT(*) FROM issues"))
        count_after = result.fetchone()[0]
        print(f"✅ Database cleared! Issues remaining: {count_after}")

    print("\n" + "="*80)
    print("Database cleared successfully!")
    print("Now run: curl -X POST http://localhost:10000/refresh")
    print("="*80)

if __name__ == '__main__':
    clear_database()
