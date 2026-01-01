# API Documentation

The Arbiter API is a RESTful API built with FastAPI. Full interactive documentation is available at `/docs` (Swagger UI) or `/redoc` when running the backend.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.arbiter.app` (configure via environment)

## Authentication

Currently, the API is open (no authentication required). Future versions will support:
- API keys for third-party integrations
- OAuth for user-specific history

## Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/ask` | 10 requests | 1 minute |
| `/ingest` | 2 requests | 5 minutes |
| Other | 60 requests | 1 minute |

Rate limit headers:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1704067200
```

---

## Endpoints

### System

#### GET /
API information and version.

**Response:**
```json
{
  "name": "The Arbiter API",
  "version": "0.1.0",
  "status": "running"
}
```

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "redis": "connected",
  "environment": "production"
}
```

---

### Q&A

#### POST /ask
Ask a rules question about a board game.

**Request Body:**
```json
{
  "game_id": 1,
  "edition": "1st",                    // optional
  "question": "Can I move twice?",
  "expansion_ids": [2, 3]              // optional
}
```

**Success Response (200):**
```json
{
  "success": true,
  "verdict": "Yes, you may take up to 2 move actions per turn.",
  "confidence": "high",
  "confidence_reason": "Quote verified exactly",
  "citations": [
    {
      "chunk_id": 123,
      "quote": "Each player may take up to 2 actions on their turn.",
      "page": 12,
      "source_type": "rulebook",
      "verified": true,
      "source_id": 1
    }
  ],
  "game_name": "Root",
  "edition": "1st",
  "question": "Can I move twice?",
  "history_id": 456,
  "response_time_ms": 1250,
  "cached": false
}
```

**Indexing Response (202):**
When sources need to be indexed first:
```json
{
  "status": "indexing",
  "job_id": "abc123",
  "job_ids": ["abc123"],
  "status_url": "/ingest/abc123/events",
  "sources_to_index": 1,
  "estimated_seconds": 45,
  "message": "Indexing official rules for Root. This happens once per game.",
  "game_name": "Root",
  "edition": "1st",
  "question": "Can I move twice?"
}
```

**Error Responses:**
- `404`: Game not found
- `422`: Validation error (bad input)
- `429`: Rate limited
- `503`: Budget exceeded

---

### Games

#### GET /games
List all available games.

**Query Parameters:**
- `search` (string): Filter by name
- `limit` (int): Max results (default: 50)
- `offset` (int): Pagination offset

**Response:**
```json
{
  "games": [
    {
      "id": 1,
      "name": "Root",
      "slug": "root",
      "bgg_id": 237182,
      "cover_image_url": "https://...",
      "editions": ["1st", "2nd"],
      "has_indexed_sources": true,
      "sources": [
        {
          "id": 1,
          "source_type": "rulebook",
          "edition": "1st",
          "needs_ocr": false,
          "expansion_id": null
        }
      ]
    }
  ],
  "total": 1
}
```

#### GET /games/{game_id}
Get details for a specific game.

**Response:**
```json
{
  "id": 1,
  "name": "Root",
  "slug": "root",
  "bgg_id": 237182,
  "cover_image_url": "https://...",
  "editions": ["1st", "2nd"],
  "has_indexed_sources": true,
  "expansions": [
    {
      "id": 2,
      "name": "Riverfolk Expansion",
      "code": "riverfolk",
      "description": "Adds the Riverfolk Company and Lizard Cult"
    }
  ],
  "sources": [...]
}
```

---

### Sources

#### GET /sources/{source_id}/pdf
Proxy PDF content for in-app viewing.

**Response:** PDF binary (application/pdf)

**Headers:**
- `Content-Type: application/pdf`
- `Content-Disposition: inline; filename="source_1.pdf"`

---

### Feedback

#### POST /feedback
Submit feedback on an answer.

**Request Body:**
```json
{
  "ask_history_id": 456,
  "feedback_type": "helpful",           // or "wrong_quote", "wrong_interpretation", etc.
  "selected_chunk_id": 123,             // optional
  "user_note": "Great answer!"          // optional
}
```

**Response:**
```json
{
  "success": true,
  "feedback_id": 789
}
```

---

### History

#### GET /history
Get question history.

**Query Parameters:**
- `game_id` (int): Filter by game
- `limit` (int): Max results (default: 20)
- `offset` (int): Pagination offset

**Response:**
```json
{
  "items": [
    {
      "id": 456,
      "game_id": 1,
      "game_name": "Root",
      "edition": "1st",
      "question": "Can I move twice?",
      "verdict": "Yes, you may...",
      "confidence": "high",
      "citations": [...],
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Ingestion

#### POST /ingest
Trigger background ingestion for a source.

**Request Body:**
```json
{
  "source_id": 1
}
```

**Response (202):**
```json
{
  "status": "enqueued",
  "job_id": "abc123",
  "status_url": "/ingest/abc123/events"
}
```

#### GET /ingest/{job_id}/events
Server-Sent Events stream for ingestion progress.

**Response:** SSE stream
```
event: progress
data: {"stage": "downloading", "progress": 0, "message": "Downloading PDF..."}

event: progress
data: {"stage": "extracting", "progress": 25, "message": "Extracting text..."}

event: progress
data: {"stage": "chunking", "progress": 50, "message": "Creating chunks..."}

event: progress
data: {"stage": "embedding", "progress": 75, "message": "Generating embeddings..."}

event: complete
data: {"success": true, "chunks_created": 120}
```

---

### Source Suggestions

#### POST /sources/suggest
Suggest a new source URL for a game.

**Request Body:**
```json
{
  "game_id": 1,
  "suggested_url": "https://example.com/better-rules.pdf",
  "user_note": "Official FAQ from publisher"
}
```

**Response:**
```json
{
  "success": true,
  "suggestion_id": 123,
  "status": "pending"
}
```

---

## Error Format

All errors follow this format:
```json
{
  "success": false,
  "error": "Human readable message",
  "error_code": "MACHINE_READABLE_CODE",
  "detail": "Additional context"
}
```

Common error codes:
- `GAME_NOT_FOUND`
- `NO_SOURCES`
- `EDITION_NOT_FOUND`
- `RATE_LIMITED`
- `BUDGET_EXCEEDED`
- `SEARCH_ERROR`
- `GENERATION_ERROR`

---

## Webhooks (Future)

Planned webhook events:
- `ingestion.complete`
- `answer.generated`
- `feedback.received`
