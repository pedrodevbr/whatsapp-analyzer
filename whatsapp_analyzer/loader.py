from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional


class ChatFileNotFoundError(FileNotFoundError):
    pass


def read_chat_from_zip(zip_path: Path | str, chat_filename: Optional[str] = None) -> str:
    """Retorna o conteudo em texto da conversa armazenada dentro de um ZIP exportado."""

    archive_path = Path(zip_path)
    if not archive_path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {archive_path}")

    with zipfile.ZipFile(archive_path, "r") as archive:
        if chat_filename:
            if chat_filename not in archive.namelist():
                raise ChatFileNotFoundError(
                    f"'chat_filename' apontou para {chat_filename}, mas o arquivo nao existe dentro do ZIP"
                )
            name = chat_filename
        else:
            txt_files = [name for name in archive.namelist() if name.lower().endswith(".txt")]
            if not txt_files:
                raise ChatFileNotFoundError("Nenhum arquivo .txt encontrado no ZIP exportado.")
            if len(txt_files) > 1:
                # Prioriza arquivos cujo nome se parece com o padrao "WhatsApp Chat ...".
                preferred = [name for name in txt_files if "whatsapp" in name.lower()]
                name = preferred[0] if preferred else txt_files[0]
            else:
                name = txt_files[0]

        raw_bytes = archive.read(name)

    return raw_bytes.decode("utf-8-sig", errors="replace")
