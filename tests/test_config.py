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
    monkeypatch.setenv("SERVEROPS_INIT_ONLY", "true")

    settings = Settings(_env_file=None)

    assert settings.owner_ids == [100, 200]
    assert settings.admin_ids == [300]
    assert settings.viewer_ids == []
    assert settings.allowed_services == ["nginx", "docker"]
    assert settings.log_level == "DEBUG"
    assert settings.serverops_init_only is True


def test_settings_require_owner_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:telegram-token-value")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-testtokenvalue")
    monkeypatch.delenv("OWNER_IDS", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
