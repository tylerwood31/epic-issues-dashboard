"""
Fetch ALL issues from Jira to get accurate count
"""
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN')
OLD_TEAM_ID = '3516f16e-7578-4940-9443-0a02386ad88c'
NEW_TEAM_ID = '600c992b-5b41-41e6-989c-08b6aeb6d48d'

jql = f'''(project = "Non Tech RT issues" OR project = "Tech incidents report") AND (
    "Team[Team]" = {OLD_TEAM_ID}
    OR "Team[Team]" = {NEW_TEAM_ID}
    OR (
        "Team[Team]" is EMPTY
        AND assignee in ("Jerry D Smith", "Jennifer Entinger", "Cassandra Fico")
    )
) ORDER BY created DESC'''

print("Fetching ALL issues from Jira...")
print(f"JQL: {jql}\n")

url = f'{JIRA_URL}/rest/api/3/search/jql'

all_issue_keys = []
start_at = 0
max_results = 100

while True:
    params = {
        'jql': jql,
        'startAt': start_at,
        'maxResults': max_results,
        'fields': 'key,created'
    }

    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN),
        headers={'Accept': 'application/json'},
        timeout=30
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        break

    data = response.json()
    issues = data.get('issues', [])

    if not issues:
        break

    batch_keys = [issue['key'] for issue in issues]
    all_issue_keys.extend(batch_keys)

    print(f"Fetched batch {start_at}-{start_at+len(issues)}: {len(batch_keys)} issues")

    if len(issues) < max_results:
        break

    start_at += max_results

print("\n" + "="*80)
print(f"TOTAL ISSUES IN JIRA: {len(all_issue_keys)}")
print(f"TOTAL ISSUES IN DATABASE: 419")
print(f"DIFFERENCE: {len(all_issue_keys) - 419}")
print("="*80)

if len(all_issue_keys) > 419:
    print(f"\n⚠️  Database is missing {len(all_issue_keys) - 419} issues!")
    print("\nFirst 10 issue keys from Jira:")
    for key in all_issue_keys[:10]:
        print(f"  - {key}")
    print("\nLast 10 issue keys from Jira:")
    for key in all_issue_keys[-10:]:
        print(f"  - {key}")
