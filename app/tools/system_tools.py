from __future__ import annotations

import time
from dataclasses import dataclass

import psutil


@dataclass(frozen=True)
class SystemSnapshot:
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime_seconds: int


def get_system_snapshot() -> SystemSnapshot:
    return SystemSnapshot(
        cpu_percent=float(psutil.cpu_percent(interval=None)),
        memory_percent=float(psutil.virtual_memory().percent),
        disk_percent=float(psutil.disk_usage("/").percent),
        uptime_seconds=max(0, int(time.time() - psutil.boot_time())),
    )

