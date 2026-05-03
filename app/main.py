from __future__ import annotations

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, ValidationError
import json
from app.services.file_service import save_file, check_duplicate, register_file, UPLOAD_DIR 

from app.utils.file_utils import validate_pdf, calculate_file_hash
from app.services.file_service import save_file, check_duplicate, register_file
from app.services.ai_service import process_text_with_ai
from app.models.nutrition_model import NutritionData
from app.services.pdf_service import extract_text_from_pdf

app = FastAPI(title="Rel360 API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Rel360 API activa"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    
    try:
        # Leer archivo completo
        file_bytes = await file.read()

        # Validar PDF
        validate_pdf(file_bytes, file)

        # Calcular hash
        file_hash = calculate_file_hash(file_bytes)

        # Verificar duplicado
        existing_file = check_duplicate(file_hash)
        if existing_file:
            return {
                "message": "Archivo ya existe",
                "file_id": existing_file,
                "duplicate": True
            }

        # Guardar archivo
        file_id, _ = save_file(file_bytes)

        # Registrar hash
        register_file(file_hash, file_id)

        return {
            "message": "Archivo subido correctamente",
            "file_id": file_id,
            "duplicate": False
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class TextRequest(BaseModel):
    text: str

class ExtractRequest(BaseModel):
    file_id: str


def _sanitize_dict(data: object) -> dict:
    """Asegura que el diccionario contiene solo tipos primitivos válidos: str, float, None."""
    if not isinstance(data, dict):
        raise ValueError(f"Esperado dict, recibido {type(data).__name__}")
    
    sanitized = {}
    for key, value in data.items():
        if not isinstance(key, str):
            key = str(key)
        
        if value is None:
            sanitized[key] = None
        elif isinstance(value, str):
            sanitized[key] = value
        elif isinstance(value, bool):
            #sanitized[key] = float(value)
            raise ValueError("Boolean no permitido")
        elif isinstance(value, (int, float)):
            sanitized[key] = float(value)
        else:
            raise ValueError(f"Tipo no válido para clave '{key}': {type(value).__name__}")
    
    return sanitized


@app.post("/process-text")
async def temp_process_text(payload: TextRequest):
    try:
        text = payload.text

        try:
            ai_response = process_text_with_ai(text)
            if not isinstance(ai_response, str):
                raise ValueError(f"AI response debe ser string, recibido {type(ai_response).__name__}")
            data_dict = json.loads(ai_response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"JSON inválido desde AI: {e}")

        try:
            data_dict = _sanitize_dict(data_dict)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=f"Datos inválidos después de JSON: {e}")

        try:
            nutrition = NutritionData.model_validate(data_dict)
        except ValidationError as ve:
            raise HTTPException(status_code=500, detail=f"Error de parsing del modelo: {ve}")

        return {"success": True, "data": nutrition.model_dump()}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/extract-text")
async def extract_text(payload: ExtractRequest):
    try:
        file_path = UPLOAD_DIR / f"{payload.file_id}.pdf"
        text = extract_text_from_pdf(file_path)
        ai_response = process_text_with_ai(text)
        data_dict = json.loads(ai_response)
        data_dict = _sanitize_dict(data_dict)
        nutrition = NutritionData.model_validate(data_dict)
        return {"success": True, "data": nutrition.model_dump()}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))