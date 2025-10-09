"""
CSV Importer for Jira issues - workaround for broken API pagination
"""
import csv
from datetime import datetime
import os
from dotenv import load_dotenv
from categorizer import categorize_issue
from database import Database

load_dotenv()


class CSVImporter:
    """Import issues from Jira CSV export"""

    def __init__(self, csv_path):
        self.csv_path = csv_path
        db_path = os.getenv('DATABASE_PATH', './issues.db')
        self.db = Database(db_path)

    def parse_date(self, date_str):
        """Parse Jira date format"""
        if not date_str or date_str.strip() == '':
            return None
        try:
            # Try common Jira date formats
            for fmt in ['%d/%b/%y %I:%M %p', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f%z']:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
            return None
        except Exception as e:
            print(f"Error parsing date '{date_str}': {e}")
            return None

    def import_from_csv(self):
        """Import all issues from CSV file"""
        print(f"Importing from CSV: {self.csv_path}", flush=True)

        stored_count = 0
        skipped_count = 0

        with open(self.csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            batch = []
            batch_size = 50

            for row in reader:
                try:
                    issue_key = row.get('Issue key', '').strip()
                    if not issue_key:
                        skipped_count += 1
                        continue

                    summary = row.get('Summary', '').strip()
                    description = row.get('Description', '').strip()

                    # Categorize the issue
                    category = categorize_issue(summary, description)

                    # Parse dates
                    created_date = self.parse_date(row.get('Created', ''))
                    updated_date = self.parse_date(row.get('Updated', ''))

                    # Prepare data
                    db_issue_data = {
                        'issue_key': issue_key,
                        'summary': summary[:500] if summary else '',
                        'description': description[:5000] if description else '',
                        'status': row.get('Status', 'Unknown').strip(),
                        'priority': row.get('Priority', 'None').strip(),
                        'category': category,
                        'created_date': created_date,
                        'updated_date': updated_date,
                        'assignee': row.get('Assignee', 'Unassigned').strip() or 'Unassigned',
                        'reporter': row.get('Reporter', 'Unknown').strip() or 'Unknown'
                    }

                    # Add to batch
                    self.db.upsert_issue(db_issue_data, commit=False)
                    batch.append(issue_key)
                    stored_count += 1

                    # Commit every batch_size issues
                    if len(batch) >= batch_size:
                        self.db.commit()
                        print(f"Imported {stored_count} issues so far...", flush=True)
                        batch = []

                except Exception as e:
                    print(f"Error processing row: {str(e)}", flush=True)
                    skipped_count += 1
                    continue

            # Commit remaining issues
            if batch:
                self.db.commit()

        print(f"\nImport complete!")
        print(f"  - Successfully imported: {stored_count} issues")
        print(f"  - Skipped: {skipped_count} rows")

        return stored_count


if __name__ == '__main__':
    # Test the importer
    csv_path = '/Users/tylerwood/Downloads/Jira (29).csv'
    importer = CSVImporter(csv_path)
    count = importer.import_from_csv()

    print(f"\nDatabase now contains:")
    print(f"Total issues: {len(importer.db.get_all_issues())}")
    print(f"Categories: {importer.db.get_category_stats()}")
