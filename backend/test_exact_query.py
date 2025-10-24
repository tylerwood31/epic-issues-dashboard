"""
Test the exact JQL query from user
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
OLD_TEAM_ID = '3516f16e-7578-4940-9443-0a02386ad88c'
NEW_TEAM_ID = '600c992b-5b41-41e6-989c-08b6aeb6d48d'

# Exact query from user
jql = f'''project in (EX, NTRI)
AND (
  "Team[Team]" = {OLD_TEAM_ID}
  OR "Team[Team]" = {NEW_TEAM_ID}
  OR (
    "Team[Team]" is EMPTY
    AND assignee in ("Jerry D Smith", "Jennifer Entinger", "Cassandra Fico")
  )
)'''

print("="*80)
print("TESTING EXACT USER QUERY")
print("="*80)
print(f"\nJQL Query:")
print(jql)
print("\n" + "="*80)

# Test the query - just get count
url = f"{JIRA_URL}/rest/api/3/search/jql"

params = {
    'jql': jql,
    'maxResults': 1,  # Minimum required
    'fields': 'key'
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

        print(f"\n✅ Query successful!")
        print(f"Total issues found: {total}")
        print("="*80)

        if total == 456:
            print("\n✅ MATCH! Found exactly 456 issues as expected!")
        else:
            print(f"\n⚠️  Expected 456, but found {total}")

except Exception as e:
    print(f"❌ Error testing query: {str(e)}")
    import traceback
    traceback.print_exc()
