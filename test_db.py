import asyncio
from api.db.database import engine
from sqlalchemy import text

async def test():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(result.fetchone())
            print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
