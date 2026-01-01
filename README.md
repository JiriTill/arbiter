# The Arbiter - Board Game Rules Q&A

**Get instant, verified answers to your board game rules questions powered by AI.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Overview

The Arbiter is an AI-powered board game rules assistant that:

- **Answers rules questions** using official rulebooks, FAQs, and errata
- **Cites sources** with page numbers for every answer
- **Verifies quotes** against the original text to prevent hallucination
- **Detects conflicts** between base game and expansion rules
- **Learns from feedback** to improve over time

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI   │────▶│  Supabase   │
│   Frontend  │     │   Backend   │     │  (Postgres) │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌─────────┐   ┌─────────┐
              │ OpenAI  │   │  Redis  │
              │   API   │   │  Cache  │
              └─────────┘   └─────────┘
```

## Features

### For Users
- 📖 Ask natural language questions about game rules
- ✅ Verified citations from official sources
- 🔍 View original rulebook pages in-app
- 📱 Mobile-first PWA design
- 🌙 Dark mode by default

### For Developers
- 🚀 FastAPI with async support
- 🔍 Hybrid search (keyword + vector)
- 📊 Real-time ingestion progress
- 💾 Answer caching with Redis
- 📈 Cost tracking and budget controls

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (via Supabase)
- Redis (optional, for production)
- OpenAI API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run migrations
psql $DATABASE_URL -f migrations/001_initial_schema.sql

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your API URL

npm run dev
```

### Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
arbiter/
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   ├── db/            # Database models & repos
│   │   ├── services/      # Business logic
│   │   ├── jobs/          # Background workers
│   │   └── middleware/    # Rate limiting, auth
│   ├── migrations/        # SQL migrations
│   ├── tests/             # Integration tests
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities
│   │   └── types/         # TypeScript types
│   └── package.json
│
└── docs/                  # Additional documentation
```

## API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ask` | Ask a rules question |
| GET | `/games` | List available games |
| GET | `/games/{id}` | Get game details |
| POST | `/feedback` | Submit answer feedback |
| GET | `/history` | Get question history |

### Ask Request

```json
{
  "game_id": 1,
  "edition": "1st",
  "question": "Can I play two actions in one turn?",
  "expansion_ids": [2, 3]
}
```

### Ask Response

```json
{
  "success": true,
  "verdict": "Yes, each player may take up to 2 actions per turn.",
  "confidence": "high",
  "citations": [
    {
      "chunk_id": 123,
      "quote": "On your turn, you may take up to 2 actions.",
      "page": 12,
      "source_type": "rulebook",
      "verified": true,
      "source_id": 1
    }
  ],
  "game_name": "Root",
  "edition": "1st",
  "response_time_ms": 1250
}
```

## Environment Variables

### Backend

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `REDIS_URL` | Redis connection URL | No |
| `DAILY_BUDGET_USD` | Daily API cost limit | No |
| `ENVIRONMENT` | development/production | No |

### Frontend

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | Yes |

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm run lint
npm run build  # Type checking
```

### Lighthouse Audit

```bash
npx lighthouse http://localhost:3000 --view
# Target: PWA score > 90, Performance > 85
```

## Deployment

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for detailed deployment guides.

### Quick Deploy

**Vercel (Frontend):**
```bash
cd frontend
vercel deploy
```

**Railway (Backend):**
```bash
cd backend
railway up
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- OpenAI for GPT-4 and embeddings
- Supabase for database hosting
- All the board game publishers who create great rulebooks
