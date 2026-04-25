from pathlib import Path
import json
import os
import uuid

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

HASH_DB_PATH = UPLOAD_DIR / "file_hashes.json"


def load_file_hashes() -> dict[str, str]:
    if not HASH_DB_PATH.exists():
        return {}

    with open(HASH_DB_PATH, "r", encoding="utf-8") as file:
        content = file.read().strip()

    if not content:
        return {}

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {}

    if not isinstance(data, dict):
        return {}

    return {str(file_hash): str(file_id) for file_hash, file_id in data.items()}


def save_file_hashes(file_hash_db: dict[str, str]) -> None:
    with open(HASH_DB_PATH, "w", encoding="utf-8") as file:
        json.dump(file_hash_db, file, ensure_ascii=False, indent=2)

# Simulación de base de datos (por ahora)
file_hash_db = load_file_hashes()

def save_file(file_bytes):
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.pdf"

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    return file_id, str(file_path)


def check_duplicate(file_hash):
    return file_hash_db.get(file_hash)


def register_file(file_hash, file_id):
    file_hash_db[file_hash] = file_id
    save_file_hashes(file_hash_db)