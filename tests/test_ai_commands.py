from __future__ import annotations

from app.ai.router import AIToolAuditContext
from app.commands.ai import authorize_and_render_ai
from app.config import Settings
from app.core.audit import AuditStore
from app.core.security import Permission, Role


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


def make_audit(tmp_path) -> tuple[AuditStore, AIToolAuditContext]:
    return (
        AuditStore(tmp_path / "serverops.db"),
        AIToolAuditContext(user_id=3, role=Role.VIEWER, command="ask"),
    )


def test_ai_command_rejects_unknown_user_before_ai_client_runs(tmp_path) -> None:
    called = False
    audit, audit_context = make_audit(tmp_path)

    def renderer(role, settings, client, audit, audit_context) -> str:
        nonlocal called
        called = True
        return "secret"

    response = authorize_and_render_ai(
        role=Role.UNKNOWN,
        permission=Permission.VIEW_STATUS,
        usage_key="usage_ask",
        argument="server thế nào?",
        settings=make_settings(),
        client=object(),
        audit=audit,
        audit_context=audit_context,
        renderer=renderer,
    )

    assert response == "Từ chối truy cập."
    assert not called


def test_ai_command_returns_usage_before_ai_client_runs(tmp_path) -> None:
    called = False
    audit, audit_context = make_audit(tmp_path)

    def renderer(role, settings, client, audit, audit_context) -> str:
        nonlocal called
        called = True
        return "secret"

    response = authorize_and_render_ai(
        role=Role.VIEWER,
        permission=Permission.VIEW_STATUS,
        usage_key="usage_ask",
        argument=None,
        settings=make_settings(),
        client=object(),
        audit=audit,
        audit_context=audit_context,
        renderer=renderer,
    )

    assert response == "Cách dùng: /ask <câu-hỏi>"
    assert not called


def test_ai_command_allows_viewer_readonly_request(tmp_path) -> None:
    audit, audit_context = make_audit(tmp_path)

    response = authorize_and_render_ai(
        role=Role.VIEWER,
        permission=Permission.VIEW_STATUS,
        usage_key="usage_ask",
        argument="server thế nào?",
        settings=make_settings(),
        client=object(),
        audit=audit,
        audit_context=audit_context,
        renderer=lambda role, settings, client, audit, audit_context: "AI trả lời.",
    )

    assert response == "AI trả lời."
