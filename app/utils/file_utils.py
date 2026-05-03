from __future__ import annotations

import hashlib

def calculate_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def validate_pdf(file_bytes: bytes, file) -> None:
    if file.content_type != "application/pdf":
        raise ValueError("El archivo debe ser un PDF")

    if not file_bytes.startswith(b"%PDF-"):
        raise ValueError("El archivo no tiene una firma PDF válida")