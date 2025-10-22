# src/data/database.py
import sqlite3
from pathlib import Path

def init_db(db_path: str):
    """Crea la base y la tabla si no existen."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tweets (
        id TEXT PRIMARY KEY,
        author TEXT,
        text TEXT,
        created_at TEXT,
        lang TEXT,
        source TEXT
    )
    """)
    conn.commit()
    conn.close()

def insert_tweets(db_path: str, tweets: list[dict]):
    """Inserta tuits nuevos en la base."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for t in tweets:
        cursor.executemany(
    "INSERT OR IGNORE INTO tweets (id, author, text, created_at, lang, source) VALUES (?, ?, ?, ?, ?, ?)",
    [(t["id"], t["author"], t["text"], t["created_at"], t["lang"], t["source"]) for t in tweets]
)
    conn.commit()
    conn.close()
