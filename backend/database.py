# backend/database.py
import sqlite3
import hashlib
from datetime import datetime

DB_PATH = "aspiralytica.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            text        TEXT NOT NULL,
            sentiment   TEXT NOT NULL,
            intent      TEXT NOT NULL,
            priority    TEXT NOT NULL,
            is_sarcasm  INTEGER DEFAULT 0,
            status      TEXT DEFAULT 'menunggu',
            created_at  TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            email      TEXT NOT NULL UNIQUE,
            password   TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ── Reports ──────────────────────────────────────────────────────

def insert_report(text, sentiment, intent, priority, is_sarcasm=False):
    conn = get_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%d %b %Y • %H:%M")
    cursor.execute("""
        INSERT INTO reports (text, sentiment, intent, priority, is_sarcasm, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (text, sentiment, intent, priority, int(is_sarcasm), created_at))
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id


def _row_to_dict(row) -> dict:
    """Konversi sqlite3.Row ke dict dengan is_sarcasm sebagai bool."""
    d = dict(row)
    d["is_sarcasm"] = bool(d.get("is_sarcasm", 0))
    return d


def get_all_reports():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_report_by_id(report_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def delete_report(report_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()


def update_report_status(report_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reports SET status = ? WHERE id = ?",
        (status, report_id)
    )
    conn.commit()
    conn.close()


# ── Users ─────────────────────────────────────────────────────────

def create_user(name, email, password):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%d %b %Y • %H:%M")
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)",
            (name, email, hashed, created_at)
        )
        user_id = cursor.lastrowid
        conn.commit()
        return {"id": user_id, "name": name, "email": email}
    except Exception:
        raise ValueError("Email sudah terdaftar")
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None