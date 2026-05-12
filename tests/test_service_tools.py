from __future__ import annotations

import subprocess

import pytest

from app.tools.service_tools import ServiceAccessError, ServiceExecutionError, restart_service


def test_restart_service_requires_allowlisted_service() -> None:
    with pytest.raises(ServiceAccessError):
        restart_service("postgres", allowed_services=["nginx"])


def test_restart_service_uses_argument_array_without_shell() -> None:
    calls = []

    def runner(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="", stderr="")

    message = restart_service("nginx", allowed_services=["nginx"], runner=runner)

    assert message == "Service restarted: nginx"
    assert calls[0][0][0] == ["systemctl", "restart", "nginx"]
    assert calls[0][1]["check"] is False
    assert "shell" not in calls[0][1]


def test_restart_service_raises_sanitized_execution_error() -> None:
    def runner(*args, **kwargs):
        del kwargs
        return subprocess.CompletedProcess(args=args[0], returncode=1, stdout="", stderr="failed")

    with pytest.raises(ServiceExecutionError, match="failed"):
        restart_service("nginx", allowed_services=["nginx"], runner=runner)

