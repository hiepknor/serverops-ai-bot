from __future__ import annotations

import pytest

from app.core.audit import AuditEvent, AuditStore
from app.db.database import database_path_from_url


def test_audit_store_records_privileged_action(tmp_path) -> None:
    store = AuditStore(tmp_path / "serverops.db")

    event_id = store.record(
        AuditEvent(
            user_id=100,
            role="owner",
            action="restart_service",
            target="nginx",
            result="success",
            command="restart",
            confirmation_status="confirmed",
        )
    )

    rows = store.list_recent()

    assert event_id == 1
    assert len(rows) == 1
    assert rows[0]["user_id"] == 100
    assert rows[0]["action"] == "restart_service"
    assert rows[0]["command"] == "restart"
    assert rows[0]["confirmation_status"] == "confirmed"


def test_database_url_supports_project_relative_sqlite_path() -> None:
    assert database_path_from_url("sqlite:///data/serverops.db").as_posix() == "data/serverops.db"


def test_database_url_rejects_non_sqlite_values() -> None:
    with pytest.raises(ValueError):
        database_path_from_url("postgresql://localhost/serverops")
