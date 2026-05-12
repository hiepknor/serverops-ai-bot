from __future__ import annotations

from app.config import Settings
from app.core.security import Permission, Role, has_permission, redact_secrets, resolve_role


def make_settings() -> Settings:
    return Settings(
        telegram_bot_token="123456:telegram-token-value",
        openai_api_key="sk-testtokenvalue",
        owner_ids=[1],
        admin_ids=[2],
        viewer_ids=[3],
    )


def test_resolve_role_from_configured_telegram_ids() -> None:
    settings = make_settings()

    assert resolve_role(1, settings) == Role.OWNER
    assert resolve_role(2, settings) == Role.ADMIN
    assert resolve_role(3, settings) == Role.VIEWER
    assert resolve_role(4, settings) == Role.UNKNOWN


def test_role_permissions_are_least_privilege() -> None:
    assert has_permission(Role.OWNER, Permission.DEPLOY)
    assert has_permission(Role.ADMIN, Permission.RESTART_SERVICE)
    assert not has_permission(Role.ADMIN, Permission.DEPLOY)
    assert has_permission(Role.VIEWER, Permission.VIEW_LOGS)
    assert not has_permission(Role.VIEWER, Permission.RESTART_SERVICE)
    assert not has_permission(Role.UNKNOWN, Permission.VIEW_STATUS)


def test_redact_secrets_removes_known_and_pattern_tokens() -> None:
    text = "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz token=123456:abcdefghijklmnopqrstuvwxyz"

    redacted = redact_secrets(text, known_secrets=["abcdefghijklmnopqrstuvwxyz"])

    assert "abcdefghijklmnopqrstuvwxyz" not in redacted
    assert "123456:" not in redacted
    assert "[REDACTED]" in redacted

