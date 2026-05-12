from __future__ import annotations

import re
from enum import StrEnum

from app.config import Settings


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    VIEWER = "viewer"
    UNKNOWN = "unknown"


class Permission(StrEnum):
    VIEW_STATUS = "view_status"
    VIEW_LOGS = "view_logs"
    VIEW_DOCKER = "view_docker"
    RESTART_SERVICE = "restart_service"
    RESTART_CONTAINER = "restart_container"
    DEPLOY = "deploy"
    VIEW_AUDIT = "view_audit"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.OWNER: frozenset(Permission),
    Role.ADMIN: frozenset(
        {
            Permission.VIEW_STATUS,
            Permission.VIEW_LOGS,
            Permission.VIEW_DOCKER,
            Permission.RESTART_SERVICE,
            Permission.RESTART_CONTAINER,
        }
    ),
    Role.VIEWER: frozenset(
        {
            Permission.VIEW_STATUS,
            Permission.VIEW_LOGS,
            Permission.VIEW_DOCKER,
        }
    ),
    Role.UNKNOWN: frozenset(),
}

SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)=([^\s]+)"),
]


def resolve_role(telegram_user_id: int, settings: Settings) -> Role:
    if telegram_user_id in settings.owner_ids:
        return Role.OWNER
    if telegram_user_id in settings.admin_ids:
        return Role.ADMIN
    if telegram_user_id in settings.viewer_ids:
        return Role.VIEWER
    return Role.UNKNOWN


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]


def redact_secrets(text: str, known_secrets: list[str] | None = None) -> str:
    redacted = text
    for secret in known_secrets or []:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")

    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(_redact_match, redacted)
    return redacted


def _redact_match(match: re.Match[str]) -> str:
    if len(match.groups()) == 2:
        return f"{match.group(1)}=[REDACTED]"
    return "[REDACTED]"

