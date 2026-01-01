# Deployment Guide

This guide covers deploying The Arbiter to production environments.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Production                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │   Vercel    │───▶│  Railway    │───▶│    Supabase     │  │
│  │  (Frontend) │    │  (Backend)  │    │   (Database)    │  │
│  └─────────────┘    └─────────────┘    └─────────────────┘  │
│                            │                                 │
│                     ┌──────┴──────┐                         │
│                     ▼             ▼                         │
│               ┌─────────┐   ┌─────────┐                     │
│               │ OpenAI  │   │  Upstash │                    │
│               │   API   │   │  Redis   │                    │
│               └─────────┘   └─────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Supabase account (database)
- Vercel account (frontend)
- Railway account (backend)
- OpenAI API key
- Upstash account (Redis, optional)

---

## 1. Database Setup (Supabase)

### Create Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note down:
   - Project URL
   - Service Role Key (Settings → API)
   - Database URL (Settings → Database → Connection string)

### Enable pgvector

```sql
-- Run in SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;
```

### Run Migrations

Run each migration file in order via the SQL Editor:

```bash
migrations/001_initial_schema.sql
migrations/002_rate_limit_violations.sql
migrations/003_add_tsvector.sql
migrations/004_expansions.sql
migrations/005_api_costs.sql
# ... etc
```

### Seed Initial Data

```bash
cd backend
python -m scripts.seed_sources
```

---

## 2. Backend Deployment (Railway)

### Option A: Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
cd backend
railway init

# Add environment variables
railway variables set DATABASE_URL=<your-supabase-url>
railway variables set SUPABASE_URL=<your-supabase-url>
railway variables set SUPABASE_SERVICE_ROLE_KEY=<your-key>
railway variables set OPENAI_API_KEY=<your-key>
railway variables set REDIS_URL=<your-upstash-url>
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false

# Deploy
railway up
```

### Option B: GitHub Integration

1. Push your code to GitHub
2. Create new project on [railway.app](https://railway.app)
3. Connect your GitHub repo
4. Select the `backend` directory
5. Configure environment variables
6. Railway auto-deploys on push

### Railway Configuration

Create `railway.json` in backend folder:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

Create `Procfile`:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: python -m app.jobs.worker
```

---

## 3. Frontend Deployment (Vercel)

### Option A: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL
# Enter your Railway backend URL
```

### Option B: GitHub Integration

1. Push code to GitHub
2. Import project at [vercel.com](https://vercel.com)
3. Select the `frontend` directory
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://your-backend.railway.app`
5. Deploy

### Vercel Configuration

Create `vercel.json` in frontend folder:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "regions": ["iad1"]
}
```

---

## 4. Redis Setup (Upstash)

### Create Database

1. Go to [upstash.com](https://upstash.com)
2. Create a new Redis database
3. Copy the connection URL
4. Add to Railway as `REDIS_URL`

### Configuration

Redis is used for:
- Answer caching (24h TTL)
- PDF caching (1h TTL)
- Rate limiting state

Without Redis, the app falls back to in-memory caching (not recommended for production).

---

## 5. Background Workers

### RQ Worker (Railway)

For background PDF ingestion, deploy a separate worker service:

1. In Railway, add a new service from the same repo
2. Set start command: `python -m app.jobs.worker`
3. Use the same environment variables

### Scheduler (Optional)

For periodic tasks like re-indexing:

```python
# Add to crontab or Railway scheduled job
python -m app.jobs.scheduler
```

---

## 6. Domain & SSL

### Custom Domain (Vercel)

1. Go to Project Settings → Domains
2. Add your domain
3. Update DNS records as shown

### Custom Domain (Railway)

1. Go to Service Settings → Networking
2. Generate a domain or add custom
3. Update DNS records

---

## 7. Monitoring

### Health Checks

Backend health endpoint:
```
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "redis": "connected"
}
```

### Logging

- Railway: View logs in dashboard
- Vercel: View function logs
- Set up Sentry for error tracking (optional)

### Metrics

Monitor:
- API response times
- Error rates
- OpenAI API costs (tracked in `api_costs` table)
- Cache hit rates

---

## 8. Environment Variables Reference

### Backend (Railway)

| Variable | Example | Required |
|----------|---------|----------|
| `DATABASE_URL` | `postgresql://...` | Yes |
| `SUPABASE_URL` | `https://xxx.supabase.co` | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJ...` | Yes |
| `OPENAI_API_KEY` | `sk-...` | Yes |
| `REDIS_URL` | `redis://...` | No |
| `ENVIRONMENT` | `production` | Yes |
| `DEBUG` | `false` | Yes |
| `DAILY_BUDGET_USD` | `10.0` | No |
| `FRONTEND_URL` | `https://arbiter.app` | Yes |

### Frontend (Vercel)

| Variable | Example | Required |
|----------|---------|----------|
| `NEXT_PUBLIC_API_URL` | `https://api.arbiter.app` | Yes |

---

## 9. Security Checklist

- [ ] HTTPS enabled (automatic on Vercel/Railway)
- [ ] CORS configured for production domain only
- [ ] Rate limiting enabled
- [ ] Budget limits configured
- [ ] Service role key secured (never in frontend)
- [ ] Environment set to `production`
- [ ] Debug mode disabled

---

## 10. Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### CORS Errors

Ensure `FRONTEND_URL` is set correctly in backend.

### OpenAI Rate Limits

The app implements exponential backoff. If persistent:
- Check your OpenAI usage limits
- Implement request queuing

### Redis Connection

Falls back gracefully to in-memory cache if Redis unavailable.

---

## Quick Checklist

- [ ] Supabase database created with pgvector
- [ ] Migrations applied
- [ ] Initial data seeded
- [ ] Backend deployed to Railway
- [ ] Worker deployed for background jobs
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured
- [ ] Custom domain set up (optional)
- [ ] Monitoring configured
- [ ] SSL working
- [ ] Health checks passing
