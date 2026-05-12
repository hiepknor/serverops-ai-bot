from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from app.commands.ai import ask_command, summarize_log_command
from app.config import Settings
from app.core.audit import AuditStore


def make_settings(**overrides) -> Settings:
    data = {
        "telegram_bot_token": "123456:telegram-token-value",
        "openai_api_key": "sk-testtokenvalue",
        "owner_ids": [1],
        "admin_ids": [2],
        "viewer_ids": [3],
    }
    data.update(overrides)
    return Settings(**data)


def fake_tool_call(
    *,
    call_id: str = "call_1",
    name: str,
    arguments: str,
    response_id: str = "resp_1",
) -> dict[str, Any]:
    return {
        "id": response_id,
        "output": [
            {
                "type": "function_call",
                "call_id": call_id,
                "name": name,
                "arguments": arguments,
            }
        ],
    }


class FakeAIClient:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def create_response(
        self,
        user_input: str,
        *,
        previous_response_id: str | None = None,
        tool_outputs: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "user_input": user_input,
                "previous_response_id": previous_response_id,
                "tool_outputs": tool_outputs,
            }
        )
        return self.responses.pop(0)


class FakeMessage:
    def __init__(self) -> None:
        self.replies: list[str] = []

    async def reply_text(self, text: str) -> None:
        self.replies.append(text)


def make_update(user_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=user_id),
        effective_message=FakeMessage(),
    )


def make_context(
    *,
    args: list[str],
    settings: Settings,
    ai_client: FakeAIClient,
    audit: AuditStore,
) -> SimpleNamespace:
    return SimpleNamespace(
        args=args,
        application=SimpleNamespace(
            bot_data={
                "settings": settings,
                "ai_client": ai_client,
                "audit": audit,
            }
        ),
    )


def test_ask_command_rejects_unknown_user_before_ai_call(tmp_path) -> None:
    settings = make_settings()
    client = FakeAIClient([{"output_text": "should not be used"}])
    update = make_update(user_id=99)
    context = make_context(
        args=["server", "thế", "nào?"],
        settings=settings,
        ai_client=client,
        audit=AuditStore(tmp_path / "serverops.db"),
    )

    asyncio.run(ask_command(update, context))

    assert update.effective_message.replies == ["Từ chối truy cập."]
    assert client.calls == []


def test_summarize_log_command_redacts_secret_before_ai_call(tmp_path) -> None:
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "ok\nOPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz\nfailed\n",
        encoding="utf-8",
    )
    settings = make_settings(allowed_log_files=[f"app:{log_file}"])
    client = FakeAIClient([{"output_text": "Log có lỗi failed, token đã được ẩn."}])
    audit = AuditStore(tmp_path / "serverops.db")
    update = make_update(user_id=3)
    context = make_context(
        args=["app"],
        settings=settings,
        ai_client=client,
        audit=audit,
    )

    asyncio.run(summarize_log_command(update, context))

    assert update.effective_message.replies == ["Log có lỗi failed, token đã được ẩn."]
    assert "failed" in client.calls[0]["user_input"]
    assert "sk-abcdefghijklmnopqrstuvwxyz" not in client.calls[0]["user_input"]
    assert "[REDACTED]" in client.calls[0]["user_input"]
    rows = audit.list_recent()
    assert rows[0]["command"] == "summarize_log"
    assert rows[0]["action"] == "ai_tool.read_log"
    assert rows[0]["target"] == "app"
    assert rows[0]["result"] == "success"


def test_ask_command_routes_read_log_tool_call_through_router(tmp_path) -> None:
    log_file = tmp_path / "app.log"
    log_file.write_text("line 1\nfailed here\n", encoding="utf-8")
    settings = make_settings(allowed_log_files=[f"app:{log_file}"])
    client = FakeAIClient(
        [
            fake_tool_call(name="read_log", arguments='{"target": "app", "lines": 20}'),
            {"output_text": "Log app có lỗi failed."},
        ]
    )
    audit = AuditStore(tmp_path / "serverops.db")
    update = make_update(user_id=3)
    context = make_context(
        args=["đọc", "log", "app"],
        settings=settings,
        ai_client=client,
        audit=audit,
    )

    asyncio.run(ask_command(update, context))

    assert update.effective_message.replies == ["Log app có lỗi failed."]
    assert len(client.calls) == 2
    assert client.calls[1]["previous_response_id"] == "resp_1"
    tool_output = client.calls[1]["tool_outputs"][0]
    assert tool_output["call_id"] == "call_1"
    assert tool_output["tool_name"] == "read_log"
    assert tool_output["result"]["ok"] is True
    assert tool_output["result"]["data"]["target"] == "app"


def test_ask_command_audits_unknown_tool_rejection(tmp_path) -> None:
    settings = make_settings()
    client = FakeAIClient(
        [
            fake_tool_call(name="run_shell", arguments='{"command": "whoami"}'),
            {"output_text": "Không thể dùng tool không được phê duyệt."},
        ]
    )
    audit = AuditStore(tmp_path / "serverops.db")
    update = make_update(user_id=3)
    context = make_context(
        args=["chạy", "whoami"],
        settings=settings,
        ai_client=client,
        audit=audit,
    )

    asyncio.run(ask_command(update, context))

    assert update.effective_message.replies == [
        "Không thể dùng tool không được phê duyệt."
    ]
    tool_output = client.calls[1]["tool_outputs"][0]
    assert tool_output["tool_name"] == "run_shell"
    assert tool_output["result"]["ok"] is False
    rows = audit.list_recent()
    assert rows[0]["user_id"] == 3
    assert rows[0]["role"] == "viewer"
    assert rows[0]["command"] == "ask"
    assert rows[0]["action"] == "ai_tool.run_shell"
    assert rows[0]["result"] == "rejected"
    assert rows[0]["error"] == "unknown tool: run_shell"


def test_ask_command_returns_vietnamese_without_changing_machine_tokens(tmp_path) -> None:
    settings = make_settings()
    client = FakeAIClient(
        [
            {
                "output_text": (
                    "Nên kiểm tra bằng /docker_logs app và giữ nguyên "
                    "CONFIRM restart_service:nginx."
                )
            }
        ]
    )
    update = make_update(user_id=3)
    context = make_context(
        args=["cần", "kiểm", "tra", "gì?"],
        settings=settings,
        ai_client=client,
        audit=AuditStore(tmp_path / "serverops.db"),
    )

    asyncio.run(ask_command(update, context))

    assert update.effective_message.replies == [
        "Nên kiểm tra bằng /docker_logs app và giữ nguyên CONFIRM restart_service:nginx."
    ]
