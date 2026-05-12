from __future__ import annotations

from typing import Any

from openai import OpenAI

from app.ai.prompts import SYSTEM_INSTRUCTIONS
from app.ai.schemas import openai_tool_definitions
from app.config import Settings


class ResponsesClient:
    def __init__(self, settings: Settings, client: OpenAI | None = None) -> None:
        self._settings = settings
        self._client = client or OpenAI(api_key=settings.openai_api_key.get_secret_value())

    def create_response(self, user_input: str) -> Any:
        return self._client.responses.create(
            model=self._settings.openai_model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=user_input,
            tools=openai_tool_definitions(),
        )
