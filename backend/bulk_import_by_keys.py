#!/usr/bin/env python3
"""
Bulk import issues by fetching them individually by issue key
This bypasses the pagination bug by fetching one issue at a time
"""

import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from dotenv import load_dotenv
from categorizer import categorize_issue
from database import Database

load_dotenv()

# List of all NTRI issue keys from the CSV export (357 total)
ISSUE_KEYS = [
    "NTRI-60", "NTRI-221", "NTRI-240", "NTRI-243", "NTRI-244", "NTRI-282", "NTRI-332", "NTRI-334",
    "NTRI-442", "NTRI-453", "NTRI-489", "NTRI-500", "NTRI-501", "NTRI-548", "NTRI-564", "NTRI-565",
    "NTRI-566", "NTRI-569", "NTRI-571", "NTRI-572", "NTRI-573", "NTRI-574", "NTRI-575", "NTRI-576",
    "NTRI-577", "NTRI-578", "NTRI-579", "NTRI-580", "NTRI-581", "NTRI-582", "NTRI-583", "NTRI-584",
    "NTRI-585", "NTRI-586", "NTRI-587", "NTRI-588", "NTRI-589", "NTRI-590", "NTRI-591", "NTRI-592",
    "NTRI-593", "NTRI-594", "NTRI-595", "NTRI-597", "NTRI-598", "NTRI-599", "NTRI-600", "NTRI-601",
    "NTRI-602", "NTRI-606", "NTRI-607", "NTRI-608", "NTRI-613", "NTRI-614", "NTRI-618", "NTRI-619",
    "NTRI-621", "NTRI-622", "NTRI-630", "NTRI-631", "NTRI-632", "NTRI-634", "NTRI-636", "NTRI-638",
    "NTRI-641", "NTRI-642", "NTRI-643", "NTRI-649", "NTRI-650", "NTRI-653", "NTRI-654", "NTRI-658",
    "NTRI-661", "NTRI-663", "NTRI-664", "NTRI-667", "NTRI-669", "NTRI-670", "NTRI-671", "NTRI-672",
    "NTRI-674", "NTRI-676", "NTRI-677", "NTRI-679", "NTRI-680", "NTRI-681", "NTRI-683", "NTRI-686",
    "NTRI-687", "NTRI-691", "NTRI-700", "NTRI-704", "NTRI-709", "NTRI-713", "NTRI-714", "NTRI-715",
    "NTRI-716", "NTRI-720", "NTRI-724", "NTRI-725", "NTRI-728", "NTRI-731", "NTRI-736", "NTRI-738",
    "NTRI-739", "NTRI-749", "NTRI-753", "NTRI-754", "NTRI-758", "NTRI-760", "NTRI-767", "NTRI-769",
    "NTRI-770", "NTRI-772", "NTRI-773", "NTRI-779", "NTRI-781", "NTRI-782", "NTRI-786", "NTRI-789",
    "NTRI-790", "NTRI-791", "NTRI-793", "NTRI-795", "NTRI-799", "NTRI-802", "NTRI-806", "NTRI-813",
    "NTRI-814", "NTRI-818", "NTRI-819", "NTRI-824", "NTRI-829", "NTRI-832", "NTRI-833", "NTRI-835",
    "NTRI-836", "NTRI-837", "NTRI-839", "NTRI-842", "NTRI-843", "NTRI-844", "NTRI-845", "NTRI-847",
    "NTRI-851", "NTRI-852", "NTRI-854", "NTRI-857", "NTRI-861", "NTRI-862", "NTRI-863", "NTRI-864",
    "NTRI-868", "NTRI-869", "NTRI-870", "NTRI-871", "NTRI-880", "NTRI-881", "NTRI-882", "NTRI-883",
    "NTRI-889", "NTRI-890", "NTRI-891", "NTRI-893", "NTRI-894", "NTRI-904", "NTRI-905", "NTRI-906",
    "NTRI-907", "NTRI-908", "NTRI-909", "NTRI-910", "NTRI-911", "NTRI-915", "NTRI-918", "NTRI-921",
    "NTRI-922", "NTRI-923", "NTRI-924", "NTRI-926", "NTRI-928", "NTRI-929", "NTRI-930", "NTRI-931",
    "NTRI-933", "NTRI-934", "NTRI-936", "NTRI-937", "NTRI-938", "NTRI-939", "NTRI-940", "NTRI-941",
    "NTRI-942", "NTRI-947", "NTRI-948", "NTRI-953", "NTRI-954", "NTRI-955", "NTRI-963", "NTRI-965",
    "NTRI-968", "NTRI-972", "NTRI-973", "NTRI-975", "NTRI-976", "NTRI-977", "NTRI-978", "NTRI-979",
    "NTRI-980", "NTRI-981", "NTRI-982", "NTRI-983", "NTRI-984", "NTRI-985", "NTRI-986", "NTRI-987",
    "NTRI-991", "NTRI-995", "NTRI-996", "NTRI-997", "NTRI-998", "NTRI-999", "NTRI-1001", "NTRI-1002",
    "NTRI-1003", "NTRI-1004", "NTRI-1005", "NTRI-1006", "NTRI-1009", "NTRI-1013", "NTRI-1014", "NTRI-1016",
    "NTRI-1019", "NTRI-1023", "NTRI-1025", "NTRI-1026", "NTRI-1028", "NTRI-1030", "NTRI-1032", "NTRI-1033",
    "NTRI-1034", "NTRI-1035", "NTRI-1036", "NTRI-1037", "NTRI-1038", "NTRI-1039", "NTRI-1044", "NTRI-1045",
    "NTRI-1049", "NTRI-1054", "NTRI-1055", "NTRI-1056", "NTRI-1060", "NTRI-1061", "NTRI-1062", "NTRI-1067",
    "NTRI-1068", "NTRI-1069", "NTRI-1070", "NTRI-1071", "NTRI-1072", "NTRI-1080", "NTRI-1082", "NTRI-1083",
    "NTRI-1084", "NTRI-1085", "NTRI-1087", "NTRI-1089", "NTRI-1090", "NTRI-1094", "NTRI-1095", "NTRI-1096",
    "NTRI-1097", "NTRI-1099", "NTRI-1100", "NTRI-1102", "NTRI-1103", "NTRI-1104", "NTRI-1106", "NTRI-1107",
    "NTRI-1108", "NTRI-1109", "NTRI-1110", "NTRI-1112", "NTRI-1113", "NTRI-1114", "NTRI-1120", "NTRI-1121",
    "NTRI-1122", "NTRI-1123", "NTRI-1124", "NTRI-1125", "NTRI-1126", "NTRI-1128", "NTRI-1129", "NTRI-1130",
    "NTRI-1131", "NTRI-1132", "NTRI-1134", "NTRI-1135", "NTRI-1136", "NTRI-1137", "NTRI-1138", "NTRI-1139",
    "NTRI-1140", "NTRI-1143", "NTRI-1144", "NTRI-1149", "NTRI-1150", "NTRI-1151", "NTRI-1152", "NTRI-1153",
    "NTRI-1155", "NTRI-1158", "NTRI-1166", "NTRI-1169", "NTRI-1170", "NTRI-1172", "NTRI-1173", "NTRI-1178",
    "NTRI-1185", "NTRI-1186", "NTRI-1187", "NTRI-1188", "NTRI-1189", "NTRI-1196", "NTRI-1197", "NTRI-1198",
    "NTRI-1199", "NTRI-1201", "NTRI-1202", "NTRI-1203", "NTRI-1204", "NTRI-1206", "NTRI-1211", "NTRI-1213",
    "NTRI-1215", "NTRI-1217", "NTRI-1219", "NTRI-1220", "NTRI-1221", "NTRI-1222", "NTRI-1224", "NTRI-1228",
    "NTRI-1229", "NTRI-1230", "NTRI-1231", "NTRI-1232", "NTRI-1233", "NTRI-1234", "NTRI-1235", "NTRI-1242",
    "NTRI-1243", "NTRI-1244", "NTRI-1245", "NTRI-1246", "NTRI-1247"
]

