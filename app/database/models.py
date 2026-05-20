from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id = Column(String, primary_key=True)
    file_name = Column(String, nullable=False)
    file_hash = Column(String, nullable=False, unique=True, index=True)
    file_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="uploaded")
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    extracted_text = relationship("ExtractedText", back_populates="file", uselist=False)
    nutrition_results = relationship("NutritionResult", back_populates="file")


class ExtractedText(Base):
    __tablename__ = "extracted_texts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String, ForeignKey("uploaded_files.id"), nullable=False, unique=True)
    extracted_text = Column(Text, nullable=False)
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())

    file = relationship("UploadedFile", back_populates="extracted_text")


class NutritionResult(Base):
    __tablename__ = "nutrition_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String, ForeignKey("uploaded_files.id"), nullable=False, index=True)
    producto = Column(String, nullable=True)
    nutrition_json = Column(JSONB)
    raw_ai_response = Column(Text, nullable=True)
    ai_model = Column(String, nullable=True)
    processing_status = Column(String, nullable=False, default="pending")
    processed_at = Column(DateTime(timezone=True), server_default=func.now())

    file = relationship("UploadedFile", back_populates="nutrition_results")
