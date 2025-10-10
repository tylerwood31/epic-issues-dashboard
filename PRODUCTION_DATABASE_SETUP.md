# Production Database Setup - Preventing Data Loss

## ⚠️ CRITICAL ISSUE

**Render uses ephemeral storage** - Every time your app restarts, the SQLite database is wiped clean. This is why you lost 334 records!

## Solution: Use PostgreSQL on Render

PostgreSQL databases on Render are **persistent** and won't lose data on restarts.

---

## Step-by-Step Setup

### 1. Create PostgreSQL Database on Render

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `epic-issues-db`
   - **Database**: `epic_issues`
   - **User**: (auto-generated)
   - **Region**: Same as your web service (for lowest latency)
   - **Plan**: Free tier is fine for now
4. Click **"Create Database"**
5. Wait for it to provision (~2 minutes)

### 2. Get the Database URL

1. Once created, click on your PostgreSQL instance
2. Find **"Internal Database URL"** (starts with `postgres://...`)
3. Copy this URL

### 3. Add DATABASE_URL to Your Web Service

1. Go to your web service: https://dashboard.render.com/web/epic-issues-dashboard
2. Go to **"Environment"** tab
3. Click **"Add Environment Variable"**
4. Add:
   - **Key**: `DATABASE_URL`
   - **Value**: (paste the Internal Database URL you copied)
5. Click **"Save Changes"**
6. Render will automatically redeploy your app

### 4. Migrate Your Data

After Render redeploys with the new DATABASE_URL, run this locally to migrate your data:

```bash
cd backend

# Set the DATABASE_URL temporarily (replace with your actual URL)
export DATABASE_URL="postgres://user:password@hostname/database"

# Run migration
python migrate_to_postgres.py
```

This will copy all 372 issues from your local SQLite to the Render PostgreSQL database.

---

## Verification

After migration, check your production dashboard:

```bash
curl https://epic-issues-dashboard.onrender.com/dashboard | python3 -m json.tool
```

You should see `"total_issues": 372`

---

## Why This Happened

1. **Render's Free Tier**: Uses ephemeral file storage that resets on every deploy/restart
2. **SQLite limitation**: File-based database stored in ephemeral storage
3. **Incremental fetcher**: Only fetches last 7 days of issues (23 records), not full history

## What We Fixed

1. ✅ Updated `database.py` to support PostgreSQL via `DATABASE_URL` environment variable
2. ✅ Added `psycopg2-binary` for PostgreSQL driver
3. ✅ Created migration script to copy data from SQLite → PostgreSQL
4. ✅ Falls back to SQLite for local development (when DATABASE_URL not set)

---

## Future Protection

### Automatic Backups

Render PostgreSQL includes automatic daily backups (retained for 7 days on free tier).

### Manual Backups

To manually backup your database:

```bash
# Get the External Database URL from Render dashboard
pg_dump <EXTERNAL_DATABASE_URL> > backup-$(date +%Y%m%d).sql
```

### Restore from Backup

```bash
psql <EXTERNAL_DATABASE_URL> < backup-20251010.sql
```

---

## Cost

- **PostgreSQL Free Tier**:
  - 256 MB RAM
  - 1 GB Storage
  - 90 days of inactivity before deletion
  - Perfect for this use case (~400 issues = ~1 MB)

- **Paid Tier** (if needed later):
  - $7/month for 1 GB RAM, 10 GB storage
  - Better performance and support

---

## Next Steps

1. ☐ Create PostgreSQL database on Render
2. ☐ Add DATABASE_URL environment variable to web service
3. ☐ Wait for automatic redeploy
4. ☐ Run migration script to restore all 372 issues
5. ☐ Verify data in production dashboard
6. ☐ Set up weekly backup script (optional)

---

## Questions?

- Render PostgreSQL docs: https://render.com/docs/databases
- Need help? Check the Render dashboard logs for any connection errors
