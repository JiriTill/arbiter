"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# Ask Endpoint Schemas
# ============================================================================

class AskRequest(BaseModel):
    """Request body for /ask endpoint."""
    game_id: int = Field(..., description="ID of the game to query")
    edition: str | None = Field(None, description="Specific edition (optional)")
    question: str = Field(..., min_length=5, max_length=1000, description="The rules question")
    expansion_ids: list[int] = Field(default=[], description="Optional expansion IDs to include")


class CitationResponse(BaseModel):
    """Citation information in the response."""
    chunk_id: int
    quote: str
    page: int
    source_type: str = "rulebook"
    verified: bool = False
    source_id: int | None = None


class SupersededRuleResponse(BaseModel):
    """Information about a base rule superseded by an expansion."""
    quote: str
    page: int
    source_type: str
    reason: str
    confidence: int | None = None


class AskResponse(BaseModel):
    """Response from /ask endpoint."""
    success: bool
    verdict: str
    confidence: Literal["high", "medium", "low"]
    confidence_reason: str | None = None
    citations: list[CitationResponse]
    game_name: str
    edition: str | None
    question: str
    history_id: int | None = None
    response_time_ms: int
    superseded_rule: SupersededRuleResponse | None = None
    conflict_note: str | None = None
    notes: list[str] | None = None
    cached: bool = False


class AskErrorResponse(BaseModel):
    """Error response from /ask endpoint."""
    success: bool = False
    error: str
    error_code: str
    detail: str | None = None


# ============================================================================
# Games Endpoint Schemas
# ============================================================================

class GameSourceResponse(BaseModel):
    """Source information."""
    id: int
    source_type: str
    edition: str
    needs_ocr: bool = False
    expansion_id: int | None = None


class GameResponse(BaseModel):
    """Game information response."""
    id: int
    name: str
    slug: str
    bgg_id: int | None
    cover_image_url: str | None
    editions: list[str] = []
    has_indexed_sources: bool = False
    sources: list[GameSourceResponse] = []


class GamesListResponse(BaseModel):
    """List of games response."""
    games: list[GameResponse]
    total: int


# ============================================================================
# History Endpoint Schemas
# ============================================================================

class HistoryItemResponse(BaseModel):
    """Single history item."""
    id: int
    game_id: int
    game_name: str
    edition: str | None
    question: str
    verdict: str
    confidence: Literal["high", "medium", "low"]
    citations: list[CitationResponse]
    created_at: datetime


class HistoryListResponse(BaseModel):
    """List of history items."""
    items: list[HistoryItemResponse]
    total: int


# ============================================================================
# Feedback Schemas
# ============================================================================

class FeedbackRequest(BaseModel):
    """Feedback submission request."""
    ask_history_id: int
    feedback_type: Literal["helpful", "wrong_quote", "wrong_interpretation", "missing_context", "wrong_source"]
    selected_chunk_id: int | None = None
    user_note: str | None = None


class FeedbackResponse(BaseModel):
    """Feedback submission response."""
    success: bool
    feedback_id: int


# ============================================================================
# Suggestion Schemas
# ============================================================================

class SourceSuggestionRequest(BaseModel):
    """Request to suggest a new source."""
    game_id: int
    suggested_url: str
    user_note: str | None = None


class SourceSuggestionResponse(BaseModel):
    """Response for suggestion submission."""
    success: bool
    suggestion_id: int
    status: str
