from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from app.config import Settings
from app.core.audit import AuditEvent, AuditStore
from app.core.security import redact_secrets
from app.tools.system_tools import SystemSnapshot, get_system_snapshot


@dataclass(frozen=True)
class Alert:
    key: str
    title: str
    metric: str
    value: float
    threshold: float
    suggested_command: str


@dataclass
class AlertCooldownState:
    last_sent_at: dict[str, float] = field(default_factory=dict)

    def is_due(self, alert_key: str, *, now: float, cooldown_seconds: int) -> bool:
        last_sent = self.last_sent_at.get(alert_key)
        if last_sent is None:
            return True
        return now - last_sent >= cooldown_seconds

    def mark_sent(self, alert_key: str, *, now: float) -> None:
        self.last_sent_at[alert_key] = now


SnapshotProvider = Callable[[], SystemSnapshot]
Clock = Callable[[], float]


def evaluate_system_alerts(snapshot: SystemSnapshot, settings: Settings) -> list[Alert]:
    alerts = []
    if snapshot.cpu_percent >= settings.alert_cpu_percent:
        alerts.append(
            Alert(
                key="system.cpu",
                title="CPU",
                metric="CPU",
                value=snapshot.cpu_percent,
                threshold=settings.alert_cpu_percent,
                suggested_command="/cpu",
            )
        )
    if snapshot.memory_percent >= settings.alert_ram_percent:
        alerts.append(
            Alert(
                key="system.ram",
                title="RAM",
                metric="RAM",
                value=snapshot.memory_percent,
                threshold=settings.alert_ram_percent,
                suggested_command="/ram",
            )
        )
    if snapshot.disk_percent >= settings.alert_disk_percent:
        alerts.append(
            Alert(
                key="system.disk",
                title="Disk",
                metric="Disk",
                value=snapshot.disk_percent,
                threshold=settings.alert_disk_percent,
                suggested_command="/disk",
            )
        )
    return alerts


def format_alert_message(alert: Alert, settings: Settings) -> str:
    if settings.bot_language == "en":
        return (
            "Server alert\n"
            f"{alert.metric} high: {alert.value:.1f}% exceeded threshold "
            f"{alert.threshold:.1f}%\n"
            f"Suggested check: {alert.suggested_command} or /status"
        )
    return (
        "Cảnh báo server\n"
        f"{alert.metric} cao: {alert.value:.1f}% vượt ngưỡng {alert.threshold:.1f}%\n"
        f"Gợi ý kiểm tra: {alert.suggested_command} hoặc /status"
    )


async def send_due_system_alerts(
    *,
    bot: object,
    settings: Settings,
    audit: AuditStore,
    cooldown_state: AlertCooldownState,
    snapshot_provider: SnapshotProvider = get_system_snapshot,
    clock: Clock = time.time,
) -> int:
    snapshot = snapshot_provider()
    alerts = evaluate_system_alerts(snapshot, settings)
    now = clock()
    sent_count = 0

    for alert in alerts:
        if not cooldown_state.is_due(
            alert.key,
            now=now,
            cooldown_seconds=settings.alert_cooldown_seconds,
        ):
            continue

        text = redact_secrets(
            format_alert_message(alert, settings),
            known_secrets=[
                settings.telegram_bot_token.get_secret_value(),
                settings.openai_api_key.get_secret_value(),
            ],
        )
        for owner_id in settings.owner_ids:
            await bot.send_message(chat_id=owner_id, text=text)
            audit.record(
                AuditEvent(
                    user_id=owner_id,
                    role="owner",
                    action="alert.system",
                    target=alert.key,
                    result="sent",
                    confirmation_status="not_required",
                )
            )
            sent_count += 1
        cooldown_state.mark_sent(alert.key, now=now)

    return sent_count
