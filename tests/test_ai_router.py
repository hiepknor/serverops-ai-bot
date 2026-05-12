from __future__ import annotations

from app.ai import router
from app.ai.prompts import system_instructions
from app.ai.router import AIToolAuditContext, route_tool_call
from app.ai.schemas import openai_tool_definitions
from app.config import Settings
from app.core.audit import AuditStore
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


def make_audit_context(
    *, user_id: int = 3, role: Role = Role.VIEWER, command: str = "ask"
) -> AIToolAuditContext:
    return AIToolAuditContext(user_id=user_id, role=role, command=command)


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


def test_successful_ai_tool_call_creates_audit_record(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        router,
        "get_system_snapshot",
        lambda: SystemSnapshot(
            cpu_percent=1.0,
            memory_percent=2.0,
            disk_percent=3.0,
            uptime_seconds=4,
        ),
    )
    audit = AuditStore(tmp_path / "serverops.db")

    result = route_tool_call(
        tool_name="get_system_status",
        arguments={},
        role=Role.VIEWER,
        settings=make_settings(),
        audit=audit,
        audit_context=make_audit_context(command="ask"),
    )

    rows = audit.list_recent()
    assert result.ok is True
    assert len(rows) == 1
    assert rows[0]["user_id"] == 3
    assert rows[0]["role"] == "viewer"
    assert rows[0]["command"] == "ask"
    assert rows[0]["action"] == "ai_tool.get_system_status"
    assert rows[0]["target"] == "system"
    assert rows[0]["result"] == "success"
    assert rows[0]["confirmation_status"] == "not_required"


def test_unknown_ai_tool_creates_rejected_audit_record(tmp_path) -> None:
    audit = AuditStore(tmp_path / "serverops.db")

    result = route_tool_call(
        tool_name="run_shell",
        arguments={"command": "whoami"},
        role=Role.OWNER,
        settings=make_settings(),
        audit=audit,
        audit_context=make_audit_context(user_id=1, role=Role.OWNER, command="ask"),
    )

    rows = audit.list_recent()
    assert result.ok is False
    assert rows[0]["user_id"] == 1
    assert rows[0]["role"] == "owner"
    assert rows[0]["command"] == "ask"
    assert rows[0]["action"] == "ai_tool.run_shell"
    assert rows[0]["result"] == "rejected"
    assert rows[0]["error"] == "unknown tool: run_shell"


def test_ai_tool_rbac_denial_creates_denied_audit_record(monkeypatch, tmp_path) -> None:
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
    audit = AuditStore(tmp_path / "serverops.db")

    result = route_tool_call(
        tool_name="get_system_status",
        arguments={},
        role=Role.UNKNOWN,
        settings=make_settings(),
        audit=audit,
        audit_context=make_audit_context(user_id=99, role=Role.UNKNOWN, command="ask"),
    )

    rows = audit.list_recent()
    assert result.ok is False
    assert called is False
    assert rows[0]["user_id"] == 99
    assert rows[0]["role"] == "unknown"
    assert rows[0]["result"] == "denied"
    assert rows[0]["error"] == "role unknown cannot use get_system_status"


def test_ai_tool_allowlist_denial_creates_denied_audit_record(tmp_path) -> None:
    audit = AuditStore(tmp_path / "serverops.db")

    result = route_tool_call(
        tool_name="read_log",
        arguments={"target": "shadow", "lines": 20},
        role=Role.VIEWER,
        settings=make_settings(allowed_log_files=[]),
        audit=audit,
        audit_context=make_audit_context(command="summarize_log"),
    )

    rows = audit.list_recent()
    assert result.ok is False
    assert rows[0]["command"] == "summarize_log"
    assert rows[0]["action"] == "ai_tool.read_log"
    assert rows[0]["target"] == "shadow"
    assert rows[0]["result"] == "denied"
    assert "'shadow' is not allowlisted" in rows[0]["error"]


def test_ai_docker_tool_is_denied_when_docker_disabled_by_default(tmp_path) -> None:
    audit = AuditStore(tmp_path / "serverops.db")

    result = route_tool_call(
        tool_name="list_docker_containers",
        arguments={},
        role=Role.VIEWER,
        settings=make_settings(allowed_containers=["api"]),
        audit=audit,
        audit_context=make_audit_context(command="ask"),
    )

    rows = audit.list_recent()
    assert result.ok is False
    assert result.message == "Docker access denied."
    assert result.error == "Docker tools are disabled."
    assert rows[0]["action"] == "ai_tool.list_docker_containers"
    assert rows[0]["result"] == "denied"


def test_ai_docker_logs_tool_is_denied_when_docker_disabled_by_default(tmp_path) -> None:
    audit = AuditStore(tmp_path / "serverops.db")

    result = route_tool_call(
        tool_name="read_docker_logs",
        arguments={"container": "api", "lines": 20},
        role=Role.VIEWER,
        settings=make_settings(allowed_containers=["api"]),
        audit=audit,
        audit_context=make_audit_context(command="ask"),
    )

    rows = audit.list_recent()
    assert result.ok is False
    assert result.message == "Docker access denied."
    assert result.error == "Docker tools are disabled."
    assert rows[0]["action"] == "ai_tool.read_docker_logs"
    assert rows[0]["target"] == "api"
    assert rows[0]["result"] == "denied"


def test_ai_tool_audit_error_is_sanitized(tmp_path) -> None:
    audit = AuditStore(tmp_path / "serverops.db")

    route_tool_call(
        tool_name="read_log",
        arguments={"target": "app", "lines": "sk-abcdefghijklmnop"},
        role=Role.VIEWER,
        settings=make_settings(),
        audit=audit,
        audit_context=make_audit_context(command="ask"),
    )

    rows = audit.list_recent()
    assert rows[0]["result"] == "rejected"
    assert "sk-abcdefghijklmnop" not in rows[0]["error"]
    assert "[REDACTED]" in rows[0]["error"]


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
    definitions_by_name = {definition["name"]: definition for definition in definitions}

    assert set(definitions_by_name) == {
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
    assert definitions_by_name["read_log"]["parameters"]["required"] == ["lines", "target"]
    assert definitions_by_name["read_docker_logs"]["parameters"]["required"] == [
        "container",
        "lines",
    ]
    assert "default" not in definitions_by_name["read_log"]["parameters"]["properties"]["lines"]


def test_ai_prompt_uses_vietnamese_without_translating_machine_tokens() -> None:
    instructions = system_instructions("vi")

    assert "Vietnamese" in instructions
    assert "Keep command names" in instructions
    assert "confirmation text unchanged" in instructions
