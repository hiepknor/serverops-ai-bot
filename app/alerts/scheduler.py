from __future__ import annotations

from telegram.ext import Application, ContextTypes

from app.config import Settings
from app.core.alerts import AlertCooldownState, send_due_system_alerts
from app.core.audit import AuditStore


async def alert_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    application = context.application
    await send_due_system_alerts(
        bot=application.bot,
        settings=application.bot_data["settings"],
        audit=application.bot_data["audit"],
        cooldown_state=application.bot_data["alert_cooldown_state"],
    )


def register_alert_jobs(
    application: Application,
    settings: Settings,
    audit: AuditStore,
) -> None:
    application.bot_data["alert_cooldown_state"] = AlertCooldownState()
    if not settings.enable_alerts:
        return
    if application.job_queue is None:
        raise RuntimeError("python-telegram-bot JobQueue is required for alerts")
    application.job_queue.run_repeating(
        alert_job,
        interval=settings.alert_interval_seconds,
        first=settings.alert_interval_seconds,
        name="system_alerts",
    )
