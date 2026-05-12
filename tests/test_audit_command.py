from __future__ import annotations

from app.commands.audit import render_audit
from app.config import Settings
from app.core.audit import AuditEvent, AuditStore
from app.core.security import Role


def make_settings(**overrides) -> Settings:
    data = {
        "telegram_bot_token": "123456:telegram-token-value",
        "openai_api_key": "sk-testtokenvalue",
        "owner_ids": [1],
        "admin_ids": [2],
        "viewer_ids": [3],
    }
    data.update(overrides)
    return Settings(**data)


def test_owner_can_view_recent_audit_rows(tmp_path) -> None:
    audit = AuditStore(tmp_path / "serverops.db")
    audit.record(
        AuditEvent(
            user_id=3,
            role="viewer",
            command="ask",
            action="ai_tool.read_log",
            target="app",
            result="success",
        )
    )

    response = render_audit(
        user_id=1,
        role=Role.OWNER,
        args=[],
        settings=make_settings(),
        audit=audit,
    )

    assert response.startswith("Audit gần đây\n")
    assert "viewer | ask | ai_tool.read_log | app | success" in response


def test_non_owner_is_denied_and_audited(tmp_path) -> None:
    audit = AuditStore(tmp_path / "serverops.db")

    response = render_audit(
        user_id=3,
        role=Role.VIEWER,
        args=[],
        settings=make_settings(),
        audit=audit,
    )

    rows = audit.list_recent()
    assert response == "Từ chối truy cập."
    assert rows[0]["user_id"] == 3
    assert rows[0]["role"] == "viewer"
    assert rows[0]["action"] == "view_audit"
    assert rows[0]["target"] == "audit"
    assert rows[0]["result"] == "denied"


def test_audit_limit_must_be_bounded_integer(tmp_path) -> None:
    audit = AuditStore(tmp_path / "serverops.db")
    settings = make_settings()

    assert (
        render_audit(
            user_id=1,
            role=Role.OWNER,
            args=["abc"],
            settings=settings,
            audit=audit,
        )
        == "Cách dùng: /audit [1-50]"
    )
    assert (
        render_audit(
            user_id=1,
            role=Role.OWNER,
            args=["51"],
            settings=settings,
            audit=audit,
        )
        == "Cách dùng: /audit [1-50]"
    )


def test_audit_output_redacts_and_truncates_error_text(tmp_path) -> None:
    audit = AuditStore(tmp_path / "serverops.db")
    audit.record(
        AuditEvent(
            user_id=2,
            role="admin",
            action="restart_service",
            target="nginx",
            result="failed",
            confirmation_status="confirmed",
            error="token=super-secret-value " + ("x" * 200),
        )
    )

    response = render_audit(
        user_id=1,
        role=Role.OWNER,
        args=["1"],
        settings=make_settings(),
        audit=audit,
    )

    assert "super-secret-value" not in response
    assert "token=[REDACTED]" in response
    assert len(response.splitlines()[1]) < 220


def test_empty_audit_output_is_compact(tmp_path) -> None:
    response = render_audit(
        user_id=1,
        role=Role.OWNER,
        args=[],
        settings=make_settings(),
        audit=AuditStore(tmp_path / "serverops.db"),
    )

    assert response == "Audit gần đây: không có"
