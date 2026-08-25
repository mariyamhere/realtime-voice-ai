from __future__ import annotations

from app.conversation.context import build_messages
from app.conversation.state import ConversationState


class ConversationManager:
    def __init__(self) -> None:
        self.state = ConversationState()

    def add_user(self, text: str) -> None:
        text = text.strip()
        if text:
            self.state.messages.append({"role": "user", "content": text})
            self.state.turn_id += 1

    def add_assistant(self, text: str) -> None:
        text = text.strip()
        if text:
            self.state.messages.append({"role": "assistant", "content": text})

    def messages_for_llm(self) -> list[dict[str, str]]:
        return build_messages(self.state.messages)

    def interrupt(self) -> None:
        self.state.interrupted = True

    def clear_interrupt(self) -> None:
        self.state.interrupted = False

    @property
    def turn_id(self) -> int:
        return self.state.turn_id
