from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_parse_csv_roles_and_allowlists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:telegram-token-value")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-testtokenvalue")
    monkeypatch.setenv("OWNER_IDS", "100, 200")
    monkeypatch.setenv("ADMIN_IDS", "300")
    monkeypatch.setenv("VIEWER_IDS", "")
    monkeypatch.setenv("ALLOWED_SERVICES", "nginx, docker")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("BOT_LANGUAGE", "vi")
    monkeypatch.setenv("SERVEROPS_INIT_ONLY", "true")
    monkeypatch.setenv("ENABLE_DOCKER_TOOLS", "true")
    monkeypatch.setenv("ENABLE_ALERTS", "true")
    monkeypatch.setenv("ALERT_INTERVAL_SECONDS", "120")
    monkeypatch.setenv("ALERT_COOLDOWN_SECONDS", "600")
    monkeypatch.setenv("ALERT_CPU_PERCENT", "80")
    monkeypatch.setenv("ALERT_RAM_PERCENT", "81")
    monkeypatch.setenv("ALERT_DISK_PERCENT", "82")
    monkeypatch.setenv("ALERT_DOCKER_ENABLED", "false")

    settings = Settings(_env_file=None)

    assert settings.owner_ids == [100, 200]
    assert settings.admin_ids == [300]
    assert settings.viewer_ids == []
    assert settings.allowed_services == ["nginx", "docker"]
    assert settings.log_level == "DEBUG"
    assert settings.bot_language == "vi"
    assert settings.serverops_init_only is True
    assert settings.enable_docker_tools is True
    assert settings.enable_alerts is True
    assert settings.alert_interval_seconds == 120
    assert settings.alert_cooldown_seconds == 600
    assert settings.alert_cpu_percent == 80
    assert settings.alert_ram_percent == 81
    assert settings.alert_disk_percent == 82
    assert settings.alert_docker_enabled is False


def test_settings_reject_unknown_bot_language(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:telegram-token-value")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-testtokenvalue")
    monkeypatch.setenv("OWNER_IDS", "100")
    monkeypatch.setenv("BOT_LANGUAGE", "fr")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_require_owner_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:telegram-token-value")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-testtokenvalue")
    monkeypatch.delenv("OWNER_IDS", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_docker_tools_are_disabled_by_default() -> None:
    settings = Settings(
        telegram_bot_token="123456:telegram-token-value",
        openai_api_key="sk-testtokenvalue",
        owner_ids=[1],
    )

    assert settings.enable_docker_tools is False
