# The Arbiter - Development & Technical Overview

**Document Version:** 1.2  
**Last Updated:** January 7, 2026

---

## 📌 What is the Project?

### Project Description

**The Arbiter** is an AI-powered board game rules assistant designed to provide instant, verified answers to rules questions during gameplay. It acts as an impartial "referee" that players can consult when disputes or confusion arise about game mechanics.

### What It Does

- **Answers natural language rules questions** using official rulebooks, FAQs, and errata documents
- **Cites sources with page numbers** for every answer, ensuring transparency
- **Verifies quotes** against original text to prevent AI hallucination
- **Detects conflicts** between base game rules and expansion rules
- **Supports multiple editions** of games with edition-specific answers
- **Learns from user feedback** to improve answer quality over time

### Problem It Solves

Board game players frequently encounter rules disputes during gameplay:

1. **Complex Rulebooks** - Modern board games have lengthy, complex rulebooks that are difficult to navigate quickly
2. **Rules Disputes** - Players often disagree on rule interpretations, disrupting gameplay
3. **Scattered Information** - Official FAQs, errata, and forum clarifications are spread across multiple sources
4. **Edition Confusion** - Different game editions have different rules, causing mix-ups
5. **Time Wasted** - Searching through rulebooks breaks game flow and reduces enjoyment

**The Arbiter solves these problems** by providing instant, verified answers with proper citations, acting as a trusted third party that all players can agree on.

---

## 🏗️ Current State

### What Has Been Built

#### Backend (FastAPI + Python)

| Component | Status | Description |
|-----------|--------|-------------|
| **Core API** | ✅ Complete | Full REST API with FastAPI |
| **Ask Endpoint** | ✅ Complete | Natural language Q&A with citations |
| **Games/Sources API** | ✅ Complete | CRUD for games and source documents |
| **History API** | ✅ Complete | Question history tracking |
| **Feedback System** | ✅ Complete | User feedback collection |
| **PDF Ingestion** | ✅ Complete | PDF processing and chunking |
| **OCR Support** | ✅ Complete | Google Cloud Vision + Tesseract |
| **Hybrid Search** | ✅ Complete | Keyword + vector (pgvector) search |
| **Citation Verification** | ✅ Complete | Quote validation against source text |
| **Conflict Detection** | ✅ Complete | Base vs expansion rule conflicts |
| **Override Detection** | ✅ Complete | Errata/FAQ overriding base rules |
| **Caching (Redis)** | ✅ Complete | Answer caching for performance |
| **Rate Limiting** | ✅ Complete | API rate limiting middleware |
| **Cost Tracking** | ✅ Complete | OpenAI API cost monitoring |
| **Background Jobs** | ✅ Complete | Redis Queue for async ingestion |
| **Admin API** | ✅ Complete | Source management, analytics |
| **SSE Events** | ✅ Complete | Real-time ingestion progress |

#### Frontend (Next.js + TypeScript)

| Component | Status | Description |
|-----------|--------|-------------|
| **Landing Page** | ✅ Complete | Hero section, game showcase |
| **Ask Page** | ✅ Complete | Game selection, question input, results |
| **Source Viewer** | ✅ Complete | In-app PDF viewing with highlights |
| **History Page** | ✅ Complete | Previous questions and answers |
| **Profile Section** | ✅ Complete | User settings placeholder |
| **Admin Panel** | ✅ Complete | Source management, ingestion |
| **Verdict Demo** | ✅ Complete | Demo verdict card showcase |
| **Dark Mode** | ✅ Complete | System-default dark theme |
| **Mobile PWA** | ⏳ Partial | Bottom nav, needs manifest.json work |
| **Bottom Navigation** | ✅ Complete | Mobile-first navigation |
| **Error Handling** | ✅ Complete | Error boundaries, toast notifications |

#### Database (PostgreSQL via Supabase)

| Feature | Status | Description |
|---------|--------|-------------|
| **Schema** | ✅ Complete | 11 migrations applied |
| **Games Table** | ✅ Complete | Game metadata, BGG integration |
| **Sources Table** | ✅ Complete | PDF sources, editions, types |
| **Chunks Table** | ✅ Complete | Text chunks with embeddings |
| **History Table** | ✅ Complete | Question/answer history (ask_history) |
| **Feedback Table** | ✅ Complete | User feedback storage |
| **Vector Search** | ✅ Complete | pgvector extension enabled |
| **Full-Text Search** | ✅ Complete | tsvector columns |

### What's Working

