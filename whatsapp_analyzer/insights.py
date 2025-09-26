from __future__ import annotations

from typing import Dict, List, Tuple

WEEKDAY_LABELS = {
    0: "Segunda",
    1: "Terca",
    2: "Quarta",
    3: "Quinta",
    4: "Sexta",
    5: "Sabado",
    6: "Domingo",
}


_COMPONENT_LABELS = {
    "balance": "equilibrio",
    "engagement": "engajamento",
    "positive_emoji": "emojis positivos",
    "responsiveness": "tempo de resposta",
    "sentiment": "sentimento",
}


_DEF_COMPONENT_ORDER = [
    "balance",
    "engagement",
    "positive_emoji",
    "responsiveness",
    "sentiment",
]


def _format_participant_dominance(participant_share: Dict[str, float]) -> str:
    if not participant_share:
        return "Nenhuma mensagem de participantes foi encontrada."
    ordered = sorted(participant_share.items(), key=lambda item: item[1], reverse=True)
    lines: List[str] = []
    for sender, share in ordered:
        lines.append(f"- {sender} enviou {share:.1f}% das mensagens de participantes")
    return "\n".join(lines)


def _format_top_hours(hourly_distribution: Dict[int, int]) -> str:
    if not hourly_distribution:
        return "Distribuicao por hora indisponivel."
    top_hours = sorted(hourly_distribution.items(), key=lambda item: item[1], reverse=True)[:3]
    parts = [f"{hour:02d}h ({count} mensagens)" for hour, count in top_hours]
    return "Horarios mais ativos: " + ", ".join(parts)


def _format_top_weekday(weekday_distribution: Dict[int, int]) -> str:
    if not weekday_distribution:
        return "Distribuicao por dia indisponivel."
    weekday, count = max(weekday_distribution.items(), key=lambda item: item[1])
    label = WEEKDAY_LABELS.get(weekday, str(weekday))
    return f"Dia mais movimentado: {label} ({count} mensagens)"


def _format_top_words(top_words_per_participant: Dict[str, List[Tuple[str, int]]]) -> str:
    if not top_words_per_participant:
        return "Nenhuma palavra frequente identificada (talvez apenas mensagens do sistema)."
    sections: List[str] = []
    for sender, words in top_words_per_participant.items():
        if not words:
            continue
        top_words = ", ".join(f"{word} ({count})" for word, count in words[:5])
        sections.append(f"- {sender}: {top_words}")
    return "\n".join(sections)


def _format_response_times(response_times: Dict[str, float]) -> str:
    if not response_times:
        return "Dados insuficientes para calcular tempo de resposta."
    parts = []
    for sender, value in sorted(response_times.items(), key=lambda item: item[0]):
        if value is None:
            parts.append(f"- {sender}: N/D")
        else:
            parts.append(f"- {sender}: {value:.1f} min")
    return "\n".join(parts)


def _format_sentiment(sentiment_per_participant: Dict[str, Dict[str, float]]) -> str:
    if not sentiment_per_participant:
        return "Sentimento nao calculado."
    lines: List[str] = []
    for sender, data in sorted(sentiment_per_participant.items(), key=lambda item: item[0]):
        score = data.get("sentiment_score")
        positive = data.get("positive", 0)
        negative = data.get("negative", 0)
        if score is None:
            lines.append(f"- {sender}: sem dados suficientes")
        else:
            lines.append(f"- {sender}: score {score:+.2f} (palavras +{positive}/-{negative})")
    return "\n".join(lines)


def summarize_relationship_score(relationship_score: Dict[str, object]) -> str:
    if not relationship_score:
        return "Pontuacao de relacionamento indisponivel."

    score = relationship_score.get("score")
    components = relationship_score.get("components", {})
    inputs = relationship_score.get("inputs", {})

    lines: List[str] = []
    if score is not None:
        lines.append(f"Pontuacao do relacionamento: {score:.1f}/100.")
    if components:
        formatted_components: List[str] = []
        for key in _DEF_COMPONENT_ORDER:
            if key not in components:
                continue
            label = _COMPONENT_LABELS.get(key, key)
            formatted_components.append(f"{label} {components[key]:.0f}/100")
        for key, value in components.items():
            if key in _DEF_COMPONENT_ORDER:
                continue
            formatted_components.append(f"{key} {value:.0f}/100")
        if formatted_components:
            lines.append("Componentes: " + ", ".join(formatted_components) + ".")
    avg_per_day = inputs.get("average_messages_per_active_day")
    positive_ratio = inputs.get("positive_emoji_ratio")
    if avg_per_day is not None:
        lines.append(f"Media de mensagens por dia ativo: {avg_per_day}.")
    if positive_ratio is not None:
        lines.append(f"Proporcao de emojis positivos: {positive_ratio * 100:.1f}%.")
    response_avg = inputs.get("average_response_time_minutes")
    if response_avg is not None:
        lines.append(f"Tempo medio de resposta (min): {response_avg:.1f}.")
    sentiment_overall = inputs.get("overall_sentiment_score")
    if sentiment_overall is not None:
        lines.append(f"Sentimento geral (palavras): {sentiment_overall:+.2f} (escala -1 a 1).")
    return "\n".join(lines)


