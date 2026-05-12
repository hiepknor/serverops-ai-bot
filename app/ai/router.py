from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.ai.schemas import (
    TOOL_ARGUMENT_MODELS,
    ReadDockerLogsArguments,
    ReadLogArguments,
    ToolArguments,
    ToolResult,
)
from app.config import Settings
from app.core.security import Permission, Role, has_permission
from app.tools.docker_tools import (
    DockerAccessError,
    DockerUnavailableError,
    get_container_logs,
    list_containers,
)
from app.tools.log_tools import LogAccessError, read_log_tail
from app.tools.system_tools import get_system_snapshot


class ToolCallRejected(ValueError):
    pass


def route_tool_call(
    *,
    tool_name: str,
    arguments: dict[str, Any] | str | None,
    role: Role,
    settings: Settings,
) -> ToolResult:
    try:
        parsed_arguments = _validate_arguments(tool_name, arguments)
        permission = _permission_for_tool(tool_name)
        if not has_permission(role, permission):
            raise ToolCallRejected(f"role {role} cannot use {tool_name}")
        return _execute_tool(tool_name, parsed_arguments, settings)
    except ToolCallRejected as exc:
        return ToolResult(
            ok=False,
            tool_name=tool_name,
            message="Tool call rejected.",
            error=str(exc),
        )


def _validate_arguments(
    tool_name: str,
    arguments: dict[str, Any] | str | None,
) -> ToolArguments:
    argument_model = TOOL_ARGUMENT_MODELS.get(tool_name)
    if argument_model is None:
        raise ToolCallRejected(f"unknown tool: {tool_name}")

    raw_arguments = _coerce_arguments(arguments)
    try:
        return argument_model.model_validate(raw_arguments)
    except ValidationError as exc:
        raise ToolCallRejected(f"invalid arguments for {tool_name}: {exc}") from exc


def _coerce_arguments(arguments: dict[str, Any] | str | None) -> dict[str, Any]:
    if arguments is None:
        return {}
    if isinstance(arguments, dict):
        return arguments
    try:
        decoded = json.loads(arguments)
    except json.JSONDecodeError as exc:
        raise ToolCallRejected("arguments must be a JSON object") from exc
    if not isinstance(decoded, dict):
        raise ToolCallRejected("arguments must be a JSON object")
    return decoded


def _permission_for_tool(tool_name: str) -> Permission:
    if tool_name == "get_system_status":
        return Permission.VIEW_STATUS
    if tool_name == "read_log":
        return Permission.VIEW_LOGS
    if tool_name in {"list_docker_containers", "read_docker_logs"}:
        return Permission.VIEW_DOCKER
    raise ToolCallRejected(f"unknown tool: {tool_name}")


def _execute_tool(tool_name: str, arguments: ToolArguments, settings: Settings) -> ToolResult:
    if tool_name == "get_system_status":
        return _get_system_status(settings)
    if tool_name == "read_log":
        return _read_log(arguments, settings)
    if tool_name == "list_docker_containers":
        return _list_docker_containers(settings)
    if tool_name == "read_docker_logs":
        return _read_docker_logs(arguments, settings)
    raise ToolCallRejected(f"unknown tool: {tool_name}")


def _get_system_status(settings: Settings) -> ToolResult:
    snapshot = get_system_snapshot()
    return ToolResult(
        ok=True,
        tool_name="get_system_status",
        message="System status read.",
        data={
            "cpu_percent": snapshot.cpu_percent,
            "memory_percent": snapshot.memory_percent,
            "disk_percent": snapshot.disk_percent,
            "uptime_seconds": snapshot.uptime_seconds,
            "allowed_services": len(settings.allowed_services),
        },
    )


def _read_log(arguments: ToolArguments, settings: Settings) -> ToolResult:
    if not isinstance(arguments, ReadLogArguments):
        raise ToolCallRejected("read_log arguments were not validated")
    try:
        result = read_log_tail(
            arguments.target,
            settings.allowed_log_files,
            line_limit=arguments.lines or settings.log_tail_lines,
            known_secrets=_known_secrets(settings),
        )
    except LogAccessError as exc:
        return ToolResult(
            ok=False,
            tool_name="read_log",
            message="Log access denied.",
            error=str(exc),
        )
    return ToolResult(
        ok=True,
        tool_name="read_log",
        message="Log read.",
        data={"target": result.name, "content": result.content},
    )


def _list_docker_containers(settings: Settings) -> ToolResult:
    try:
        containers = list_containers(allowed_names=settings.allowed_containers)
    except DockerUnavailableError as exc:
        return ToolResult(
            ok=False,
            tool_name="list_docker_containers",
            message="Docker unavailable.",
            error=str(exc),
        )
    return ToolResult(
        ok=True,
        tool_name="list_docker_containers",
        message="Docker containers read.",
        data={"containers": [container.__dict__ for container in containers]},
    )


def _read_docker_logs(arguments: ToolArguments, settings: Settings) -> ToolResult:
    if not isinstance(arguments, ReadDockerLogsArguments):
        raise ToolCallRejected("read_docker_logs arguments were not validated")
    try:
        result = get_container_logs(
            arguments.container,
            allowed_names=settings.allowed_containers,
            line_limit=arguments.lines or settings.docker_log_tail_lines,
            known_secrets=_known_secrets(settings),
        )
    except DockerAccessError as exc:
        return ToolResult(
            ok=False,
            tool_name="read_docker_logs",
            message="Docker access denied.",
            error=str(exc),
        )
    except DockerUnavailableError as exc:
        return ToolResult(
            ok=False,
            tool_name="read_docker_logs",
            message="Docker unavailable.",
            error=str(exc),
        )
    return ToolResult(
        ok=True,
        tool_name="read_docker_logs",
        message="Docker logs read.",
        data={"container": result.name, "content": result.content},
    )


def _known_secrets(settings: Settings) -> list[str]:
    return [
        settings.telegram_bot_token.get_secret_value(),
        settings.openai_api_key.get_secret_value(),
    ]
