# The Arbiter - Backend

FastAPI backend for The Arbiter board game rules Q&A application.

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: Supabase Postgres with pgvector
- **AI**: OpenAI (embeddings + chat)
- **PDF Processing**: PyMuPDF
- **Background Jobs**: Redis + RQ
- **Configuration**: pydantic-settings

## Quick Start

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
# - SUPABASE_URL
# - SUPABASE_SERVICE_ROLE_KEY
# - DATABASE_URL
# - OPENAI_API_KEY
# - REDIS_URL (optional for dev)
```

### 4. Run Database Migrations

```bash
# Connect to your PostgreSQL database and run migrations in order:

# 001 - Initial schema (if not created)
psql $DATABASE_URL -f migrations/001_initial_schema.sql

# 002 - Rate limit violations table
psql $DATABASE_URL -f migrations/002_rate_limit_violations.sql

# 003 - Full-text search (tsvector)
psql $DATABASE_URL -f migrations/003_add_tsvector.sql
```

### 5. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Verify

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

### 5. Run Background Worker (for ingestion jobs)

```bash
# Terminal 1 - Start Redis (if not running)
# Windows: Use Docker or install Redis for Windows
docker run -d -p 6379:6379 redis:latest

# macOS
brew services start redis

# Terminal 2 - Start RQ Worker
cd backend
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Using script
start_worker.bat        # Windows
./start_worker.sh       # macOS/Linux

# Or directly
python -m app.jobs.worker
```

The worker processes background jobs like:
- PDF ingestion with progress tracking
- Embedding generation

## Project Structure

```
backend/
├── app/
│   ├── __init__.py          # Package + version
│   ├── main.py               # FastAPI app + CORS
│   ├── config.py             # Environment settings
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py         # Route handlers
│   ├── services/
│   │   ├── __init__.py
│   │   └── README.md         # Service documentation
│   ├── db/
│   │   ├── __init__.py
│   │   └── connection.py     # Database connection pool
│   └── jobs/
│       ├── __init__.py
│       └── README.md         # Job documentation
├── migrations/
│   ├── 001_initial_schema.sql
│   └── README.md
├── requirements.txt
├── .env.example
└── README.md
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ENVIRONMENT` | `development`, `staging`, or `production` | No (default: development) |
| `DEBUG` | Enable debug mode | No (default: true) |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `REDIS_URL` | Redis connection URL | No (default: localhost) |
| `FRONTEND_URL` | Frontend URL for CORS | No (default: localhost:3000) |

## API Endpoints

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI (dev only) |
| GET | `/redoc` | ReDoc (dev only) |

### Q&A (Coming Soon)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ask` | Ask a rules question |
| GET | `/history` | Get question history |
| POST | `/feedback` | Submit answer feedback |

### Games (Coming Soon)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/games` | List available games |
| GET | `/games/{id}` | Get game details |

## Database

### Apply Migrations

Before running the app, apply the database schema to your Supabase project:

```bash
# Using psql
psql "$DATABASE_URL" -f migrations/001_initial_schema.sql

# Or use Supabase SQL Editor:
# 1. Go to Supabase Dashboard → SQL Editor
# 2. Paste contents of migrations/001_initial_schema.sql
# 3. Run
```

### Seed Initial Data

Populate the database with initial games and sources:

```bash
# Make sure .env is configured with DATABASE_URL
python -m scripts.seed_sources
```

This will:
- Insert 5 popular games (Root, Wingspan, Catan, Terraforming Mars, Splendor)
- Add official rulebook/FAQ sources for each game
- Script is idempotent - safe to run multiple times

**To add more games:** Edit `seed_data.json` and run the script again.

### Verify Database

```bash
# Test database connection
python -c "from app.db.connection import test_connection; test_connection()"

# Check seeded data
psql "$DATABASE_URL" -c "SELECT name, slug FROM games ORDER BY name;"
```

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
# Format
black app/
isort app/

# Lint
ruff check app/
```

### Adding Dependencies

```bash
pip install package-name
pip freeze > requirements.txt
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment

Set `ENVIRONMENT=production` and `DEBUG=false` for production deployments.

## License

MIT
