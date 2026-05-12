from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.ai.client import ResponsesClient
from app.ai.router import AIToolAuditContext, route_tool_call
from app.config import Settings
from app.core.audit import AuditStore
from app.core.security import Role, redact_secrets


class AIClient(Protocol):
    def create_response(
        self,
        user_input: str,
        *,
        previous_response_id: str | None = None,
        tool_outputs: list[dict[str, Any]] | None = None,
    ) -> Any:
        pass


@dataclass(frozen=True)
class AIAnswer:
    text: str
    tool_results: list[dict[str, Any]]


def answer_operational_question(
    *,
    question: str,
    role: Role,
    settings: Settings,
    client: AIClient | None = None,
    audit: AuditStore | None = None,
    audit_context: AIToolAuditContext | None = None,
) -> AIAnswer:
    ai_client = client or ResponsesClient(settings)
    response = ai_client.create_response(question)
    tool_outputs = _route_tool_calls(
        response,
        role=role,
        settings=settings,
        audit=audit,
        audit_context=audit_context,
    )
    if tool_outputs:
        response = ai_client.create_response(
            question,
            previous_response_id=_response_id(response),
            tool_outputs=tool_outputs,
        )
    text = _extract_text(response) or _fallback_text(settings)
    return AIAnswer(
        text=_sanitize_text(text, settings),
        tool_results=tool_outputs,
    )


def summarize_log_context(
    *,
    target: str,
    role: Role,
    settings: Settings,
    client: AIClient | None = None,
    incident_mode: bool = False,
    audit: AuditStore | None = None,
    audit_context: AIToolAuditContext | None = None,
) -> AIAnswer:
    context_result = route_tool_call(
        tool_name="read_log",
        arguments={"target": target, "lines": settings.log_tail_lines},
        role=role,
        settings=settings,
        audit=audit,
        audit_context=audit_context,
    )
    if not context_result.ok:
        return AIAnswer(text=_tool_error_text(context_result.error, settings), tool_results=[])

    content = str(context_result.data.get("content", ""))
    if incident_mode:
        prompt = (
            "Phân tích log sau theo dạng incident report ngắn gọn bằng tiếng Việt. "
            "Nêu dấu hiệu chính, nguyên nhân có khả năng, mức độ ảnh hưởng, "
            "và bước kiểm tra an toàn tiếp theo. Không đề xuất lệnh phá hoại.\n\n"
            f"Log target: {target}\n"
            f"Log content:\n{content}"
        )
    else:
        prompt = (
            "Tóm tắt log sau bằng tiếng Việt cho người vận hành server. "
            "Nêu lỗi đáng chú ý và bước kiểm tra an toàn tiếp theo nếu cần.\n\n"
            f"Log target: {target}\n"
            f"Log content:\n{content}"
        )
    answer = answer_operational_question(
        question=prompt,
        role=role,
        settings=settings,
        client=client,
        audit=audit,
        audit_context=audit_context,
    )
    return AIAnswer(
        text=answer.text,
        tool_results=[context_result.model_dump(), *answer.tool_results],
    )


def _route_tool_calls(
    response: Any,
    *,
    role: Role,
    settings: Settings,
    audit: AuditStore | None,
    audit_context: AIToolAuditContext | None,
) -> list[dict[str, Any]]:
    tool_outputs = []
    for call in _extract_tool_calls(response):
        result = route_tool_call(
            tool_name=call["name"],
            arguments=call["arguments"],
            role=role,
            settings=settings,
            audit=audit,
            audit_context=audit_context,
        )
        tool_outputs.append(
            {
                "call_id": call["call_id"],
                "output": result.model_dump_json(),
                "tool_name": call["name"],
                "result": result.model_dump(),
            }
        )
    return tool_outputs


def _extract_tool_calls(response: Any) -> list[dict[str, Any]]:
    calls = []
    for item in _response_output(response):
        item_type = _read_field(item, "type")
        if item_type not in {"function_call", "tool_call"}:
            continue
        name = _read_field(item, "name") or _read_field(item, "function", "name")
        arguments = _read_field(item, "arguments") or _read_field(item, "function", "arguments")
        call_id = _read_field(item, "call_id") or _read_field(item, "id")
        if not name or not call_id:
            continue
        calls.append(
            {
                "call_id": str(call_id),
                "name": str(name),
                "arguments": arguments,
            }
        )
    return calls


def _extract_text(response: Any) -> str:
    output_text = _read_field(response, "output_text")
    if output_text:
        return str(output_text)

    parts = []
    for item in _response_output(response):
        if _read_field(item, "type") == "message":
            for content in _read_field(item, "content") or []:
                text = _read_field(content, "text")
                if text:
                    parts.append(str(text))
        text = _read_field(item, "text")
        if text:
            parts.append(str(text))
    return "\n".join(parts).strip()


def _response_output(response: Any) -> list[Any]:
    output = _read_field(response, "output")
    if isinstance(output, list):
        return output
    return []


def _response_id(response: Any) -> str | None:
    response_id = _read_field(response, "id")
    return str(response_id) if response_id else None


def _read_field(value: Any, *path: str) -> Any:
    current = value
    for key in path:
        current = current.get(key) if isinstance(current, dict) else getattr(current, key, None)
        if current is None:
            return None
    return current


def _sanitize_text(text: str, settings: Settings) -> str:
    return redact_secrets(
        text,
        known_secrets=[
            settings.telegram_bot_token.get_secret_value(),
            settings.openai_api_key.get_secret_value(),
        ],
    )


def _fallback_text(settings: Settings) -> str:
    if settings.bot_language == "en":
        return "The AI did not return a usable response."
    return "AI không trả về phản hồi có thể sử dụng."


def _tool_error_text(error: str | None, settings: Settings) -> str:
    safe_error = _sanitize_text(error or "unknown error", settings)
    if settings.bot_language == "en":
        return f"Unable to build AI context: {safe_error}"
    return f"Không thể tạo ngữ cảnh AI: {safe_error}"
