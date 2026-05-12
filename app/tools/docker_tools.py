from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import docker
from docker.errors import DockerException, NotFound

from app.core.security import redact_secrets


class DockerUnavailableError(RuntimeError):
    pass


class DockerAccessError(ValueError):
    pass


@dataclass(frozen=True)
class ContainerStatus:
    name: str
    status: str


@dataclass(frozen=True)
class DockerLogTail:
    name: str
    content: str


def list_containers(
    *,
    allowed_names: list[str],
    client: Any | None = None,
) -> list[ContainerStatus]:
    if not allowed_names:
        return []

    docker_client = client or _client_from_env()
    try:
        containers = docker_client.containers.list(all=True)
    except DockerException as exc:
        raise DockerUnavailableError(str(exc)) from exc

    allowed = set(allowed_names)
    result = []
    for container in containers:
        name = _container_name(container)
        if name not in allowed:
            continue
        result.append(
            ContainerStatus(
                name=name,
                status=str(getattr(container, "status", "unknown")),
            )
        )
    return result


def get_container_logs(
    name: str,
    *,
    allowed_names: list[str],
    line_limit: int,
    known_secrets: list[str] | None = None,
    client: Any | None = None,
) -> DockerLogTail:
    if name not in set(allowed_names):
        raise DockerAccessError(f"{name!r} is not allowlisted")

    docker_client = client or _client_from_env()
    try:
        container = docker_client.containers.get(name)
        raw_logs = container.logs(tail=line_limit)
    except (DockerException, NotFound) as exc:
        raise DockerUnavailableError(str(exc)) from exc

    if isinstance(raw_logs, bytes):
        content = raw_logs.decode("utf-8", errors="replace")
    else:
        content = str(raw_logs)
    return DockerLogTail(
        name=name,
        content=redact_secrets(content.rstrip("\n"), known_secrets=known_secrets),
    )


def restart_container(
    name: str,
    *,
    allowed_names: list[str],
    client: Any | None = None,
) -> str:
    if name not in set(allowed_names):
        raise DockerAccessError(f"{name!r} is not allowlisted")

    docker_client = client or _client_from_env()
    try:
        container = docker_client.containers.get(name)
        container.restart()
    except (DockerException, NotFound) as exc:
        raise DockerUnavailableError(str(exc)) from exc
    return f"Container restarted: {name}"



def _client_from_env() -> Any:
    try:
        return docker.from_env()
    except DockerException as exc:
        raise DockerUnavailableError(str(exc)) from exc


def _container_name(container: Any) -> str:
    name = str(getattr(container, "name", ""))
    return name.lstrip("/")
