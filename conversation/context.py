from __future__ import annotations

from app.config import settings


def build_messages(history: list[dict[str, str]]) -> list[dict[str, str]]:
    system = {"role": "system", "content": settings.system_prompt}
    return [system, *history[-settings.max_history_turns * 2 :]]
