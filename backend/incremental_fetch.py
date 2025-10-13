"""
Incremental fetch of new Jira issues using date filter
Workaround for broken pagination by fetching only new issues since last update
"""
from jira import JIRA
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from categorizer import categorize_issue
from database import Database
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()


class IncrementalFetcher:
    """Fetch only new issues since last update"""

    def __init__(self):
        self.jira_url = os.getenv('JIRA_URL')
        self.jira_email = os.getenv('JIRA_EMAIL')
        self.jira_token = os.getenv('JIRA_API_TOKEN')
        self.team_id = os.getenv('JIRA_TEAM_ID')

        # Initialize database (will use DATABASE_URL if set, otherwise SQLite)
        self.db = Database()

    def get_last_issue_date(self):
        """Get the most recent issue date from database"""
        issues = self.db.get_all_issues()
        if not issues:
            # If no issues, fetch from 1 year ago
            return (datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%d')

        # Get the most recent updated_date
        latest_date = max(issue.updated_date for issue in issues if issue.updated_date)
        return latest_date.strftime('%Y-%m-%d')

    def fetch_new_issues(self, since_date=None):
        """Fetch only issues created or updated since the given date"""
        if since_date is None:
            since_date = self.get_last_issue_date()

        # Query for new issues: EPIC team OR assigned to Jerry (who manages EPIC tickets)
        # This catches tickets even if Team field is not set but Jerry is the assignee
        jql = f'project = "Non Tech RT issues" AND ("Team[Team]" = {self.team_id} OR assignee = "Jerry Xu") AND created >= "{since_date}" ORDER BY created DESC'

        print(f"Fetching new issues created since {since_date}", flush=True)
        print(f"JQL: {jql}", flush=True)

        url = f"{self.jira_url}/rest/api/3/search/jql"

        params = {
            'jql': jql,
            'maxResults': 100,  # Should be enough for daily updates
            'fields': 'summary,description,status,priority,created,updated,assignee,reporter'
        }

        try:
            response = requests.get(
                url,
                params=params,
                auth=HTTPBasicAuth(self.jira_email, self.jira_token),
                headers={'Accept': 'application/json'},
                timeout=30
            )

            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}", flush=True)
                print(f"Response: {response.text}", flush=True)
                return []

            data = response.json()
            issues = data.get('issues', [])

            print(f"Found {len(issues)} new issues", flush=True)

            new_issues = []
            stored_count = 0

            for issue_data in issues:
                try:
                    issue_key = issue_data.get('key')
                    summary = issue_data['fields'].get('summary', '')
                    description = issue_data['fields'].get('description', '')

                    # Handle description object/list
                    if isinstance(description, dict):
                        description = str(description)
                    elif isinstance(description, list):
                        description = ' '.join([str(item) for item in description])

                    # Categorize
                    category = categorize_issue(summary, description)

                    # Parse dates
                    created = issue_data['fields'].get('created')
                    updated = issue_data['fields'].get('updated')

                    # Prepare data
                    db_issue_data = {
                        'issue_key': issue_key,
                        'summary': summary,
                        'description': str(description)[:5000],
                        'status': issue_data['fields'].get('status', {}).get('name', 'Unknown'),
                        'priority': issue_data['fields'].get('priority', {}).get('name', 'None'),
                        'category': category,
                        'created_date': datetime.strptime(created, '%Y-%m-%dT%H:%M:%S.%f%z') if created else None,
                        'updated_date': datetime.strptime(updated, '%Y-%m-%dT%H:%M:%S.%f%z') if updated else None,
                        'assignee': issue_data['fields'].get('assignee', {}).get('displayName', 'Unassigned') if issue_data['fields'].get('assignee') else 'Unassigned',
                        'reporter': issue_data['fields'].get('reporter', {}).get('displayName', 'Unknown') if issue_data['fields'].get('reporter') else 'Unknown'
                    }

                    # Store
                    self.db.upsert_issue(db_issue_data, commit=False)
                    stored_count += 1

                    # Add to return list
                    new_issues.append({
                        'key': issue_key,
                        'summary': summary,
                        'category': category,
                        'status': db_issue_data['status'],
                        'created': created
                    })

                except Exception as e:
                    print(f"Error processing issue {issue_data.get('key')}: {str(e)}", flush=True)
                    import traceback
                    traceback.print_exc()
                    continue

            # Commit all at once
            if stored_count > 0:
                self.db.commit()
                print(f"Successfully stored {stored_count} new issues", flush=True)

            return new_issues

        except Exception as e:
            print(f"Error fetching issues: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            return []


if __name__ == '__main__':
    fetcher = IncrementalFetcher()

    # Fetch issues created since yesterday
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    new_issues = fetcher.fetch_new_issues(since_date=yesterday)

    print(f"\n{'='*60}")
    print(f"NEW ISSUES ADDED:")
    print(f"{'='*60}\n")

    for issue in new_issues:
        print(f"🆕 {issue['key']}: {issue['summary'][:60]}")
        print(f"   Category: {issue['category']}")
        print(f"   Status: {issue['status']}")
        print(f"   Created: {issue['created']}\n")

    print(f"{'='*60}")
    print(f"Total new issues: {len(new_issues)}")
    print(f"{'='*60}")
