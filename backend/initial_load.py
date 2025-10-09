#!/usr/bin/env python3
"""
Initial data load script - fetches ALL issues for the EPIC team
Run this once to populate the database with all historical data
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from jira_client import JiraClient
from database import Database

# Load environment variables
load_dotenv()

def main():
    """Fetch all issues and populate database"""
    print(f"[{datetime.now()}] Starting initial data load...")
    print("=" * 60)

    # Initialize database
    db = Database()

    # Build JQL query for ALL issues (no date filter for initial load)
    jira_url = os.getenv('JIRA_URL')
    jira_email = os.getenv('JIRA_EMAIL')
    jira_token = os.getenv('JIRA_API_TOKEN')
    team_id = os.getenv('JIRA_TEAM_ID')

    jql = f'(project = "Non Tech RT issues" OR project = "Tech incidents report") AND "Team[Team]" = {team_id} ORDER BY created DESC'

    print(f"JQL Query: {jql}")
    print("=" * 60)

    # Fetch issues using direct API calls
    import requests
    from requests.auth import HTTPBasicAuth

    auth = HTTPBasicAuth(jira_email, jira_token)
    headers = {"Accept": "application/json"}

    all_issues = []
    start_at = 0
    max_results = 50
    total_fetched = 0

    while True:
        # Build API URL
        api_url = f"{jira_url}/rest/api/3/search"
        params = {
            'jql': jql,
            'startAt': start_at,
            'maxResults': max_results,
            'fields': 'summary,status,priority,created,updated,description'
        }

        print(f"\n[{datetime.now()}] Fetching batch starting at {start_at}...")

        try:
            response = requests.get(api_url, headers=headers, params=params, auth=auth)
            response.raise_for_status()
            data = response.json()

            issues = data.get('issues', [])
            total = data.get('total', 0)

            if not issues:
                print("No more issues to fetch.")
                break

            print(f"  Retrieved {len(issues)} issues (Total in Jira: {total})")

            # Process and store each issue
            for issue in issues:
                from categorizer import categorize_issue

                issue_key = issue['key']
                fields = issue['fields']

                # Extract fields
                summary = fields.get('summary', '')
                description = fields.get('description', '') or ''
                status = fields.get('status', {}).get('name', 'Unknown')
                priority = fields.get('priority', {}).get('name', 'Medium')

                # Parse dates
                created = fields.get('created', '')
                updated = fields.get('updated', '')

                try:
                    created_date = datetime.fromisoformat(created.replace('Z', '+00:00')) if created else None
                    updated_date = datetime.fromisoformat(updated.replace('Z', '+00:00')) if updated else None
                except:
                    created_date = None
                    updated_date = None

                # Categorize
                category = categorize_issue(summary, description)

                # Prepare issue data
                issue_data = {
                    'issue_key': issue_key,
                    'summary': summary,
                    'description': description,
                    'status': status,
                    'priority': priority,
                    'category': category,
                    'created_date': created_date,
                    'updated_date': updated_date
                }

                # Store in database (don't commit yet)
                db.upsert_issue(issue_data, commit=False)
                all_issues.append(issue_key)

            total_fetched += len(issues)
            print(f"  Processed {total_fetched} issues so far...")

            # Check if we've fetched all issues
            if total_fetched >= total or len(issues) < max_results:
                print(f"\n[{datetime.now()}] Reached end of results.")
                break

            # Move to next batch
            start_at += max_results

            # Safety limit to prevent infinite loops
            if total_fetched >= 1000:
                print(f"\n[{datetime.now()}] Safety limit reached (1000 issues)")
                break

        except Exception as e:
            print(f"Error fetching batch: {str(e)}")
            break

    # Commit all changes at once
    print(f"\n[{datetime.now()}] Committing {len(all_issues)} issues to database...")
    db.commit()

    print("=" * 60)
    print(f"[{datetime.now()}] Initial load complete!")
    print(f"Total issues loaded: {len(all_issues)}")
    print("=" * 60)

    # Print sample of loaded issues
    if all_issues:
        print(f"\nFirst 5 issues: {all_issues[:5]}")
        print(f"Last 5 issues: {all_issues[-5:]}")

if __name__ == "__main__":
    main()
