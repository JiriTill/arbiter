
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.connection import get_async_connection

async def fix_image_urls():
    print("🔧 Connecting to database...")
    async with get_async_connection() as conn:
        async with conn.cursor() as cur:
            # 1. Get all games with "filters:" in the URL
            await cur.execute("SELECT id, name, cover_image_url FROM games WHERE cover_image_url LIKE '%filters:%'")
            rows = await cur.fetchall()
            
            print(f"👉 Found {len(rows)} games with broken URLs")
            
            count = 0
            for row in rows:
                game_id, name, url = row
                # Convert: .../fit-in/900x600/filters:no_upscale():strip_icc()/pic123.jpg
                # To: .../pic123.jpg
                
                if "/fit-in" in url and "/pic" in url:
                    # Split by /fit-in and take the first part
                    base_part = url.split("/fit-in")[0]
                    # Split by the last slash to get the filename
                    filename = url.split("/")[-1]
                    
                    new_url = f"{base_part}/{filename}"
                    
                    print(f"  - Fixing {name}:")
                    print(f"    OLD: {url}")
                    print(f"    NEW: {new_url}")
                    
                    await cur.execute(
                        "UPDATE games SET cover_image_url = %s WHERE id = %s",
                        (new_url, game_id)
                    )
                    count += 1
            
            await conn.commit()
            print(f"✅ Fixed {count} game images!")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(fix_image_urls())
