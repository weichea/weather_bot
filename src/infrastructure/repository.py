"""Repository wrappers over the raw SQLite helpers in `db.py`.

These functions present a slightly higher-level persistence API suitable for the
`src/interface` layer to consume. They map raw rows into typed structures.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

from src.domain.weather import Location
from src.infrastructure import db


@dataclass
class UserRecord:
    telegram_id: int
    chat_id: int
    # `locations` contains all saved coordinates; `location` is a convenience
    # property representing the most-recent (primary) saved location for
    # backward compatibility with older code paths.
    locations: List[Location]
    location: Optional[Location]
    daily_blast_enabled: bool
    daily_blast_time: Optional[str]
    last_sent: Optional[str]


def _row_to_user(
    record: dict[str, Any], locations_rows: List[dict[str, Any]]
) -> UserRecord:
    # Convert location rows to `Location` objects
    locations: List[Location] = []
    for lr in locations_rows:
        try:
            loc = Location(
                name=lr.get("location_name") or "",
                latitude=float(lr["latitude"]),
                longitude=float(lr["longitude"]),
            )
            locations.append(loc)
        except Exception:
            continue

    primary = locations[0] if locations else None

    return UserRecord(
        telegram_id=int(record["telegram_id"]),
        chat_id=int(record["chat_id"]),
        locations=locations,
        location=primary,
        daily_blast_enabled=bool(record.get("daily_blast_enabled")),
        daily_blast_time=record.get("daily_blast_time"),
        last_sent=record.get("last_sent"),
    )


def save_user_location(
    telegram_id: int,
    chat_id: int,
    latitude: Optional[float],
    longitude: Optional[float],
    location_name: Optional[str] = None,
    db_path: str | None = None,
) -> None:
    """Add or update a user's location record.

    If latitude/longitude are provided we persist a new saved location in the
    `locations` table. If not, fall back to updating the users table.
    """
    if db_path is None:
        db_path = db.DEFAULT_DB_PATH
    # Persist as an appended saved location
    if latitude is None or longitude is None:
        # Fallback to previous behavior: update user row if no coords provided
        db.add_or_update_user(
            telegram_id=telegram_id,
            chat_id=chat_id,
            latitude=None,
            longitude=None,
            location_name=location_name,
            db_path=db_path,
        )
        return

    db.add_location_for_user(
        telegram_id=telegram_id,
        chat_id=chat_id,
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        db_path=db_path,
    )


def get_active_users(db_path: str | None = None) -> List[UserRecord]:
    if db_path is None:
        db_path = db.DEFAULT_DB_PATH
    rows = db.get_active_users(db_path=db_path)
    users: List[UserRecord] = []
    for r in rows:
        locations = db.get_locations_for_user(int(r["telegram_id"]), db_path=db_path)
        users.append(_row_to_user(r, locations))
    return users


def get_user(telegram_id: int, db_path: str | None = None) -> Optional[UserRecord]:
    if db_path is None:
        db_path = db.DEFAULT_DB_PATH
    row = db.get_user_by_telegram_id(telegram_id, db_path=db_path)
    if not row:
        return None
    locations = db.get_locations_for_user(telegram_id, db_path=db_path)
    return _row_to_user(row, locations)


def disable_user_record(telegram_id: int, db_path: str | None = None) -> None:
    if db_path is None:
        db_path = db.DEFAULT_DB_PATH
    db.disable_user(telegram_id, db_path=db_path)


def update_last_sent(
    telegram_id: int, when: Optional[datetime] = None, db_path: str | None = None
) -> None:
    if db_path is None:
        db_path = db.DEFAULT_DB_PATH
    db.update_last_sent(telegram_id, when=when, db_path=db_path)
