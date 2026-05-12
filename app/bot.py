from __future__ import annotations

from telegram.ext import Application, CommandHandler

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


def build_application(settings: Settings) -> Application:
    application = (
        Application.builder()
        .token(settings.telegram_bot_token.get_secret_value())
        .build()
    )
    register_handlers(application, settings)
    return application


def register_handlers(application: Application, settings: Settings) -> None:
    application.bot_data["settings"] = settings
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


def run_polling(settings: Settings) -> None:
    build_application(settings).run_polling()
