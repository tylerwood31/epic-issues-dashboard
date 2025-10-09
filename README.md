# EPIC System Issues Dashboard

An interactive dashboard for tracking and categorizing EPIC system integration issues from Jira. The system automatically fetches issues daily, categorizes them using intelligent logic, and displays comprehensive analytics.

## Features

- **Automated Jira Integration**: Fetches issues from specified Jira projects daily
- **Intelligent Categorization**: Automatically assigns issues to 7 predefined categories
- **Real-time Dashboard**: Beautiful, interactive React dashboard with charts and statistics
- **Daily Refresh**: Scheduled automatic data refresh at 2 AM
- **Manual Refresh**: On-demand data refresh via dashboard button
- **SQLite Database**: Persistent storage of issues and analytics

## Categories

Issues are automatically categorized into:

1. **Missing SSR**
2. **Missing Policy Header**
3. **Missing Policy**
4. **Account/Client Missing**
5. **Producer Updates**
6. **Endorsement Issues**
7. **Premium/Data Entry Issues**

## Architecture

```
epic-issues-dashboard/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # API server & scheduler
│   ├── jira_client.py      # Jira API integration
│   ├── categorizer.py      # Issue categorization logic
│   ├── database.py         # SQLite database operations
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables
└── frontend/               # React frontend
    ├── src/
    │   ├── components/
    │   │   ├── Dashboard.js    # Main dashboard component
    │   │   └── Dashboard.css   # Dashboard styles
    │   ├── App.js
    │   ├── App.css
    │   ├── index.js
    │   └── index.css
    ├── public/
    │   └── index.html
    └── package.json
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd epic-issues-dashboard/backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. The `.env` file is already configured with your Jira credentials. Review it to ensure settings are correct:
   ```
   JIRA_URL=https://coverwallet.atlassian.net
   JIRA_EMAIL=tyler.wood@coverwallet.com
   JIRA_API_TOKEN=<your-token>
   JIRA_TEAM_ID=3516f16e-7578-4940-9443-0a02386ad88c
   DATABASE_PATH=./issues.db
   API_HOST=0.0.0.0
   API_PORT=8000
   ```

5. Initialize the database and fetch initial data:
   ```bash
   python jira_client.py
   ```

6. Start the backend server:
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd epic-issues-dashboard/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

   The dashboard will open at `http://localhost:3003`

## Usage

### Initial Data Load

After starting the backend for the first time, run:

```bash
cd backend
python jira_client.py
```

This will fetch all issues from Jira, categorize them, and store them in the database.

### Accessing the Dashboard

1. Ensure the backend is running on port 8000
2. Ensure the frontend is running on port 3003
3. Open your browser to `http://localhost:3003`

### Manual Refresh

Click the "🔄 Refresh Data" button in the dashboard header to trigger an immediate data refresh from Jira.

### Automated Daily Refresh

The system automatically refreshes data from Jira every day at 2:00 AM. No manual intervention required.

## API Endpoints

- `GET /` - API information
- `GET /dashboard` - Complete dashboard data
- `POST /refresh` - Trigger manual data refresh
- `GET /categories` - Category statistics
- `GET /status` - Status statistics
- `GET /priority` - Priority statistics
- `GET /category-details` - Detailed category breakdown
- `GET /health` - Health check

## Customization

### Changing the Refresh Schedule

Edit `backend/main.py`, line ~36:

```python
scheduler.add_job(
    refresh_data,
    CronTrigger(hour=2, minute=0),  # Change hour/minute here
    id='daily_refresh',
    replace_existing=True
)
```

### Modifying Categorization Logic

Edit `backend/categorizer.py` to adjust the categorization rules. The function `categorize_issue()` contains all the logic.

### Updating the JQL Query

Edit `backend/jira_client.py`, the `build_jql_query()` method:

```python
def build_jql_query(self):
    return f'(project = "Non Tech RT issues" OR project = "Tech incidents report") AND "Team[Team]" = {self.team_id}'
```

## Production Deployment

### Backend Deployment

1. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```

2. Set up as a systemd service or use Docker

3. Configure environment variables securely (don't commit `.env` to git)

### Frontend Deployment

1. Build the production version:
   ```bash
   cd frontend
   npm run build
   ```

2. Serve the `build/` folder using Nginx, Apache, or a static hosting service

3. Update the API URL in the frontend to point to your production backend

### Database Backup

The SQLite database (`issues.db`) should be backed up regularly:

```bash
cp backend/issues.db backend/issues_backup_$(date +%Y%m%d).db
```

## Troubleshooting

### Backend won't start
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify `.env` file exists and has correct credentials
- Check port 8000 is not already in use

### Frontend can't connect to API
- Ensure backend is running on port 8000
- Check the proxy setting in `frontend/package.json`
- Clear browser cache and restart

### No data showing in dashboard
- Run `python jira_client.py` to fetch initial data
- Check Jira credentials are correct
- Verify the JQL query returns results in Jira

### Categorization seems incorrect
- Review the categorization logic in `backend/categorizer.py`
- Test specific issue summaries/descriptions
- Adjust keyword matching as needed

## Security Notes

- **IMPORTANT**: Never commit the `.env` file to version control
- Use read-only Jira API tokens
- In production, restrict CORS to your frontend domain
- Implement authentication if exposing publicly
- Regularly rotate API tokens

## Support

For issues or questions:
1. Check the API health endpoint: `http://localhost:8000/health`
2. Review backend logs for errors
3. Test Jira connectivity: `python jira_client.py`

## License

Internal use only - CoverWallet
