#!/usr/bin/env python3
"""
Migrate from SQLite to PostgreSQL for production persistence
"""
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from database import Base, Issue
from sqlalchemy.orm import sessionmaker

load_dotenv()

def migrate_to_postgres():
    """Migrate data from SQLite to PostgreSQL"""

    # Get PostgreSQL URL from environment
    postgres_url = os.getenv('DATABASE_URL')
    if not postgres_url:
        print("ERROR: DATABASE_URL not set in environment")
        print("Set it to your Render PostgreSQL URL")
        return

    # Handle Render's postgres:// vs postgresql:// prefix
    if postgres_url.startswith('postgres://'):
        postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)

    print("Connecting to PostgreSQL...")
    pg_engine = create_engine(postgres_url)

    # Create tables in PostgreSQL
    print("Creating tables...")
    Base.metadata.create_all(pg_engine)

    # Connect to SQLite
    print("Loading data from SQLite...")
    sqlite_engine = create_engine('sqlite:///issues.db')
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()

    # Get all issues from SQLite
    issues = sqlite_session.query(Issue).all()
    print(f"Found {len(issues)} issues in SQLite")

    # Insert into PostgreSQL
    print("Migrating to PostgreSQL...")
    PgSession = sessionmaker(bind=pg_engine)
    pg_session = PgSession()

    for issue in issues:
        # Create new issue object with same data
        new_issue = Issue(
            issue_key=issue.issue_key,
            summary=issue.summary,
            description=issue.description,
            status=issue.status,
            priority=issue.priority,
            category=issue.category,
            created_date=issue.created_date,
            updated_date=issue.updated_date,
            assignee=issue.assignee,
            reporter=issue.reporter,
            last_fetched=issue.last_fetched
        )
        pg_session.merge(new_issue)  # Use merge to handle duplicates

    pg_session.commit()
    print(f"✅ Successfully migrated {len(issues)} issues to PostgreSQL")

    sqlite_session.close()
    pg_session.close()

if __name__ == "__main__":
    migrate_to_postgres()
