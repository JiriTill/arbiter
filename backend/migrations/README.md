# The Arbiter - Database Migrations

This directory contains SQL migrations for the Supabase Postgres database.

## Migration Files

| File | Description |
|------|-------------|
| `001_initial_schema.sql` | Initial schema with pgvector, all tables, and indexes |

---

## Prerequisites

1. **Supabase Project**: Create a project at [supabase.com](https://supabase.com)
2. **pgvector Enabled**: Supabase has pgvector pre-installed, but the extension needs to be created
3. **Connection String**: Get your connection string from Supabase Dashboard → Settings → Database

---

## Connection String Format

```
postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

**Example:**
```
postgresql://postgres.abcdefghijklmnop:YourPassword123@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Finding Your Connection String

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Settings** → **Database**
4. Copy the **Connection string** (URI format)
5. Replace `[YOUR-PASSWORD]` with your database password

---

## Applying Migrations

### Option 1: Using psql (Recommended)

```bash
# Navigate to migrations directory
cd backend/migrations

# Apply the migration
psql "YOUR_SUPABASE_CONNECTION_STRING" -f 001_initial_schema.sql
```

**Example:**
```bash
psql "postgresql://postgres.abcdefghijklmnop:MyPassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres" -f 001_initial_schema.sql
```

### Option 2: Using Supabase SQL Editor

1. Go to Supabase Dashboard → **SQL Editor**
2. Click **New Query**
3. Copy the contents of `001_initial_schema.sql`
4. Paste into the editor
5. Click **Run**

### Option 3: Using Supabase CLI

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Run migration
supabase db push
```

---

## Verification Queries

After applying the migration, run these queries to verify everything was created correctly:

### 1. Check pgvector Extension

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

**Expected:** One row with `extname = 'vector'`

### 2. List All Tables

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

**Expected Tables:**
- `answer_feedback`
- `ask_history`
- `expansions`
- `game_sources`
- `games`
- `rule_chunks`
- `source_health`

### 3. Check Indexes

```sql
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;
```

**Expected:** Multiple indexes including `rule_chunks_embedding_idx` (ivfflat)

### 4. Verify Vector Column

```sql
\d rule_chunks
```

Or using SQL:
```sql
SELECT column_name, data_type, udt_name
FROM information_schema.columns 
WHERE table_name = 'rule_chunks' AND column_name = 'embedding';
```

**Expected:** `data_type = 'USER-DEFINED'`, `udt_name = 'vector'`

### 5. Check IVFFlat Index

```sql
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE indexname LIKE '%embedding%';
```

**Expected:** Index using `ivfflat` with `vector_cosine_ops`

---

## Schema Overview

```
┌─────────────┐      ┌─────────────┐
│   games     │──┬──▶│ expansions  │
└─────────────┘  │   └─────────────┘
                 │
                 │   ┌──────────────┐
                 └──▶│ game_sources │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐      ┌────────────────┐
                     │ rule_chunks  │      │ source_health  │
                     │ (embeddings) │      │ (monitoring)   │
                     └──────────────┘      └────────────────┘
                            
┌─────────────┐      ┌──────────────────┐
│ ask_history │──────│ answer_feedback  │
│ (Q&A cache) │      │ (user feedback)  │
└─────────────┘      └──────────────────┘
```

---

## Table Descriptions

| Table | Purpose |
|-------|---------|
| `games` | Base games catalog with BGG reference |
| `expansions` | Game expansions with their own rules |
| `game_sources` | Source documents (rulebooks, FAQs, errata) |
| `rule_chunks` | Chunked text with embeddings for RAG |
| `ask_history` | Q&A history for caching and analytics |
| `answer_feedback` | User feedback for improvement |
| `source_health` | URL health monitoring |

---

## Key Features

### Vector Search (pgvector)

The `rule_chunks.embedding` column stores OpenAI `text-embedding-ada-002` vectors (1536 dimensions). The IVFFlat index enables fast approximate nearest neighbor search:

```sql
-- Find similar chunks for a question embedding
SELECT id, chunk_text, 1 - (embedding <=> '[query_embedding]'::vector) AS similarity
FROM rule_chunks
WHERE source_id IN (SELECT id FROM game_sources WHERE game_id = 1)
ORDER BY embedding <=> '[query_embedding]'::vector
LIMIT 5;
```

### Precedence System

Rules can override each other based on `precedence_level`:
- **1**: Base rulebook
- **2**: Expansion rules
- **3**: Errata/FAQ (highest priority)

The `overrides_chunk_id` column creates explicit override relationships.

### Cache System

The `ask_history` table provides two cache mechanisms:
1. **Exact match**: `normalized_question` for identical questions
2. **Semantic match**: `question_embedding` for similar questions

---

## Troubleshooting

### "extension vector does not exist"

Run this first:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### "permission denied for schema public"

Use the service role key or connect as the postgres user.

### IVFFlat index not working well

Rebuild the index after loading data:
```sql
REINDEX INDEX rule_chunks_embedding_idx;
```

---

## Future Migrations

New migrations should be numbered sequentially:
- `002_add_user_tables.sql`
- `003_add_analytics.sql`
- etc.

Always test migrations on a development database before applying to production.
