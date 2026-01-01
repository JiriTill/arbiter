"""
Tests for override detector.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.override_detector import (
    has_override_keywords,
    cosine_similarity,
    classify_override,
    detect_overrides,
)


class TestHasOverrideKeywords:
    """Tests for override keyword detection."""
    
    def test_detects_instead(self):
        text = "Instead of drawing 2 cards, draw 3 cards."
        assert has_override_keywords(text) is True
    
    def test_detects_replaces(self):
        text = "This ability replaces the standard movement rules."
        assert has_override_keywords(text) is True
    
    def test_detects_supersedes(self):
        text = "This rule supersedes all previous rules about combat."
        assert has_override_keywords(text) is True
    
    def test_detects_in_place_of(self):
        text = "Use this card in place of the starting card."
        assert has_override_keywords(text) is True
    
    def test_detects_no_longer(self):
        text = "Players no longer start with 5 gold."
        assert has_override_keywords(text) is True
    
    def test_ignores_normal_text(self):
        text = "Draw 2 cards at the start of your turn."
        assert has_override_keywords(text) is False
    
    def test_ignores_unrelated_text(self):
        text = "The game is played over multiple rounds."
        assert has_override_keywords(text) is False


class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""
    
    def test_identical_vectors(self):
        vec = [1.0, 0.0, 0.5]
        assert abs(cosine_similarity(vec, vec) - 1.0) < 0.001
    
    def test_orthogonal_vectors(self):
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        assert abs(cosine_similarity(vec1, vec2)) < 0.001
    
    def test_opposite_vectors(self):
        vec1 = [1.0, 0.0]
        vec2 = [-1.0, 0.0]
        assert abs(cosine_similarity(vec1, vec2) + 1.0) < 0.001
    
    def test_empty_vectors(self):
        vec1 = [0.0, 0.0]
        vec2 = [1.0, 0.0]
        assert cosine_similarity(vec1, vec2) == 0.0
    
    def test_different_lengths(self):
        vec1 = [1.0, 0.0]
        vec2 = [1.0, 0.0, 0.5]
        assert cosine_similarity(vec1, vec2) == 0.0


class TestClassifyOverride:
    """Tests for LLM-based override classification."""
    
    @patch('app.services.override_detector.get_openai_client')
    def test_detects_override(self, mock_client):
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"is_override": true, "confidence": 85, "evidence_phrase": "instead of"}'
        mock_client.return_value.chat.completions.create.return_value = mock_response
        
        # Create mock chunks
        exp_chunk = MagicMock()
        exp_chunk.chunk_text = "Instead of drawing 2 cards, draw 3 cards."
        
        base_chunk = MagicMock()
        base_chunk.chunk_text = "At the start of your turn, draw 2 cards."
        
        result = classify_override(exp_chunk, base_chunk)
        
        assert result["is_override"] is True
        assert result["confidence"] == 85
        assert "instead" in result["evidence_phrase"].lower()
    
    @patch('app.services.override_detector.get_openai_client')
    def test_no_override(self, mock_client):
        # Mock LLM response for non-override
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"is_override": false, "confidence": 10, "evidence_phrase": ""}'
        mock_client.return_value.chat.completions.create.return_value = mock_response
        
        exp_chunk = MagicMock()
        exp_chunk.chunk_text = "New faction: The Riverfolk Company."
        
        base_chunk = MagicMock()
        base_chunk.chunk_text = "The game supports 2-4 players."
        
        result = classify_override(exp_chunk, base_chunk)
        
        assert result["is_override"] is False
        assert result["confidence"] <= 50


class TestDetectOverrides:
    """Tests for the full override detection pipeline."""
    
    def test_empty_chunks(self):
        result = detect_overrides([], [])
        assert result == []
    
    def test_no_keyword_matches(self):
        # Chunks without override keywords should be skipped
        exp_chunk = MagicMock()
        exp_chunk.chunk_text = "New faction: The Riverfolk Company."
        exp_chunk.embedding = [0.1] * 10
        
        base_chunk = MagicMock()
        base_chunk.chunk_text = "The game supports 2-4 players."
        base_chunk.embedding = [0.1] * 10
        
        result = detect_overrides([exp_chunk], [base_chunk])
        assert result == []  # No LLM calls needed
    
    @patch('app.services.override_detector.classify_override')
    def test_keyword_match_triggers_llm(self, mock_classify):
        # Chunk with keyword should trigger LLM check
        mock_classify.return_value = {
            "is_override": True,
            "confidence": 90,
            "evidence_phrase": "instead of",
        }
        
        exp_chunk = MagicMock()
        exp_chunk.id = 1
        exp_chunk.chunk_text = "Instead of drawing 2 cards, draw 3 cards."
        exp_chunk.embedding = [0.1] * 10
        
        base_chunk = MagicMock()
        base_chunk.id = 2
        base_chunk.chunk_text = "At the start of your turn, draw 2 cards."
        base_chunk.embedding = [0.11] * 10  # Similar embedding
        
        result = detect_overrides([exp_chunk], [base_chunk])
        
        # Should call LLM due to keyword match + high similarity
        mock_classify.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
