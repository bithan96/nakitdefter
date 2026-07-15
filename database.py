import sqlite3, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "finance.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    c  = db.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE, email TEXT UNIQUE,
        password TEXT NOT NULL,
        profile_pic TEXT DEFAULT 'default.png',
        is_verified INTEGER DEFAULT 0,
        verification_code TEXT, code_expiry INTEGER, reset_code TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, title TEXT NOT NULL,
        amount REAL NOT NULL, type TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS goals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, goal_name TEXT DEFAULT 'Hedefim',
        target_amount REAL, start_date TEXT, end_date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    # Mock linked bank accounts
    c.execute("""CREATE TABLE IF NOT EXISTS linked_accounts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, bank_name TEXT,
        account_no TEXT, balance REAL DEFAULT 0,
        linked_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    # Safe column additions for existing DBs
    for migration in [
        "ALTER TABLE goals ADD COLUMN goal_name TEXT DEFAULT 'Hedefim'",
        "ALTER TABLE users ADD COLUMN code_expiry INTEGER",
    ]:
        try: c.execute(migration)
        except: pass

    db.commit()
    db.close()
