from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from .models import Conversation, Message

WORD_PATTERN = re.compile(r"\b[\w']+\b", re.UNICODE)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002700-\U000027BF"
    "]"
)
STOPWORDS = {
    "a",
    "ao",
    "aos",
    "arquivo",
    "as",
    "ate",
    "audio",
    "com",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "entao",
    "essa",
    "esse",
    "estao",
    "esta",
    "ficar",
    "foi",
    "imagem",
    "isso",
    "ja",
    "la",
    "mas",
    "midia",
    "na",
    "nas",
    "nao",
    "nos",
    "num",
    "numa",
    "oculta",
    "oculto",
    "omitida",
    "omitido",
    "o",
    "os",
    "para",
    "por",
    "pra",
    "pro",
    "que",
    "quem",
    "se",
    "sem",
    "sim",
    "sou",
    "sua",
    "suas",
    "ta",
    "tava",
    "tem",
    "tudo",
    "um",
    "uma",
    "vou",
}
IGNORED_NORMALIZED_MESSAGES = {
    "arquivo de midia oculta",
    "<arquivo de midia oculta>",
    "imagem omitida",
    "<imagem omitida>",
    "audio omitido",
    "<audio omitido>",
}
POSITIVE_EMOJIS = {
    "😍",
    "❤",
    "❤️",
    "🥰",
    "😘",
    "😊",
    "😁",
    "💕",
    "💞",
    "💖",
    "💗",
    "💓",
    "💘",
    "☺",
    "😄",
    "😃",
    "😆",
    "🤗",
}
POSITIVE_WORDS = {
    "amor",
    "amo",
    "amada",
    "amado",
    "amiga",
    "amigo",
    "beijo",
    "carinho",
    "caro",
    "carinhosa",
    "carinhoso",
    "feliz",
    "fofa",
    "fofo",
    "gostei",
    "grata",
    "grato",
    "linda",
    "lindo",
    "obrigada",
    "obrigado",
    "otimo",
    "perfeito",
    "querida",
    "querido",
    "saudade",
    "sucesso",
}
NEGATIVE_WORDS = {
    "briga",
    "cansada",
    "cansado",
    "chateada",
    "chateado",
    "erro",
    "irritada",
    "irritado",
    "magoada",
    "magoado",
    "medo",
    "problema",
    "raiva",
    "sozinha",
    "sozinho",
    "stress",
    "triste",
}


def _normalize_word(word: str) -> str:
    decomposed = unicodedata.normalize("NFKD", word)
    ascii_only = decomposed.encode("ASCII", "ignore").decode("ASCII")
    return ascii_only.strip("'")


def _normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _should_ignore_for_word_counts(text: str) -> bool:
    normalized = _normalize_text(text).strip()
    return normalized in IGNORED_NORMALIZED_MESSAGES


