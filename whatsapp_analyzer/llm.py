from __future__ import annotations

import json
import os
from typing import Dict, Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependencia opcional
    OpenAI = None

DEFAULT_MODEL = "gpt-5-2025-08-07"
SYSTEM_PROMPT = (
    "Analise a conversa e de sugestoes espeficicas como presente de dia dos namorados e um lugar para sair."
)


def generate_recommendations(
    statistics: Dict[str, object],
    insights: str,
    *,
    model: Optional[str] = None,
    temperature: float = 0.7,
    dry_run: bool = False,
) -> str:
    """Usa uma LLM (OpenAI) para sugerir recomendacoes personalizadas."""

    if dry_run:
        return "Modo dry-run habilitado: nenhuma chamada a LLM foi realizada."

    if OpenAI is None:
        raise RuntimeError(
            "O pacote 'openai' nao esta instalado. Instale-o para habilitar as recomendacoes com LLM."
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "A variavel de ambiente OPENAI_API_KEY nao foi encontrada. Defina-a antes de gerar recomendacoes."
        )

    client = OpenAI(api_key=api_key)
    chosen_model = model or DEFAULT_MODEL

    stats_snapshot = json.dumps(statistics, default=str, ensure_ascii=False, indent=2)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Aqui estao estatisticas de uma conversa do WhatsApp, seguidas de insights"
                " extraidos automaticamente. Gere ate cinco recomendacoes praticas para"
                " os participantes, considerando tom, horarios habituais, interesses e"
                " oportunidade de melhoria.\n\n"
                f"Estatisticas (JSON):\n{stats_snapshot}\n\n"
                f"Insights textuais:\n{insights}"
            ),
        },
    ]

    response = client.chat.completions.create(
        model=chosen_model,
        temperature=temperature,
        messages=messages,
    )

    choice = response.choices[0]
    return choice.message.content.strip()
