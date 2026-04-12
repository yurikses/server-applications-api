# database.py
import sqlite3

DB_NAME = "task.db"

def get_db_connection():
    """Создает и возвращает подключение к базе данных."""
    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Создает таблицу users, если она еще не существует."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
  
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed INTEGER NOT NULL DEFAULT 0
            )
        """)
    
    conn.commit()
    conn.close()
