from __future__ import annotations

from fastapi import FastAPI, UploadFile, File, HTTPException
from app.services.file_service import save_file, check_duplicate, register_file, UPLOAD_DIR
from app.database import repositories
from app.utils.file_utils import validate_pdf, calculate_file_hash
from app.services.pdf_service import extract_text_from_pdf
from app.services.nutrition_service import process_nutrition_text, process_nutrition_text_with_raw
from app.services.nutrition_service import process_full_nutrition_table
from app.rules.invima import TipoAlimento
from app.models.request_models import TextRequest, ExtractRequest, NutritionTableRequest

app = FastAPI(title="Rel360 API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Rel360 API activa"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Recibe el PDF, valida, calcula hash y registra en BD.
    Si ya existe retorna el file_id cacheado.
    """
    try:
        file_bytes = await file.read()
        validate_pdf(file_bytes, file)
        file_hash = calculate_file_hash(file_bytes)

        try:
            existing_file_id = check_duplicate(file_hash)
        except RuntimeError as exc:
            print(f"[upload] Error verificando duplicado: {exc}")
            raise HTTPException(status_code=503, detail="No se pudo verificar duplicado en BD")

        if existing_file_id:
            return {
                "message": "Archivo ya existe",
                "file_id": existing_file_id,
                "duplicate": True,
            }

        file_id, file_path = save_file(file_bytes)

        try:
            register_file(
                file_id=file_id,
                file_name=file.filename,
                file_hash=file_hash,
                file_path=file_path,
            )
        except Exception as exc:
            print(f"[upload] Error registrando en BD: {exc}")
            raise HTTPException(status_code=500, detail="No se pudo registrar el archivo en BD")

        return {
            "message": "Archivo subido correctamente",
            "file_id": file_id,
            "duplicate": False,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/process-text")
async def process_text(payload: TextRequest):
    """
    Recibe texto plano y retorna NutritionData crudo.
    Útil para pruebas sin PDF.
    """
    try:
        nutrition = process_nutrition_text(payload.text)
        return nutrition.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract-text")
async def extract_text(payload: ExtractRequest):
    """
    Extrae el texto del PDF y lo guarda en BD.
    No llama a la IA — eso es responsabilidad de /nutrition-table.
    """
    try:
        # Si ya fue extraído, retornar el texto guardado
        existing = repositories.get_extracted_text_by_file_id(payload.file_id)
        if existing:
            return {
                "success": True,
                "cached": True,
                "file_id": payload.file_id,
                "extracted_text": existing.extracted_text,
            }

        file_path = UPLOAD_DIR / f"{payload.file_id}.pdf"
        text = extract_text_from_pdf(file_path)

        repositories.create_extracted_text(payload.file_id, text)

        return {
            "success": True,
            "cached": False,
            "file_id": payload.file_id,
            "extracted_text": text,
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/nutrition-table")
async def get_nutrition_table(payload: NutritionTableRequest):
    """
    Construye la tabla nutricional completa con sellos INVIMA.
    Depende de que /extract-text ya haya sido llamado antes.
    """
    # 1. Cache: ya tiene tabla calculada?
    try:
        cached = repositories.get_nutrition_result_by_file_id(payload.file_id)
        if cached and cached.nutrition_json:
            return {"success": True, "cached": True, "data": cached.nutrition_json}
    except Exception as exc:
        print(f"[nutrition-table] Error consultando cache: {exc}")

    # 2. Buscar texto ya extraído por /extract-text
    try:
        extracted = repositories.get_extracted_text_by_file_id(payload.file_id)
        if not extracted:
            raise HTTPException(
                status_code=400,
                detail="Primero debes llamar a /extract-text para procesar el PDF",
            )
        text = extracted.extracted_text
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error obteniendo texto: {exc}")

    # 3. Construir tabla nutricional completa
    tipo = TipoAlimento.LIQUIDO if payload.tipo_alimento == "liquido" else TipoAlimento.SOLIDO

    try:
        table, nutrition_raw, _ = process_full_nutrition_table(
            text=text,
            tipo_alimento=tipo,
            contiene_edulcorantes=payload.contiene_edulcorantes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # 4. Guardar resultado en BD
    table_dict = table.model_dump()
    try:
        from app.services.ai_service import GEMINI_MODEL_NAME
        ai_model = GEMINI_MODEL_NAME
    except Exception:
        ai_model = "simulated"

    try:
        repositories.create_nutrition_result(
            file_id=payload.file_id,
            producto=table.producto,
            nutrition_json=table_dict,
            raw_ai_response=nutrition_raw,
            ai_model=ai_model,
            processing_status="completed",
        )
    except Exception as exc:
        print(f"[nutrition-table] Error guardando en BD: {exc}")

    return {"success": True, "cached": False, "data": table_dict}