"""
Verify database contents after refresh
Run this on production to check that data is correct
"""
import os
from database import Database
from dotenv import load_dotenv

load_dotenv()

def verify_database():
    """Verify database has correct data"""
    print("Connecting to database...")
    db = Database()

    issues = db.get_all_issues()
    print(f"\n{'='*80}")
    print(f"Total issues: {len(issues)}")
    print(f"{'='*80}\n")

    if issues:
        # Show first 3 issues as samples
        print("Sample issues:")
        for i, issue in enumerate(issues[:3], 1):
            print(f"\n{i}. {issue.issue_key}")
            print(f"   Category: {issue.category}")
            print(f"   Confidence: {issue.confidence}")
            print(f"   Status: {issue.status}")
            print(f"   Created: {issue.created_date}")

        # Count by category
        print(f"\n{'='*80}")
        print("Issues by Category:")
        print(f"{'='*80}")

        category_counts = {}
        for issue in issues:
            cat = issue.category
            category_counts[cat] = category_counts.get(cat, 0) + 1

        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count}")

        # Count by confidence level
        print(f"\n{'='*80}")
        print("Confidence Distribution:")
        print(f"{'='*80}")

        high = len([i for i in issues if i.confidence and i.confidence >= 90])
        medium = len([i for i in issues if i.confidence and 60 <= i.confidence < 90])
        low = len([i for i in issues if i.confidence and i.confidence < 60])
        missing = len([i for i in issues if not i.confidence])

        print(f"  High (≥90%): {high}")
        print(f"  Medium (60-89%): {medium}")
        print(f"  Low (<60%): {low}")
        if missing:
            print(f"  Missing confidence: {missing}")

    else:
        print("⚠️  No issues found in database!")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    verify_database()
