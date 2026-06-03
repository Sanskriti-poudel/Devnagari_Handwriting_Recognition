import time
import uuid
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import aiofiles

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, UPLOAD_DIR
from schemas import OCRResult, ModelInfo, HealthResponse
from models.loader import loaded_models, load_all_models
from services.ocr import run_ocr
from db import SessionLocal, DocumentImage, RecognizedText, create_tables

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    load_all_models()
    yield


app = FastAPI(title="Devanagari OCR API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    ms = round((time.time() - start) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({ms}ms)")
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"error": "Validation failed", "detail": str(exc)})


@app.exception_handler(Exception)
async def generic_error_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", models_loaded=list(loaded_models.keys()))


@app.get("/models", response_model=list[ModelInfo])
def list_models():
    return [
        ModelInfo(name="crnn", description="CNN-RNN-CTC baseline", available="crnn" in loaded_models),
        ModelInfo(name="transformer", description="TrOCR Transformer", available="transformer" in loaded_models),
    ]


@app.post("/ocr", response_model=OCRResult)
async def ocr(
    file: UploadFile = File(...),
    model_name: str = Form("crnn"),
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: .{ext}")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_FILE_SIZE_MB} MB limit")

    save_name = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(contents)

    start = time.time()
    result_text, confidence = run_ocr(save_path, model_name)
    elapsed_ms = round((time.time() - start) * 1000, 2)

    db = SessionLocal()
    try:
        doc = DocumentImage(original_filename=file.filename, saved_path=save_path)
        db.add(doc)
        db.flush()
        rec = RecognizedText(
            document_id=doc.id,
            model_used=model_name,
            text=result_text,
            confidence=confidence,
            processing_time_ms=elapsed_ms,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        result_id = rec.id
        created_at = rec.created_at
    finally:
        db.close()

    return OCRResult(
        id=result_id,
        filename=file.filename,
        model_used=model_name,
        recognized_text=result_text,
        confidence=confidence,
        processing_time_ms=elapsed_ms,
        created_at=created_at,
    )


@app.get("/history/{result_id}", response_model=OCRResult)
def get_history(result_id: int):
    db = SessionLocal()
    try:
        rec = db.query(RecognizedText).filter(RecognizedText.id == result_id).first()
        if not rec:
            raise HTTPException(404, "Result not found")
        doc = db.query(DocumentImage).filter(DocumentImage.id == rec.document_id).first()
        return OCRResult(
            id=rec.id,
            filename=doc.original_filename if doc else "unknown",
            model_used=rec.model_used,
            recognized_text=rec.text,
            confidence=rec.confidence,
            processing_time_ms=rec.processing_time_ms,
            created_at=rec.created_at,
        )
    finally:
        db.close()
