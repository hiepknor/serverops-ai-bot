from __future__ import annotations

from typing import Any

from app.ai.service import answer_operational_question, summarize_log_context
from app.config import Settings
from app.core.security import Role
from app.tools.system_tools import SystemSnapshot


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


def test_answer_operational_question_returns_text_without_tools() -> None:
    client = FakeAIClient([{"output_text": "Máy chủ đang ổn."}])

    answer = answer_operational_question(
        question="server thế nào?",
        role=Role.VIEWER,
        settings=make_settings(),
        client=client,
    )

    assert answer.text == "Máy chủ đang ổn."
    assert answer.tool_results == []
    assert len(client.calls) == 1


def test_answer_operational_question_routes_model_tool_calls(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.ai.router.get_system_snapshot",
        lambda: SystemSnapshot(
            cpu_percent=10.0,
            memory_percent=20.0,
            disk_percent=30.0,
            uptime_seconds=40,
        ),
    )
    client = FakeAIClient(
        [
            {
                "id": "resp_1",
                "output": [
                    {
                        "type": "function_call",
                        "call_id": "call_1",
                        "name": "get_system_status",
                        "arguments": "{}",
                    }
                ],
            },
            {"output_text": "CPU 10%, RAM 20%, Disk 30%."},
        ]
    )

    answer = answer_operational_question(
        question="kiểm tra server",
        role=Role.VIEWER,
        settings=make_settings(),
        client=client,
    )

    assert answer.text == "CPU 10%, RAM 20%, Disk 30%."
    assert len(answer.tool_results) == 1
    assert answer.tool_results[0]["tool_name"] == "get_system_status"
    assert client.calls[1]["previous_response_id"] == "resp_1"
    assert client.calls[1]["tool_outputs"][0]["call_id"] == "call_1"


def test_summarize_log_context_reads_allowlisted_sanitized_log(tmp_path) -> None:
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "ok\nOPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz\nfailed\n",
        encoding="utf-8",
    )
    client = FakeAIClient([{"output_text": "Log có lỗi failed, token đã được ẩn."}])

    answer = summarize_log_context(
        target="app",
        role=Role.VIEWER,
        settings=make_settings(allowed_log_files=[f"app:{log_file}"]),
        client=client,
    )

    assert answer.text == "Log có lỗi failed, token đã được ẩn."
    assert "failed" in client.calls[0]["user_input"]
    assert "sk-abcdefghijklmnopqrstuvwxyz" not in client.calls[0]["user_input"]
    assert "[REDACTED]" in client.calls[0]["user_input"]
    assert answer.tool_results[0]["tool_name"] == "read_log"


def test_summarize_log_context_rejects_unallowlisted_log_before_ai_call() -> None:
    client = FakeAIClient([{"output_text": "should not be used"}])

    answer = summarize_log_context(
        target="shadow",
        role=Role.VIEWER,
        settings=make_settings(allowed_log_files=[]),
        client=client,
    )

    assert answer.text.startswith("Không thể tạo ngữ cảnh AI:")
    assert "'shadow' is not allowlisted" in answer.text
    assert client.calls == []
