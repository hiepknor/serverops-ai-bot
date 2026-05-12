from __future__ import annotations

import asyncio

from app.bot import build_application
from app.config import Settings
from app.core.alerts import (
    AlertCooldownState,
    evaluate_system_alerts,
    send_due_system_alerts,
)
from app.core.audit import AuditStore
from app.tools.system_tools import SystemSnapshot


def make_settings(**overrides) -> Settings:
    data = {
        "telegram_bot_token": "123456:telegram-token-value",
        "openai_api_key": "sk-testtokenvalue",
        "owner_ids": [1, 2],
        "admin_ids": [3],
        "viewer_ids": [4],
    }
    data.update(overrides)
    return Settings(**data)


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []

    async def send_message(self, *, chat_id: int, text: str) -> None:
        self.messages.append((chat_id, text))


def test_evaluate_system_alerts_uses_readonly_thresholds() -> None:
    settings = make_settings(
        alert_cpu_percent=90,
        alert_ram_percent=90,
        alert_disk_percent=90,
    )
    snapshot = SystemSnapshot(
        cpu_percent=91.0,
        memory_percent=80.0,
        disk_percent=95.0,
        uptime_seconds=100,
    )

    alerts = evaluate_system_alerts(snapshot, settings)

    assert [alert.key for alert in alerts] == ["system.cpu", "system.disk"]
    assert [alert.suggested_command for alert in alerts] == ["/cpu", "/disk"]


def test_send_due_system_alerts_sends_only_to_owners_and_audits(tmp_path) -> None:
    settings = make_settings(alert_cpu_percent=50)
    audit = AuditStore(tmp_path / "serverops.db")
    bot = FakeBot()
    state = AlertCooldownState()

    sent_count = asyncio.run(
        send_due_system_alerts(
            bot=bot,
            settings=settings,
            audit=audit,
            cooldown_state=state,
            snapshot_provider=lambda: SystemSnapshot(
                cpu_percent=51.0,
                memory_percent=10.0,
                disk_percent=10.0,
                uptime_seconds=100,
            ),
            clock=lambda: 1000.0,
        )
    )

    assert sent_count == 2
    assert [chat_id for chat_id, _ in bot.messages] == [1, 2]
    assert all("Cảnh báo server" in text for _, text in bot.messages)
    assert all("/cpu hoặc /status" in text for _, text in bot.messages)
    rows = audit.list_recent()
    assert len(rows) == 2
    assert {row["user_id"] for row in rows} == {1, 2}
    assert all(row["action"] == "alert.system" for row in rows)
    assert all(row["target"] == "system.cpu" for row in rows)


def test_send_due_system_alerts_respects_cooldown(tmp_path) -> None:
    settings = make_settings(alert_cpu_percent=50, alert_cooldown_seconds=900)
    audit = AuditStore(tmp_path / "serverops.db")
    bot = FakeBot()
    state = AlertCooldownState()
    snapshot = SystemSnapshot(
        cpu_percent=51.0,
        memory_percent=10.0,
        disk_percent=10.0,
        uptime_seconds=100,
    )

    first = asyncio.run(
        send_due_system_alerts(
            bot=bot,
            settings=settings,
            audit=audit,
            cooldown_state=state,
            snapshot_provider=lambda: snapshot,
            clock=lambda: 1000.0,
        )
    )
    second = asyncio.run(
        send_due_system_alerts(
            bot=bot,
            settings=settings,
            audit=audit,
            cooldown_state=state,
            snapshot_provider=lambda: snapshot,
            clock=lambda: 1200.0,
        )
    )

    assert first == 2
    assert second == 0
    assert len(bot.messages) == 2
    assert len(audit.list_recent()) == 2


def test_disabled_alerts_do_not_register_scheduler_jobs(tmp_path) -> None:
    settings = make_settings(enable_alerts=False)
    audit = AuditStore(tmp_path / "serverops.db")

    application = build_application(settings, audit=audit)

    assert "alert_cooldown_state" in application.bot_data
    if application.job_queue is not None:
        assert application.job_queue.jobs() == ()


def test_enabled_alerts_register_scheduler_job(tmp_path) -> None:
    settings = make_settings(enable_alerts=True)
    audit = AuditStore(tmp_path / "serverops.db")
    application = build_application(settings, audit=audit)

    assert application.job_queue is not None
    jobs = application.job_queue.jobs()
    assert len(jobs) == 1
    assert jobs[0].name == "system_alerts"
