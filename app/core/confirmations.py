from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.db.database import database_path_from_url


@dataclass(frozen=True)
class PendingConfirmation:
    id: int
    user_id: int
    role: str
    action: str
    target: str
    confirmation_text: str
    status: str


class ConfirmationStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    @classmethod
    def from_database_url(cls, database_url: str) -> ConfirmationStore:
        return cls(database_path_from_url(database_url))

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS confirmations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    confirmed_at TEXT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT NOT NULL,
                    confirmation_text TEXT NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )

    def create(
        self,
        *,
        user_id: int,
        role: str,
        action: str,
        target: str,
        confirmation_text: str,
    ) -> PendingConfirmation:
        self.initialize()
        created_at = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                UPDATE confirmations
                SET status = 'superseded'
                WHERE user_id = ? AND action = ? AND target = ? AND status = 'pending'
                """,
                (user_id, action, target),
            )
            cursor = connection.execute(
                """
                INSERT INTO confirmations (
                    created_at,
                    user_id,
                    role,
                    action,
                    target,
                    confirmation_text,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """,
                (created_at, user_id, role, action, target, confirmation_text),
            )
            confirmation_id = int(cursor.lastrowid)
        return PendingConfirmation(
            id=confirmation_id,
            user_id=user_id,
            role=role,
            action=action,
            target=target,
            confirmation_text=confirmation_text,
            status="pending",
        )

    def get_pending_by_text(
        self,
        *,
        user_id: int,
        confirmation_text: str,
    ) -> PendingConfirmation | None:
        self.initialize()
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT *
                FROM confirmations
                WHERE user_id = ? AND confirmation_text = ? AND status = 'pending'
                """,
                (user_id, confirmation_text),
            ).fetchone()
        if row is None:
            return None
        return PendingConfirmation(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            role=str(row["role"]),
            action=str(row["action"]),
            target=str(row["target"]),
            confirmation_text=str(row["confirmation_text"]),
            status=str(row["status"]),
        )

    def mark_confirmed(self, confirmation_id: int) -> None:
        self.initialize()
        confirmed_at = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                UPDATE confirmations
                SET status = 'confirmed', confirmed_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (confirmed_at, confirmation_id),
            )


def confirmation_text_for(action: str, target: str) -> str:
    return f"CONFIRM {action.upper().replace('_', ' ')} {target.upper()}"
