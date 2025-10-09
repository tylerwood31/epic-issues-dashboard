# EPIC Issues Dashboard - Deployment Guide

This guide will walk you through deploying the EPIC Issues Dashboard to production so your colleagues can access it.

## Architecture Overview

- **Frontend**: React app deployed to **Vercel** (free tier)
- **Backend**: FastAPI Python server deployed to **Render** (free tier)
- **Database**: SQLite file stored on Render's persistent disk

---

## Step 1: Deploy Backend to Render

### 1.1 Create a Render Account
1. Go to https://render.com and sign up (use GitHub for easy integration)
2. Verify your email

### 1.2 Create a New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository (or use "Public Git repository" if not connected)
   - Repository URL: Your GitHub repo URL
3. Configure the service:
   - **Name**: `epic-issues-backend` (or your preferred name)
   - **Region**: Choose closest to your location
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 1.3 Add Environment Variables
In the Render dashboard, add these environment variables:

```
JIRA_URL=https://coverwallet.atlassian.net
JIRA_EMAIL=tyler.wood@coverwallet.com
JIRA_API_TOKEN=<your-jira-api-token>
JIRA_TEAM_ID=3516f16e-7578-4940-9443-0a02386ad88c
DATABASE_PATH=./issues.db
```

### 1.4 Add Persistent Disk (Important!)
1. In your service settings, go to **"Disks"**
2. Click **"Add Disk"**
3. Configure:
   - **Name**: `issues-db`
   - **Mount Path**: `/app/backend`
   - **Size**: 1 GB (free tier)

This ensures your database persists between deployments.

### 1.5 Deploy
1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. Once deployed, copy your backend URL (e.g., `https://epic-issues-backend.onrender.com`)

### 1.6 Initialize Database
After first deployment, run the CSV importer once:
1. Go to Render dashboard → Shell
2. Run:
   ```bash
   python csv_importer.py
   ```
   Or use the incremental fetcher:
   ```bash
   python incremental_fetch.py
   ```

---

## Step 2: Deploy Frontend to Vercel

### 2.1 Update Frontend Configuration
1. Open `frontend/vercel.json` and update the backend URL:
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

2. Update `frontend/.env.production`:
   ```
   REACT_APP_API_URL=https://YOUR-RENDER-URL.onrender.com
   ```

### 2.2 Create Vercel Account
1. Go to https://vercel.com and sign up (use GitHub for easy integration)
2. Install Vercel CLI (optional):
   ```bash
   npm install -g vercel
   ```

### 2.3 Deploy via Vercel Dashboard
1. Click **"Add New..." → "Project"**
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
   - **Install Command**: `npm install`

4. Add Environment Variables:
   - `REACT_APP_API_URL` = `https://YOUR-RENDER-URL.onrender.com`

5. Click **"Deploy"**

### 2.4 Alternative: Deploy via CLI
```bash
cd frontend
vercel --prod
```

---

## Step 3: Verify Deployment

### 3.1 Test Backend
Open your browser and visit:
```
https://YOUR-RENDER-URL.onrender.com/health
```

You should see:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-09T..."
}
```

### 3.2 Test Frontend
1. Visit your Vercel URL (e.g., `https://epic-issues-dashboard.vercel.app`)
2. Dashboard should load with all issues
3. Try clicking "Refresh Data" button

---

## Step 4: Configure CORS (Production Security)

### 4.1 Update Backend CORS
Edit `backend/main.py` line 22:

```python
allow_origins=["https://YOUR-VERCEL-URL.vercel.app"],  # Add your exact Vercel URL
```

Redeploy backend after this change.

---

## Step 5: Set Up Automated Updates

The backend is already configured to:
- ✅ Automatically fetch new issues daily at 2 AM
- ✅ Check for issues from the last 7 days
- ✅ Update the database incrementally

**No manual intervention needed!** Your colleagues will always see up-to-date data.

---

## Monitoring & Maintenance

### Check Backend Logs
- Go to Render dashboard → Your service → "Logs"
- Look for daily refresh messages: `[TIMESTAMP] Refresh complete. Fetched X new/updated issues.`

### Manual Refresh
If you need to manually trigger a refresh:
1. Open your dashboard in browser
2. Click the **"🔄 Refresh Data"** button

Or use the API directly:
```bash
curl -X POST https://YOUR-RENDER-URL.onrender.com/refresh
```

### Database Backup
To backup your database:
1. Go to Render Shell
2. Run:
   ```bash
   cp issues.db issues_backup_$(date +%Y%m%d).db
   ```

---

## Cost Breakdown

- **Render (Backend)**: Free tier
  - 750 hours/month free
  - Auto-sleeps after inactivity (wakes up in ~30 seconds)

- **Vercel (Frontend)**: Free tier
  - Unlimited bandwidth
  - Always instant (no sleep)

**Total Cost: $0/month** 🎉

---

## Troubleshooting

### Backend sleeping (Render free tier)
**Problem**: First request after inactivity takes 30 seconds

**Solution**:
1. Upgrade to Render paid plan ($7/month for always-on)
2. Or set up a free uptime monitor (like UptimeRobot) to ping your backend every 10 minutes

### CORS errors
**Problem**: Frontend can't connect to backend

**Solution**:
1. Check environment variables in both Vercel and Render
2. Ensure `REACT_APP_API_URL` matches your Render URL
3. Update CORS settings in `backend/main.py`

### Database not persisting
**Problem**: Data resets after deployment

**Solution**:
1. Ensure you added the Persistent Disk in Render
2. Check mount path matches: `/app/backend`

### Jira API errors
**Problem**: Issues not fetching

**Solution**:
1. Check Jira API token is still valid
2. Verify team ID is correct
3. Check Render logs for error messages

---

## Share with Colleagues

Once deployed, share your Vercel URL with your team:
```
https://YOUR-APP-NAME.vercel.app
```

They can:
- ✅ View all issues in real-time
- ✅ See categorization and statistics
- ✅ Click issue links to open in Jira
- ✅ Use the refresh button for immediate updates
- ✅ Access from any device (fully responsive)

---

## Custom Domain (Optional)

### Add Custom Domain to Vercel
1. Go to Vercel project → Settings → Domains
2. Add your domain (e.g., `epic-dashboard.yourcompany.com`)
3. Follow DNS configuration instructions
4. Update CORS in backend to allow your custom domain

---

## Next Steps

1. ✅ Deploy backend to Render
2. ✅ Deploy frontend to Vercel
3. ✅ Test end-to-end
4. ✅ Share URL with team
5. ✅ Set up uptime monitoring (optional)
6. ✅ Add custom domain (optional)

**Questions?** Check the logs in Render/Vercel or the troubleshooting section above.
