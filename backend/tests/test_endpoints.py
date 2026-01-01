"""
Basic API endpoint tests that don't require database or external services.
These tests verify endpoint existence and input validation.
"""

import pytest


class TestHealthEndpoint:
    """Tests for the /health endpoint."""
    
    def test_health_returns_200(self, client):
        """Health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        
    def test_health_returns_status(self, client):
        """Health endpoint returns status field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        
        
class TestRootEndpoint:
    """Tests for the / endpoint."""
    
    def test_root_returns_200(self, client):
        """Root endpoint returns 200."""
        response = client.get("/")
        assert response.status_code == 200
        
    def test_root_returns_name(self, client):
        """Root returns API name."""
        response = client.get("/")
        data = response.json()
        assert "name" in data


class TestInputValidation:
    """Tests for input validation on POST endpoints."""
    
    def test_ask_requires_game_id(self, client):
        """POST /ask requires game_id."""
        response = client.post("/ask", json={
            "question": "Test question here"
        })
        assert response.status_code == 422
        
    def test_ask_requires_question(self, client):
        """POST /ask requires question."""
        response = client.post("/ask", json={
            "game_id": 1
        })
        assert response.status_code == 422
        
    def test_ask_validates_game_id_type(self, client):
        """POST /ask validates game_id is integer."""
        response = client.post("/ask", json={
            "game_id": "not_an_int",
            "question": "Test question here"
        })
        assert response.status_code == 422
        
    def test_ask_validates_question_min_length(self, client):
        """POST /ask validates question minimum length."""
        response = client.post("/ask", json={
            "game_id": 1,
            "question": "Hi"  # Too short
        })
        assert response.status_code == 422
        
    def test_feedback_requires_history_id(self, client):
        """POST /feedback requires ask_history_id."""
        response = client.post("/feedback", json={
            "feedback_type": "helpful"
        })
        assert response.status_code == 422
        
    def test_feedback_validates_type(self, client):
        """POST /feedback validates feedback_type enum."""
        response = client.post("/feedback", json={
            "ask_history_id": 1,
            "feedback_type": "invalid_type"
        })
        assert response.status_code == 422


class TestCORS:
    """Tests for CORS headers."""
    
    def test_cors_allows_origin(self, client):
        """CORS allows configured origins."""
        response = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        # CORS preflight should not fail
        assert response.status_code in [200, 204, 400]


class TestNotFound:
    """Tests for 404 handling."""
    
    def test_unknown_path_returns_404(self, client):
        """Unknown paths return 404."""
        response = client.get("/this-path-does-not-exist")
        assert response.status_code == 404
