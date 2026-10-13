import asyncio
import aiosqlite

DB_NAME = "mimic.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # User profile to give the model context
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                context_profile TEXT,
                mbti TEXT
            )
        """)
        
        # Core prediction loop: Scenario -> User's Blind Answer -> Model's Prediction
        await db.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                scenario TEXT NOT NULL,
                user_actual_answer TEXT,
                model_predicted_answer TEXT,
                confidence_score REAL,
                baseline_prediction TEXT,
                mimic_correct INTEGER,
                baseline_correct INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        # Upgrade older DBs in place
        for table, col, typ in [("users", "mbti", "TEXT"), ("predictions", "baseline_prediction", "TEXT"),
                                ("predictions", "mimic_correct", "INTEGER"), ("predictions", "baseline_correct", "INTEGER")]:
            try:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
            except Exception:
                pass
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
