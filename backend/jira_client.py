"""
Jira API client for fetching issues
"""
from jira import JIRA
from datetime import datetime
import os
from dotenv import load_dotenv
from categorizer import categorize_issue
from database import Database

load_dotenv()


class JiraClient:
    """Client for interacting with Jira API"""

    def __init__(self):
        self.jira_url = os.getenv('JIRA_URL')
        self.jira_email = os.getenv('JIRA_EMAIL')
        self.jira_token = os.getenv('JIRA_API_TOKEN')
        self.old_team_id = os.getenv('JIRA_OLD_TEAM_ID', '3516f16e-7578-4940-9443-0a02386ad88c')
        self.new_team_id = os.getenv('JIRA_NEW_TEAM_ID', '600c992b-5b41-41e6-989c-08b6aeb6d48d')

        # Initialize Jira connection (use API v3)
        self.jira = JIRA(
            server=self.jira_url,
            basic_auth=(self.jira_email, self.jira_token),
            options={'rest_api_version': '3'}
        )

        # Initialize database
        db_path = os.getenv('DATABASE_PATH', './issues.db')
        self.db = Database(db_path)

    def build_jql_query(self):
        """Build the JQL query for fetching issues"""
        # Query only includes NTRI project (Non Tech RT issues), not EX project
        return f'''project = "Non Tech RT issues" AND (
            "Team[Team]" = {self.old_team_id}
            OR "Team[Team]" = {self.new_team_id}
            OR (
                "Team[Team]" is EMPTY
                AND assignee in ("Jerry D Smith", "Jennifer Entinger", "Cassandra Fico")
            )
        ) ORDER BY created DESC'''

    def fetch_and_store_issues(self):
        """Fetch issues from Jira and store in database - process batches incrementally"""
        jql = self.build_jql_query()

        print(f"Fetching issues with JQL: {jql}", flush=True)

        # Use requests directly to call the Jira API v3 with proper pagination
        import requests
        from requests.auth import HTTPBasicAuth

        start_at = 0
        max_results = 50  # Smaller batches for faster incremental processing
        total_fetched = 0
        stored_count = 0
        seen_issue_keys = set()  # Track seen issues to detect infinite loops

        while True:  # Fetch all issues (no limit)
            url = f"{self.jira_url}/rest/api/3/search/jql"

            params = {
                'jql': jql,
                'startAt': start_at,
                'maxResults': max_results,
                'fields': 'summary,description,status,priority,created,updated,assignee,reporter'
            }

            try:
                print(f"Fetching startAt={start_at}, maxResults={max_results}", flush=True)
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
                    break

                data = response.json()
                batch_issues = data.get('issues', [])
                is_last = data.get('isLast', False)
                total_available = data.get('total', 0)

                print(f"Batch: got {len(batch_issues)} issues, isLast={is_last}, total={total_available}", flush=True)

                # If we got no issues OR less than max_results, we're done
                if not batch_issues or len(batch_issues) < max_results:
                    if batch_issues:
                        print(f"Got {len(batch_issues)} issues (less than {max_results}), assuming end of results", flush=True)
                    break

                # Process and store each issue (batch commits after full batch)
                issue_keys = [issue_data.get('key') for issue_data in batch_issues]
                print(f"Issue keys in batch: {issue_keys[:5]}...", flush=True)

                # Check for duplicate issues (infinite loop detection)
                new_keys = set(issue_keys) - seen_issue_keys
                if not new_keys:
                    print(f"⚠️  All {len(issue_keys)} issues in this batch were already seen! Breaking to avoid infinite loop.", flush=True)
                    break
                seen_issue_keys.update(issue_keys)
                print(f"New unique issues in this batch: {len(new_keys)}", flush=True)

                for issue_data in batch_issues:
                    try:
                        # Extract data
                        summary = issue_data['fields'].get('summary', '')
                        description = issue_data['fields'].get('description', '')

                        # Handle description object/list
                        if isinstance(description, dict):
                            description = str(description)
                        elif isinstance(description, list):
                            description = ' '.join([str(item) for item in description])

                        # Categorize (returns tuple of category and confidence)
                        category, confidence = categorize_issue(summary, description)

                        # Parse dates
                        created = issue_data['fields'].get('created')
                        updated = issue_data['fields'].get('updated')

                        # Prepare data
                        db_issue_data = {
                            'issue_key': issue_data.get('key'),
                            'summary': summary,
                            'description': str(description)[:5000],  # Limit description length
                            'status': issue_data['fields'].get('status', {}).get('name', 'Unknown'),
                            'priority': issue_data['fields'].get('priority', {}).get('name', 'None'),
                            'category': category,
                            'confidence': confidence,
                            'created_date': datetime.strptime(created, '%Y-%m-%dT%H:%M:%S.%f%z') if created else None,
                            'updated_date': datetime.strptime(updated, '%Y-%m-%dT%H:%M:%S.%f%z') if updated else None,
                            'assignee': issue_data['fields'].get('assignee', {}).get('displayName', 'Unassigned') if issue_data['fields'].get('assignee') else 'Unassigned',
                            'reporter': issue_data['fields'].get('reporter', {}).get('displayName', 'Unknown') if issue_data['fields'].get('reporter') else 'Unknown'
                        }

                        # Store without commit (batch at end)
                        self.db.upsert_issue(db_issue_data, commit=False)
                        stored_count += 1

                    except Exception as e:
                        print(f"Error processing issue {issue_data.get('key')}: {str(e)}", flush=True)
                        import traceback
                        traceback.print_exc()
                        continue

                # Commit the entire batch at once
                try:
                    self.db.commit()
                except Exception as e:
                    print(f"Error committing batch: {str(e)}", flush=True)
                    import traceback
                    traceback.print_exc()

                total_fetched += len(batch_issues)
                print(f"Fetched and stored {total_fetched} issues so far...", flush=True)

                # Check if this is the last page
                if is_last:
                    print(f"Reached end: fetched all {total_fetched} available issues", flush=True)
                    break

                start_at += max_results

            except Exception as e:
                print(f"Error fetching batch at {start_at}: {str(e)}", flush=True)
                break

        print(f"Successfully stored {stored_count} issues in database", flush=True)
        return stored_count

    def get_dashboard_data(self):
        """Get all dashboard data from database"""
        total_issues = len(self.db.get_all_issues())

        return {
            'total_issues': total_issues,
            'category_stats': self.db.get_category_stats(),
            'status_stats': self.db.get_status_stats(),
            'priority_stats': self.db.get_priority_stats(),
            'category_details': self.db.get_category_details(),
            'last_updated': datetime.utcnow().isoformat()
        }


if __name__ == '__main__':
    # Test the client
    client = JiraClient()
    print("Testing Jira connection...")
    count = client.fetch_and_store_issues()
    print(f"\nFetched and categorized {count} issues")

    print("\nDashboard data:")
    data = client.get_dashboard_data()
    print(f"Total issues: {data['total_issues']}")
    print(f"Categories: {data['category_stats']}")
