
import sqlite3

DB_NAME = "inspector.db"


def init_db():
    with sqlite3.connect(DB_NAME) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT
            )
        """)


def register_user(telegram_id, username):
    with sqlite3.connect(DB_NAME) as db:
        db.execute("""
            INSERT OR REPLACE INTO users
            (telegram_id, username)
            VALUES (?, ?)
        """, (telegram_id, username))


def get_user(telegram_id):
    with sqlite3.connect(DB_NAME) as db:
        return db.execute("""
            SELECT telegram_id, username
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,)).fetchone()

