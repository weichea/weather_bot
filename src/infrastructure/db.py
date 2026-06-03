"""SQLite persistence layer for user records and preferences.

This module lives in `src/infrastructure` and implements the storage contract
that the `src/domain` layer relies on. It provides simple CRUD helpers for
user registration, location storage, and scheduling metadata.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = "data/weather_bot.db"


def set_default_db_path(db_path: str) -> None:
    global DEFAULT_DB_PATH
    DEFAULT_DB_PATH = db_path


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | None = None) -> None:
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    conn = get_connection(db_path)
    try:
        _create_tables(conn)
        conn.commit()
    finally:
        conn.close()


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            chat_id INTEGER NOT NULL,
            latitude REAL,
            longitude REAL,
            location_name TEXT,
            daily_blast_enabled INTEGER DEFAULT 1,
            daily_blast_time TEXT,
            last_sent TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    # Table to store multiple locations per user. Each user may save many
    # coordinates; the scheduler and UI will prefer the most-recent one when
    # a single location is required for backward compatibility.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            location_name TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )


def add_or_update_user(
    telegram_id: int,
    chat_id: int,
    latitude: Optional[float],
    longitude: Optional[float],
    location_name: Optional[str],
    daily_blast_enabled: bool = True,
    daily_blast_time: Optional[str] = None,
    db_path: str | None = None,
) -> None:
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO users (
                telegram_id, chat_id, latitude, longitude, location_name,
                daily_blast_enabled, daily_blast_time, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(telegram_id) DO UPDATE SET
                chat_id=excluded.chat_id,
                latitude=excluded.latitude,
                longitude=excluded.longitude,
                location_name=excluded.location_name,
                daily_blast_enabled=excluded.daily_blast_enabled,
                daily_blast_time=excluded.daily_blast_time,
                updated_at=datetime('now')
            """,
            (
                telegram_id,
                chat_id,
                latitude,
                longitude,
                location_name,
                1 if daily_blast_enabled else 0,
                daily_blast_time,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def add_location_for_user(
    telegram_id: int,
    chat_id: int,
    latitude: float,
    longitude: float,
    location_name: str | None = None,
    db_path: str | None = None,
) -> None:
    """Insert a new saved location for a user and ensure the user row exists.

    This function appends to the `locations` table. For backward compatibility
    the user's `chat_id` is created/updated in the `users` table so older APIs
    that read the users table still function.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    conn = get_connection(db_path)
    try:
        # Ensure a user row exists (or update chat_id)
        conn.execute(
            """
            INSERT INTO users (telegram_id, chat_id, updated_at, created_at)
            VALUES (?, ?, datetime('now'), datetime('now'))
            ON CONFLICT(telegram_id) DO UPDATE SET
                chat_id=excluded.chat_id,
                updated_at=datetime('now')
            """,
            (telegram_id, chat_id),
        )

        conn.execute(
            """
            INSERT INTO locations (telegram_id, chat_id, latitude, longitude,
            location_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (telegram_id, chat_id, latitude, longitude, location_name),
        )
        conn.commit()
    finally:
        conn.close()


def get_locations_for_user(
    telegram_id: int, db_path: str | None = None
) -> list[dict[str, Any]]:
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT * FROM locations WHERE telegram_id = ? ORDER BY id DESC",
            (telegram_id,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def migrate_existing_locations(db_path: str | None = None) -> None:
    """Migrate any existing latitude/longitude stored on `users` into
    the `locations` table. This is best-effort and safe to run multiple times.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            (
                "SELECT telegram_id, chat_id, latitude, longitude, location_name "
                "FROM users WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
            )
        )
        rows = cur.fetchall()
        for r in rows:
            conn.execute(
                (
                    "INSERT INTO locations (telegram_id, chat_id, latitude, "
                    "longitude, location_name) VALUES (?, ?, ?, ?, ?)"
                ),
                (
                    r["telegram_id"],
                    r["chat_id"],
                    r["latitude"],
                    r["longitude"],
                    r["location_name"],
                ),
            )
        conn.commit()
    finally:
        conn.close()


def get_user_by_telegram_id(
    telegram_id: int, db_path: str | None = None
) -> Optional[Dict[str, Any]]:
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ? LIMIT 1", (telegram_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_active_users(db_path: str | None = None) -> List[Dict[str, Any]]:
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT * FROM users WHERE daily_blast_enabled = 1 ORDER BY id"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def disable_user(telegram_id: int, db_path: str | None = None) -> None:
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE users SET daily_blast_enabled = 0, updated_at = datetime('now') "
            "WHERE telegram_id = ?",
            (telegram_id,),
        )
        conn.commit()
    finally:
        conn.close()


def update_last_sent(
    telegram_id: int, when: Optional[datetime] = None, db_path: str | None = None
) -> None:
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    when_str = when.isoformat() if when else datetime.utcnow().isoformat()
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE users SET last_sent = ?, updated_at = datetime('now') "
            "WHERE telegram_id = ?",
            (when_str, telegram_id),
        )
        conn.commit()
    finally:
        conn.close()
