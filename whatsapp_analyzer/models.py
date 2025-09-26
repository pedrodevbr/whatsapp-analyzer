from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(slots=True)
class Message:
    """Representa uma mensagem individual dentro de uma conversa."""

    timestamp: datetime
    sender: Optional[str]
    content: str
    is_system: bool = False

    def word_count(self) -> int:
        return len(self.content.split())

    def char_count(self) -> int:
        return len(self.content)


@dataclass
class Conversation:
    """Container com metadados e mensagens de uma conversa."""

    participants: List[str]
    messages: List[Message]
    metadata: Dict[str, str] = field(default_factory=dict)

    def participant_message_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {participant: 0 for participant in self.participants}
        for message in self.messages:
            if message.sender:
                counts.setdefault(message.sender, 0)
                counts[message.sender] += 1
        return counts
