"""
History repository for Q&A history and caching.
"""

import json
from datetime import datetime
from typing import Any

from app.db.models import (
    AskHistory, 
    AskHistoryCreate, 
    AskHistoryWithGame,
    AnswerFeedback,
    AnswerFeedbackCreate,
    Citation,
)
from app.db.repositories.base import BaseRepository


class HistoryRepository(BaseRepository[AskHistory, AskHistoryCreate]):
    """Repository for ask_history table."""
    
    table_name = "ask_history"
    model_class = AskHistory
    
    # ========================================================================
    # Save & Retrieve
    # ========================================================================
    
    async def save_query(self, history: AskHistoryCreate) -> AskHistory:
        """
        Save a Q&A interaction to history.
        
        Args:
            history: The history entry to save
            
        Returns:
            Created AskHistory with ID
        """
        embedding_value = None
        if history.question_embedding:
            embedding_value = "[" + ",".join(map(str, history.question_embedding)) + "]"
        
        # Convert citations to JSON
        citations_json = json.dumps([c.model_dump() for c in history.citations])
        expansions_json = json.dumps(history.expansions_used)
        
        query = """
            INSERT INTO ask_history (
                game_id, edition, expansions_used, question, normalized_question,
                question_embedding, verdict, confidence, confidence_reason, citations,
                response_time_ms, model_used
            )
            VALUES (%s, %s, %s::jsonb, %s, %s, %s::vector, %s, %s, %s, %s::jsonb, %s, %s)
            RETURNING id, game_id, edition, expansions_used, question, 
                      normalized_question, verdict, confidence, confidence_reason, citations,
                      response_time_ms, model_used, created_at
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (
                history.game_id,
                history.edition,
                expansions_json,
                history.question,
                history.normalized_question,
                embedding_value,
                history.verdict,
                history.confidence,
                history.confidence_reason,
                citations_json,
                history.response_time_ms,
                history.model_used,
            ))
            row = await cur.fetchone()
            await self.conn.commit()
            
            # Parse citations back
            result = dict(row)
            if isinstance(result.get("citations"), str):
                result["citations"] = json.loads(result["citations"])
            if isinstance(result.get("expansions_used"), str):
                result["expansions_used"] = json.loads(result["expansions_used"])
            
            return AskHistory.model_validate(result)
    
    async def get_history(
        self,
        game_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AskHistoryWithGame]:
        """
        Get Q&A history with game info.
        
        Args:
            game_id: Optional filter by game
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of history entries with game info
        """
        conditions = []
        params: list = []
        
        if game_id is not None:
            conditions.append("ah.game_id = %s")
            params.append(game_id)
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        params.extend([limit, offset])
        
        query = f"""
            SELECT 
                ah.*,
                g.name as game_name,
                g.slug as game_slug,
                g.cover_image_url as cover_image_url
            FROM ask_history ah
            JOIN games g ON ah.game_id = g.id
            WHERE {where_clause}
            ORDER BY ah.created_at DESC
            LIMIT %s OFFSET %s
        """
        
        async with self._get_cursor() as cur:
            await cur.execute(query, tuple(params))
            rows = await cur.fetchall()
            
            results = []
            for row in rows:
                row_dict = dict(row)
                # Parse JSON fields
                if isinstance(row_dict.get("citations"), str):
                    row_dict["citations"] = json.loads(row_dict["citations"])
                if isinstance(row_dict.get("expansions_used"), str):
                    row_dict["expansions_used"] = json.loads(row_dict["expansions_used"])
                results.append(AskHistoryWithGame.model_validate(row_dict))
            
            return results
    
    async def get_history_entry(self, history_id: int) -> AskHistoryWithGame | None:
        """Get a single history entry with game info."""
        query = """
            SELECT 
                ah.*,
                g.name as game_name,
                g.slug as game_slug
            FROM ask_history ah
            JOIN games g ON ah.game_id = g.id
            WHERE ah.id = %s
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (history_id,))
            row = await cur.fetchone()
            
            if not row:
                return None
            
            row_dict = dict(row)
            if isinstance(row_dict.get("citations"), str):
                row_dict["citations"] = json.loads(row_dict["citations"])
            if isinstance(row_dict.get("expansions_used"), str):
                row_dict["expansions_used"] = json.loads(row_dict["expansions_used"])
            
            return AskHistoryWithGame.model_validate(row_dict)
    
    # ========================================================================
    # Cache Lookup
    # ========================================================================
    
    async def find_cached_exact(
        self,
        game_id: int,
        normalized_question: str,
    ) -> AskHistory | None:
        """
        Find an exact cache hit by normalized question.
        
        Args:
            game_id: The game to search in
            normalized_question: Normalized (lowered, trimmed) question text
            
        Returns:
            Cached answer if found
        """
        query = """
            SELECT * FROM ask_history
            WHERE game_id = %s AND normalized_question = %s
            ORDER BY created_at DESC
            LIMIT 1
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (game_id, normalized_question))
            row = await cur.fetchone()
            
            if not row:
                return None
            
            row_dict = dict(row)
            if isinstance(row_dict.get("citations"), str):
                row_dict["citations"] = json.loads(row_dict["citations"])
            if isinstance(row_dict.get("expansions_used"), str):
                row_dict["expansions_used"] = json.loads(row_dict["expansions_used"])
            
            return AskHistory.model_validate(row_dict)
    
    async def find_cached_semantic(
        self,
        game_id: int,
        question_embedding: list[float],
        min_similarity: float = 0.95,
    ) -> AskHistory | None:
        """
        Find a semantic cache hit by question embedding.
        
        Args:
            game_id: The game to search in
            question_embedding: Question embedding vector
            min_similarity: Minimum similarity threshold (default 0.95 = very similar)
            
        Returns:
            Cached answer if found with high similarity
        """
        embedding_str = "[" + ",".join(map(str, question_embedding)) + "]"
        
        query = """
            SELECT *,
                   1 - (question_embedding <=> %s::vector) as similarity
            FROM ask_history
            WHERE game_id = %s 
                  AND question_embedding IS NOT NULL
                  AND 1 - (question_embedding <=> %s::vector) >= %s
            ORDER BY question_embedding <=> %s::vector
            LIMIT 1
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (
                embedding_str, game_id, embedding_str, min_similarity, embedding_str
            ))
            row = await cur.fetchone()
            
            if not row:
                return None
            
            row_dict = dict(row)
            if isinstance(row_dict.get("citations"), str):
                row_dict["citations"] = json.loads(row_dict["citations"])
            if isinstance(row_dict.get("expansions_used"), str):
                row_dict["expansions_used"] = json.loads(row_dict["expansions_used"])
            
            return AskHistory.model_validate(row_dict)
    
    # ========================================================================
    # Stats
    # ========================================================================
    
    async def get_stats(self, game_id: int | None = None) -> dict:
        """Get usage statistics."""
        conditions = []
        params: list = []
        
        if game_id is not None:
            conditions.append("game_id = %s")
            params.append(game_id)
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"""
            SELECT 
                COUNT(*) as total_queries,
                COUNT(DISTINCT game_id) as games_queried,
                AVG(response_time_ms) as avg_response_time_ms,
                COUNT(*) FILTER (WHERE confidence = 'high') as high_confidence,
                COUNT(*) FILTER (WHERE confidence = 'medium') as medium_confidence,
                COUNT(*) FILTER (WHERE confidence = 'low') as low_confidence
            FROM ask_history
            WHERE {where_clause}
        """
        
        async with self._get_cursor() as cur:
            await cur.execute(query, tuple(params))
            row = await cur.fetchone()
            return dict(row) if row else {}


