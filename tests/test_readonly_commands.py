from __future__ import annotations

from app.commands import readonly
from app.commands.readonly import authorize_and_render, render_docker_logs, render_log
from app.config import Settings
from app.core.security import Permission, Role
from app.tools.system_tools import SystemSnapshot


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


def test_authorize_and_render_denies_unknown_user_before_renderer_runs() -> None:
    called = False

    def renderer(settings: Settings) -> str:
        nonlocal called
        called = True
        return "secret"

    response = authorize_and_render(
        Role.UNKNOWN,
        Permission.VIEW_LOGS,
        renderer,
        make_settings(),
    )

    assert response == "Access denied."
    assert not called


def test_viewer_can_render_allowlisted_log(tmp_path) -> None:
    log_file = tmp_path / "app.log"
    log_file.write_text("ok\n", encoding="utf-8")
    settings = make_settings(allowed_log_files=[f"app:{log_file}"])

    response = authorize_and_render(
        Role.VIEWER,
        Permission.VIEW_LOGS,
        lambda current_settings: render_log(current_settings, "app"),
        settings,
    )

    assert response == "Log: app\nok"


def test_status_metric_renderers_are_specific(monkeypatch) -> None:
    monkeypatch.setattr(
        readonly,
        "get_system_snapshot",
        lambda: SystemSnapshot(
            cpu_percent=12.5,
            memory_percent=34.5,
            disk_percent=56.5,
            uptime_seconds=3660,
        ),
    )
    settings = make_settings()

    assert readonly.render_cpu(settings) == "CPU: 12.5%"
    assert readonly.render_ram(settings) == "RAM: 34.5%"
    assert readonly.render_disk(settings) == "Disk: 56.5%"
    assert readonly.render_uptime(settings) == "Uptime: 1h 1m"


def test_docker_logs_unlisted_container_is_access_denied() -> None:
    response = render_docker_logs(make_settings(allowed_containers=["api"]), "db")

    assert response == "Docker access denied: 'db' is not allowlisted"
