from __future__ import annotations

from dataclasses import dataclass, field

@dataclass
class ConversationState:
    messages: list[dict[str, str]] = field(default_factory=list)
    turn_id: int = 0
    interrupted: bool = False
    active_response_id: str | None = None
