from __future__ import annotations

import subprocess
from collections.abc import Callable


class ServiceAccessError(ValueError):
    pass


class ServiceExecutionError(RuntimeError):
    pass


Runner = Callable[..., subprocess.CompletedProcess[str]]


def restart_service(
    service_name: str,
    *,
    allowed_services: list[str],
    runner: Runner = subprocess.run,
    timeout_seconds: int = 30,
) -> str:
    if service_name not in set(allowed_services):
        raise ServiceAccessError(f"{service_name!r} is not allowlisted")

    result = runner(
        ["systemctl", "restart", service_name],
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        error = (result.stderr or result.stdout or "service restart failed").strip()
        raise ServiceExecutionError(error)
    return f"Service restarted: {service_name}"

