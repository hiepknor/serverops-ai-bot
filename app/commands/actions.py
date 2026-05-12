from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.config import Settings
from app.core.audit import AuditEvent, AuditStore
from app.core.confirmations import ConfirmationStore, confirmation_text_for
from app.core.messages import message
from app.core.security import Permission, Role, has_permission, resolve_role
from app.tools.docker_tools import DockerAccessError, DockerUnavailableError, restart_container
from app.tools.service_tools import ServiceAccessError, ServiceExecutionError, restart_service


async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target = _first_arg(context)
    await _request_confirmation(
        update,
        context,
        permission=Permission.RESTART_SERVICE,
        action="restart_service",
        target=target,
    )


async def docker_restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target = _first_arg(context)
    await _request_confirmation(
        update,
        context,
        permission=Permission.RESTART_CONTAINER,
        action="restart_container",
        target=target,
    )


async def confirmation_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.effective_message is None:
        return
    text = (update.effective_message.text or "").strip()
    if not text.startswith("CONFIRM "):
        return

    settings = context.application.bot_data["settings"]
    confirmations = context.application.bot_data["confirmations"]
    audit = context.application.bot_data["audit"]
    pending = confirmations.get_pending_by_text(
        user_id=update.effective_user.id,
        confirmation_text=text,
    )
    if pending is None:
        await update.effective_message.reply_text(message(settings, "confirmation_no_match"))
        return

    result = execute_confirmed_action(pending.action, pending.target, settings)
    confirmations.mark_confirmed(pending.id)
    audit.record(
        AuditEvent(
            user_id=pending.user_id,
            role=pending.role,
            action=pending.action,
            target=pending.target,
            result="success" if result.ok else "failed",
            confirmation_status="confirmed",
            error=result.error,
        )
    )
    await update.effective_message.reply_text(result.message)


class ActionResult:
    def __init__(self, *, ok: bool, message: str, error: str | None = None) -> None:
        self.ok = ok
        self.message = message
        self.error = error


def execute_confirmed_action(action: str, target: str, settings: Settings) -> ActionResult:
    try:
        if action == "restart_service":
            restart_service(target, allowed_services=settings.allowed_services)
            result_message = message(settings, "action_service_restarted", target=target)
        elif action == "restart_container":
            restart_container(target, allowed_names=settings.allowed_containers)
            result_message = message(settings, "action_container_restarted", target=target)
        else:
            return ActionResult(
                ok=False,
                message=message(settings, "action_unsupported", action=action),
                error=action,
            )
    except (ServiceAccessError, DockerAccessError) as exc:
        return ActionResult(
            ok=False,
            message=message(settings, "access_denied") + f" {exc}",
            error=str(exc),
        )
    except (ServiceExecutionError, DockerUnavailableError) as exc:
        return ActionResult(
            ok=False,
            message=message(settings, "action_failed", error=exc),
            error=str(exc),
        )
    return ActionResult(ok=True, message=result_message)


async def _request_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    permission: Permission,
    action: str,
    target: str | None,
) -> None:
    if update.effective_user is None or update.effective_message is None:
        return

    settings = context.application.bot_data["settings"]
    confirmations = context.application.bot_data["confirmations"]
    audit = context.application.bot_data["audit"]
    role = resolve_role(update.effective_user.id, settings)

    response = request_confirmation(
        user_id=update.effective_user.id,
        role=role,
        permission=permission,
        action=action,
        target=target,
        settings=settings,
        confirmations=confirmations,
        audit=audit,
    )
    await update.effective_message.reply_text(response)


def request_confirmation(
    *,
    user_id: int,
    role: Role,
    permission: Permission,
    action: str,
    target: str | None,
    settings: Settings,
    confirmations: ConfirmationStore,
    audit: AuditStore,
) -> str:
    if not target:
        return message(settings, "restart_usage")

    if not has_permission(role, permission):
        audit.record(
            AuditEvent(
                user_id=user_id,
                role=str(role),
                action=action,
                target=target,
                result="denied",
                confirmation_status="not_requested",
            )
        )
        return message(settings, "access_denied")

    access_error = _validate_target(action, target, settings)
    if access_error is not None:
        audit.record(
            AuditEvent(
                user_id=user_id,
                role=str(role),
                action=action,
                target=target,
                result="denied",
                confirmation_status="not_requested",
                error=access_error,
            )
        )
        return f"{message(settings, 'access_denied')} {access_error}"

    confirmation_text = confirmation_text_for(action, target)
    confirmations.create(
        user_id=user_id,
        role=str(role),
        action=action,
        target=target,
        confirmation_text=confirmation_text,
    )
    audit.record(
        AuditEvent(
            user_id=user_id,
            role=str(role),
            action=action,
            target=target,
            result="pending_confirmation",
            confirmation_status="pending",
        )
    )
    return message(
        settings,
        "confirmation_required",
        action=action,
        target=target,
        confirmation_text=confirmation_text,
    )


def _validate_target(action: str, target: str, settings: Settings) -> str | None:
    if action == "restart_service" and target not in set(settings.allowed_services):
        return f"{target!r} is not allowlisted"
    if action == "restart_container" and target not in set(settings.allowed_containers):
        return f"{target!r} is not allowlisted"
    return None


def _first_arg(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    if not context.args:
        return None
    return str(context.args[0]).strip()
