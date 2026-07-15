import time
import uuid
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from starlette.concurrency import run_in_threadpool
import aiofiles

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, UPLOAD_DIR
from schemas import (
    OCRResult, ModelInfo, HealthResponse,
    DocumentOCRResponse, ExportRequest,
)
from ml_models.loader import loaded_models, load_all_models
from services.ocr import run_ocr, run_ocr_pdf
from services.document import read_upload_to_pages, run_document_ocr, get_cached_doc
from services.export import build_docx, build_searchable_pdf
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
    if ext == "pdf":
        pages = await run_in_threadpool(run_ocr_pdf, save_path, model_name)
        result_text = "\n\n".join(f"[Page {p['page']}]\n{p['text']}" for p in pages)
        confidence = sum(p["confidence"] for p in pages) / len(pages) if pages else 0.0
    else:
        result_text, confidence = await run_in_threadpool(run_ocr, save_path, model_name)
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


@app.post("/document", response_model=DocumentOCRResponse)
async def document(file: UploadFile = File(...)):
    """Document mode: a page or multi-page PDF -> editable Devanagari Unicode text.

    Uses the real word-level TrOCR (reads whole lines, including matras /
    conjuncts / punctuation) when a trained checkpoint is loaded; otherwise
    falls back to the honest CRNN character-segmentation path.
    """
    raw = await file.read()
    pages, err = read_upload_to_pages(file.filename, raw)
    if err is not None:
        raise HTTPException(400, err)

    response, err = await run_in_threadpool(run_document_ocr, pages)
    if err is not None:
        raise HTTPException(400, err)
    return response


@app.post("/export")
async def export_document(body: ExportRequest):
    """Download the recognized text as txt | docx | (searchable) pdf.

    txt/docx use the (possibly user-edited) `text`; pdf rebuilds a searchable
    PDF from the cached page images + OCR line boxes for `doc_id`.
    """
    fmt = (body.format or "").lower()

    if fmt == "txt":
        return Response(
            content=body.text.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="recognized.txt"'},
        )

    if fmt == "docx":
        data = build_docx(body.text)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": 'attachment; filename="recognized.docx"'},
        )

    if fmt == "pdf":
        pages = get_cached_doc(body.doc_id) if body.doc_id else None
        if not pages:
            raise HTTPException(410, "This document expired — re-run the scan, then export.")
        data = build_searchable_pdf(pages)
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="recognized.pdf"'},
        )

    raise HTTPException(400, "Unknown export format. Use txt, docx or pdf.")


@app.get("/history", response_model=list[OCRResult])
def list_history(limit: int = 20):
    db = SessionLocal()
    try:
        recs = db.query(RecognizedText).order_by(RecognizedText.id.desc()).limit(limit).all()
        results = []
        for rec in recs:
            doc = db.query(DocumentImage).filter(DocumentImage.id == rec.document_id).first()
            results.append(OCRResult(
                id=rec.id,
                filename=doc.original_filename if doc else "unknown",
                model_used=rec.model_used,
                recognized_text=rec.text,
                confidence=rec.confidence,
                processing_time_ms=rec.processing_time_ms,
                created_at=rec.created_at,
            ))
        return results
    finally:
        db.close()


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
