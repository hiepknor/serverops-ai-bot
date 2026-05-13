from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.config import Settings
from app.core.messages import message
from app.core.security import Role, resolve_role


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_help(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_help(update, context)


def render_help(role: Role, settings: Settings) -> str:
    if role == Role.UNKNOWN:
        return message(settings, "access_denied")

    if settings.bot_language == "en":
        lines = [
            "ServerOps AI Bot",
            "Read-only: /status /health /cpu /ram /disk /uptime",
            "Logs: /log <name> /errors /nginx_errors",
            "AI: /ask <question> /summarize_log <name> /incident <name>",
        ]
        if role in {Role.OWNER, Role.ADMIN}:
            lines.append("Actions: /restart <service> /docker_restart <container>")
        if role == Role.OWNER:
            lines.append("Owner: /audit [limit]")
        if settings.enable_docker_tools:
            lines.append("Docker: /docker /docker_logs <container>")
        else:
            lines.append("Docker tools are disabled.")
        return "\n".join(lines)

    lines = [
        "ServerOps AI Bot",
        "Chỉ đọc: /status /health /cpu /ram /disk /uptime",
        "Log: /log <tên> /errors /nginx_errors",
        "AI: /ask <câu-hỏi> /summarize_log <tên> /incident <tên>",
    ]
    if role in {Role.OWNER, Role.ADMIN}:
        lines.append("Thao tác: /restart <service> /docker_restart <container>")
    if role == Role.OWNER:
        lines.append("Owner: /audit [limit]")
    if settings.enable_docker_tools:
        lines.append("Docker: /docker /docker_logs <container>")
    else:
        lines.append("Docker tools đang tắt.")
    return "\n".join(lines)


async def _reply_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.effective_message is None:
        return

    settings = context.application.bot_data["settings"]
    role = resolve_role(update.effective_user.id, settings)
    await update.effective_message.reply_text(render_help(role, settings))