def build_insights(statistics: Dict[str, object]) -> str:
    """Gera um texto com observacoes interessantes com base nas estatisticas calculadas."""

    parts: List[str] = []

    total_messages = statistics.get("total_messages", 0)
    duration_days = statistics.get("duration_days", 0)
    if total_messages and duration_days:
        parts.append(
            f"Volume total: {total_messages} mensagens ao longo de {duration_days} dias (media de {total_messages / max(duration_days, 1):.1f}/dia)."
        )

    avg_response = statistics.get("overall_average_response_time_minutes")
    response_details = statistics.get("average_response_time_minutes", {})
    if avg_response is not None:
        parts.append(f"Tempo medio de resposta: {avg_response:.1f} min entre mensagens de participantes.")
        formatted = _format_response_times(response_details)
        if formatted:
            parts.append("Tempos individuais:\n" + formatted)

    overall_sentiment = statistics.get("overall_sentiment_score")
    sentiment_details = statistics.get("sentiment_per_participant", {})
    if overall_sentiment is not None:
        parts.append(f"Indice de sentimento (palavras positivas vs negativas): {overall_sentiment:+.2f}.")
        formatted_sentiment = _format_sentiment(sentiment_details)
        if formatted_sentiment:
            parts.append("Sentimento por participante:\n" + formatted_sentiment)

    participant_share = statistics.get("participant_share", {})
    if participant_share:
        parts.append("Participacao por pessoa:\n" + _format_participant_dominance(participant_share))

    hourly_distribution = statistics.get("hourly_distribution", {})
    if hourly_distribution:
        parts.append(_format_top_hours(hourly_distribution))

    weekday_distribution = statistics.get("weekday_distribution", {})
    if weekday_distribution:
        parts.append(_format_top_weekday(weekday_distribution))

    top_words_per_participant = statistics.get("top_words_per_participant", {})
    formatted_words = _format_top_words(top_words_per_participant)
    if formatted_words:
        parts.append("Palavras que mais aparecem:\n" + formatted_words)

    emoji_counts = statistics.get("emoji_counts", [])
    if emoji_counts:
        top_emojis = ", ".join(f"{emoji} ({count})" for emoji, count in emoji_counts[:5])
        parts.append(f"Emojis favoritos: {top_emojis}")

    if not parts:
        return "Nenhum insight relevante foi gerado a partir desta conversa."

    return "\n\n".join(parts)


def build_business_suggestions(statistics: Dict[str, object]) -> str:
    """Sugestoes de posicionamento e monetizacao pensando como gerente de produto."""

    suggestions: List[str] = []

    relationship = statistics.get("relationship_score", {})
    score = relationship.get("score")
    avg_per_day = statistics.get("average_messages_per_active_day", 0.0)
    duration_days = statistics.get("duration_days", 0)
    participants = statistics.get("participants", [])
    positive_ratio = statistics.get("positive_emoji_ratio", 0.0)
    response_avg = statistics.get("overall_average_response_time_minutes")
    overall_sentiment = statistics.get("overall_sentiment_score")

    if score is not None:
        if score >= 80:
            suggestions.append(
                "Lancar um plano premium focado em casais altamente engajados, oferecendo relatorios semanais e desafios personalizados para manter o nivel atual."
            )
        elif score >= 60:
            suggestions.append(
                "Criar um pacote de insights com alertas preventivos (ex: quedas de engajamento) e tarefas leves de reconexao para casais em evolucao."
            )
        else:
            suggestions.append(
                "Oferecer servicos de acompanhamento guiado (coaching ou terapeutas parceiros) para casais que precisam de suporte para melhorar a comunicacao."
            )

    if avg_per_day >= 25:
        suggestions.append(
            "Monetizar via assinatura com historicos diarios e lembretes contextuais, aproveitando o alto volume medio de mensagens."
        )
    else:
        suggestions.append(
            "Adicionar uma camada freemium com relatorios mensais e upsell para analises detalhadas quando o engajamento aumentar."
        )

    if response_avg is not None and response_avg > 45:
        suggestions.append(
            "Criar feature de nudges inteligentes que alertam quando as respostas estao demorando, oferecendo scripts prontos para reengajar." 
        )
    elif response_avg is not None and response_avg < 10:
        suggestions.append(
            "Testar gamificacao leve com metas de resposta rapida e recompensas digitais para casais altamente responsivos."
        )

    if len(participants) == 2 and positive_ratio >= 0.1:
        suggestions.append(
            "Explorar parcerias com marcas de bem-estar e experiencias para casais (ex: gift cards, descontos) usando o engajamento positivo como gatilho."
        )
    elif duration_days >= 180:
        suggestions.append(
            "Vender pacotes corporativos para terapeutas ou coaches, fornecendo dashboards de progresso para acompanhamentos de longo prazo."
        )

    if overall_sentiment is not None and overall_sentiment < -0.1:
        suggestions.append(
            "Adicionar alerta de humor/sentimento com encaminhamento para conteudos de mediação ou profissionais parceiros quando o tom ficar negativo."
        )
    elif overall_sentiment is not None and overall_sentiment > 0.2:
        suggestions.append(
            "Criar campanhas de marketing destacando historias positivas (mediante consentimento), posicionando o produto como reforcador de bons habitos." 
        )

    if not suggestions:
        return ""

    seen: set[str] = set()
    unique_suggestions: List[str] = []
    for item in suggestions:
        if item in seen:
            continue
        seen.add(item)
        unique_suggestions.append(item)

    return "\n".join(f"- {item}" for item in unique_suggestions)
