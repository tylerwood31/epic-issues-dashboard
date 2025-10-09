# Quick Deploy Guide - TL;DR

## Prerequisites
- GitHub account
- Render account (sign up at render.com)
- Vercel account (sign up at vercel.com)

## Deploy in 10 Minutes

### 1. Push to GitHub (if not already)
```bash
cd /Users/tylerwood/epic-issues-dashboard
git init
git add .
git commit -m "Initial commit - EPIC Issues Dashboard"
gh repo create epic-issues-dashboard --public
git push -u origin main
```

### 2. Deploy Backend to Render
1. Go to https://render.com
2. Click **"New +" → "Web Service"**
3. Connect your GitHub repo
4. Settings:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   ```
   JIRA_URL=https://coverwallet.atlassian.net
   JIRA_EMAIL=tyler.wood@coverwallet.com
   JIRA_API_TOKEN=<your-token>
   JIRA_TEAM_ID=3516f16e-7578-4940-9443-0a02386ad88c
   DATABASE_PATH=./issues.db
   ```
6. Add Disk:
   - Mount Path: `/app/backend`
   - Size: 1 GB
7. Click **"Create Web Service"**
8. Copy your backend URL (e.g., `https://epic-issues-backend.onrender.com`)

### 3. Update Frontend Configuration
Update `frontend/.env.production`:
```
REACT_APP_API_URL=https://YOUR-RENDER-URL.onrender.com
```

Update `frontend/vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://YOUR-RENDER-URL.onrender.com/:path*"
    }
  ]
}
```

Commit and push:
```bash
git add .
git commit -m "Update production URLs"
git push
```

### 4. Deploy Frontend to Vercel
1. Go to https://vercel.com
2. Click **"Add New... → Project"**
3. Import your GitHub repository
4. Settings:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
5. Add environment variable:
   - `REACT_APP_API_URL` = `https://YOUR-RENDER-URL.onrender.com`
6. Click **"Deploy"**
7. Copy your Vercel URL

### 5. Initialize Database
In Render dashboard → Shell:
```bash
python csv_importer.py
```

### 6. Done! 🎉
Share your Vercel URL with your team:
```
https://YOUR-APP.vercel.app
```

## Total Cost: $0/month
Both services have free tiers that are perfect for internal dashboards.

## What Happens Next?
- ✅ Dashboard updates automatically daily at 2 AM
- ✅ Team can click "Refresh Data" for immediate updates
- ✅ All 372+ issues displayed with categories
- ✅ Direct links to Jira issues

## Troubleshooting
See `DEPLOYMENT.md` for detailed troubleshooting steps.
