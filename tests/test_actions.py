from __future__ import annotations

import sqlite3

from app.commands import actions
from app.commands.actions import execute_confirmed_action, request_confirmation
from app.config import Settings
from app.core.audit import AuditStore
from app.core.confirmations import ConfirmationStore, confirmation_text_for
from app.core.security import Permission, Role


def make_settings(**overrides) -> Settings:
    data = {
        "telegram_bot_token": "123456:telegram-token-value",
        "openai_api_key": "sk-testtokenvalue",
        "owner_ids": [1],
        "admin_ids": [2],
        "viewer_ids": [3],
        "allowed_services": ["nginx"],
        "allowed_containers": ["api"],
    }
    data.update(overrides)
    return Settings(**data)


def test_request_confirmation_creates_pending_record_and_audit_event(tmp_path) -> None:
    database_path = tmp_path / "serverops.db"
    confirmations = ConfirmationStore(database_path)
    audit = AuditStore(database_path)

    response = request_confirmation(
        user_id=1,
        role=Role.OWNER,
        permission=Permission.RESTART_SERVICE,
        action="restart_service",
        target="nginx",
        settings=make_settings(),
        confirmations=confirmations,
        audit=audit,
    )

    text = confirmation_text_for("restart_service", "nginx")
    pending = confirmations.get_pending_by_text(user_id=1, confirmation_text=text)
    audit_rows = audit.list_recent()

    assert text in response
    assert "Cần xác nhận trước khi thực thi." in response
    assert "Vui lòng trả lời chính xác:" in response
    assert pending is not None
    assert audit_rows[0]["result"] == "pending_confirmation"
    assert audit_rows[0]["confirmation_status"] == "pending"


def test_request_confirmation_denies_viewer_before_creating_confirmation(tmp_path) -> None:
    database_path = tmp_path / "serverops.db"
    confirmations = ConfirmationStore(database_path)
    audit = AuditStore(database_path)

    response = request_confirmation(
        user_id=3,
        role=Role.VIEWER,
        permission=Permission.RESTART_SERVICE,
        action="restart_service",
        target="nginx",
        settings=make_settings(),
        confirmations=confirmations,
        audit=audit,
    )

    text = confirmation_text_for("restart_service", "nginx")
    assert response == "Từ chối truy cập."
    assert confirmations.get_pending_by_text(user_id=3, confirmation_text=text) is None
    assert audit.list_recent()[0]["result"] == "denied"


def test_request_confirmation_denies_unallowlisted_target(tmp_path) -> None:
    database_path = tmp_path / "serverops.db"
    confirmations = ConfirmationStore(database_path)
    audit = AuditStore(database_path)

    response = request_confirmation(
        user_id=1,
        role=Role.OWNER,
        permission=Permission.RESTART_CONTAINER,
        action="restart_container",
        target="db",
        settings=make_settings(),
        confirmations=confirmations,
        audit=audit,
    )

    assert response == "Từ chối truy cập. 'db' is not allowlisted"
    assert audit.list_recent()[0]["error"] == "'db' is not allowlisted"


def test_confirmation_table_is_created_in_same_database_as_audit(tmp_path) -> None:
    database_path = tmp_path / "serverops.db"
    ConfirmationStore(database_path).initialize()
    AuditStore(database_path).initialize()

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert {"audit_events", "confirmations"}.issubset(tables)


def test_execute_confirmed_restart_service_calls_service_tool(monkeypatch) -> None:
    calls = []

    def fake_restart_service(target, *, allowed_services):
        calls.append((target, allowed_services))
        return f"Service restarted: {target}"

    monkeypatch.setattr(actions, "restart_service", fake_restart_service)

    result = execute_confirmed_action("restart_service", "nginx", make_settings())

    assert result.ok is True
    assert result.message == "Đã khởi động lại service: nginx"
    assert calls == [("nginx", ["nginx"])]


def test_execute_confirmed_restart_container_calls_docker_tool(monkeypatch) -> None:
    calls = []

    def fake_restart_container(target, *, allowed_names):
        calls.append((target, allowed_names))
        return f"Container restarted: {target}"

    monkeypatch.setattr(actions, "restart_container", fake_restart_container)

    result = execute_confirmed_action("restart_container", "api", make_settings())

    assert result.ok is True
    assert result.message == "Đã khởi động lại container: api"
    assert calls == [("api", ["api"])]