def _count_words(messages: Iterable[Message]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for message in messages:
        if _should_ignore_for_word_counts(message.content):
            continue
        for match in WORD_PATTERN.finditer(message.content.lower()):
            normalized = _normalize_word(match.group())
            if not normalized or normalized in STOPWORDS:
                continue
            counts[normalized] += 1
    return counts


def _count_emojis(messages: Iterable[Message]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for message in messages:
        for emoji in EMOJI_PATTERN.findall(message.content):
            counts[emoji] += 1
    return counts


def _compute_sentiment(per_participant: Dict[str, List[Message]]) -> Dict[str, Dict[str, float]]:
    sentiment: Dict[str, Dict[str, float]] = {}
    for sender, personal_messages in per_participant.items():
        positive = 0
        negative = 0
        for message in personal_messages:
            if _should_ignore_for_word_counts(message.content):
                continue
            for match in WORD_PATTERN.finditer(message.content.lower()):
                normalized = _normalize_word(match.group())
                if normalized in POSITIVE_WORDS:
                    positive += 1
                elif normalized in NEGATIVE_WORDS:
                    negative += 1
        total = positive + negative
        score = ((positive - negative) / total) if total else 0.0
        sentiment[sender] = {
            "positive": positive,
            "negative": negative,
            "sentiment_score": round(score, 3) if total else 0.0,
        }
    return sentiment


def _compute_response_times(messages: List[Message]) -> Dict[str, List[float]]:
    response_times: Dict[str, List[float]] = defaultdict(list)
    previous_message: Optional[Message] = None

    for message in messages:
        if message.sender is None:
            continue
        if previous_message and previous_message.sender != message.sender and previous_message.sender is not None:
            delta = (message.timestamp - previous_message.timestamp).total_seconds() / 60.0
            if delta >= 0:
                response_times[message.sender].append(delta)
        previous_message = message

    return response_times


def _compute_relationship_score(
    messages_per_participant: Dict[str, int],
    participant_share: Dict[str, float],
    participant_messages: List[Message],
    emoji_counts: Counter[str],
    active_days: int,
    average_response_minutes: Dict[str, Optional[float]],
    overall_average_response: Optional[float],
    sentiment_per_participant: Dict[str, Dict[str, float]],
    overall_sentiment_score: Optional[float],
) -> Dict[str, object]:
    if not participant_messages:
        return {
            "score": 0.0,
            "scale": "0-100",
            "components": {},
            "inputs": {},
        }

    if participant_share:
        largest_share = max(participant_share.values())
        smallest_share = min(participant_share.values())
        balance_score = max(0.0, 1.0 - ((largest_share - smallest_share) / 100.0))
    else:
        balance_score = 0.5

    active_days = max(active_days, 1)
    avg_messages_per_active_day = len(participant_messages) / active_days
    engagement_score = min(avg_messages_per_active_day / 40.0, 1.0)

    total_emojis = sum(emoji_counts.values())
    positive_emojis = sum(count for emoji, count in emoji_counts.items() if emoji in POSITIVE_EMOJIS)
    positive_ratio = positive_emojis / total_emojis if total_emojis else 0.0
    positive_emoji_score = min(positive_ratio / 0.25, 1.0)

    if overall_average_response is None:
        responsiveness_score = 0.5
    elif overall_average_response <= 5:
        responsiveness_score = 1.0
    elif overall_average_response >= 60:
        responsiveness_score = 0.0
    else:
        responsiveness_score = max(0.0, 1.0 - ((overall_average_response - 5) / 55.0))

    if overall_sentiment_score is None:
        sentiment_component = 0.5
    else:
        normalized_sentiment = (max(-1.0, min(overall_sentiment_score, 1.0)) + 1.0) / 2.0
        sentiment_component = normalized_sentiment

    final_score = (
        (balance_score * 0.30)
        + (engagement_score * 0.25)
        + (positive_emoji_score * 0.20)
        + (responsiveness_score * 0.15)
        + (sentiment_component * 0.10)
    ) * 100.0

    return {
        "score": round(final_score, 1),
        "scale": "0-100",
        "components": {
            "balance": round(balance_score * 100, 1),
            "engagement": round(engagement_score * 100, 1),
            "positive_emoji": round(positive_emoji_score * 100, 1),
            "responsiveness": round(responsiveness_score * 100, 1),
            "sentiment": round(sentiment_component * 100, 1),
        },
        "inputs": {
            "participant_share": participant_share,
            "average_messages_per_active_day": round(avg_messages_per_active_day, 2),
            "positive_emoji_ratio": round(positive_ratio, 3),
            "average_response_time_minutes": overall_average_response,
            "average_response_time_per_participant": average_response_minutes,
            "overall_sentiment_score": overall_sentiment_score,
            "sentiment_per_participant": sentiment_per_participant,
            "total_emojis": total_emojis,
        },
    }


def compute_statistics(conversation: Conversation) -> Dict[str, object]:
    messages = [message for message in conversation.messages if message.content]

    total_messages = len(messages)
    system_messages = sum(1 for m in messages if m.is_system)
    participant_messages = [m for m in messages if not m.is_system]

    per_participant: Dict[str, List[Message]] = defaultdict(list)
    for message in participant_messages:
        if message.sender is None:
            continue
        per_participant[message.sender].append(message)

    words_per_participant = {
        sender: _count_words(personal_messages)
        for sender, personal_messages in per_participant.items()
    }

    top_words_per_participant = {
        sender: counter.most_common(10) for sender, counter in words_per_participant.items()
    }

    emoji_counts = _count_emojis(participant_messages)
    hourly_distribution: Dict[int, int] = defaultdict(int)
    weekday_distribution: Dict[int, int] = defaultdict(int)
    messages_per_day: Dict[str, int] = defaultdict(int)

    for message in participant_messages:
        hourly_distribution[message.timestamp.hour] += 1
        weekday_distribution[message.timestamp.weekday()] += 1
        messages_per_day[message.timestamp.strftime("%Y-%m-%d")] += 1

    chars_per_participant = {
        sender: sum(m.char_count() for m in personal_messages) / max(1, len(personal_messages))
        for sender, personal_messages in per_participant.items()
    }

    words_per_message = {
        sender: sum(m.word_count() for m in personal_messages) / max(1, len(personal_messages))
        for sender, personal_messages in per_participant.items()
    }

    first_timestamp: Optional[datetime] = messages[0].timestamp if messages else None
    last_timestamp: Optional[datetime] = messages[-1].timestamp if messages else None

    messages_per_participant = {
        sender: len(personal_messages) for sender, personal_messages in per_participant.items()
    }

    participant_share = {
        sender: (count / total_messages) * 100 if total_messages else 0.0
        for sender, count in messages_per_participant.items()
    }

    active_days = len(messages_per_day)
    average_messages_per_active_day = (
        len(participant_messages) / active_days if active_days else float(len(participant_messages))
    )

    response_times = _compute_response_times(participant_messages)
    average_response_minutes: Dict[str, Optional[float]] = {}
    for sender, times in response_times.items():
        if times:
            average_response_minutes[sender] = round(sum(times) / len(times), 2)
        else:
            average_response_minutes[sender] = None
    valid_response_averages = [value for value in average_response_minutes.values() if value is not None]
    overall_average_response = (
        round(sum(valid_response_averages) / len(valid_response_averages), 2)
        if valid_response_averages
        else None
    )

    sentiment_per_participant = _compute_sentiment(per_participant)
    sentiment_scores = [data["sentiment_score"] for data in sentiment_per_participant.values() if data]
    overall_sentiment_score = (
        round(sum(sentiment_scores) / len(sentiment_scores), 3)
        if sentiment_scores
        else None
    )

    relationship_score = _compute_relationship_score(
        messages_per_participant,
        participant_share,
        participant_messages,
        emoji_counts,
        active_days,
        average_response_minutes,
        overall_average_response,
        sentiment_per_participant,
        overall_sentiment_score,
    )

    positive_emoji_ratio = relationship_score.get("inputs", {}).get("positive_emoji_ratio", 0.0)

    return {
        "total_messages": total_messages,
        "system_messages": system_messages,
        "participant_messages": len(participant_messages),
        "participants": sorted(conversation.participants),
        "messages_per_participant": messages_per_participant,
        "participant_share": participant_share,
        "average_chars_per_message": chars_per_participant,
        "average_words_per_message": words_per_message,
        "top_words_per_participant": top_words_per_participant,
        "emoji_counts": emoji_counts.most_common(15),
        "hourly_distribution": dict(sorted(hourly_distribution.items())),
        "weekday_distribution": dict(sorted(weekday_distribution.items())),
        "messages_per_day": dict(sorted(messages_per_day.items())),
        "first_message_at": first_timestamp,
        "last_message_at": last_timestamp,
        "duration_days": (
            (last_timestamp - first_timestamp).days + 1 if first_timestamp and last_timestamp else 0
        ),
        "active_days_with_messages": active_days,
        "average_messages_per_active_day": round(average_messages_per_active_day, 2),
        "positive_emoji_ratio": positive_emoji_ratio,
        "average_response_time_minutes": average_response_minutes,
        "overall_average_response_time_minutes": overall_average_response,
        "sentiment_per_participant": sentiment_per_participant,
        "overall_sentiment_score": overall_sentiment_score,
        "relationship_score": relationship_score,
    }
