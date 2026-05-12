from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmptyArguments(ToolArguments):
    pass


class ReadLogArguments(ToolArguments):
    target: str = Field(min_length=1, max_length=80)
    lines: int | None = Field(default=None, ge=1, le=1000)


class ReadDockerLogsArguments(ToolArguments):
    container: str = Field(min_length=1, max_length=120)
    lines: int | None = Field(default=None, ge=1, le=1000)


ToolName = Literal[
    "get_system_status",
    "read_log",
    "list_docker_containers",
    "read_docker_logs",
]


TOOL_ARGUMENT_MODELS: dict[str, type[ToolArguments]] = {
    "get_system_status": EmptyArguments,
    "read_log": ReadLogArguments,
    "list_docker_containers": EmptyArguments,
    "read_docker_logs": ReadDockerLogsArguments,
}


class ToolResult(BaseModel):
    ok: bool
    tool_name: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


def openai_tool_definitions() -> list[dict[str, Any]]:
    return [
        _tool_definition(
            "get_system_status",
            "Read current CPU, RAM, disk, uptime, and configured service count.",
            EmptyArguments,
        ),
        _tool_definition(
            "read_log",
            "Read a sanitized, bounded tail from an allowlisted log target.",
            ReadLogArguments,
        ),
        _tool_definition(
            "list_docker_containers",
            "List status for configured allowlisted Docker containers only.",
            EmptyArguments,
        ),
        _tool_definition(
            "read_docker_logs",
            "Read sanitized, bounded logs from an allowlisted Docker container.",
            ReadDockerLogsArguments,
        ),
    ]


def _tool_definition(
    name: str,
    description: str,
    model: type[ToolArguments],
) -> dict[str, Any]:
    schema = _strict_json_schema(model.model_json_schema())
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": schema,
        "strict": True,
    }


def _strict_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    strict_schema = dict(schema)
    strict_schema.pop("default", None)

    if strict_schema.get("type") == "object":
        properties = strict_schema.get("properties", {})
        strict_schema["additionalProperties"] = False
        strict_schema["required"] = sorted(properties)
        strict_schema["properties"] = {
            name: _strict_json_schema(property_schema)
            for name, property_schema in properties.items()
        }

    for key in ("anyOf", "oneOf", "allOf"):
        if key in strict_schema:
            strict_schema[key] = [_strict_json_schema(item) for item in strict_schema[key]]

    if "items" in strict_schema and isinstance(strict_schema["items"], dict):
        strict_schema["items"] = _strict_json_schema(strict_schema["items"])

    return strict_schema