✅ **Core Q&A Flow** - Users can ask questions and receive verified, cited answers  
✅ **PDF Ingestion** - Source documents are processed, chunked, and embedded  
✅ **Hybrid Search** - Both keyword and semantic search working  
✅ **Citation Verification** - Quotes are verified against source text  
✅ **Real-time Progress** - SSE events for ingestion status  
✅ **Caching** - Redis caching reduces duplicate API calls  
✅ **Rate Limiting** - Protection against abuse  
✅ **Admin Functions** - Source management and analytics  
✅ **History API** - `/history` endpoint for Q&A history retrieval  
✅ **History Saving** - Verdicts are saved to database after each question  
✅ **Game Images** - Manual image uploads via Admin Panel (replaced BGG sync)  

### What Needs Work

⚠️ **PWA Manifest** - `manifest.json` needs configuration for home screen install  
⚠️ **Mobile Gestures** - Swipe actions for history items not implemented  
⚠️ **Authentication** - Currently open API, no user accounts  
⚠️ **Game Library** - Only 5 seed games, needs expansion  
⚠️ **Landing Page Polish** - Dynamic typing effect, better visuals planned  
⚠️ **Source Page UX** - PDF viewer dark mode, highlight improvements  
⚠️ **User Profile History** - Show user's own answers in profile (needs auth)  

### Existing Documentation

| Document | Location | Content |
|----------|----------|---------|
| README.md | `/README.md` | Project overview, quick start |
| Backend README | `/backend/README.md` | Backend-specific setup |
| Frontend README | `/frontend/README.md` | Frontend-specific setup |
| API Docs | `/docs/API.md` | Full API reference |
| Deployment Guide | `/docs/DEPLOYMENT.md` | Vercel/Railway deployment |
| Environment Guide | `/docs/ENVIRONMENT.md` | Environment variables |
| Improvement Plan | `/docs/IMPROVEMENT_PLAN.md` | Phased roadmap |
| Design Feedback | `/docs/Design Feedback *.md` | AI design reviews |

---

## 🎯 Goals

### Next Milestones

#### Immediate (Phase 6 - Landing Page & Source Polish)

1. **Landing Page Revamp**
   - Dynamic typing effect for hero headline
   - Verdict card carousel showcasing examples
   - Richer game "box" visuals instead of initials

2. **Source Page Polish**
   - Dark mode support for PDF viewer wrapper
   - Improved citation highlight visibility
   - Auto-scroll to highlighted citations

#### Short-Term (Phase 7 - Profile & Settings)

1. **Settings Page**
   - Theme toggle (Dark/Light/System)
   - Text size accessibility slider

2. **"My Rulebooks" Feature**
   - "Request Game" flow
   - "Upload PDF" placeholder

3. **About Page**
   - "How it works" explanation
   - Trust-building content

#### Medium-Term (Phase 8 - Mobile UX)

1. **Navigation Improvements**
   - Smart bottom nav hide/show
   - iPhone notch handling

2. **Gesture Support**
   - Swipe actions for history
   - Pull-to-refresh

3. **Full PWA**
   - Complete manifest.json
   - Home screen installation
   - Offline indicator

#### Long-Term (Phase 9 - Feedback Loop)

1. **Inline Feedback**
   - Thumb buttons in VerdictCard footer
   - "Report Issue" formalized flow

2. **Answer Quality**
   - Feedback analytics dashboard
   - Auto-retraining signals

### Specific Features Planned

| Feature | Priority | Complexity | Phase |
|---------|----------|------------|-------|
| Typing effect hero | High | Low | 6 |
| Verdict carousel | High | Medium | 6 |
| PDF dark mode | Medium | Low | 6 |
| Theme toggle | Medium | Low | 7 |
| Request game flow | Medium | Medium | 7 |
| Swipe gestures | Low | Medium | 8 |
| PWA manifest | Medium | Low | 8 |
| Inline feedback | High | Medium | 9 |
| User authentication | High | High | Future |
| Game library expansion | High | Low | Ongoing |

---

## ⚙️ Technical Context

### Technology Stack

#### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Core language |
| **FastAPI** | ≥0.109 | Web framework |
| **Uvicorn** | ≥0.27 | ASGI server |
| **PostgreSQL** | 15+ | Primary database |
| **Supabase** | - | Hosted Postgres + Storage |
| **pgvector** | - | Vector similarity search |
| **OpenAI API** | - | GPT-4 + Embeddings |
| **Redis** | ≥5.0 | Caching + job queue |
| **RQ (Redis Queue)** | ≥1.15 | Background job processing |
| **PyMuPDF** | ≥1.23 | PDF text extraction |
| **Tesseract/GCV** | - | OCR for scanned PDFs |

#### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 14.2.35 | React framework |
| **React** | 18.x | UI library |
| **TypeScript** | 5.x | Type safety |
| **Tailwind CSS** | 3.4.x | Styling |
| **Lucide React** | - | Icons |
| **react-pdf** | 10.x | PDF rendering |
| **dnd-kit** | - | Drag-and-drop |
| **Radix UI** | - | Accessible components |

#### Infrastructure

| Service | Purpose |
|---------|---------|
| **Vercel** | Frontend hosting |
| **Railway** | Backend hosting |
| **Supabase** | Database + file storage |
| **Upstash Redis** | Managed Redis (optional) |

### Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│    Next.js      │      │    FastAPI      │      │    Supabase     │
│    Frontend     │─────▶│    Backend      │─────▶│   PostgreSQL    │
│   (Vercel)      │      │   (Railway)     │      │   + pgvector    │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  OpenAI  │ │   Redis  │ │ Supabase │
              │   API    │ │  Cache   │ │ Storage  │
              └──────────┘ └──────────┘ └──────────┘
```

### Constraints & Requirements

1. **API Cost Control** - Daily budget limits for OpenAI API ($10-50/day typical)
2. **Rate Limiting** - Must protect against abuse (10 asks/min)
3. **OCR Quality** - Scanned PDFs require Google Cloud Vision for accuracy
4. **Vector Dimensions** - Using OpenAI text-embedding-3-small (1536 dimensions)
5. **PDF Size** - Large rulebooks may need chunking optimization
6. **CORS** - Backend must allow frontend origin

### Key Environment Variables

```bash
# Backend Required
DATABASE_URL=postgresql://...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
OPENAI_API_KEY=sk-...

# Backend Optional
REDIS_URL=redis://...
DAILY_BUDGET_USD=10
ENVIRONMENT=production

# Frontend Required
NEXT_PUBLIC_API_URL=https://api.arbiter.app
```

---

## 📋 Scope & Planning

### Current Planning Focus

**Recommendation:** Start with **Phase 6** (Landing Page & Source Polish) to maximize visual impact for new users, then proceed to Phase 7 for feature completeness.

### Roadmap Type

| Type | Description | Current Focus |
|------|-------------|---------------|
| **High-Level Roadmap** | ✅ Defined | Phases 6-9 outlined |
| **Detailed Task Breakdown** | ⏳ Needed | Individual tasks TBD |
| **Sprint Planning** | ⏳ Needed | 2-week sprints suggested |

### Suggested Sprint Structure

#### Sprint 1 (Weeks 1-2): Landing Page Polish
- [ ] Implement typing effect for hero headline
- [ ] Create verdict card carousel component
- [ ] Replace game initials with better visuals
- [ ] Review and test landing page UX

#### Sprint 2 (Weeks 3-4): Source Page & PDF
- [ ] Add dark mode wrapper for PDF viewer
- [ ] Improve citation highlighting
- [ ] Implement auto-scroll to highlighted citations
- [ ] Test source viewing on mobile

#### Sprint 3 (Weeks 5-6): Profile & Settings
- [ ] Create Settings page with theme toggle
- [ ] Add text size accessibility option
- [ ] Build "Request Game" placeholder flow
- [ ] Create About page content

#### Sprint 4 (Weeks 7-8): Mobile UX
- [ ] Configure complete manifest.json for PWA
- [ ] Handle iPhone safe areas/notch
- [ ] Implement swipe gestures for history
- [ ] Full mobile testing pass

### Long-Term Vision

1. **User Accounts** - Personal history, saved games, preferences
2. **Game Library Expansion** - Community-driven game additions
3. **Premium Features** - Unlimited asks, priority support
4. **Community Features** - User-submitted corrections, discussions
5. **Browser Extension** - Quick lookups from BoardGameGeek
6. **Mobile Apps** - Native iOS/Android apps

---

## 📁 Project Structure

```
arbiter/
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers (routes.py, admin.py, sse.py)
│   │   ├── db/            # Database models & repositories
│   │   ├── services/      # Business logic (18 service modules)
│   │   ├── jobs/          # Background workers (RQ jobs)
│   │   └── middleware/    # Rate limiting, error handling
│   ├── migrations/        # SQL migrations (11 files)
│   ├── tests/             # Integration tests (pytest)
│   ├── scripts/           # Utility scripts
│   └── requirements.txt   # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages (8 routes)
│   │   ├── components/    # React components (25+ components)
│   │   ├── contexts/      # React contexts
│   │   ├── lib/           # Utilities (API client, helpers)
│   │   └── types/         # TypeScript type definitions
│   ├── public/            # Static assets
│   └── package.json       # Node dependencies
│
├── docs/                  # Documentation (7 files)
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── ENVIRONMENT.md
│   ├── IMPROVEMENT_PLAN.md
│   └── DEVELOPMENT_OVERVIEW.md (this file)
│
└── README.md              # Project overview
```

---

## 🗄️ Database Schema

### Entity Relationship Diagram

```
┌─────────────┐      ┌──────────────┐
│   games     │──────│  expansions  │
└──────┬──────┘      └──────────────┘
       │
       ▼
