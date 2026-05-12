from __future__ import annotations

import pytest

from app.tools.docker_tools import DockerAccessError, get_container_logs, list_containers


class FakeContainer:
    def __init__(self, name: str, status: str = "running", logs: bytes = b"") -> None:
        self.name = name
        self.status = status
        self._logs = logs

    def logs(self, tail: int) -> bytes:
        del tail
        return self._logs


class FakeContainers:
    def __init__(self, containers: list[FakeContainer]) -> None:
        self._containers = containers

    def list(self, all: bool) -> list[FakeContainer]:
        del all
        return self._containers

    def get(self, name: str) -> FakeContainer:
        for container in self._containers:
            if container.name == name:
                return container
        raise AssertionError("unexpected container lookup")


class FakeClient:
    def __init__(self, containers: list[FakeContainer]) -> None:
        self.containers = FakeContainers(containers)


def test_list_containers_filters_to_allowlist() -> None:
    client = FakeClient(
        [
            FakeContainer("api", "running"),
            FakeContainer("db", "exited"),
        ]
    )

    containers = list_containers(allowed_names=["api"], client=client)

    assert len(containers) == 1
    assert containers[0].name == "api"
    assert containers[0].status == "running"


def test_list_containers_returns_none_when_allowlist_empty() -> None:
    client = FakeClient([FakeContainer("api", "running")])

    assert list_containers(allowed_names=[], client=client) == []


def test_get_container_logs_requires_allowlist_and_redacts() -> None:
    client = FakeClient(
        [
            FakeContainer("api", logs=b"token=123456:abcdefghijklmnopqrstuvwxyz\nready\n"),
        ]
    )

    result = get_container_logs("api", allowed_names=["api"], line_limit=200, client=client)

    assert result.name == "api"
    assert "123456:" not in result.content
    assert "ready" in result.content


def test_get_container_logs_rejects_unlisted_container() -> None:
    with pytest.raises(DockerAccessError):
        get_container_logs("db", allowed_names=["api"], line_limit=200, client=FakeClient([]))
