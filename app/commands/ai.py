from __future__ import annotations

from collections.abc import Callable

from telegram import Update
from telegram.ext import ContextTypes

from app.ai.client import ResponsesClient
from app.ai.router import AIToolAuditContext
from app.ai.service import answer_operational_question, summarize_log_context
from app.config import Settings
from app.core.audit import AuditStore
from app.core.messages import message
from app.core.security import Permission, Role, has_permission, resolve_role


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = _joined_args(context)
    await _reply_ai(
        update,
        context,
        permission=Permission.VIEW_STATUS,
        usage_key="usage_ask",
        argument=question,
        command="ask",
        renderer=lambda role, settings, client, audit, audit_context: answer_operational_question(
            question=question or "",
            role=role,
            settings=settings,
            client=client,
            audit=audit,
            audit_context=audit_context,
        ).text,
    )


async def summarize_log_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target = _first_arg(context)
    await _reply_ai(
        update,
        context,
        permission=Permission.VIEW_LOGS,
        usage_key="usage_summarize_log",
        argument=target,
        command="summarize_log",
        renderer=lambda role, settings, client, audit, audit_context: summarize_log_context(
            target=target or "",
            role=role,
            settings=settings,
            client=client,
            audit=audit,
            audit_context=audit_context,
        ).text,
    )


async def incident_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target = _first_arg(context)
    await _reply_ai(
        update,
        context,
        permission=Permission.VIEW_LOGS,
        usage_key="usage_incident",
        argument=target,
        command="incident",
        renderer=lambda role, settings, client, audit, audit_context: summarize_log_context(
            target=target or "",
            role=role,
            settings=settings,
            client=client,
            incident_mode=True,
            audit=audit,
            audit_context=audit_context,
        ).text,
    )


async def _reply_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    permission: Permission,
    usage_key: str,
    argument: str | None,
    command: str,
    renderer: Callable[
        [Role, Settings, object, AuditStore, AIToolAuditContext],
        str,
    ],
) -> None:
    if update.effective_user is None or update.effective_message is None:
        return

    settings = context.application.bot_data["settings"]
    audit = context.application.bot_data["audit"]
    role = resolve_role(update.effective_user.id, settings)
    client = context.application.bot_data.get("ai_client") or ResponsesClient(settings)
    audit_context = AIToolAuditContext(
        user_id=update.effective_user.id,
        role=role,
        command=command,
    )
    response = authorize_and_render_ai(
        role=role,
        permission=permission,
        usage_key=usage_key,
        argument=argument,
        settings=settings,
        client=client,
        audit=audit,
        audit_context=audit_context,
        renderer=renderer,
    )
    await update.effective_message.reply_text(response)


def authorize_and_render_ai(
    *,
    role: Role,
    permission: Permission,
    usage_key: str,
    argument: str | None,
    settings: Settings,
    client: object,
    audit: AuditStore,
    audit_context: AIToolAuditContext,
    renderer: Callable[
        [Role, Settings, object, AuditStore, AIToolAuditContext],
        str,
    ],
) -> str:
    if not argument:
        return message(settings, usage_key)
    if not has_permission(role, permission):
        return message(settings, "access_denied")
    return renderer(role, settings, client, audit, audit_context)


def _joined_args(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    if not context.args:
        return None
    text = " ".join(str(arg).strip() for arg in context.args).strip()
    return text or None


def _first_arg(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    if not context.args:
        return None
    return str(context.args[0]).strip()
