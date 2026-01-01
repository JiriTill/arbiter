"""
Pytest fixtures for The Arbiter backend tests.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import os

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from app.main import app
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_db():
    """Mock database connection."""
    with patch("app.db.get_db") as mock:
        mock.return_value = AsyncMock()
        yield mock


@pytest.fixture
def mock_games_repo():
    """Mock games repository."""
    mock = MagicMock()
    mock.get_game = AsyncMock(return_value=MagicMock(
        id=1,
        name="Test Game",
        slug="test-game",
        bgg_id=12345,
        cover_image_url=None,
    ))
    mock.get_game_with_sources = AsyncMock(return_value=MagicMock(
        id=1,
        name="Test Game",
        slug="test-game",
        sources=[MagicMock(id=1, edition="1st", source_type="rulebook", needs_ocr=False)]
    ))
    mock.list_games_with_sources = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_sources_repo():
    """Mock sources repository."""
    mock = MagicMock()
    mock.sources_are_indexed = AsyncMock(return_value=True)
    mock.get_unindexed_source_ids = AsyncMock(return_value=[])
    mock.get_source = AsyncMock(return_value=MagicMock(
        id=1,
        source_url="https://example.com/rulebook.pdf"
    ))
    return mock


@pytest.fixture
def mock_chunks_repo():
    """Mock chunks repository."""
    mock = MagicMock()
    mock.search_similar = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch("app.services.answer_generator.get_openai_client") as mock:
        client = MagicMock()
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"verdict": "Yes", "confidence": "high", "quote_exact": "Test quote", "quote_chunk_id": 1, "page": 5, "source_type": "rulebook", "notes": []}'))],
            usage=MagicMock(prompt_tokens=100, completion_tokens=50)
        )
        mock.return_value = client
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis for caching."""
    with patch("app.services.cache.redis") as mock:
        mock.from_url.return_value.__aenter__ = AsyncMock()
        mock.from_url.return_value.__aexit__ = AsyncMock()
        yield mock


@pytest.fixture
def sample_ask_request():
    """Sample valid ask request."""
    return {
        "game_id": 1,
        "edition": "1st",
        "question": "Can I play two actions in one turn?",
        "expansion_ids": []
    }


@pytest.fixture
def sample_feedback_request():
    """Sample feedback request."""
    return {
        "ask_history_id": 1,
        "feedback_type": "helpful",
        "user_note": "Great answer!"
    }
