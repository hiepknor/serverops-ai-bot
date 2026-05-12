from __future__ import annotations

from app.bot import build_application
from app.config import Settings


def test_build_application_registers_readonly_commands() -> None:
    settings = Settings(
        telegram_bot_token="123456:telegram-token-value",
        openai_api_key="sk-testtokenvalue",
        owner_ids=[1],
    )

    application = build_application(settings)
    registered = {
        command
        for handlers in application.handlers.values()
        for handler in handlers
        for command in getattr(handler, "commands", [])
    }

    assert {
        "status",
        "health",
        "cpu",
        "ram",
        "disk",
        "uptime",
        "log",
        "errors",
        "nginx_errors",
        "docker",
        "docker_logs",
        "restart",
        "docker_restart",
    }.issubset(registered)
    assert application.bot_data["settings"] is settings
    assert "audit" in application.bot_data
    assert "confirmations" in application.bot_data
