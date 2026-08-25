from __future__ import annotations

import asyncio
from typing import AsyncIterator

from google import genai
from google.genai import types

from app.config import settings
from app.llm.base import LLMProvider


class GeminiLLM(LLMProvider):
    def __init__(self) -> None:
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required.")
        self.client = genai.Client(api_key=settings.google_api_key)
        self.model = settings.gemini_model

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        prompt_parts = []
        for message in messages:
            role = message["role"]
            content = message["content"]
            if role == "system":
                prompt_parts.append(f"SYSTEM:\n{content}")
            elif role == "user":
                prompt_parts.append(f"USER:\n{content}")
            elif role == "assistant":
                prompt_parts.append(f"ASSISTANT:\n{content}")

        prompt = "\n\n".join(prompt_parts) + "\n\nASSISTANT:\n"

        def blocking_stream():
            return self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    max_output_tokens=300,
                ),
            )

        stream = await asyncio.to_thread(blocking_stream)

        for chunk in stream:
            text = getattr(chunk, "text", None)
            if text:
                yield text

    async def close(self) -> None:
        # The GenAI client does not require an explicit close for this use.
        return
