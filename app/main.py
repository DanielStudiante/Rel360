from fastapi import FastAPI, UploadFile, File, HTTPException
from app.utils.file_utils import validate_pdf, calculate_file_hash
from app.services.file_service import save_file, check_duplicate, register_file

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