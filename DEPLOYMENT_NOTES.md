# PWR Deployment Configuration — Railway

## What's Configured

✅ **Procfile** — Streamlit startup command for Railway
✅ **requirements.txt** — Complete Python dependencies
✅ **railway.json** — Railway service descriptor
✅ **.streamlit/config.toml** — Streamlit runtime config
✅ **.env.example** — Environment variable template

---

## CRITICAL: Database Persistence Model in Railway

### Current Setup
- **Database**: SQLite (pwr.db, local filesystem)
- **Persistence**: ✅ Works locally and between app restarts **on same dyno**
- **Railway dyno restart**: ❌ **Data is LOST** (ephemeral filesystem)

### What This Means
1. **First deploy + N hours of usage**: Data persists normally
2. **When Railway restarts dyno** (deploys, scaling, maintenance): Database resets to initial state
3. **Workaround**: Copy database to Railway Volumes (not yet configured) OR migrate to PostgreSQL

### For This Test Phase
**ACCEPT LIMITATION**: Use SQLite for 3-5 day test, understand that data will reset if dyno restarts.

To detect if this happens:
- Check timestamp of pwr.db file on Railway
- If it's much newer than when you last deployed, dyno restarted
- Data in DB will be from initial setup

### To Make Persistence Real
Implement ONE of:
1. **Railway PostgreSQL** (recommended)
   - Add PostgreSQL service to Railway
   - Update DB layer to use psycopg2
   - Data persists across dyno restarts

2. **Railway Volumes**
   - Mount persistent volume to /pwr_data
   - Survives dyno restarts
   - Limited to ~5GB per service

3. **External Database** (Firebase, Supabase, etc.)
   - Most robust
   - Most complex setup

---

## Environment Variables Required

For Railway to work, set these in Railway dashboard:

```
GEMINI_API_KEY=<your_actual_gemini_key>
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
```

---

## Deployment Steps

1. Push this code to a git repository (GitHub, GitLab, etc.)
2. Connect repository to Railway
3. Set `GEMINI_API_KEY` environment variable
4. Deploy

Railway will:
- Read Procfile
- Install requirements.txt
- Start Streamlit on assigned port
- Generate public URL

---

## Validating Deployment

After Railway deploys:

1. **Access the URL** — Should load PWR Home
2. **Create a test task** — Should appear in "Proyectos"
3. **Execute a task** — Should run and show result
4. **Restart dyno** (manual via Railway dashboard)
5. **Check if data persists** — If it does, persistence is working. If not, dyno restart cleared DB.

---

## Known Limitations (Stabilization Phase)

| Limitation | Impact | Fix |
|-----------|--------|-----|
| Ephemeral SQLite | Data lost on dyno restart | Add PostgreSQL or Volumes |
| No auth | Anyone with URL can use | Add Streamlit auth (future) |
| Single dyno | Not scalable to N users | Not needed for test phase |
| No monitoring | No error visibility | Add Railway logs reader |

---

## Next Steps (Post-Stabilization)

1. Implement persistent database (PostgreSQL recommended)
2. Add proper logging/monitoring
3. Add user authentication if needed
4. Scale to production

