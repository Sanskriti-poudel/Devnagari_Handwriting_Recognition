import time
import uuid
import os
import io
import base64
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from starlette.concurrency import run_in_threadpool
import aiofiles

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, UPLOAD_DIR, CORS_ORIGINS
from schemas import (
    OCRResult,
    DocumentOCRResult,
    DocumentOCRResponse,
    ExportRequest,
    SignupBody,
    LoginBody,
    ForgotPasswordBody,
    ResetPasswordBody,
    UserOut,
    AuthResponse,
    OcrModelOut,
    HealthOut,
    HistoryItemOut,
    PaginatedHistoryOut,
    DashboardStatsOut,
    ConfidenceTrendPoint,
    ActivityItemOut,
)
from ml_models.loader import loaded_models, load_all_models
from services.ocr import run_ocr, run_ocr_pdf
from services.document import read_upload_to_pages, run_document_ocr, get_cached_doc
from services.export import build_docx, build_searchable_pdf
from db import SessionLocal, DocumentImage, RecognizedText, User, create_tables
from deps import get_db, get_current_user, get_optional_user
from security import hash_password, verify_password, create_access_token

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    load_all_models()
    yield


app = FastAPI(title="Devanagari OCR API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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


@app.exception_handler(HTTPException)
async def http_error_handler(request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(Exception)
async def generic_error_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


# --------------------------------------------------------------------------
# Models & health
# --------------------------------------------------------------------------

MODEL_CATALOG = [
    {"id": "crnn", "name": "CRNN (CNN + RNN + CTC)", "description": "Better for character-level recognition"},
    {"id": "transformer", "name": "Transformer (TrOCR)", "description": "Better for word & line recognition"},
]


def _model_status(model_id: str) -> str:
    return "active" if model_id in loaded_models else "degraded"


def _models_payload() -> list[OcrModelOut]:
    return [
        OcrModelOut(id=m["id"], name=m["name"], description=m["description"], status=_model_status(m["id"]))
        for m in MODEL_CATALOG
    ]


@app.get("/models", response_model=list[OcrModelOut])
def list_models():
    return _models_payload()


@app.get("/health", response_model=HealthOut)
def health():
    models = _models_payload()
    any_real = any(m.status == "active" for m in models)
    return HealthOut(
        status="operational" if any_real else "degraded",
        message="All systems operational" if any_real else "Running in mock-inference mode — no trained model weights are loaded",
        models=models,
        checked_at=datetime.now(timezone.utc),
    )


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------

def _user_out(user: User) -> UserOut:
    return UserOut(
        id=str(user.id),
        full_name=user.full_name,
        email=user.email,
        university=user.university,
        role=user.role,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


@app.post("/signup", response_model=AuthResponse)
def signup(body: SignupBody, db=Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(400, "An account with this email already exists.")
    user = User(
        full_name=body.full_name,
        email=body.email,
        password_hash=hash_password(body.password),
        role="Student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return AuthResponse(user=_user_out(user), access_token=create_access_token(user.id))


@app.post("/login", response_model=AuthResponse)
def login(body: LoginBody, db=Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password.")
    return AuthResponse(user=_user_out(user), access_token=create_access_token(user.id))


@app.post("/logout")
def logout():
    # Stateless JWT — nothing to invalidate server-side for this project's scope.
    return {"ok": True}


@app.post("/refresh-token", response_model=AuthResponse)
def refresh_token(user: User = Depends(get_current_user)):
    return AuthResponse(user=_user_out(user), access_token=create_access_token(user.id))


@app.post("/forgot-password")
def forgot_password(body: ForgotPasswordBody, db=Depends(get_db)):
    # Never reveal whether the email exists. Real email delivery is out of scope
    # for this project; log it instead so it's visible during a demo/defense.
    user = db.query(User).filter(User.email == body.email).first()
    if user:
        logger.info(f"[forgot-password] would email a reset link to {user.email}")
    return {"ok": True}


@app.post("/reset-password")
def reset_password(body: ResetPasswordBody):
    logger.info("[reset-password] no-op — token-based email reset is not implemented")
    return {"ok": True}


# --------------------------------------------------------------------------
# OCR — the real recognizer, persisted per user
# --------------------------------------------------------------------------

def _make_thumbnail(raw: bytes, filename: str) -> str | None:
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img.thumbnail((320, 320))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception as exc:
        logger.debug(f"Could not build thumbnail for {filename}: {exc}")
        return None


@app.post("/api/document", response_model=DocumentOCRResult)
async def api_document(
    image: UploadFile = File(...),
    model: str = Form("crnn"),
    db=Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    filename = image.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: .{ext}")

    contents = await image.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_FILE_SIZE_MB} MB limit")

    if model not in ("crnn", "transformer"):
        model = "crnn"

    save_name = f"{uuid.uuid4().hex}_{filename}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(contents)

    is_pdf = ext == "pdf"
    start = time.time()
    if is_pdf:
        pages = await run_in_threadpool(run_ocr_pdf, save_path, model)
        text = "\n\n".join(p["text"] for p in pages)
        confidence = sum(p["confidence"] for p in pages) / len(pages) if pages else 0.0
    else:
        text, confidence = await run_in_threadpool(run_ocr, save_path, model)
    elapsed_ms = round((time.time() - start) * 1000, 2)

    num_chars = len(text.replace("\n", ""))
    num_lines = max(1, len([line for line in text.split("\n") if line.strip()])) if text else 0
    model_simulated = model not in loaded_models

    thumbnail = None if is_pdf else _make_thumbnail(contents, filename)

    doc = DocumentImage(original_filename=filename, saved_path=save_path)
    db.add(doc)
    db.flush()
    rec = RecognizedText(
        document_id=doc.id,
        user_id=user.id if user else None,
        model_used=model,
        model_simulated=model_simulated,
        text=text,
        confidence=confidence,
        processing_time_ms=elapsed_ms,
        file_name=filename,
        file_type="pdf" if is_pdf else "image",
        thumbnail=thumbnail,
        num_chars=num_chars,
        num_lines=num_lines,
        status="completed",
    )
    db.add(rec)
    db.commit()

    return DocumentOCRResult(
        text=text,
        num_chars=num_chars,
        num_lines=num_lines,
        avg_confidence=confidence,
        time_ms=elapsed_ms,
        model_simulated=model_simulated,
    )


@app.post("/api/document/pages", response_model=DocumentOCRResponse)
async def api_document_pages(file: UploadFile = File(...)):
    """Multi-page document OCR with per-line boxes, feeding /api/export.

    Uses the real word-level TrOCR (reads whole lines, including matras /
    conjuncts / punctuation) when a trained checkpoint is loaded; otherwise
    falls back to the honest CRNN character-segmentation path. Kept separate
    from /api/document (which persists a single flattened result to history)
    since export needs the per-page images + line boxes this returns.
    """
    raw = await file.read()
    pages, err = read_upload_to_pages(file.filename, raw)
    if err is not None:
        raise HTTPException(400, err)

    response, err = await run_in_threadpool(run_document_ocr, pages)
    if err is not None:
        raise HTTPException(400, err)
    return response


@app.post("/api/export")
async def api_export(body: ExportRequest):
    """Download recognized text as txt | docx | (searchable) pdf.

    txt/docx use the (possibly user-edited) `text`; pdf rebuilds a searchable
    PDF from the cached page images + OCR line boxes for `doc_id` (returned
    by /api/document/pages).
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


@app.get("/api/random")
def api_random():
    # No held-out test set is bundled with the backend in this deployment.
    raise HTTPException(404, "No sample images are available on this server.")


# --------------------------------------------------------------------------
# Legacy Contract-B endpoint, kept so nothing that already depends on it breaks
# --------------------------------------------------------------------------

@app.post("/ocr", response_model=OCRResult)
async def ocr(file: UploadFile = File(...), model_name: str = Form("crnn")):
    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: .{ext}")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_FILE_SIZE_MB} MB limit")

    save_name = f"{uuid.uuid4().hex}_{filename}"
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
        doc = DocumentImage(original_filename=filename, saved_path=save_path)
        db.add(doc)
        db.flush()
        rec = RecognizedText(
            document_id=doc.id,
            model_used=model_name,
            text=result_text,
            confidence=confidence,
            processing_time_ms=elapsed_ms,
            file_name=filename,
            file_type="pdf" if ext == "pdf" else "image",
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
        filename=filename,
        model_used=model_name,
        recognized_text=result_text,
        confidence=confidence,
        processing_time_ms=elapsed_ms,
        created_at=created_at,
    )


@app.get("/history/{result_id}", response_model=OCRResult)
def get_history_one(result_id: int, db=Depends(get_db), user: User = Depends(get_current_user)):
    rec = (
        db.query(RecognizedText)
        .filter(RecognizedText.id == result_id, RecognizedText.user_id == user.id)
        .first()
    )
    if not rec:
        raise HTTPException(404, "Result not found")
    doc = db.query(DocumentImage).filter(DocumentImage.id == rec.document_id).first()
    return OCRResult(
        id=rec.id,
        filename=doc.original_filename if doc else rec.file_name or "unknown",
        model_used=rec.model_used,
        recognized_text=rec.text,
        confidence=rec.confidence,
        processing_time_ms=rec.processing_time_ms,
        created_at=rec.created_at,
    )


# --------------------------------------------------------------------------
# History — paginated, filtered, sorted, scoped to the logged-in user
# --------------------------------------------------------------------------

def _history_item_out(rec: RecognizedText) -> HistoryItemOut:
    return HistoryItemOut(
        id=str(rec.id),
        text=rec.text or "",
        confidence=rec.confidence or 0.0,
        model=rec.model_used if rec.model_used in ("crnn", "transformer") else "crnn",
        file_name=rec.file_name or "unknown",
        file_type=rec.file_type if rec.file_type in ("image", "pdf") else "image",
        thumbnail=rec.thumbnail,
        num_chars=rec.num_chars,
        num_lines=rec.num_lines,
        time_ms=rec.processing_time_ms,
        created_at=rec.created_at,
        status=rec.status if rec.status in ("completed", "failed") else "completed",
        model_simulated=rec.model_simulated,
    )


@app.get("/history", response_model=PaginatedHistoryOut)
def list_history(
    search: str = "",
    model: str = "all",
    status: str = "all",
    sortBy: str = Query("date", alias="sortBy"),
    sortDir: str = Query("desc", alias="sortDir"),
    page: int = 1,
    pageSize: int = Query(10, alias="pageSize"),
    db=Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(RecognizedText).filter(RecognizedText.user_id == user.id)

    if search.strip():
        like = f"%{search.strip()}%"
        q = q.filter((RecognizedText.file_name.ilike(like)) | (RecognizedText.text.ilike(like)))
    if model != "all":
        q = q.filter(RecognizedText.model_used == model)
    if status != "all":
        q = q.filter(RecognizedText.status == status)

    total = q.count()

    sort_column = {
        "date": RecognizedText.created_at,
        "confidence": RecognizedText.confidence,
        "name": RecognizedText.file_name,
    }.get(sortBy, RecognizedText.created_at)
    sort_column = sort_column.asc() if sortDir == "asc" else sort_column.desc()
    q = q.order_by(sort_column)

    page = max(1, page)
    pageSize = max(1, min(pageSize, 100))
    items = q.offset((page - 1) * pageSize).limit(pageSize).all()

    return PaginatedHistoryOut(
        items=[_history_item_out(r) for r in items],
        total=total,
        page=page,
        page_size=pageSize,
    )


@app.delete("/history/{result_id}")
def delete_history(result_id: int, db=Depends(get_db), user: User = Depends(get_current_user)):
    rec = (
        db.query(RecognizedText)
        .filter(RecognizedText.id == result_id, RecognizedText.user_id == user.id)
        .first()
    )
    if not rec:
        raise HTTPException(404, "Result not found")
    db.delete(rec)
    db.commit()
    return {"ok": True}


# --------------------------------------------------------------------------
# Dashboard — aggregated from the same recognitions table
# --------------------------------------------------------------------------

@app.get("/dashboard/stats", response_model=DashboardStatsOut)
def dashboard_stats(db=Depends(get_db), user: User = Depends(get_current_user)):
    recs = db.query(RecognizedText).filter(RecognizedText.user_id == user.id).all()

    total_documents = len(recs)
    completed = [r for r in recs if r.status == "completed"]
    avg_confidence = (sum(r.confidence or 0 for r in completed) / len(completed)) if completed else 0.0
    total_characters = sum(r.num_chars or 0 for r in recs)

    by_day: dict[str, list[float]] = {}
    for r in sorted(recs, key=lambda r: r.created_at):
        label = r.created_at.strftime("%b %#d") if os.name == "nt" else r.created_at.strftime("%b %-d")
        by_day.setdefault(label, []).append(r.confidence or 0.0)
    trend = [ConfidenceTrendPoint(label=label, value=round((sum(v) / len(v)) * 100, 1)) for label, v in by_day.items()]
    if not trend:
        trend = [ConfidenceTrendPoint(label="Today", value=0)]

    return DashboardStatsOut(
        total_documents=total_documents,
        total_documents_delta=0,
        total_recognitions=len(completed),
        total_recognitions_delta=0,
        avg_confidence=round(avg_confidence * 100, 1),
        avg_confidence_delta=0,
        total_characters=total_characters,
        total_characters_delta=0,
        confidence_trend=trend,
        storage_used_bytes=sum(len(r.thumbnail or "") for r in recs) * 0.75,  # rough base64 -> bytes
        storage_total_bytes=10 * 1024**3,
    )


@app.get("/dashboard/activity", response_model=list[ActivityItemOut])
def dashboard_activity(db=Depends(get_db), user: User = Depends(get_current_user)):
    recs = (
        db.query(RecognizedText)
        .filter(RecognizedText.user_id == user.id)
        .order_by(RecognizedText.created_at.desc())
        .limit(8)
        .all()
    )
    return [
        ActivityItemOut(
            id=f"activity_{r.id}",
            type="ocr",
            message=f'Recognized "{r.file_name}" with {(r.confidence or 0) * 100:.1f}% confidence',
            created_at=r.created_at,
        )
        for r in recs
    ]
