#!/usr/bin/env python3
"""
Seed script to populate the database with initial games and sources.

Usage:
    python -m scripts.seed_sources

This script is idempotent - running it multiple times will not create duplicates.
Games are matched by slug, sources are matched by (game_id, edition, source_type).
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.connection import get_sync_connection
from app.db.models import GameCreate, GameSourceCreate


def load_seed_data() -> dict:
    """Load seed data from JSON file."""
    seed_file = Path(__file__).parent.parent / "seed_data.json"
    
    if not seed_file.exists():
        print(f"✗ Seed file not found: {seed_file}")
        sys.exit(1)
    
    with open(seed_file, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_games_and_sources():
    """
    Seed the database with games and sources from seed_data.json.
    
    This function is idempotent - it uses upsert logic:
    - Games are matched by slug
    - Sources are matched by (game_id, edition, source_type)
    """
    data = load_seed_data()
    games = data.get("games", [])
    
    if not games:
        print("⚠ No games found in seed data")
        return
    
    games_inserted = 0
    games_updated = 0
    sources_inserted = 0
    sources_updated = 0
    
    try:
        with get_sync_connection() as conn:
            with conn.cursor() as cur:
                for game_data in games:
                    # Check if game exists by slug
                    cur.execute(
                        "SELECT id FROM games WHERE slug = %s",
                        (game_data["slug"],)
                    )
                    existing_game = cur.fetchone()
                    
                    if existing_game:
                        # Update existing game
                        game_id = existing_game[0]
                        cur.execute(
                            """
                            UPDATE games 
                            SET name = %s, bgg_id = %s, cover_image_url = %s, updated_at = NOW()
                            WHERE id = %s
                            """,
                            (
                                game_data["name"],
                                game_data.get("bgg_id"),
                                game_data.get("cover_image_url"),
                                game_id,
                            )
                        )
                        games_updated += 1
                        print(f"  ↻ Updated game: {game_data['name']}")
                    else:
                        # Insert new game
                        cur.execute(
                            """
                            INSERT INTO games (name, slug, bgg_id, cover_image_url)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id
                            """,
                            (
                                game_data["name"],
                                game_data["slug"],
                                game_data.get("bgg_id"),
                                game_data.get("cover_image_url"),
                            )
                        )
                        result = cur.fetchone()
                        game_id = result[0]
                        games_inserted += 1
                        print(f"  + Inserted game: {game_data['name']}")
                    
                    # Process sources for this game
                    sources = game_data.get("sources", [])
                    for source_data in sources:
                        # Check if source exists
                        cur.execute(
                            """
                            SELECT id FROM game_sources 
                            WHERE game_id = %s AND edition = %s AND source_type = %s
                            """,
                            (game_id, source_data["edition"], source_data["source_type"])
                        )
                        existing_source = cur.fetchone()
                        
                        if existing_source:
                            # Update existing source
                            cur.execute(
                                """
                                UPDATE game_sources
                                SET source_url = %s, is_official = %s, verified_by = %s, updated_at = NOW()
                                WHERE id = %s
                                """,
                                (
                                    source_data.get("source_url"),
                                    source_data.get("is_official", True),
                                    source_data.get("verified_by"),
                                    existing_source[0],
                                )
                            )
                            sources_updated += 1
                        else:
                            # Insert new source
                            cur.execute(
                                """
                                INSERT INTO game_sources (
                                    game_id, edition, source_type, source_url, 
                                    is_official, verified_by
                                )
                                VALUES (%s, %s, %s, %s, %s, %s)
                                """,
                                (
                                    game_id,
                                    source_data["edition"],
                                    source_data["source_type"],
                                    source_data.get("source_url"),
                                    source_data.get("is_official", True),
                                    source_data.get("verified_by"),
                                )
                            )
                            sources_inserted += 1
                
                # Commit all changes
                conn.commit()
        
        # Print summary
        print()
        print("=" * 50)
        print("Seed Summary")
        print("=" * 50)
        print(f"  Games inserted:   {games_inserted}")
        print(f"  Games updated:    {games_updated}")
        print(f"  Sources inserted: {sources_inserted}")
        print(f"  Sources updated:  {sources_updated}")
        print()
        total_sources = sources_inserted + sources_updated
        total_games = games_inserted + games_updated
        print(f"✓ Seeded {total_games} games with {total_sources} sources")
        
    except Exception as e:
        print(f"✗ Error during seeding: {e}")
        sys.exit(1)


def verify_seed():
    """Verify the seed was successful by querying the database."""
    print()
    print("Verifying seed...")
    
    try:
        with get_sync_connection() as conn:
            with conn.cursor() as cur:
                # Count games
                cur.execute("SELECT COUNT(*) FROM games")
                game_count = cur.fetchone()[0]
                
                # Count sources
                cur.execute("SELECT COUNT(*) FROM game_sources")
                source_count = cur.fetchone()[0]
                
                # List games
                cur.execute("SELECT name, slug FROM games ORDER BY name")
                games = cur.fetchall()
                
                print(f"  Total games in database:   {game_count}")
                print(f"  Total sources in database: {source_count}")
                print()
                print("  Games:")
                for name, slug in games:
                    print(f"    - {name} ({slug})")
                
    except Exception as e:
        print(f"✗ Verification error: {e}")


def main():
    """Main entry point."""
    print()
    print("=" * 50)
    print("The Arbiter - Database Seeder")
    print("=" * 50)
    print()
    
    # Load and display seed data info
    data = load_seed_data()
    games = data.get("games", [])
    total_sources = sum(len(g.get("sources", [])) for g in games)
    
    print(f"Found {len(games)} games with {total_sources} sources in seed_data.json")
    print()
    print("Seeding database...")
    print()
    
    # Run seed
    seed_games_and_sources()
    
    # Verify
    verify_seed()


if __name__ == "__main__":
    main()
