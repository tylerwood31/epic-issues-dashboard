"""
Test the new JQL query to verify it works correctly
"""
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

# Get environment variables
JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN')
OLD_TEAM_ID = os.getenv('JIRA_OLD_TEAM_ID', '3516f16e-7578-4940-9443-0a02386ad88c')
NEW_TEAM_ID = os.getenv('JIRA_NEW_TEAM_ID', '600c992b-5b41-41e6-989c-08b6aeb6d48d')

# Build the new JQL query
jql = f'''(project = "Non Tech RT issues" OR project = "Tech incidents report") AND (
    "Team[Team]" = {OLD_TEAM_ID}
    OR "Team[Team]" = {NEW_TEAM_ID}
    OR (
        "Team[Team]" is EMPTY
        AND assignee in ("Jerry D Smith", "Jennifer Entinger", "Cassandra Fico")
    )
) ORDER BY created DESC'''

print("="*80)
print("TESTING NEW JQL QUERY")
print("="*80)
print(f"\nJQL Query:")
print(jql)
print("\n" + "="*80)

# Test the query
url = f"{JIRA_URL}/rest/api/3/search/jql"

params = {
    'jql': jql,
    'maxResults': 10,  # Just get first 10 for testing
    'fields': 'summary,status,created,assignee'
}

try:
    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN),
        headers={'Accept': 'application/json'},
        timeout=30
    )

    if response.status_code != 200:
        print(f"❌ Error: HTTP {response.status_code}")
        print(f"Response: {response.text}")
    else:
        data = response.json()
        total = data.get('total', 0)
        issues = data.get('issues', [])

        print(f"\n✅ Query successful!")
        print(f"Total issues found: {total}")
        print(f"\nFirst 10 issues:")
        print("-"*80)

        for issue in issues:
            key = issue['key']
            summary = issue['fields'].get('summary', 'No summary')[:60]
            status = issue['fields'].get('status', {}).get('name', 'Unknown')
            created = issue['fields'].get('created', 'Unknown')[:10]
            assignee = issue['fields'].get('assignee', {}).get('displayName', 'Unassigned') if issue['fields'].get('assignee') else 'Unassigned'

            print(f"{key} | {created} | {status:20s} | {assignee:25s}")
            print(f"  {summary}")
            print()

        print("="*80)
        print(f"\n✅ SUCCESS: New query is working correctly!")
        print(f"   Total issues accessible: {total}")
        print("="*80)

except Exception as e:
    print(f"❌ Error testing query: {str(e)}")
    import traceback
    traceback.print_exc()
