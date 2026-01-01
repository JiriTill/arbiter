"""
Games repository for game and expansion management.
"""

from psycopg.rows import dict_row

from app.db.models import Game, GameCreate, Expansion, ExpansionCreate, GameWithSources
from app.db.repositories.base import BaseRepository


class GamesRepository(BaseRepository[Game, GameCreate]):
    """Repository for games table."""
    
    table_name = "games"
    model_class = Game
    
    # ========================================================================
    # Async Methods
    # ========================================================================
    
    async def list_games(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
    ) -> list[Game]:
        """
        List games with optional search.
        
        Args:
            limit: Maximum number of games to return
            offset: Number of games to skip
            search: Optional search term for name
            
        Returns:
            List of Game objects
        """
        if search:
            query = """
                SELECT * FROM games
                WHERE name ILIKE %s OR slug ILIKE %s
                ORDER BY name ASC
                LIMIT %s OFFSET %s
            """
            search_pattern = f"%{search}%"
            params = (search_pattern, search_pattern, limit, offset)
        else:
            query = """
                SELECT * FROM games
                ORDER BY name ASC
                LIMIT %s OFFSET %s
            """
            params = (limit, offset)
        
        async with self._get_cursor() as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return [Game.model_validate(row) for row in rows]
    
    async def get_game(self, game_id: int) -> Game | None:
        """Get a single game by ID."""
        return await self.get_by_id_async(game_id)
    
    async def get_game_by_slug(self, slug: str) -> Game | None:
        """Get a game by its slug."""
        query = "SELECT * FROM games WHERE slug = %s"
        async with self._get_cursor() as cur:
            await cur.execute(query, (slug,))
            row = await cur.fetchone()
            if row:
                return Game.model_validate(row)
            return None
    
    async def create_game(self, game: GameCreate) -> Game:
        """
        Create a new game.
        
        Args:
            game: Game data to create
            
        Returns:
            Created Game with ID
        """
        query = """
            INSERT INTO games (name, slug, bgg_id, cover_image_url)
            VALUES (%s, %s, %s, %s)
            RETURNING *
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (
                game.name,
                game.slug,
                game.bgg_id,
                game.cover_image_url,
            ))
            row = await cur.fetchone()
            await self.conn.commit()
            return Game.model_validate(row)
    
    async def update_game(self, game_id: int, game: GameCreate) -> Game | None:
        """Update an existing game."""
        query = """
            UPDATE games
            SET name = %s, slug = %s, bgg_id = %s, cover_image_url = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (
                game.name,
                game.slug,
                game.bgg_id,
                game.cover_image_url,
                game_id,
            ))
            row = await cur.fetchone()
            await self.conn.commit()
            if row:
                return Game.model_validate(row)
            return None
    
    async def get_game_with_sources(self, game_id: int) -> GameWithSources | None:
        """Get a game with all its sources and expansions."""
        game = await self.get_game(game_id)
        if not game:
            return None
        
        # Get expansions
        expansions_query = "SELECT * FROM expansions WHERE game_id = %s ORDER BY release_date"
        async with self._get_cursor() as cur:
            await cur.execute(expansions_query, (game_id,))
            expansion_rows = await cur.fetchall()
        
        # Get sources
        sources_query = "SELECT * FROM game_sources WHERE game_id = %s ORDER BY edition"
        async with self._get_cursor() as cur:
            await cur.execute(sources_query, (game_id,))
            source_rows = await cur.fetchall()
        
        from app.db.models import GameSource
        return GameWithSources(
            **game.model_dump(),
            expansions=[Expansion.model_validate(r) for r in expansion_rows],
            sources=[GameSource.model_validate(r) for r in source_rows],
        )
    
    async def list_games_with_sources(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
    ) -> list[GameWithSources]:
        """List games with their sources populated."""
        games = await self.list_games(limit, offset, search)
        if not games:
            return []
            
        game_ids = [g.id for g in games]
        
        # Get sources
        query = "SELECT * FROM game_sources WHERE game_id = ANY(%s)"
        async with self._get_cursor() as cur:
            await cur.execute(query, (game_ids,))
            rows = await cur.fetchall()
            
        from app.db.models import GameSource
        sources = [GameSource.model_validate(r) for r in rows]
        
        # Map
        sources_map = {gid: [] for gid in game_ids}
        for s in sources:
            if s.game_id in sources_map:
                sources_map[s.game_id].append(s)
                
        # Build result
        return [
            GameWithSources(
                **g.model_dump(),
                sources=sources_map[g.id],
                expansions=[] # Expansions not populated for list view
            )
            for g in games
        ]

    # ========================================================================
    # Sync Methods (for background jobs)
    # ========================================================================
    
    def list_games_sync(self, limit: int = 100, offset: int = 0) -> list[Game]:
        """List games (sync version)."""
        return self.list_sync(limit, offset, order_by="name")
    
    def get_game_sync(self, game_id: int) -> Game | None:
        """Get a game by ID (sync version)."""
        return self.get_by_id_sync(game_id)
    
    def create_game_sync(self, game: GameCreate) -> Game:
        """Create a game (sync version)."""
        query = """
            INSERT INTO games (name, slug, bgg_id, cover_image_url)
            VALUES (%s, %s, %s, %s)
            RETURNING *
        """
        with self._get_cursor() as cur:
            cur.execute(query, (
                game.name,
                game.slug,
                game.bgg_id,
                game.cover_image_url,
            ))
            row = cur.fetchone()
            self.conn.commit()
            return Game.model_validate(row)


class ExpansionsRepository(BaseRepository[Expansion, ExpansionCreate]):
    """Repository for expansions table."""
    
    table_name = "expansions"
    model_class = Expansion
    
    async def list_by_game(self, game_id: int) -> list[Expansion]:
        """List all expansions for a game."""
        query = """
            SELECT * FROM expansions
            WHERE game_id = %s
            ORDER BY release_date ASC NULLS LAST
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (game_id,))
            rows = await cur.fetchall()
            return [Expansion.model_validate(row) for row in rows]
    
    async def create_expansion(self, expansion: ExpansionCreate) -> Expansion:
        """Create a new expansion."""
        query = """
            INSERT INTO expansions (game_id, name, code, bgg_id, release_date)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (
                expansion.game_id,
                expansion.name,
                expansion.code,
                expansion.bgg_id,
                expansion.release_date,
            ))
            row = await cur.fetchone()
            await self.conn.commit()
            return Expansion.model_validate(row)
