import asyncio
from api.db.database import engine
from sqlalchemy import text

async def fix_alembic():
    try:
        async with engine.connect() as conn:
            # Check current version
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            print(f"Current alembic version: {row}")
            
            # Update to my new initial version or just delete it so stamp works
            await conn.execute(text("DELETE FROM alembic_version"))
            await conn.commit()
            print("Cleared alembic_version table.")
    except Exception as e:
        print(f"Failed to fix alembic: {e}")

if __name__ == "__main__":
    asyncio.run(fix_alembic())
