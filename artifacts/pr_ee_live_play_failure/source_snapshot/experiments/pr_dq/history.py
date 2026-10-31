"""One chronological history for IC and OOC messages."""

from __future__ import annotations

from experiments.pr_dq.envelope import PlayerMessage


class ConversationHistory:
    """Append-only log of the same message objects that were routed.

    Logical routing does not insert a second copy.
    """

    def __init__(self) -> None:
        self._messages: list[PlayerMessage] = []

    def append(self, message: PlayerMessage) -> None:
        if any(item.message_id == message.message_id for item in self._messages):
            raise ValueError(f"duplicate message id {message.message_id}")
        self._messages.append(message)

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self):
        return iter(self._messages)

    def ids(self) -> list[str]:
        return [item.message_id for item in self._messages]

    def messages(self) -> list[PlayerMessage]:
        return list(self._messages)

    def records(self) -> list[dict]:
        return [item.to_record() for item in self._messages]
