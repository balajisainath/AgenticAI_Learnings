import aiosqlite
import json
import os
from pathlib import Path

DB_PATH = Path(os.getenv("DB_PATH", "prompt_playground.db"))


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS prompts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS prompt_versions (
            id TEXT PRIMARY KEY,
            prompt_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            system_prompt TEXT DEFAULT '',
            user_prompt_template TEXT NOT NULL,
            model TEXT DEFAULT '',
            temperature REAL DEFAULT 0.7,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
            UNIQUE(prompt_id, version_number)
        );

        CREATE TABLE IF NOT EXISTS test_cases (
            id TEXT PRIMARY KEY,
            prompt_id TEXT NOT NULL,
            name TEXT NOT NULL,
            variables TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            version_id TEXT NOT NULL,
            test_case_id TEXT,
            input_text TEXT NOT NULL,
            variables TEXT DEFAULT '{}',
            output_text TEXT NOT NULL,
            model_used TEXT NOT NULL,
            temperature REAL NOT NULL,
            latency_ms INTEGER DEFAULT 0,
            token_count INTEGER DEFAULT 0,
            rating INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (version_id) REFERENCES prompt_versions(id) ON DELETE CASCADE,
            FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS comparisons (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            prompt_id TEXT NOT NULL,
            version_ids TEXT NOT NULL,
            test_input TEXT NOT NULL,
            variables TEXT DEFAULT '{}',
            results TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
        );
    """)
    await db.commit()
    await db.close()
