
import asyncio
import sys
import os

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.db.connection import get_async_connection

async def inspect_urls():
    print("Inpecting URLs...")
    try:
        async with get_async_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT name, cover_image_url FROM games")
                rows = await cur.fetchall()
                print(f"Found {len(rows)} games.")
                for row in rows:
                    print(f"Game: {row['name']}")
                    print(f"URL:  {row['cover_image_url']}")
                    print("-" * 20)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(inspect_urls())
