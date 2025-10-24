"""
Import tickets from Jira CSV export
"""
import csv
import os
from datetime import datetime
from dotenv import load_dotenv
from categorizer import categorize_issue
from database import Database

load_dotenv()

def parse_jira_date(date_str):
    """Parse Jira date format: 23/Oct/25 7:26 PM"""
    if not date_str or date_str.strip() == '':
        return None

    try:
        # Jira format: 23/Oct/25 7:26 PM
        return datetime.strptime(date_str.strip(), '%d/%b/%y %I:%M %p')
    except:
        try:
            # Alternative format without time
            return datetime.strptime(date_str.strip(), '%d/%b/%y')
        except:
            return None

def import_csv(csv_path):
    """Import tickets from CSV file"""
    print(f"Importing tickets from: {csv_path}")
    print("="*80)

    # Initialize database
    db_path = os.getenv('DATABASE_PATH', './issues.db')
    db = Database(db_path)

    imported_count = 0
    skipped_count = 0
    error_count = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                issue_key = row.get('Issue key', '').strip()
                summary = row.get('Summary', '').strip()
                description = row.get('Description', '').strip()
                status = row.get('Status', 'Unknown').strip()
                priority = row.get('Priority', 'None').strip()
                created = row.get('Created', '').strip()
                updated = row.get('Updated', '').strip()
                assignee = row.get('Assignee', 'Unassigned').strip()
                reporter = row.get('Reporter', 'Unknown').strip()

                if not issue_key:
                    skipped_count += 1
                    continue

                # Parse dates
                created_date = parse_jira_date(created)
                updated_date = parse_jira_date(updated)

                # Categorize
                category = categorize_issue(summary, description)

                # Prepare data
                issue_data = {
                    'issue_key': issue_key,
                    'summary': summary[:500] if summary else '',  # Limit length
                    'description': description[:5000] if description else '',  # Limit length
                    'status': status if status else 'Unknown',
                    'priority': priority if priority else 'None',
                    'category': category,
                    'created_date': created_date,
                    'updated_date': updated_date,
                    'assignee': assignee if assignee else 'Unassigned',
                    'reporter': reporter if reporter else 'Unknown'
                }

                # Insert/update in database
                db.upsert_issue(issue_data, commit=False)
                imported_count += 1

                if imported_count % 50 == 0:
                    print(f"Processed {imported_count} tickets...")

            except Exception as e:
                error_count += 1
                print(f"Error processing {row.get('Issue key', 'unknown')}: {str(e)}")
                continue

    # Commit all at once
    db.commit()

    print("\n" + "="*80)
    print(f"✅ Import complete!")
    print(f"   Imported: {imported_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Errors: {error_count}")
    print("="*80)

    # Show category breakdown
    print("\n📊 Category Breakdown:")
    category_stats = db.get_category_stats()
    for stat in category_stats:
        print(f"   {stat['name']}: {stat['value']}")

    # Show status breakdown
    print("\n📊 Status Breakdown:")
    status_stats = db.get_status_stats()
    for stat in status_stats:
        print(f"   {stat['name']}: {stat['value']}")

    print("\n" + "="*80)
    return imported_count

if __name__ == '__main__':
    csv_path = '/Users/tylerwood/Downloads/Jira (32).csv'

    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
    else:
        import_csv(csv_path)
