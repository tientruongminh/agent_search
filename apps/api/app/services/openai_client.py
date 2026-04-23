from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIJsonClient:
    def __init__(self) -> None:
        self.enabled = bool(settings.openai_api_key)
        self.client = OpenAI(api_key=settings.openai_api_key) if self.enabled else None

    def generate_json(self, *, system_prompt: str, user_prompt: str, schema_name: str, schema: dict[str, Any]) -> dict[str, Any] | None:
        if not self.enabled or self.client is None:
            return None
        try:
            response = self.client.responses.create(
                model=settings.openai_model,
                input=[
                    {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                    {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "schema": schema,
                        "strict": True,
                    }
                },
            )
            if getattr(response, "output_text", None):
                return json.loads(response.output_text)
            return None
        except Exception:
            logger.exception("OpenAI structured output failed")
            return None

