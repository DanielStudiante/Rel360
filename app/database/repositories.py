from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, desc

from app.database.database import SessionLocal, create_tables
from app.database.models import UploadedFile, ExtractedText, NutritionResult


def _ensure_tables():
    try:
        create_tables()
    except Exception:
        logging.exception("Could not create tables (may already exist or DB unreachable)")


def create_uploaded_file(file_id: str, file_name: str, file_hash: str, file_path: str, status: str = "uploaded") -> UploadedFile:
    _ensure_tables()
    db = SessionLocal()
    try:
        uf = UploadedFile(id=file_id, file_name=file_name, file_hash=file_hash, file_path=file_path, status=status)
        db.add(uf)
        db.commit()
        db.refresh(uf)
        return uf
    except SQLAlchemyError:
        db.rollback()
        logging.exception("DB error creating uploaded file")
        raise
    finally:
        db.close()


def get_uploaded_file_by_hash(file_hash: str) -> Optional[UploadedFile]:
    db = SessionLocal()
    try:
        stmt = select(UploadedFile).where(UploadedFile.file_hash == file_hash)
        res = db.execute(stmt).scalar_one_or_none()
        return res
    except SQLAlchemyError:
        logging.exception("DB error fetching uploaded file by hash")
        raise
    finally:
        db.close()


def create_extracted_text(file_id: str, extracted_text: str) -> ExtractedText:
    db = SessionLocal()
    try:
        et = ExtractedText(file_id=file_id, extracted_text=extracted_text)
        db.add(et)
        db.commit()
        db.refresh(et)
        return et
    except SQLAlchemyError:
        db.rollback()
        logging.exception("DB error creating extracted text")
        raise
    finally:
        db.close()


def create_nutrition_result(file_id: str, producto: Optional[str], nutrition_json: dict, raw_ai_response: str, ai_model: str, processing_status: str = "completed") -> NutritionResult:
    db = SessionLocal()
    try:
        nr = NutritionResult(
            file_id=file_id,
            producto=producto,
            nutrition_json=nutrition_json,
            raw_ai_response=raw_ai_response,
            ai_model=ai_model,
            processing_status=processing_status,
        )
        db.add(nr)
        db.commit()
        db.refresh(nr)
        return nr
    except SQLAlchemyError:
        db.rollback()
        logging.exception("DB error creating nutrition result")
        raise
    finally:
        db.close()


def get_nutrition_result_by_file_id(file_id: str) -> Optional[NutritionResult]:
    db = SessionLocal()
    try:
        stmt = select(NutritionResult).where(NutritionResult.file_id == file_id).order_by(desc(NutritionResult.processed_at))
        res = db.execute(stmt).scalars().first()
        return res
    except SQLAlchemyError:
        logging.exception("DB error fetching nutrition results")
        raise
    finally:
        db.close()
