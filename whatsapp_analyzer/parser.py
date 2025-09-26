from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Set

from .models import Conversation, Message

LINE_PATTERN = re.compile(
    r"^(?P<date>\d{1,2}/\d{1,2}/\d{2,4})[ ,]+(?P<time>\d{2}:\d{2}) - (?P<rest>.+)$"
)
SENDER_PATTERN = re.compile(r"^(?P<sender>[^:]+): (?P<message>.*)$")

DATE_FORMATS: Sequence[str] = ("%d/%m/%Y %H:%M", "%d/%m/%y %H:%M")


def _parse_timestamp(date_str: str, time_str: str) -> datetime:
    text = f"{date_str} {time_str}"
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    raise ValueError(f"Nao foi possivel interpretar a data: {text}")


def parse_exported_text(raw_text: str) -> Conversation:
    """Converte o conteudo bruto exportado pelo WhatsApp em uma conversa estruturada."""

    messages: List[Message] = []
    participants: Set[str] = set()

    current_timestamp: Optional[datetime] = None
    current_sender: Optional[str] = None
    current_is_system = False
    current_content_lines: List[str] = []

    def flush_current() -> None:
        nonlocal current_timestamp, current_sender, current_is_system, current_content_lines
        if current_timestamp is None:
            return
        content = "\n".join(line.rstrip() for line in current_content_lines).strip()
        messages.append(
            Message(
                timestamp=current_timestamp,
                sender=None if current_is_system else current_sender,
                content=content,
                is_system=current_is_system,
            )
        )
        current_timestamp = None
        current_sender = None
        current_is_system = False
        current_content_lines = []

    for raw_line in raw_text.splitlines():
        line = raw_line.rstrip("\ufeff")
        if not line:
            if current_content_lines:
                current_content_lines.append("")
            continue

        header_match = LINE_PATTERN.match(line)
        if header_match:
            flush_current()
            timestamp = _parse_timestamp(header_match.group("date"), header_match.group("time"))
            rest = header_match.group("rest").strip()
            sender_match = SENDER_PATTERN.match(rest)

            if sender_match:
                sender = sender_match.group("sender").strip()
                content = sender_match.group("message").strip()
                participants.add(sender)
                current_timestamp = timestamp
                current_sender = sender
                current_is_system = False
                current_content_lines = [content]
            else:
                current_timestamp = timestamp
                current_sender = None
                current_is_system = True
                current_content_lines = [rest]
            continue

        if current_timestamp is None:
            # Linha que nao pertence a nenhuma mensagem identificavel, ignora.
            continue

        current_content_lines.append(line)

    flush_current()

    ordered_participants = sorted(participants)
    return Conversation(participants=ordered_participants, messages=messages)
