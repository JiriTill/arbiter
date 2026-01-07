"""
Pydantic models for database entities.
These models match the SQL schema in migrations/001_initial_schema.sql
"""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


# ============================================================================
# Type Aliases
# ============================================================================

SourceType = Literal["rulebook", "faq", "errata", "reference_card"]
Confidence = Literal["high", "medium", "low"]
FeedbackType = Literal["helpful", "wrong_quote", "wrong_interpretation", "missing_context", "wrong_source"]
HealthStatus = Literal["ok", "changed", "error", "not_found"]


# ============================================================================
# Base Model
# ============================================================================

class BaseDBModel(BaseModel):
    """Base model with common configuration for ORM compatibility."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# ============================================================================
# Game Models
# ============================================================================

class GameBase(BaseDBModel):
    """Base game fields for creation."""
    name: str
    slug: str
    bgg_id: int | None = None
    cover_image_url: str | None = None


class GameCreate(GameBase):
    """Fields for creating a new game."""
    pass


class Game(GameBase):
    """Full game model with all fields."""
    id: int
    created_at: datetime
    updated_at: datetime


class GameWithSources(Game):
    """Game with related sources."""
    sources: list["GameSource"] = []
    expansions: list["Expansion"] = []


# ============================================================================
# Expansion Models
# ============================================================================

class ExpansionBase(BaseDBModel):
    """Base expansion fields."""
    game_id: int
    name: str
    code: str | None = None
    bgg_id: int | None = None
    release_date: date | None = None


class ExpansionCreate(ExpansionBase):
    """Fields for creating a new expansion."""
    pass


class Expansion(ExpansionBase):
    """Full expansion model."""
    id: int
    created_at: datetime


# ============================================================================
# Game Source Models
# ============================================================================

class GameSourceBase(BaseDBModel):
    """Base source fields."""
    game_id: int
    expansion_id: int | None = None
    edition: str
    source_type: SourceType
    source_url: str | None = None
    is_official: bool = True
    file_hash: str | None = None
    needs_ocr: bool | None = False
    needs_reingest: bool | None = False
    verified_by: str | None = None


class GameSourceCreate(GameSourceBase):
    """Fields for creating a new source."""
    pass


class GameSource(GameSourceBase):
    """Full source model."""
    id: int
    last_ingested_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class GameSourceWithChunks(GameSource):
    """Source with related chunks."""
    chunks_count: int = 0


# ============================================================================
# Source Suggestion Models
# ============================================================================

class SourceSuggestionBase(BaseDBModel):
    """Base fields for source suggestion."""
    game_id: int
    suggested_url: str
    user_note: str | None = None


class SourceSuggestionCreate(SourceSuggestionBase):
    """Fields for creating a new suggestion."""
    pass


class SourceSuggestion(SourceSuggestionBase):
    """Full suggestion model."""
    id: int
    status: Literal["pending", "approved", "rejected"]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Rule Chunk Models
# ============================================================================

class RuleChunkBase(BaseDBModel):
    """Base chunk fields."""
    source_id: int
    page_number: int
    chunk_index: int
    section_title: str | None = None
    chunk_text: str
    precedence_level: int = 1
    overrides_chunk_id: int | None = None
    override_confidence: float | None = None
    phase_tags: list[str] | None = None
    expires_at: datetime | None = None


class RuleChunkCreate(RuleChunkBase):
    """Fields for creating a new chunk."""
    embedding: list[float] | None = None  # 1536-dim vector


class RuleChunk(RuleChunkBase):
    """Full chunk model (without embedding for efficiency)."""
    id: int
    created_at: datetime


class RuleChunkWithEmbedding(RuleChunk):
    """Chunk with embedding vector (for search operations)."""
    embedding: list[float] | None = None


class RuleChunkSearchResult(RuleChunk):
    """Chunk with similarity score from vector search."""
    similarity: float
    source_edition: str | None = None
    game_name: str | None = None


# ============================================================================
# Ask History Models
# ============================================================================

class Citation(BaseDBModel):
    """Citation structure stored in JSON."""
    chunk_id: int
    quote: str
    page: int
    verified: bool = False


class AskHistoryBase(BaseDBModel):
    """Base history fields."""
    game_id: int
    edition: str | None = None
    expansions_used: list[int] = []
    question: str
    normalized_question: str | None = None
    verdict: str
    confidence: Confidence
    confidence_reason: str | None = None
    citations: list[Citation] = []
    response_time_ms: int | None = None
    model_used: str | None = None


class AskHistoryCreate(AskHistoryBase):
    """Fields for creating a history entry."""
    question_embedding: list[float] | None = None


class AskHistory(AskHistoryBase):
    """Full history model."""
    id: int
    created_at: datetime


class AskHistoryWithGame(AskHistory):
    """History with game info."""
    game_name: str
    game_slug: str
    cover_image_url: str | None = None



# ============================================================================
# Answer Feedback Models
# ============================================================================

class AnswerFeedbackBase(BaseDBModel):
    """Base feedback fields."""
    ask_history_id: int
    feedback_type: FeedbackType
    selected_chunk_id: int | None = None
    user_note: str | None = None


class AnswerFeedbackCreate(AnswerFeedbackBase):
    """Fields for creating feedback."""
    pass


class AnswerFeedback(AnswerFeedbackBase):
    """Full feedback model."""
    id: int
    created_at: datetime


# ============================================================================
# Source Health Models
# ============================================================================

class SourceHealthBase(BaseDBModel):
    """Base health check fields."""
    source_id: int
    last_checked_at: datetime
    status: HealthStatus
    http_code: int | None = None
    file_hash: str | None = None
    content_length: int | None = None
    error: str | None = None


class SourceHealthCreate(SourceHealthBase):
    """Fields for creating a health check."""
    pass


class SourceHealth(SourceHealthBase):
    """Full health check model."""
    id: int
    created_at: datetime


# ============================================================================
# API Cost Models
# ============================================================================

class ApiCostBase(BaseDBModel):
    """Base API cost fields."""
    request_id: str
    endpoint: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    cache_hit: bool = False


class ApiCostCreate(ApiCostBase):
    """Fields for creating an API cost entry."""
    pass


class ApiCost(ApiCostBase):
    """Full API cost model."""
    id: int
    created_at: datetime


# ============================================================================
# Circular Reference Resolution
# ============================================================================

GameWithSources.model_rebuild()
