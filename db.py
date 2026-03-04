import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "pokedex.db")

def get_conn():
    """
    Return a DB connection.

    SQLite file (local).
    Later will switch to function to Postgres without touching app routes.
    """
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    """
    Initialize the database and create the favorites table if it doesn't exist.
    """

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
                   password_hash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pokemon_name TEXT NOT NULL,
            UNIQUE(user_id, pokemon_name),
                   FOREIGN KEY(user_id) REFERENCES users(id
        )
    """)

def reset_favorites_table():
    """
    Development helper: drop and recreate favorites table.
    Use if you had the old global favorites schema.
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS favorites")
    conn.commit()
    conn.close()
    init_db()