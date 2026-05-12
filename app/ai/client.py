from __future__ import annotations

from typing import Any

from openai import OpenAI

from app.ai.prompts import system_instructions
from app.ai.schemas import openai_tool_definitions
from app.config import Settings


class ResponsesClient:
    def __init__(self, settings: Settings, client: OpenAI | None = None) -> None:
        self._settings = settings
        self._client = client or OpenAI(api_key=settings.openai_api_key.get_secret_value())

    def create_response(
        self,
        user_input: str,
        *,
        previous_response_id: str | None = None,
        tool_outputs: list[dict[str, Any]] | None = None,
    ) -> Any:
        input_payload: str | list[dict[str, Any]]
        if tool_outputs:
            input_payload = [
                {
                    "type": "function_call_output",
                    "call_id": output["call_id"],
                    "output": output["output"],
                }
                for output in tool_outputs
            ]
        else:
            input_payload = user_input

        request: dict[str, Any] = {
            "model": self._settings.openai_model,
            "instructions": system_instructions(self._settings.bot_language),
            "input": input_payload,
            "tools": openai_tool_definitions(),
        }
        if previous_response_id is not None:
            request["previous_response_id"] = previous_response_id
        return self._client.responses.create(**request)
