"""
Recalculate confidence scores for all existing issues
"""
import os
from dotenv import load_dotenv
from categorizer import categorize_issue
from database import Database

load_dotenv()

def recalculate_all_confidence():
    """Recalculate confidence for all issues in database"""
    print("Recalculating confidence scores for all issues...")
    print("="*80)

    # Initialize database
    db_path = os.getenv('DATABASE_PATH', './issues.db')
    db = Database(db_path)

    # Get all issues
    issues = db.get_all_issues()
    total = len(issues)

    print(f"Found {total} issues to process\n")

    updated_count = 0
    for i, issue in enumerate(issues, 1):
        try:
            # Recategorize with confidence
            category, confidence = categorize_issue(issue.summary, issue.description)

            # Update the issue
            issue.category = category
            issue.confidence = confidence

            updated_count += 1

            if i % 50 == 0:
                print(f"Processed {i}/{total} issues...")

        except Exception as e:
            print(f"Error processing {issue.issue_key}: {str(e)}")
            continue

    # Commit all changes
    db.commit()

    print(f"\n{'='*80}")
    print(f"✅ Successfully updated {updated_count}/{total} issues")
    print(f"{'='*80}")

    # Show confidence distribution
    print("\n📊 Confidence Distribution:")
    high_conf = len([i for i in issues if i.confidence >= 90])
    medium_conf = len([i for i in issues if 60 <= i.confidence < 90])
    low_conf = len([i for i in issues if i.confidence < 60])

    print(f"   High (≥90%): {high_conf} issues ({high_conf/total*100:.1f}%)")
    print(f"   Medium (60-89%): {medium_conf} issues ({medium_conf/total*100:.1f}%)")
    print(f"   Low (<60%): {low_conf} issues ({low_conf/total*100:.1f}%)")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    recalculate_all_confidence()
