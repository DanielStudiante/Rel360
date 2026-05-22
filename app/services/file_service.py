from __future__ import annotations

from pathlib import Path
import os
import uuid
from typing import Optional

from app.database import repositories

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_file(file_bytes: bytes) -> tuple[str, str]:
    """Guarda el PDF en disco y devuelve (file_id, file_path)."""
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.pdf"

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    return file_id, str(file_path)


def check_duplicate(file_hash: str) -> Optional[str]:
    """Retorna file_id si existe un UploadedFile con ese hash en la BD."""
    try:
        existing = repositories.get_uploaded_file_by_hash(file_hash)
        if existing:
            return existing.id
        return None
    except Exception as exc:
        print(f"[file_service] Error consultando duplicado por hash: {exc}")
        raise RuntimeError("No se pudo consultar la base de datos para verificar duplicados") from exc


def register_file(file_id: str, file_name: str, file_hash: str, file_path: str, status: str = "uploaded") -> None:
    """Registra metadatos del archivo en la BD."""
    try:
        repositories.create_uploaded_file(file_id=file_id, file_name=file_name, file_hash=file_hash, file_path=file_path, status=status)
    except Exception as exc:
        print(f"[file_service] Error registrando archivo en BD: {exc}")
        raise