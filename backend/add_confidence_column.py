"""
Add confidence column to PostgreSQL database
Run this once on production to add the confidence column
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def add_confidence_column():
    """Add confidence column to issues table if it doesn't exist"""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return

    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    print(f"Connecting to PostgreSQL database...")
    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Check if confidence column exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='issues' AND column_name='confidence'
        """))

        if result.fetchone():
            print("✅ Confidence column already exists")
        else:
            print("Adding confidence column...")
            conn.execute(text("""
                ALTER TABLE issues
                ADD COLUMN confidence REAL DEFAULT 0.0
            """))
            conn.commit()
            print("✅ Confidence column added successfully")

    print("\n" + "="*80)
    print("Migration complete! You can now run recalculate_confidence.py")
    print("="*80)

if __name__ == '__main__':
    add_confidence_column()
