
import asyncio
import os
from dotenv import load_dotenv
from app.db.connection import get_async_connection

load_dotenv()

async def check_games():
    async with get_async_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT name, cover_image_url FROM games")
            rows = await cur.fetchall()
            for row in rows:
                print(f"Game: {row[0]}")
                print(f"URL: {row[1]}")
                print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_games())
