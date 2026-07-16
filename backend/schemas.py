from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OCRResult(BaseModel):
    id: Optional[int] = None
    filename: str
    model_used: str
    recognized_text: str
    confidence: Optional[float] = None
    processing_time_ms: Optional[float] = None
    preprocessed_b64: Optional[str] = None  # base64 PNG of 64×64 preprocessed input
    created_at: Optional[datetime] = None


class PaginatedResults(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[OCRResult]


class DeleteResponse(BaseModel):
    deleted: bool
    id: int


class ModelInfo(BaseModel):
    name: str
    description: str
    available: bool


class HealthResponse(BaseModel):
    status: str
    models_loaded: list[str]


class DocumentPageResult(BaseModel):
    annotated: Optional[str] = None
    text: str
    num_lines: int
    num_chars: int
    avg_confidence: float


class DocumentOCRResponse(BaseModel):
    doc_id: str
    engine: str
    text: str
    num_chars: int
    num_lines: int
    num_pages: int
    avg_confidence: float
    time_ms: float
    annotated: Optional[str] = None
    pages: list[DocumentPageResult]


class ExportRequest(BaseModel):
    format: str
    text: str
    doc_id: Optional[str] = None
