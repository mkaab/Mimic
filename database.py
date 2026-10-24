import asyncio
import aiosqlite
import json
from datetime import datetime

DB_NAME = "strata.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS discovery_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id TEXT NOT NULL,
                scenario_title TEXT NOT NULL,
                target_workflow TEXT NOT NULL,
                blueprint_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    print(f"Database '{DB_NAME}' initialized successfully.")

async def get_db():
    db = await aiosqlite.connect(DB_NAME)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(init_db())
