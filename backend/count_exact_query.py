"""
Count actual issues from exact user query
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

jql = f'''project in (EX, NTRI)
AND (
  "Team[Team]" = {OLD_TEAM_ID}
  OR "Team[Team]" = {NEW_TEAM_ID}
  OR (
    "Team[Team]" is EMPTY
    AND assignee in ("Jerry D Smith", "Jennifer Entinger", "Cassandra Fico")
  )
) ORDER BY key ASC'''

print("Counting issues with exact query...")
print(f"JQL: {jql}\n")

url = f'{JIRA_URL}/rest/api/3/search/jql'

all_issue_keys = set()  # Use set to detect duplicates
start_at = 0
max_results = 100
max_iterations = 10  # Safety limit

iteration = 0
while iteration < max_iterations:
    params = {
        'jql': jql,
        'startAt': start_at,
        'maxResults': max_results,
        'fields': 'key'
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
        print(f"No more issues at startAt={start_at}")
        break

    batch_keys = [issue['key'] for issue in issues]
    before_count = len(all_issue_keys)
    all_issue_keys.update(batch_keys)
    after_count = len(all_issue_keys)

    duplicates_in_batch = len(batch_keys) - (after_count - before_count)

    print(f"Batch {iteration+1}: startAt={start_at}, fetched={len(batch_keys)}, unique_added={after_count - before_count}, duplicates={duplicates_in_batch}, total_unique={after_count}")

    if len(issues) < max_results:
        print("Reached end (batch smaller than max_results)")
        break

    start_at += max_results
    iteration += 1

print("\n" + "="*80)
print(f"TOTAL UNIQUE ISSUES: {len(all_issue_keys)}")
print(f"EXPECTED: 456")
if len(all_issue_keys) == 456:
    print("✅ MATCH!")
else:
    print(f"⚠️  DIFFERENCE: {len(all_issue_keys) - 456}")
print("="*80)
