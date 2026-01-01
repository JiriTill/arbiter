# Environment Variables Reference

This document lists all environment variables used by The Arbiter.

## Backend Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string with pgvector | `postgresql://user:pass@host:5432/db?sslmode=require` |
| `SUPABASE_URL` | Supabase project URL | `https://xxxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (secret) | `eyJhbGciOiJIUz...` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings and chat | `sk-...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `REDIS_URL` | Redis connection URL for caching | `redis://localhost:6379` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` |
| `DAILY_BUDGET_USD` | Daily API cost limit | `10.0` |
| `RATE_LIMIT_REQUESTS` | Rate limit requests per window | `10` |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate limit window in seconds | `60` |

### Environment Values

**ENVIRONMENT**:
- `development` - Local development, debug enabled
- `staging` - Staging environment
- `production` - Production, debug disabled

## Frontend Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | Yes |

## Example .env Files

### Backend (.env)

```bash
# Required
DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
OPENAI_API_KEY=sk-proj-xxxxx

# Optional
ENVIRONMENT=development
DEBUG=true
REDIS_URL=redis://localhost:6379
FRONTEND_URL=http://localhost:3000
DAILY_BUDGET_USD=10.0
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production Backend

```bash
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
OPENAI_API_KEY=sk-...
ENVIRONMENT=production
DEBUG=false
REDIS_URL=redis://...upstash.io:6379
FRONTEND_URL=https://arbiter.app
DAILY_BUDGET_USD=25.0
```

### Production Frontend

```bash
NEXT_PUBLIC_API_URL=https://api.arbiter.app
```

## Security Notes

1. **Never commit** `.env` files to version control
2. **Use secrets management** in production (Vercel/Railway built-in)
3. **Rotate keys** periodically, especially `SUPABASE_SERVICE_ROLE_KEY`
4. **Restrict CORS** to specific domains in production
5. **Set budget limits** to prevent runaway API costs

## Validation

The backend validates environment on startup. Missing required variables will cause the app to fail fast with a clear error message.

```python
# app/config.py
class Settings(BaseSettings):
    database_url: str  # Required, no default
    openai_api_key: str  # Required, no default
    environment: Literal["development", "staging", "production"] = "development"
    # ...
```
