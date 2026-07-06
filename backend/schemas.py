from pydantic import BaseModel, ConfigDict, EmailStr
from pydantic.alias_generators import to_camel
from typing import Optional, Literal
from datetime import datetime


class CamelModel(BaseModel):
    """Base for schemas the frontend consumes directly — serializes snake_case
    fields as camelCase to match the TypeScript types in frontend/src/types."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ---- Legacy "Contract B" shape, kept for the original /ocr + tests ----------

class OCRResult(BaseModel):
    id: Optional[int] = None
    filename: str
    model_used: str
    recognized_text: str
    confidence: Optional[float] = None
    processing_time_ms: Optional[float] = None
    created_at: Optional[datetime] = None


class DeleteResponse(BaseModel):
    deleted: bool
    id: int


# ---- /api/document — matches ocr.service.ts's DocumentApiResponse exactly ---

class DocumentOCRResult(BaseModel):
    text: str
    num_chars: int
    num_lines: int
    avg_confidence: float
    time_ms: float
    annotated: Optional[str] = None
    model_simulated: bool = False


# ---- Auth --------------------------------------------------------------------

class SignupBody(CamelModel):
    full_name: str
    email: EmailStr
    password: str


class LoginBody(CamelModel):
    email: EmailStr
    password: str


class ForgotPasswordBody(CamelModel):
    email: EmailStr


class ResetPasswordBody(CamelModel):
    token: str
    password: str


class UserOut(CamelModel):
    id: str
    full_name: str
    email: str
    university: Optional[str] = None
    role: str
    avatar_url: Optional[str] = None
    created_at: datetime


class AuthResponse(CamelModel):
    user: UserOut
    access_token: str


# ---- Models & health -----------------------------------------------------

class OcrModelOut(CamelModel):
    id: Literal["crnn", "transformer"]
    name: str
    description: str
    status: Literal["active", "inactive", "degraded"]


class HealthOut(CamelModel):
    status: Literal["operational", "degraded", "down"]
    message: str
    models: list[OcrModelOut]
    checked_at: datetime


# ---- History ---------------------------------------------------------------

class HistoryItemOut(CamelModel):
    id: str
    text: str
    confidence: float
    model: Literal["crnn", "transformer"]
    file_name: str
    file_type: Literal["image", "pdf"]
    thumbnail: Optional[str] = None
    num_chars: Optional[int] = None
    num_lines: Optional[int] = None
    time_ms: Optional[float] = None
    created_at: datetime
    status: Literal["completed", "failed"]
    model_simulated: Optional[bool] = None


class PaginatedHistoryOut(CamelModel):
    items: list[HistoryItemOut]
    total: int
    page: int
    page_size: int


# ---- Dashboard ---------------------------------------------------------------

class ConfidenceTrendPoint(CamelModel):
    label: str
    value: float


class DashboardStatsOut(CamelModel):
    total_documents: int
    total_documents_delta: float
    total_recognitions: int
    total_recognitions_delta: float
    avg_confidence: float
    avg_confidence_delta: float
    total_characters: int
    total_characters_delta: float
    confidence_trend: list[ConfidenceTrendPoint]
    storage_used_bytes: float
    storage_total_bytes: float


class ActivityItemOut(CamelModel):
    id: str
    type: Literal["ocr", "login", "settings", "account"]
    message: str
    created_at: datetime
