#!/usr/bin/env python3
"""
Populate production database by copying from local SQLite
This bypasses Jira API pagination issues entirely
"""

import sqlite3
import os
from dotenv import load_dotenv
from database import Database

load_dotenv()

def main():
    print("="*80)
    print("POPULATE PRODUCTION FROM LOCAL DATABASE")
    print("="*80)

    # Read all issues from local SQLite database
    local_db_path = os.getenv('DATABASE_PATH', './issues.db')
    print(f"\n1. Reading from local database: {local_db_path}")

    conn = sqlite3.connect(local_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM issues")
    total = cursor.fetchone()[0]
    print(f"   Found {total} issues in local database")

    cursor.execute("""
        SELECT issue_key, summary, description, status, priority, category, confidence,
               created_date, updated_date, assignee, reporter
        FROM issues
        ORDER BY issue_key
    """)

    local_issues = cursor.fetchall()
    conn.close()

    # Connect to production database
    print(f"\n2. Connecting to production database...")
    prod_db = Database()  # Will use DATABASE_URL from environment

    print(f"\n3. Inserting {total} issues into production...")
    success = 0
    errors = 0

    for i, row in enumerate(local_issues, 1):
        try:
            issue_data = {
                'issue_key': row[0],
                'summary': row[1],
                'description': row[2],
                'status': row[3],
                'priority': row[4],
                'category': row[5],
                'confidence': row[6],
                'created_date': row[7],
                'updated_date': row[8],
                'assignee': row[9],
                'reporter': row[10]
            }

            prod_db.upsert_issue(issue_data, commit=True)
            success += 1

            if i % 50 == 0:
                print(f"   Processed {i}/{total} issues...")

        except Exception as e:
            print(f"   Error on {row[0]}: {str(e)}")
            errors += 1

    print(f"\n{'='*80}")
    print(f"✅ COMPLETE!")
    print(f"{'='*80}")
    print(f"Success: {success}/{total}")
    print(f"Errors: {errors}/{total}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
