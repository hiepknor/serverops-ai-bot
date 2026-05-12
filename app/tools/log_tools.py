from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.security import redact_secrets


class LogAccessError(ValueError):
    pass


@dataclass(frozen=True)
class LogTarget:
    name: str
    path: Path


@dataclass(frozen=True)
class LogTail:
    name: str
    path: Path
    content: str


def read_log_tail(
    target_name: str,
    allowed_entries: list[str],
    *,
    line_limit: int,
    known_secrets: list[str] | None = None,
) -> LogTail:
    target = resolve_log_target(target_name, allowed_entries)
    lines = _tail_lines(target.path, line_limit)
    return LogTail(
        name=target.name,
        path=target.path,
        content=redact_secrets("\n".join(lines), known_secrets=known_secrets),
    )


def resolve_log_target(target_name: str, allowed_entries: list[str]) -> LogTarget:
    targets = {_parse_entry(entry).name: _parse_entry(entry) for entry in allowed_entries}
    if target_name not in targets:
        raise LogAccessError(f"{target_name!r} is not allowlisted")
    return targets[target_name]


def _parse_entry(entry: str) -> LogTarget:
    if ":" in entry:
        name, raw_path = entry.split(":", 1)
        name = name.strip()
        path = raw_path.strip()
    else:
        path = entry.strip()
        name = Path(path).stem
    if not name or not path:
        raise LogAccessError("invalid allowlisted log entry")
    return LogTarget(name=name, path=Path(path))


def _tail_lines(path: Path, line_limit: int) -> list[str]:
    if not path.is_file():
        raise LogAccessError(f"{path} is not readable")
    with path.open("r", encoding="utf-8", errors="replace") as file:
        lines = file.readlines()
    return [line.rstrip("\n") for line in lines[-line_limit:]]

