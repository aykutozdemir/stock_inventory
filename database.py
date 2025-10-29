import sqlite3
import os
from datetime import datetime

def init_database(db_path='inventory.db'):
    """Initialize the SQLite database with categories and stocks tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create stocks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            unit TEXT DEFAULT 'pcs',
            location TEXT,
            description TEXT,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
        )
    ''')
    
    # Create conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create chat_messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
        )
    ''')
    
    # --- Lightweight migrations: add missing timestamp columns ---
    def ensure_column(table: str, col: str, ddl: str):
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in cursor.fetchall()]
        if col not in cols:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")
            except Exception:
                pass
    # categories.updated_at
    ensure_column('categories', 'updated_at', 'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    # stocks.created_at / updated_at (usually present already)
    ensure_column('stocks', 'created_at', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ensure_column('stocks', 'updated_at', 'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    # conversations timestamps
    ensure_column('conversations', 'created_at', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ensure_column('conversations', 'updated_at', 'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    # chat_messages.updated_at
    ensure_column('chat_messages', 'updated_at', 'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {os.path.abspath(db_path)}")
    return db_path

if __name__ == '__main__':
    db_path = input("Enter the database file path (or press Enter for 'inventory.db' in current directory): ").strip()
    if not db_path:
        db_path = 'inventory.db'
    
    init_database(db_path)
    print(f"\nDatabase created successfully!")
    print(f"Location: {os.path.abspath(db_path)}")

