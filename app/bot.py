from __future__ import annotations

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.alerts.scheduler import register_alert_jobs
from app.commands.actions import (
    confirmation_text_handler,
    docker_restart_command,
    restart_command,
)
from app.commands.ai import ask_command, incident_command, summarize_log_command
from app.commands.audit import audit_command
from app.commands.readonly import (
    cpu_command,
    disk_command,
    docker_command,
    docker_logs_command,
    errors_command,
    health_command,
    log_command,
    nginx_errors_command,
    ram_command,
    status_command,
    uptime_command,
)
from app.config import Settings
from app.core.audit import AuditStore
from app.core.confirmations import ConfirmationStore


def build_application(
    settings: Settings,
    *,
    audit: AuditStore | None = None,
    confirmations: ConfirmationStore | None = None,
) -> Application:
    application = (
        Application.builder()
        .token(settings.telegram_bot_token.get_secret_value())
        .build()
    )
    register_handlers(application, settings, audit=audit, confirmations=confirmations)
    return application


def register_handlers(
    application: Application,
    settings: Settings,
    *,
    audit: AuditStore | None = None,
    confirmations: ConfirmationStore | None = None,
) -> None:
    application.bot_data["settings"] = settings
    audit_store = audit or AuditStore.from_database_url(settings.database_url)
    application.bot_data["audit"] = audit_store
    application.bot_data["confirmations"] = confirmations or ConfirmationStore.from_database_url(
        settings.database_url
    )
    register_alert_jobs(application, settings, audit_store)
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("health", health_command))
    application.add_handler(CommandHandler("cpu", cpu_command))
    application.add_handler(CommandHandler("ram", ram_command))
    application.add_handler(CommandHandler("disk", disk_command))
    application.add_handler(CommandHandler("uptime", uptime_command))
    application.add_handler(CommandHandler("log", log_command))
    application.add_handler(CommandHandler("errors", errors_command))
    application.add_handler(CommandHandler("nginx_errors", nginx_errors_command))
    application.add_handler(CommandHandler("docker", docker_command))
    application.add_handler(CommandHandler("docker_logs", docker_logs_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("summarize_log", summarize_log_command))
    application.add_handler(CommandHandler("incident", incident_command))
    application.add_handler(CommandHandler("audit", audit_command))
    application.add_handler(CommandHandler("restart", restart_command))
    application.add_handler(CommandHandler("docker_restart", docker_restart_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, confirmation_text_handler)
    )


def run_polling(settings: Settings) -> None:
    build_application(settings).run_polling()
