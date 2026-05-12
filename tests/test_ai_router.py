from __future__ import annotations

from app.ai import router
from app.ai.router import route_tool_call
from app.ai.schemas import openai_tool_definitions
from app.config import Settings
from app.core.security import Role
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


def test_unknown_ai_tool_is_rejected_before_execution() -> None:
    result = route_tool_call(
        tool_name="run_shell",
        arguments={"command": "whoami"},
        role=Role.OWNER,
        settings=make_settings(),
    )

    assert result.ok is False
    assert result.message == "Tool call rejected."
    assert result.error == "unknown tool: run_shell"


def test_ai_tool_arguments_reject_extra_fields() -> None:
    result = route_tool_call(
        tool_name="read_log",
        arguments={"target": "app", "path": "/etc/passwd"},
        role=Role.VIEWER,
        settings=make_settings(),
    )

    assert result.ok is False
    assert "invalid arguments for read_log" in str(result.error)


def test_unknown_role_is_denied_before_tool_execution(monkeypatch) -> None:
    called = False

    def fake_snapshot() -> SystemSnapshot:
        nonlocal called
        called = True
        return SystemSnapshot(
            cpu_percent=1.0,
            memory_percent=2.0,
            disk_percent=3.0,
            uptime_seconds=4,
        )

    monkeypatch.setattr(router, "get_system_snapshot", fake_snapshot)

    result = route_tool_call(
        tool_name="get_system_status",
        arguments={},
        role=Role.UNKNOWN,
        settings=make_settings(),
    )

    assert result.ok is False
    assert not called


def test_viewer_can_read_sanitized_allowlisted_log(tmp_path) -> None:
    log_file = tmp_path / "app.log"
    log_file.write_text("ok\nOPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8")

    result = route_tool_call(
        tool_name="read_log",
        arguments={"target": "app", "lines": 10},
        role=Role.VIEWER,
        settings=make_settings(allowed_log_files=[f"app:{log_file}"]),
    )

    assert result.ok is True
    assert result.data["target"] == "app"
    assert "ok" in result.data["content"]
    assert "sk-abcdefghijklmnopqrstuvwxyz" not in result.data["content"]


def test_unallowlisted_log_target_is_rejected_by_router() -> None:
    result = route_tool_call(
        tool_name="read_log",
        arguments='{"target": "shadow"}',
        role=Role.VIEWER,
        settings=make_settings(allowed_log_files=[]),
    )

    assert result.ok is False
    assert result.message == "Log access denied."
    assert "'shadow' is not allowlisted" in str(result.error)


def test_openai_tool_definitions_are_strict_function_tools() -> None:
    definitions = openai_tool_definitions()

    assert {definition["name"] for definition in definitions} == {
        "get_system_status",
        "read_log",
        "list_docker_containers",
        "read_docker_logs",
    }
    assert all(definition["type"] == "function" for definition in definitions)
    assert all(definition["strict"] is True for definition in definitions)
    assert all(
        definition["parameters"]["additionalProperties"] is False
        for definition in definitions
    )