┌──────────────┐      ┌───────────────┐
│ game_sources │──────│ source_health │
└──────┬───────┘      └───────────────┘
       │
       ▼
┌──────────────┐
│ rule_chunks  │
│ (embeddings) │
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌─────────────────┐
│ ask_history  │──────│ answer_feedback │
│ (Q&A cache)  │      │ (user ratings)  │
└──────────────┘      └─────────────────┘
```

### Core Tables Summary

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `games` | Game catalog | id, name, slug, bgg_id, cover_image_url, image_filename |
| `expansions` | Game expansions | id, game_id, name, code |
| `game_sources` | Source documents | id, game_id, edition, source_type |
| `rule_chunks` | Chunked text + embeddings | id, source_id, chunk_text, embedding |
| `ask_history` | Questions & answers | id, game_id, question, verdict, citations |
| `answer_feedback` | User feedback | id, ask_history_id, feedback_type |
| `source_health` | URL monitoring | id, source_id, status, last_checked_at |

### Q&A Data Flow

```
User Question
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│                    ask_history                          │
│  - game_id → games                                      │
│  - question (user's text)                               │
│  - verdict (AI answer)                                  │
│  - confidence (high/medium/low)                         │
│  - citations (JSONB array)                              │
│     └─ [{chunk_id, quote, page, verified}]              │
│  - model_used, response_time_ms                         │
│  - created_at (timestamp)                               │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────┐
│ answer_feedback │
│ (thumbs up/down)│
│  - feedback_type│
│  - user_note    │
└─────────────────┘
```

### Key Indexes for Performance

| Index | Table | Purpose |
|-------|-------|---------|
| `ask_history_user_id_created_idx` | ask_history | User history queries |
| `ask_history_game_id_created_idx` | ask_history | Game-filtered history |
| `answer_citations_ask_history_id_idx` | answer_citations | Citation lookups |
| `rule_chunks_embedding_idx` | rule_chunks | Vector similarity search |
| `ask_history_question_embedding_idx` | ask_history | Semantic cache |

### Migration Files

| File | Description |
|------|-------------|
| `001_initial_schema.sql` | Core tables, pgvector, indexes |
| `002_rate_limit_violations.sql` | Rate limiting tracking |
| `003_add_tsvector.sql` | Full-text search columns |
| `004_source_health.sql` | URL health monitoring |
| `005_expansions.sql` | Expansion handling |
| `006_override_columns.sql` | Rule override system |
| `007_confidence_analytics.sql` | Confidence scoring |
| `008_feedback.sql` | Answer feedback table |
| `009_api_costs.sql` | API cost tracking |
| `010_source_suggestions.sql` | Community source suggestions |
| `011_performance_indexes.sql` | Query optimization |
| `009_local_images.sql` | Local image storage support |

---

## �📞 Quick Reference

### Local Development Commands

```bash
# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Tests
cd backend && pytest tests/ -v
cd frontend && npm run lint && npm run build
```

### Key URLs (Development)

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Supported Games (Seed Data)

1. Root (BGG: 237182)
2. Wingspan (BGG: 266192)
3. Catan (BGG: 13)
4. Terraforming Mars (BGG: 167791)
5. Splendor (BGG: 148228)

---


---

## 📜 Archived Integrations

### BoardGameGeek (BGG) Image Sync
**Status:** Removed (January 2026)
**Reason:** Persistent IP blocking and 403 Forbidden errors from BGG API.
**History:**
- Attempted direct XML API integration -> Blocked.
- Attempted `api.allorigins.win` proxy client-side -> Blocked/Unreliable.
- Attempted custom User-Agent headers -> Blocked.
**Resolution:** Switched to manual image uploads via Admin Panel. Images are stored locally in `frontend/public/images/games/` (or served via backend static files).

---

*This document provides a comprehensive overview for developers joining the project or planning future development work.*

