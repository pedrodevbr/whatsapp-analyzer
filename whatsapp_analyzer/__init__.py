"""Ferramentas para analise de conversas exportadas do WhatsApp."""

from __future__ import annotations

from typing import Iterable

__all__ = ["app"]


def app(argv: Iterable[str] | None = None) -> int:
    """Proxy para whatsapp_analyzer.cli.app sem importar o modulo na carga do pacote."""

    from .cli import app as cli_app

    return cli_app(argv)
