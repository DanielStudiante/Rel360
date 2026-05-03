from __future__ import annotations

from pathlib import Path
import pdfplumber


def extract_text_from_pdf(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF no encontrado: {file_path}")

    pages: list[str] = []
    with pdfplumber.open(path) as pdf: #esto abre el PDF y lo cierra automáticamente al finalizar el bloque
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())

    if not pages:
        raise ValueError("No se pudo extraer texto. Puede ser un PDF escaneado.")

    full_text = "\n".join(pages)
    lines = [line for line in full_text.splitlines() if line.strip()]
    return "\n".join(lines)