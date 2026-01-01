"""
Integration tests for the /ask endpoint flow.

Tests cover:
- Happy path with indexed sources
- 202 response triggering ingestion
- Verification failure fallback
- Rate limiting (429)
- Budget limiting (503)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


class TestAskEndpointHappyPath:
    """Tests for successful ask flow."""
    
    def test_ask_returns_200_for_indexed_source(self, client, sample_ask_request):
        """When sources are indexed, returns a verdict."""
        with patch("app.api.routes.check_ask_rate_limit") as rate_mock, \
             patch("app.api.routes.check_budget") as budget_mock, \
             patch("app.api.routes.get_games_repo") as games_mock, \
             patch("app.api.routes.get_sources_repo") as sources_mock, \
             patch("app.api.routes.get_chunks_repo") as chunks_mock, \
             patch("app.api.routes.get_cached_answer") as cache_mock, \
             patch("app.api.routes.hybrid_search") as search_mock, \
             patch("app.api.routes.generate_answer_with_verification") as gen_mock, \
             patch("app.api.routes.estimate_answer_quality") as quality_mock, \
             patch("app.api.routes.get_history_repo") as history_mock, \
             patch("app.api.routes.get_costs_repo") as costs_mock:
            
            # Setup mocks
            rate_mock.return_value = MagicMock(allowed=True, remaining=10)
            budget_mock.return_value = MagicMock(allowed=True, remaining_usd=10.0)
            cache_mock.return_value = None
            
            games_repo = MagicMock()
            games_repo.get_game = AsyncMock(return_value=MagicMock(id=1, name="Test Game"))
            games_repo.get_game_with_sources = AsyncMock(return_value=MagicMock(
                id=1, name="Test Game", 
                sources=[MagicMock(id=1, edition="1st", source_type="rulebook")]
            ))
            games_mock.return_value = games_repo
            
            sources_repo = MagicMock()
            sources_repo.sources_are_indexed = AsyncMock(return_value=True)
            sources_mock.return_value = sources_repo
            
            chunks_repo = MagicMock()
            chunks_mock.return_value = chunks_repo
            
            # Mock search returning chunks
            mock_chunk = MagicMock(
                id=1, source_id=1, page_number=5, chunk_text="Test rule text", source_type="rulebook"
            )
            search_mock.return_value = ([mock_chunk], None)
            
            # Mock answer generation
            gen_mock.return_value = {
                "verdict": "Yes, you can play two actions.",
                "quote_exact": "A player may take up to two actions per turn.",
                "quote_chunk_id": 1,
                "page": 5,
                "source_type": "rulebook",
                "verified_quote": True,
                "notes": []
            }
            
            quality_mock.return_value = ("high", "Quote verified exactly")
            
            history_repo = MagicMock()
            history_repo.create_entry = AsyncMock(return_value=MagicMock(id=1))
            history_mock.return_value = history_repo
            
            costs_repo = MagicMock()
            costs_repo.log_cost = AsyncMock()
            costs_mock.return_value = costs_repo
            
            # Make request
            response = client.post("/ask", json=sample_ask_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "verdict" in data
            assert data["confidence"] == "high"

    def test_ask_validates_game_id(self, client):
        """Invalid game_id type returns 422."""
        response = client.post("/ask", json={
            "game_id": "not_a_number",
            "question": "Test question?"
        })
        
        assert response.status_code == 422
        
    def test_ask_validates_question_length(self, client):
        """Question too short returns 422."""
        response = client.post("/ask", json={
            "game_id": 1,
            "question": "Hi"  # Less than 5 chars
        })
        
        assert response.status_code == 422


class TestAskEndpointIndexing:
    """Tests for indexing flow (202 response)."""
    
    def test_ask_returns_202_when_not_indexed(self, client, sample_ask_request):
        """When sources need indexing, returns 202 with job info."""
        with patch("app.api.routes.check_ask_rate_limit") as rate_mock, \
             patch("app.api.routes.check_budget") as budget_mock, \
             patch("app.api.routes.get_games_repo") as games_mock, \
             patch("app.api.routes.get_sources_repo") as sources_mock, \
             patch("app.api.routes.get_cached_answer") as cache_mock, \
             patch("app.api.routes.get_history_repo"), \
             patch("app.api.routes.get_costs_repo"), \
             patch("app.jobs.enqueue_batch_ingestion") as ingest_mock:
            
            rate_mock.return_value = MagicMock(allowed=True)
            budget_mock.return_value = MagicMock(allowed=True)
            cache_mock.return_value = None
            
            games_repo = MagicMock()
            games_repo.get_game = AsyncMock(return_value=MagicMock(id=1, name="Test Game"))
            games_repo.get_game_with_sources = AsyncMock(return_value=MagicMock(
                id=1, name="Test Game", 
                sources=[MagicMock(id=1, edition="1st")]
            ))
            games_mock.return_value = games_repo
            
            sources_repo = MagicMock()
            sources_repo.sources_are_indexed = AsyncMock(return_value=False)
            sources_repo.get_unindexed_source_ids = AsyncMock(return_value=[1])
            sources_mock.return_value = sources_repo
            
            ingest_mock.return_value = ["job-123"]
            
            response = client.post("/ask", json=sample_ask_request)
            
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "indexing"
            assert "job_id" in data
            assert data["sources_to_index"] == 1


class TestAskEndpointRateLimiting:
    """Tests for rate limiting."""
    
    def test_ask_returns_429_when_rate_limited(self, client, sample_ask_request):
        """When rate limited, returns 429."""
        with patch("app.api.routes.check_ask_rate_limit") as rate_mock:
            rate_mock.return_value = MagicMock(
                allowed=False, 
                remaining=0, 
                reset_at="2024-01-01T12:00:00Z"
            )
            
            response = client.post("/ask", json=sample_ask_request)
            
            assert response.status_code == 429


class TestAskEndpointBudgetLimit:
    """Tests for budget limiting."""
    
    def test_ask_returns_503_when_budget_exceeded(self, client, sample_ask_request):
        """When budget exceeded, returns 503."""
        with patch("app.api.routes.check_ask_rate_limit") as rate_mock, \
             patch("app.api.routes.check_budget") as budget_mock:
            
            rate_mock.return_value = MagicMock(allowed=True)
            budget_mock.return_value = MagicMock(
                allowed=False, 
                remaining_usd=0.0,
                message="Daily budget exhausted"
            )
            
            response = client.post("/ask", json=sample_ask_request)
            
            assert response.status_code == 503


class TestAskEndpointCaching:
    """Tests for answer caching."""
    
    def test_ask_returns_cached_answer(self, client, sample_ask_request):
        """Cached answers are returned without processing."""
        with patch("app.api.routes.check_ask_rate_limit") as rate_mock, \
             patch("app.api.routes.check_budget") as budget_mock, \
             patch("app.api.routes.get_cached_answer") as cache_mock, \
             patch("app.api.routes.get_costs_repo") as costs_mock:
            
            rate_mock.return_value = MagicMock(allowed=True)
            budget_mock.return_value = MagicMock(allowed=True)
            
            # Return cached response
            cache_mock.return_value = {
                "success": True,
                "verdict": "Cached verdict",
                "confidence": "high",
                "confidence_reason": "From cache",
                "citations": [],
                "game_name": "Test Game",
                "edition": "1st",
                "question": "Test?",
                "history_id": 1,
                "response_time_ms": 50
            }
            
            costs_repo = MagicMock()
            costs_repo.log_cost = AsyncMock()
            costs_mock.return_value = costs_repo
            
            response = client.post("/ask", json=sample_ask_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["cached"] is True
            assert data["verdict"] == "Cached verdict"


class TestAskEndpointErrorHandling:
    """Tests for error handling."""
    
    def test_ask_handles_game_not_found(self, client, sample_ask_request):
        """Returns 404 when game doesn't exist."""
        with patch("app.api.routes.check_ask_rate_limit") as rate_mock, \
             patch("app.api.routes.check_budget") as budget_mock, \
             patch("app.api.routes.get_games_repo") as games_mock, \
             patch("app.api.routes.get_cached_answer") as cache_mock:
            
            rate_mock.return_value = MagicMock(allowed=True)
            budget_mock.return_value = MagicMock(allowed=True)
            cache_mock.return_value = None
            
            games_repo = MagicMock()
            games_repo.get_game = AsyncMock(return_value=None)
            games_mock.return_value = games_repo
            
            response = client.post("/ask", json=sample_ask_request)
            
            assert response.status_code == 404
            
    def test_ask_handles_no_sources(self, client, sample_ask_request):
        """Returns 404 when game has no sources."""
        with patch("app.api.routes.check_ask_rate_limit") as rate_mock, \
             patch("app.api.routes.check_budget") as budget_mock, \
             patch("app.api.routes.get_games_repo") as games_mock, \
             patch("app.api.routes.get_cached_answer") as cache_mock:
            
            rate_mock.return_value = MagicMock(allowed=True)
            budget_mock.return_value = MagicMock(allowed=True)
            cache_mock.return_value = None
            
            games_repo = MagicMock()
            games_repo.get_game = AsyncMock(return_value=MagicMock(id=1, name="Test"))
            games_repo.get_game_with_sources = AsyncMock(return_value=MagicMock(
                id=1, sources=[]
            ))
            games_mock.return_value = games_repo
            
            response = client.post("/ask", json=sample_ask_request)
            
            assert response.status_code == 404
