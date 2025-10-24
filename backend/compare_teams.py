"""
Compare tickets between old and new Jira teams
"""
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

# Team IDs
OLD_TEAM_ID = "3516f16e-7578-4940-9443-0a02386ad88c"  # Epic Team and Friends
NEW_TEAM_ID = "600c992b-5b41-41e6-989c-08b6aeb6d48d"  # ConnectPortalResources

# Jira config
JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN')


def fetch_team_issues(team_id, team_name):
    """Fetch all issues for a given team"""
    jql = f'(project = "Non Tech RT issues" OR project = "Tech incidents report") AND "Team[Team]" = {team_id} ORDER BY created DESC'

    print(f"\n{'='*80}")
    print(f"Querying: {team_name}")
    print(f"Team ID: {team_id}")
    print(f"JQL: {jql}")
    print(f"{'='*80}\n")

    url = f"{JIRA_URL}/rest/api/3/search/jql"

    all_issues = []
    start_at = 0
    max_results = 100

    while True:
        params = {
            'jql': jql,
            'startAt': start_at,
            'maxResults': max_results,
            'fields': 'summary,status,created,updated'
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
                print(f"Error: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                break

            data = response.json()
            issues = data.get('issues', [])
            total = data.get('total', 0)

            print(f"Fetched {len(issues)} issues (batch starting at {start_at})")

            all_issues.extend(issues)

            if len(all_issues) >= total:
                break

            start_at += max_results

        except Exception as e:
            print(f"Error fetching: {str(e)}")
            break

    return all_issues


def analyze_issues(issues):
    """Analyze issue collection"""
    if not issues:
        return {
            'count': 0,
            'keys': [],
            'statuses': {},
            'date_range': None
        }

    keys = [issue['key'] for issue in issues]

    # Count by status
    statuses = defaultdict(int)
    for issue in issues:
        status = issue['fields'].get('status', {}).get('name', 'Unknown')
        statuses[status] += 1

    # Get date range
    dates = []
    for issue in issues:
        created = issue['fields'].get('created')
        if created:
            dates.append(created)

    date_range = None
    if dates:
        dates.sort()
        date_range = {
            'earliest': dates[0][:10],
            'latest': dates[-1][:10]
        }

    return {
        'count': len(issues),
        'keys': keys,
        'statuses': dict(statuses),
        'date_range': date_range
    }


def main():
    print("\n" + "="*80)
    print("JIRA TEAM MIGRATION ANALYSIS")
    print("="*80)

    # Fetch issues from both teams
    old_team_issues = fetch_team_issues(OLD_TEAM_ID, "Epic Team and Friends (OLD)")
    new_team_issues = fetch_team_issues(NEW_TEAM_ID, "ConnectPortalResources (NEW)")

    # Analyze
    old_analysis = analyze_issues(old_team_issues)
    new_analysis = analyze_issues(new_team_issues)

    # Find overlaps
    old_keys = set(old_analysis['keys'])
    new_keys = set(new_analysis['keys'])
    overlap = old_keys & new_keys
    only_old = old_keys - new_keys
    only_new = new_keys - old_keys

    # Print results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    print(f"\n📊 OLD TEAM (Epic Team and Friends)")
    print(f"   Team ID: {OLD_TEAM_ID}")
    print(f"   Total Issues: {old_analysis['count']}")
    if old_analysis['date_range']:
        print(f"   Date Range: {old_analysis['date_range']['earliest']} to {old_analysis['date_range']['latest']}")
    print(f"   Status Breakdown:")
    for status, count in sorted(old_analysis['statuses'].items(), key=lambda x: x[1], reverse=True):
        print(f"      - {status}: {count}")

    if old_analysis['count'] > 0:
        print(f"   Sample Issues (first 10):")
        for key in old_analysis['keys'][:10]:
            print(f"      - {key}")

    print(f"\n📊 NEW TEAM (ConnectPortalResources)")
    print(f"   Team ID: {NEW_TEAM_ID}")
    print(f"   Total Issues: {new_analysis['count']}")
    if new_analysis['date_range']:
        print(f"   Date Range: {new_analysis['date_range']['earliest']} to {new_analysis['date_range']['latest']}")
    print(f"   Status Breakdown:")
    for status, count in sorted(new_analysis['statuses'].items(), key=lambda x: x[1], reverse=True):
        print(f"      - {status}: {count}")

    if new_analysis['count'] > 0:
        print(f"   Sample Issues (first 10):")
        for key in new_analysis['keys'][:10]:
            print(f"      - {key}")

    print(f"\n🔄 OVERLAP ANALYSIS")
    print(f"   Issues in BOTH teams: {len(overlap)}")
    print(f"   Issues ONLY in old team: {len(only_old)}")
    print(f"   Issues ONLY in new team: {len(only_new)}")

    if overlap:
        print(f"\n   Issues appearing in both teams (first 10):")
        for key in list(overlap)[:10]:
            print(f"      - {key}")

    if only_old:
        print(f"\n   Issues ONLY in old team (first 10):")
        for key in list(only_old)[:10]:
            print(f"      - {key}")

    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    if old_analysis['count'] == 0 and new_analysis['count'] > 0:
        print("\n✅ All tickets have been moved to ConnectPortalResources!")
        print("   RECOMMENDATION: Update .env to use new team ID:")
        print(f"   JIRA_TEAM_ID={NEW_TEAM_ID}")

    elif old_analysis['count'] > 0 and new_analysis['count'] == 0:
        print("\n⚠️  No tickets found in new team, all still in old team.")
        print("   RECOMMENDATION: Keep current configuration or investigate migration status.")

    elif old_analysis['count'] > 0 and new_analysis['count'] > 0:
        if len(overlap) == old_analysis['count']:
            print("\n✅ All old team tickets are also in new team!")
            print("   RECOMMENDATION: Update .env to use new team ID:")
            print(f"   JIRA_TEAM_ID={NEW_TEAM_ID}")
        else:
            print("\n⚠️  Teams are in transition - tickets exist in both.")
            print("   RECOMMENDATION: Consider querying both teams during transition:")
            print("   Option 1: Update to new team ID and monitor")
            print("   Option 2: Query both teams temporarily with OR condition")
            print(f"\n   Transition stats:")
            print(f"   - {len(only_old)} tickets still only in old team")
            print(f"   - {len(only_new)} tickets only in new team")
            print(f"   - {len(overlap)} tickets in both teams")
    else:
        print("\n❌ No tickets found in either team!")
        print("   RECOMMENDATION: Verify team IDs and Jira access.")

    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    main()
