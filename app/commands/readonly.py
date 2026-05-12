from __future__ import annotations

from collections.abc import Callable

from telegram import Update
from telegram.ext import ContextTypes

from app.config import Settings
from app.core.security import Permission, Role, has_permission, resolve_role
from app.tools.docker_tools import (
    DockerAccessError,
    DockerUnavailableError,
    get_container_logs,
    list_containers,
)
from app.tools.log_tools import LogAccessError, read_log_tail
from app.tools.system_tools import get_system_snapshot


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, context, Permission.VIEW_STATUS, render_status)


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, context, Permission.VIEW_STATUS, render_health)


async def cpu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, context, Permission.VIEW_STATUS, render_cpu)


async def ram_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, context, Permission.VIEW_STATUS, render_ram)


async def disk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, context, Permission.VIEW_STATUS, render_disk)


async def uptime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, context, Permission.VIEW_STATUS, render_uptime)


async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target = _first_arg(context)
    await _reply(
        update,
        context,
        Permission.VIEW_LOGS,
        lambda settings: render_log(settings, target),
    )


async def errors_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(
        update,
        context,
        Permission.VIEW_LOGS,
        lambda settings: render_log(settings, "errors"),
    )


async def nginx_errors_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(
        update,
        context,
        Permission.VIEW_LOGS,
        lambda settings: render_log(settings, "nginx_errors"),
    )


async def docker_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, context, Permission.VIEW_DOCKER, render_docker)


async def docker_logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target = _first_arg(context)
    await _reply(
        update,
        context,
        Permission.VIEW_DOCKER,
        lambda settings: render_docker_logs(settings, target),
    )


def render_status(settings: Settings) -> str:
    snapshot = get_system_snapshot()
    return (
        "Server status\n"
        f"CPU: {snapshot.cpu_percent:.1f}%\n"
        f"RAM: {snapshot.memory_percent:.1f}%\n"
        f"Disk: {snapshot.disk_percent:.1f}%\n"
        f"Uptime: {snapshot.uptime_seconds // 60}m\n"
        f"Allowed services: {len(settings.allowed_services)}"
    )


def render_health(settings: Settings) -> str:
    snapshot = get_system_snapshot()
    warnings = []
    if snapshot.cpu_percent >= 90:
        warnings.append("high CPU")
    if snapshot.memory_percent >= 90:
        warnings.append("high RAM")
    if snapshot.disk_percent >= 90:
        warnings.append("high disk")
    state = "OK" if not warnings else "WARN: " + ", ".join(warnings)
    return f"Health: {state}"


def render_cpu(settings: Settings) -> str:
    snapshot = get_system_snapshot()
    del settings
    return f"CPU: {snapshot.cpu_percent:.1f}%"


def render_ram(settings: Settings) -> str:
    snapshot = get_system_snapshot()
    del settings
    return f"RAM: {snapshot.memory_percent:.1f}%"


def render_disk(settings: Settings) -> str:
    snapshot = get_system_snapshot()
    del settings
    return f"Disk: {snapshot.disk_percent:.1f}%"


def render_uptime(settings: Settings) -> str:
    snapshot = get_system_snapshot()
    del settings
    hours, remainder = divmod(snapshot.uptime_seconds, 3600)
    minutes = remainder // 60
    return f"Uptime: {hours}h {minutes}m"


def render_log(settings: Settings, target: str | None) -> str:
    if not target:
        return "Usage: /log <allowed-log-name>"
    try:
        result = read_log_tail(
            target,
            settings.allowed_log_files,
            line_limit=settings.log_tail_lines,
            known_secrets=_known_secrets(settings),
        )
    except LogAccessError as exc:
        return f"Log access denied: {exc}"
    return f"Log: {result.name}\n{result.content or '(empty)'}"


def render_docker(settings: Settings) -> str:
    try:
        containers = list_containers(allowed_names=settings.allowed_containers)
    except DockerUnavailableError as exc:
        return f"Docker unavailable: {exc}"
    if not containers:
        return "Docker containers: none"
    lines = ["Docker containers"]
    for container in containers:
        lines.append(f"- {container.name}: {container.status}")
    return "\n".join(lines)


def render_docker_logs(settings: Settings, target: str | None) -> str:
    if not target:
        return "Usage: /docker_logs <allowed-container>"
    try:
        result = get_container_logs(
            target,
            allowed_names=settings.allowed_containers,
            line_limit=settings.docker_log_tail_lines,
            known_secrets=_known_secrets(settings),
        )
    except DockerAccessError as exc:
        return f"Docker access denied: {exc}"
    except DockerUnavailableError as exc:
        return f"Docker unavailable: {exc}"
    return f"Docker logs: {result.name}\n{result.content or '(empty)'}"


async def _reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    permission: Permission,
    renderer: Callable[[Settings], str],
) -> None:
    if update.effective_user is None or update.effective_message is None:
        return

    settings = context.application.bot_data["settings"]
    role = resolve_role(update.effective_user.id, settings)
    response = authorize_and_render(role, permission, renderer, settings)
    await update.effective_message.reply_text(response)


def authorize_and_render(
    role: Role,
    permission: Permission,
    renderer: Callable[[Settings], str],
    settings: Settings,
) -> str:
    if not has_permission(role, permission):
        return "Access denied."
    return renderer(settings)


def _first_arg(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    if not context.args:
        return None
    return str(context.args[0]).strip()


def _known_secrets(settings: Settings) -> list[str]:
    return [
        settings.telegram_bot_token.get_secret_value(),
        settings.openai_api_key.get_secret_value(),
    ]
