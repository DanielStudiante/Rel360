from __future__ import annotations

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.services.file_service import save_file, check_duplicate, register_file, UPLOAD_DIR 
from app.database import repositories

from app.utils.file_utils import validate_pdf, calculate_file_hash
from app.services.pdf_service import extract_text_from_pdf
from app.services.nutrition_service import process_nutrition_text, process_nutrition_text_with_raw

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

        # Verificar duplicado en BD
        try:
            existing_file_id = check_duplicate(file_hash)
        except RuntimeError as exc:
            print(f"[upload] Error verificando duplicado: {exc}")
            raise HTTPException(status_code=503, detail="No se pudo verificar si el archivo ya existe en la base de datos")
        if existing_file_id:
            # Si ya existe, intentar devolver resultados nutricionales cacheados
            try:
                cached_result = repositories.get_nutrition_result_by_file_id(existing_file_id)
                if cached_result:
                    return {
                        "message": "Archivo ya existe, retornando resultado cacheado",
                        "file_id": existing_file_id,
                        "duplicate": True,
                        "nutrition_result": {
                            "producto": cached_result.producto,
                            "nutrition_json": cached_result.nutrition_json,
                            "raw_ai_response": cached_result.raw_ai_response,
                            "ai_model": cached_result.ai_model,
                            "processing_status": cached_result.processing_status,
                            "processed_at": cached_result.processed_at.isoformat() if cached_result.processed_at else None,
                        },
                    }
                return {"message": "Archivo ya existe", "file_id": existing_file_id, "duplicate": True}
            except Exception as exc:
                print(f"[upload] Error consultando cache nutricional: {exc}")
                return {"message": "Archivo ya existe", "file_id": existing_file_id, "duplicate": True}

        # Guardar archivo en disco
        file_id, file_path = save_file(file_bytes)

        # Registrar metadatos en BD
        try:
            register_file(file_id=file_id, file_name=file.filename, file_hash=file_hash, file_path=file_path)
        except Exception as exc:
            print(f"[upload] Error registrando archivo en BD: {exc}")
            raise HTTPException(status_code=500, detail="No se pudo registrar el archivo en la base de datos")

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


@app.post("/process-text")
async def process_text(payload: TextRequest):
    try:
        text = payload.text

        try:
            nutrition = process_nutrition_text(text)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        return nutrition.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/extract-text")
async def extract_text(payload: ExtractRequest):
    try:
        file_path = UPLOAD_DIR / f"{payload.file_id}.pdf"

        cached_result = repositories.get_nutrition_result_by_file_id(payload.file_id)
        if cached_result:
            return {
                "success": True,
                "data": cached_result.nutrition_json,
                "cached": True,
            }

        text = extract_text_from_pdf(file_path)
        # Guardar texto extraído en BD
        try:
            repositories.create_extracted_text(payload.file_id, text)
        except Exception as exc:
            print(f"[extract-text] Error guardando texto extraído: {exc}")

        try:
            nutrition, raw_ai_response = process_nutrition_text_with_raw(text)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        # Guardar resultado nutricional en BD
        try:
            from app.services.ai_service import GEMINI_MODEL_NAME
            ai_model = GEMINI_MODEL_NAME
        except Exception as exc:
            print(f"[extract-text] Error obteniendo modelo IA: {exc}")
            ai_model = "simulated"

        try:
            repositories.create_nutrition_result(
                file_id=payload.file_id,
                producto=nutrition.producto if hasattr(nutrition, "producto") else None,
                nutrition_json=nutrition.model_dump(),
                raw_ai_response=raw_ai_response,
                ai_model=ai_model,
                processing_status="completed",
            )
        except Exception as exc:
            print(f"[extract-text] Error guardando resultado nutricional: {exc}")

        return {"success": True, "data": nutrition.model_dump()}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))