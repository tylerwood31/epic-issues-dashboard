"""
Full refresh of all issues - NO LIMITS
Run this directly to fetch all issues from Jira
"""
import os
from jira_client import JiraClient
from dotenv import load_dotenv

load_dotenv()

def main():
    """Run a full refresh of all issues"""
    print("="*80)
    print("FULL REFRESH - Fetching ALL issues from Jira")
    print("="*80)

    client = JiraClient()

    # Fetch and store all issues
    print("\nStarting fetch...")
    client.fetch_and_store_issues()

    # Show final count
    from database import Database
    db = Database()
    issues = db.get_all_issues()

    print("\n" + "="*80)
    print(f"✅ Refresh complete! Total issues in database: {len(issues)}")
    print("="*80)

    # Show sample
    if issues:
        print("\nSample issue:")
        sample = issues[0]
        print(f"  Key: {sample.issue_key}")
        print(f"  Category: {sample.category}")
        print(f"  Confidence: {sample.confidence}")
        print(f"  Status: {sample.status}")

if __name__ == '__main__':
    main()