def fetch_issue_by_key(jira_url, email, token, issue_key):
    """Fetch a single issue by its key"""
    url = f"{jira_url}/rest/api/3/issue/{issue_key}"
    auth = HTTPBasicAuth(email, token)
    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, auth=auth, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error fetching {issue_key}: {str(e)}")
        return None

def main():
    print(f"[{datetime.now()}] Starting bulk import by issue keys...")
    print("=" * 60)

    # Initialize
    jira_url = os.getenv('JIRA_URL')
    jira_email = os.getenv('JIRA_EMAIL')
    jira_token = os.getenv('JIRA_API_TOKEN')
    db = Database()

    print(f"Total issues to import: {len(ISSUE_KEYS)}")
    print("=" * 60)

    success_count = 0
    error_count = 0

    for i, issue_key in enumerate(ISSUE_KEYS, 1):
        print(f"\n[{i}/{len(ISSUE_KEYS)}] Fetching {issue_key}...", end=" ")

        issue_data = fetch_issue_by_key(jira_url, jira_email, jira_token, issue_key)

        if not issue_data:
            error_count += 1
            print("❌ FAILED")
            continue

        try:
            fields = issue_data.get('fields', {})

            # Extract fields
            summary = fields.get('summary', '')
            description = fields.get('description', '') or ''

            # Handle description object/dict
            if isinstance(description, dict):
                description = str(description)
            elif isinstance(description, list):
                description = ' '.join([str(item) for item in description])

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

            # Categorize (returns tuple of category and confidence)
            category, confidence = categorize_issue(summary, str(description))

            # Store
            db.upsert_issue({
                'issue_key': issue_key,
                'summary': summary,
                'description': str(description)[:5000],
                'status': status,
                'priority': priority,
                'category': category,
                'confidence': confidence,
                'created_date': created_date,
                'updated_date': updated_date
            }, commit=True)

            success_count += 1
            print(f"✅ {category}")

        except Exception as e:
            error_count += 1
            print(f"❌ Error: {str(e)}")

    print("\n" + "=" * 60)
    print(f"[{datetime.now()}] Import complete!")
    print(f"Success: {success_count}/{len(ISSUE_KEYS)}")
    print(f"Errors: {error_count}/{len(ISSUE_KEYS)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
