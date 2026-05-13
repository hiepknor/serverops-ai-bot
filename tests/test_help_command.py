from __future__ import annotations

from app.commands.help import render_help
from app.config import Settings
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


def test_start_help_denies_unknown_user_with_response() -> None:
    assert render_help(Role.UNKNOWN, make_settings()) == "Từ chối truy cập."


def test_start_help_lists_viewer_commands() -> None:
    response = render_help(Role.VIEWER, make_settings())

    assert "ServerOps AI Bot" in response
    assert "/status" in response
    assert "/ask <câu-hỏi>" in response
    assert "/restart" not in response
    assert "Docker tools đang tắt." in response


def test_start_help_lists_owner_commands_and_docker_when_enabled() -> None:
    response = render_help(Role.OWNER, make_settings(enable_docker_tools=True))

    assert "/restart <service>" in response
    assert "/audit [limit]" in response
    assert "/docker_logs <container>" in response


def test_start_help_uses_english_when_configured() -> None:
    response = render_help(Role.ADMIN, make_settings(bot_language="en"))

    assert "Read-only:" in response
    assert "Actions:" in response
    assert "Docker tools are disabled." in response
