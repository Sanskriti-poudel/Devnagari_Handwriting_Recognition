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
