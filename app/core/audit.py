from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.db.database import database_path_from_url


@dataclass(frozen=True)
class AuditEvent:
    user_id: int
    role: str
    action: str
    target: str
    result: str
    confirmation_status: str = "not_required"
    error: str | None = None


class AuditStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    @classmethod
    def from_database_url(cls, database_url: str) -> AuditStore:
        return cls(database_path_from_url(database_url))

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT NOT NULL,
                    result TEXT NOT NULL,
                    confirmation_status TEXT NOT NULL,
                    error TEXT
                )
                """
            )

    def record(self, event: AuditEvent) -> int:
        self.initialize()
        created_at = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO audit_events (
                    created_at,
                    user_id,
                    role,
                    action,
                    target,
                    result,
                    confirmation_status,
                    error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    event.user_id,
                    event.role,
                    event.action,
                    event.target,
                    event.result,
                    event.confirmation_status,
                    event.error,
                ),
            )
            return int(cursor.lastrowid)

    def list_recent(self, limit: int = 20) -> list[sqlite3.Row]:
        self.initialize()
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(
                """
                SELECT *
                FROM audit_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            return list(cursor.fetchall())

