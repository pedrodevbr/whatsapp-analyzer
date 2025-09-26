from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except ValueError:
        pass

from .analysis import compute_statistics
from .insights import build_business_suggestions, build_insights, summarize_relationship_score
from .loader import read_chat_from_zip
from .parser import parse_exported_text

try:
    from .llm import generate_recommendations
except Exception:  # pragma: no cover - LLM opcional
    generate_recommendations = None


def _format_timestamp(value: datetime | None) -> str:
    return value.strftime("%d/%m/%Y %H:%M") if isinstance(value, datetime) else "-"


def _print_basic_summary(statistics: Dict[str, Any]) -> None:
    print("=== Resumo da conversa ===")
    print(f"Mensagens totais: {statistics['total_messages']}")
    print(f"Mensagens de participantes: {statistics['participant_messages']}")
    print(f"Mensagens do sistema: {statistics['system_messages']}")
    print(f"Inicio: {_format_timestamp(statistics.get('first_message_at'))}")
    print(f"Fim: {_format_timestamp(statistics.get('last_message_at'))}")
    print(f"Duracao (dias): {statistics.get('duration_days', 0)}")

    print("\nMensagens por participante:")
    participant_counts = statistics.get("messages_per_participant", {})
    participant_share = statistics.get("participant_share", {})
    for sender, count in sorted(participant_counts.items(), key=lambda item: item[1], reverse=True):
        share = participant_share.get(sender, 0.0)
        print(f"- {sender}: {count} mensagens ({share:.1f}% do total)")

    print("\nTop emojis:")
    emoji_counts = statistics.get("emoji_counts", [])
    if emoji_counts:
        for emoji, count in emoji_counts[:5]:
            try:
                print(f"- {emoji}: {count}")
            except UnicodeEncodeError:
                print(f"- unicode {emoji.encode('unicode_escape').decode('ascii')}: {count}")
    else:
        print("Nenhum emoji detectado.")

    average_response_overall = statistics.get("overall_average_response_time_minutes")
    average_response_details = statistics.get("average_response_time_minutes", {})
    if average_response_overall is not None or average_response_details:
        print("\nTempo medio de resposta (min):")
        if average_response_overall is not None:
            print(f"- Geral: {average_response_overall:.1f}")
        for sender, value in sorted(average_response_details.items(), key=lambda item: item[0]):
            label = f"{value:.1f}" if value is not None else "N/D"
            print(f"- {sender}: {label}")

    overall_sentiment = statistics.get("overall_sentiment_score")
    sentiment_per_participant = statistics.get("sentiment_per_participant", {})
    if overall_sentiment is not None or sentiment_per_participant:
        print("\nSentimento (palavras, escala -1 a 1):")
        if overall_sentiment is not None:
            print(f"- Geral: {overall_sentiment:+.2f}")
        for sender, data in sorted(sentiment_per_participant.items(), key=lambda item: item[0]):
            score = data.get("sentiment_score")
            if score is None:
                label = "sem dados"
            else:
                label = f"{score:+.2f}"
            print(f"- {sender}: {label}")

    print("\nDistribuicao por hora:")
    hourly_distribution = statistics.get("hourly_distribution", {})
    if hourly_distribution:
        for hour, count in hourly_distribution.items():
            print(f"- {hour:02d}h: {count}")
    else:
        print("Nao ha dados suficientes.")


def app(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analisa conversas exportadas do WhatsApp.")
    parser.add_argument("zip_path", type=Path, help="Caminho para o arquivo ZIP exportado do WhatsApp")
    parser.add_argument(
        "--chat-file",
        dest="chat_filename",
        help="Nome exato do arquivo .txt dentro do ZIP (opcional)",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Envia dados para uma LLM (requer variavel OPENAI_API_KEY)",
    )
    parser.add_argument("--llm-model", default=None, help="Modelo da LLM a ser utilizado")
    parser.add_argument(
        "--llm-temperature",
        type=float,
        default=0.7,
        help="Temperatura da LLM (padrao 0.7)",
    )
    parser.add_argument(
        "--llm-dry-run",
        action="store_true",
        help="Nao chama a LLM (apenas simula a execucao)",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Imprime as estatisticas completas em JSON",
    )

    args = parser.parse_args(args=argv)

    raw_text = read_chat_from_zip(args.zip_path, chat_filename=args.chat_filename)
    conversation = parse_exported_text(raw_text)
    statistics = compute_statistics(conversation)
    insights = build_insights(statistics)

    _print_basic_summary(statistics)

    relationship_score = statistics.get("relationship_score")
    if relationship_score:
        print("\n=== Pontuacao do relacionamento ===")
        print(summarize_relationship_score(relationship_score))

    print("\n=== Insights sintetizados ===")
    print(insights)

    business_suggestions = build_business_suggestions(statistics)
    if business_suggestions:
        print("\n=== Sugestoes de negocio ===")
        print(business_suggestions)

    if args.output_json:
        print("\n=== Estatisticas (JSON) ===")
        print(json.dumps(statistics, indent=2, default=str, ensure_ascii=False))

    if args.llm:
        if generate_recommendations is None:
            print("\n[LLM] Pacote openai nao encontrado. Instale-o para habilitar as recomendacoes.")
        else:
            try:
                response = generate_recommendations(
                    statistics,
                    insights,
                    model=args.llm_model,
                    temperature=args.llm_temperature,
                    dry_run=args.llm_dry_run,
                )
                print("\n=== Recomendacoes personalizadas ===")
                print(response)
            except Exception as exc:  # pragma: no cover - erros externos
                print(f"\n[LLM] Falha ao gerar recomendacoes: {exc}")

    return 0


def main() -> None:
    raise SystemExit(app())


if __name__ == "__main__":  # pragma: no cover
    main()