class FeedbackRepository(BaseRepository[AnswerFeedback, AnswerFeedbackCreate]):
    """Repository for answer_feedback table."""
    
    table_name = "answer_feedback"
    model_class = AnswerFeedback
    
    async def save_feedback(self, feedback: AnswerFeedbackCreate) -> AnswerFeedback:
        """Save user feedback on an answer."""
        query = """
            INSERT INTO answer_feedback (
                ask_history_id, feedback_type, selected_chunk_id, user_note
            )
            VALUES (%s, %s, %s, %s)
            RETURNING *
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (
                feedback.ask_history_id,
                feedback.feedback_type,
                feedback.selected_chunk_id,
                feedback.user_note,
            ))
            row = await cur.fetchone()
            await self.conn.commit()
            return AnswerFeedback.model_validate(row)
    
    async def get_feedback_for_history(self, history_id: int) -> list[AnswerFeedback]:
        """Get all feedback for a history entry."""
        query = """
            SELECT * FROM answer_feedback
            WHERE ask_history_id = %s
            ORDER BY created_at DESC
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (history_id,))
            rows = await cur.fetchall()
            return [AnswerFeedback.model_validate(row) for row in rows]
    
    async def get_feedback_stats(self) -> dict:
        """Get feedback statistics."""
        query = """
            SELECT 
                feedback_type,
                COUNT(*) as count
            FROM answer_feedback
            GROUP BY feedback_type
            ORDER BY count DESC
        """
        async with self._get_cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return {row["feedback_type"]: row["count"] for row in rows}

    async def get_recent_feedback(
        self,
        feedback_type: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        Get recent feedback with context.
        Returns generic dicts because we're joining with ask_history.
        """
        conditions = ["TRUE"]
        params: list[Any] = []
        
        if feedback_type:
            conditions.append("af.feedback_type = %s")
            params.append(feedback_type)
        
        params.extend([limit, offset])
        
        query = f"""
            SELECT 
                af.id,
                af.feedback_type,
                af.user_note,
                af.created_at,
                ah.question,
                ah.verdict,
                ah.game_id,
                g.name as game_name
            FROM answer_feedback af
            JOIN ask_history ah ON af.ask_history_id = ah.id
            JOIN games g ON ah.game_id = g.id
            WHERE {" AND ".join(conditions)}
            ORDER BY af.created_at DESC
            LIMIT %s OFFSET %s
        """
        
        async with self._get_cursor() as cur:
            await cur.execute(query, tuple(params))
            rows = await cur.fetchall()
            return [dict(row) for row in rows]
