"""
FastAPI backend for EPIC Issues Dashboard
"""
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import os
from dotenv import load_dotenv
from jira_client import JiraClient
from incremental_fetch import IncrementalFetcher
from datetime import timedelta

load_dotenv()

app = FastAPI(title="EPIC Issues Dashboard API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Jira client
jira_client = JiraClient()

# Scheduler for daily updates
scheduler = BackgroundScheduler()


def refresh_data():
    """Background task to refresh Jira data - incremental updates only"""
    print(f"[{datetime.now()}] Starting incremental data refresh...")
    try:
        fetcher = IncrementalFetcher()
        # Fetch issues from the last 7 days to catch any new or updated issues
        since_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
        new_issues = fetcher.fetch_new_issues(since_date=since_date)
        print(f"[{datetime.now()}] Refresh complete. Fetched {len(new_issues)} new/updated issues.")
    except Exception as e:
        print(f"[{datetime.now()}] Error during refresh: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Initialize scheduler on startup"""
    # Schedule daily refresh at 2 AM
    scheduler.add_job(
        refresh_data,
        CronTrigger(hour=2, minute=0),
        id='daily_refresh',
        replace_existing=True
    )
    scheduler.start()
    print("Scheduler started - daily refresh at 2:00 AM")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    scheduler.shutdown()


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "EPIC Issues Dashboard API",
        "version": "1.0.0",
        "endpoints": {
            "/dashboard": "Get complete dashboard data",
            "/refresh": "Manually trigger data refresh",
            "/categories": "Get category statistics",
            "/status": "Get status statistics",
            "/priority": "Get priority statistics"
        }
    }


@app.get("/dashboard")
async def get_dashboard():
    """Get complete dashboard data"""
    try:
        data = jira_client.get_dashboard_data()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/refresh")
async def refresh_issues(background_tasks: BackgroundTasks):
    """Manually trigger data refresh"""
    background_tasks.add_task(refresh_data)
    return {
        "success": True,
        "message": "Data refresh started in background"
    }


@app.post("/full-reload")
async def full_reload(background_tasks: BackgroundTasks):
    """Trigger full reload of all issues from Jira"""
    def do_full_reload():
        print(f"[{datetime.now()}] Starting full reload of all issues...")
        try:
            # Import bulk_import_by_keys and run it
            import subprocess
            import sys
            result = subprocess.run(
                [sys.executable, "bulk_import_by_keys.py"],
                capture_output=True,
                text=True
            )
            print(f"[{datetime.now()}] Full reload complete.")
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
        except Exception as e:
            print(f"[{datetime.now()}] Error during full reload: {str(e)}")

    background_tasks.add_task(do_full_reload)
    return {
        "success": True,
        "message": "Full reload started in background. This will fetch all 357 issues from Jira."
    }


@app.get("/categories")
async def get_categories():
    """Get category statistics"""
    try:
        stats = jira_client.db.get_category_stats()
        total = sum(s['value'] for s in stats)

        # Add percentages
        for stat in stats:
            stat['percentage'] = round((stat['value'] / total * 100), 1) if total > 0 else 0

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/status")
async def get_status():
    """Get status statistics"""
    try:
        stats = jira_client.db.get_status_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/priority")
async def get_priority():
    """Get priority statistics"""
    try:
        stats = jira_client.db.get_priority_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/category-details")
async def get_category_details():
    """Get detailed breakdown by category"""
    try:
        details = jira_client.db.get_category_details()
        return {
            "success": True,
            "data": details
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/issues")
async def get_all_issues():
    """Get all issues with core details"""
    try:
        issues = jira_client.db.get_all_issues()
        # Convert to simple dict format
        issues_list = [
            {
                "issue_key": issue.issue_key,
                "summary": issue.summary,
                "status": issue.status,
                "category": issue.category,
                "priority": issue.priority,
                "created_date": issue.created_date.isoformat() if issue.created_date else None,
                "updated_date": issue.updated_date.isoformat() if issue.updated_date else None
            }
            for issue in issues
        ]
        # Sort by issue number descending (newest first) - extract numeric part for proper sorting
        issues_list.sort(key=lambda x: int(x['issue_key'].split('-')[1]), reverse=True)

        return {
            "success": True,
            "data": issues_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/trends")
async def get_weekly_trends():
    """Get week-over-week trend data"""
    try:
        trends = jira_client.db.get_weekly_trends()
        return {
            "success": True,
            "data": trends
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/scheduler/status")
async def scheduler_status():
    """Get scheduler status and next run time"""
    jobs = scheduler.get_jobs()
    job_info = []

    for job in jobs:
        next_run = job.next_run_time
        job_info.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "trigger": str(job.trigger)
        })

    return {
        "success": True,
        "scheduler_running": scheduler.running,
        "jobs": job_info,
        "timezone": "UTC",
        "current_time": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 8000))

    print(f"Starting EPIC Issues Dashboard API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
