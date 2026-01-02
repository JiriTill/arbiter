
import asyncio
import httpx

URLS = [
    "https://cf.geekdo-images.com/JUAUWaVUzeBgzirhZNmHHw__imagepage/img/ZF-dta5ffawuKAkAt2LB-QTIv5M=/fit-in/900x600/filters:no_upscale():strip_icc()/pic4254509.jpg",
    "https://cf.geekdo-images.com/JUAUWaVUzeBgzirhZNmHHw__imagepage/img/ZF-dta5ffawuKAkAt2LB-QTIv5M=/pic4254509.jpg"
]

async def check_urls():
    async with httpx.AsyncClient() as client:
        for url in URLS:
            try:
                resp = await client.head(url)
                print(f"Status: {resp.status_code} | URL: {url}")
            except Exception as e:
                print(f"Error: {e} | URL: {url}")

if __name__ == "__main__":
    asyncio.run(check_urls())
