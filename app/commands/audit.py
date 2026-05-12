from __future__ import annotations

from sqlite3 import Row

from telegram import Update
from telegram.ext import ContextTypes

from app.config import Settings
from app.core.audit import AuditEvent, AuditStore
from app.core.messages import message
from app.core.security import Permission, Role, has_permission, redact_secrets, resolve_role

DEFAULT_AUDIT_LIMIT = 10
MAX_AUDIT_LIMIT = 50
MAX_ERROR_CHARS = 120


async def audit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.effective_message is None:
        return

    settings = context.application.bot_data["settings"]
    audit = context.application.bot_data["audit"]
    role = resolve_role(update.effective_user.id, settings)
    response = render_audit(
        user_id=update.effective_user.id,
        role=role,
        args=[str(arg) for arg in context.args],
        settings=settings,
        audit=audit,
    )
    await update.effective_message.reply_text(response)


def render_audit(
    *,
    user_id: int,
    role: Role,
    args: list[str],
    settings: Settings,
    audit: AuditStore,
) -> str:
    if not has_permission(role, Permission.VIEW_AUDIT):
        audit.record(
            AuditEvent(
                user_id=user_id,
                role=str(role),
                action="view_audit",
                target="audit",
                result="denied",
            )
        )
        return message(settings, "access_denied")

    limit = _parse_limit(args)
    if limit is None:
        return message(settings, "usage_audit", max_limit=MAX_AUDIT_LIMIT)

    rows = audit.list_recent(limit)
    if not rows:
        return message(settings, "audit_empty")

    lines = [message(settings, "audit_header")]
    lines.extend(_format_row(row, settings) for row in rows)
    return "\n".join(lines)


def _parse_limit(args: list[str]) -> int | None:
    if not args:
        return DEFAULT_AUDIT_LIMIT
    if len(args) != 1:
        return None
    try:
        limit = int(args[0])
    except ValueError:
        return None
    if limit < 1 or limit > MAX_AUDIT_LIMIT:
        return None
    return limit


def _format_row(row: Row, settings: Settings) -> str:
    timestamp = str(row["created_at"])[:19]
    command = row["command"] or "-"
    target = row["target"] or "-"
    line = (
        f"- {timestamp} | {row['role']} | {command} | {row['action']} | "
        f"{target} | {row['result']}"
    )
    error = _format_error(row["error"], settings)
    if error:
        line = f"{line} | {error}"
    return line


def _format_error(error: str | None, settings: Settings) -> str | None:
    if not error:
        return None
    safe_error = redact_secrets(error, known_secrets=_known_secrets(settings))
    if len(safe_error) <= MAX_ERROR_CHARS:
        return safe_error
    return safe_error[: MAX_ERROR_CHARS - 3] + "..."


def _known_secrets(settings: Settings) -> list[str]:
    return [
        settings.telegram_bot_token.get_secret_value(),
        settings.openai_api_key.get_secret_value(),
    ]
