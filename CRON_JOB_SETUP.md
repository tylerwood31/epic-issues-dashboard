# Daily Cron Job Setup & Verification

## Overview

Your EPIC Issues Dashboard has a **scheduled daily cron job** that automatically fetches new Jira issues every day at **2:00 AM UTC** and stores them in the PostgreSQL database.

---

## How It Works

### 1. **Scheduler Configuration** (`backend/main.py`)

The APScheduler library runs a background job:

```python
@app.on_event("startup")
async def startup_event():
    """Initialize scheduler on startup"""
    scheduler.add_job(
        refresh_data,
        CronTrigger(hour=2, minute=0),
        id='daily_refresh',
        replace_existing=True
    )
    scheduler.start()
    print("Scheduler started - daily refresh at 2:00 AM")
```

### 2. **Refresh Function** (`backend/main.py`)

The `refresh_data()` function:
- Uses `IncrementalFetcher` to fetch only new/updated issues
- Queries Jira for issues created in the **last 7 days**
- Automatically stores them in PostgreSQL (when `DATABASE_URL` is set)

```python
def refresh_data():
    """Background task to refresh Jira data - incremental updates only"""
    fetcher = IncrementalFetcher()
    since_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
    new_issues = fetcher.fetch_new_issues(since_date=since_date)
```

### 3. **Database Connection** (`backend/incremental_fetch.py`)

The `IncrementalFetcher` now automatically uses:
- **PostgreSQL** (production) - when `DATABASE_URL` environment variable is set
- **SQLite** (local development) - when `DATABASE_URL` is not set

This ensures new issues are saved to the persistent PostgreSQL database on Render.

---

## Verification

### Check Scheduler Status

Once Render deploys the latest code, you can check the scheduler status:

```bash
curl https://epic-issues-dashboard.onrender.com/scheduler/status | python3 -m json.tool
```

**Expected Output:**
```json
{
  "success": true,
  "scheduler_running": true,
  "jobs": [
    {
      "id": "daily_refresh",
      "name": "refresh_data",
      "next_run": "2025-10-11T02:00:00",
      "trigger": "cron[hour='2', minute='0']"
    }
  ],
  "timezone": "UTC",
  "current_time": "2025-10-10T08:00:00"
}
```

### Manual Trigger (for testing)

You can manually trigger the refresh job without waiting for 2 AM:

```bash
curl -X POST https://epic-issues-dashboard.onrender.com/refresh
```

**Response:**
```json
{
  "success": true,
  "message": "Data refresh started in background"
}
```

Wait a few seconds, then check the dashboard to see if new issues were added.

### Check Render Logs

To see the cron job execution logs:

1. Go to https://dashboard.render.com/web/srv-ctok56ggph6c73b71e6g
2. Click **"Logs"** tab
3. Look for messages like:
   ```
   [2025-10-11 02:00:00] Starting incremental data refresh...
   Fetching new issues created since 2025-10-04
   Found 5 new issues
   Successfully stored 5 new issues
   [2025-10-11 02:00:05] Refresh complete. Fetched 5 new/updated issues.
   ```

---

## Important Changes Made

### 1. **Fixed `incremental_fetch.py`** ✅
**Problem**: Was hardcoded to use SQLite via `DATABASE_PATH`
**Solution**: Changed to use `Database()` without arguments so it respects `DATABASE_URL`

**Before:**
```python
db_path = os.getenv('DATABASE_PATH', './issues.db')
self.db = Database(db_path)
```

**After:**
```python
# Initialize database (will use DATABASE_URL if set, otherwise SQLite)
self.db = Database()
```

### 2. **Added Scheduler Status Endpoint** ✅
Added `/scheduler/status` to monitor the cron job:
- Check if scheduler is running
- View next scheduled run time
- Verify job configuration

---

## Schedule Details

- **Frequency**: Daily
- **Time**: 2:00 AM UTC
- **What it fetches**: Issues created in the last 7 days
- **Where it stores**: PostgreSQL database (persistent)
- **Why 7 days**: Ensures we catch any issues that might have been created or updated recently

---

## Troubleshooting

### Scheduler not running

**Check Render logs for startup message:**
```
Scheduler started - daily refresh at 2:00 AM
```

If missing, the FastAPI app might not have started correctly.

### No new issues being added

1. **Check if there are actually new issues in Jira** from the last 7 days
2. **Check Render logs** at 2:00 AM UTC for error messages
3. **Manually trigger refresh** to test:
   ```bash
   curl -X POST https://epic-issues-dashboard.onrender.com/refresh
   ```
4. **Verify DATABASE_URL is set** in Render environment variables

### Database connection errors

If you see errors like:
```
could not connect to server
```

**Solution**: Verify `DATABASE_URL` environment variable is correctly set in Render dashboard:
1. Go to https://dashboard.render.com/web/srv-ctok56ggph6c73b71e6g
2. Click **"Environment"** tab
3. Confirm `DATABASE_URL` is set to your **Internal Database URL** (starts with `postgresql://`)

---

## Testing Locally

To test the cron job locally:

```bash
cd backend
source venv/bin/activate

# Run incremental fetch manually
python incremental_fetch.py

# Or start the FastAPI server (scheduler runs automatically)
python main.py
```

The scheduler will start and you'll see:
```
Scheduler started - daily refresh at 2:00 AM
```

To test immediately without waiting for 2 AM:
```bash
curl -X POST http://localhost:8000/refresh
```

---

## Next Steps

1. ✅ **Fixed**: IncrementalFetcher now uses PostgreSQL
2. ✅ **Added**: Scheduler status endpoint
3. ⏳ **Waiting**: Render to deploy latest code
4. 📋 **TODO**: Monitor logs tomorrow at 2:00 AM UTC to verify first automated run

---

## Summary

✅ **Cron job is configured** to run daily at 2:00 AM UTC
✅ **Fetches issues from last 7 days** to catch new and updated issues
✅ **Stores in PostgreSQL** for persistent storage (no more data loss!)
✅ **Can be manually triggered** via `/refresh` endpoint for testing
✅ **Can be monitored** via `/scheduler/status` endpoint (once deployed)

Your dashboard will now stay up-to-date automatically! 🎉
