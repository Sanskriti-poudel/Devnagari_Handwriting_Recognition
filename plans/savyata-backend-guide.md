# Savyata — Backend Developer Step-by-Step Guide

**Project:** Devanagari Handwritten Document Recognition (OCR)
**Your role:** Build the FastAPI inference service that wraps the trained model(s) and persists results.
**Your branch:** `backend`
**Skills reference:** `.claude/skills.md` §2

---

## Before you start — install these once

```bash
pip install fastapi uvicorn[standard] python-multipart pillow opencv-python-headless numpy sqlalchemy aiofiles python-dotenv
```

You will add `torch`, `pdf2image`, `PyMuPDF` later when you reach Phase 2.

---

## Phase 0 — Scaffold & Contracts

### Step 0.1 — Create the folder structure

Create every file listed below inside a new `backend/` folder in the repo root.
Leave them empty or with the minimal stub shown — you will fill them in the steps that follow.

```
backend/
  main.py
  config.py
  schemas.py
  db.py
  services/
    __init__.py
    ocr.py
  models/
    __init__.py
    loader.py
  requirements.txt
  Dockerfile
  .env.example
```

PowerShell commands to create the structure:

```powershell
cd "C:\Users\SuperPc\Desktop\OCM Project\Devnagari_Handwriting_Recognition"
New-Item -ItemType Directory -Force backend, backend\services, backend\models
New-Item -ItemType File backend\main.py, backend\config.py, backend\schemas.py, backend\db.py
New-Item -ItemType File backend\services\__init__.py, backend\services\ocr.py
New-Item -ItemType File backend\models\__init__.py, backend\models\loader.py
New-Item -ItemType File backend\requirements.txt, backend\Dockerfile, backend\.env.example
```

---

### Step 0.2 — Write `config.py`

This reads all settings from environment variables so nothing is hardcoded.

```python
# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

DEVICE = os.getenv("DEVICE", "cpu")
CRNN_MODEL_PATH = os.getenv("CRNN_MODEL_PATH", "../models/crnn.pth")
TRANSFORMER_MODEL_PATH = os.getenv("TRANSFORMER_MODEL_PATH", "../models/transformer.pth")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ocr_results.db")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tiff", "pdf"}
```

Create `.env.example` (this goes in git; the real `.env` does NOT):

```
DEVICE=cpu
CRNN_MODEL_PATH=../models/crnn.pth
TRANSFORMER_MODEL_PATH=../models/transformer.pth
DATABASE_URL=sqlite:///./ocr_results.db
MAX_FILE_SIZE_MB=10
UPLOAD_DIR=./uploads
```

Add `.env` to `.gitignore`:

```
# add this line to .gitignore at the repo root
backend/.env
```

---

### Step 0.3 — Write `schemas.py`

Pydantic models define the exact JSON contract (Contract B) with the frontend.

```python
# backend/schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OCRRequest(BaseModel):
    model_name: str = "crnn"  # "crnn" or "transformer"


class OCRResult(BaseModel):
    id: Optional[int] = None
    filename: str
    model_used: str
    recognized_text: str
    confidence: Optional[float] = None
    processing_time_ms: Optional[float] = None
    created_at: Optional[datetime] = None


class ModelInfo(BaseModel):
    name: str
    description: str
    available: bool


class HealthResponse(BaseModel):
    status: str
    models_loaded: list[str]
```

Share this file with the frontend developer immediately — it is Contract B.

---

### Step 0.4 — Write `main.py` (skeleton + mock `/ocr`)

This gives the frontend a working endpoint to develop against before the real model is ready.

```python
# backend/main.py
import time
import uuid
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, UPLOAD_DIR
from schemas import OCRResult, ModelInfo, HealthResponse
from models.loader import loaded_models
from services.ocr import run_ocr

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Devanagari OCR API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    # validate extension
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: .{ext}")

    # validate size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_FILE_SIZE_MB} MB limit")

    # save upload
    save_name = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(contents)

    # run OCR (or mock)
    start = time.time()
    result_text, confidence = run_ocr(save_path, model_name)
    elapsed_ms = (time.time() - start) * 1000

    return OCRResult(
        filename=file.filename,
        model_used=model_name,
        recognized_text=result_text,
        confidence=confidence,
        processing_time_ms=round(elapsed_ms, 2),
    )
```

---

### Step 0.5 — Write the mock `services/ocr.py`

Returns hardcoded text so the frontend can build immediately.

```python
# backend/services/ocr.py
from models.loader import loaded_models

# MOCK text — replace with real inference in Phase 2
MOCK_TEXT = "नमस्ते, यो एक परीक्षण पाठ हो।"


def run_ocr(image_path: str, model_name: str) -> tuple[str, float]:
    """
    Returns (recognized_text, confidence).
    Uses mock output until real model artifacts are available.
    """
    if model_name not in ("crnn", "transformer"):
        model_name = "crnn"

    # TODO Phase 2: replace with real inference
    return MOCK_TEXT, 0.95
```

---

### Step 0.6 — Write `models/loader.py`

Empty dict for now — real model loading happens in Phase 2.

```python
# backend/models/loader.py

# Holds loaded model objects keyed by name: {"crnn": <model>, "transformer": <model>}
# Populated at startup in Phase 2 via FastAPI lifespan events.
loaded_models: dict = {}
```

---

### Step 0.7 — Write `requirements.txt`

```
fastapi
uvicorn[standard]
python-multipart
pillow
opencv-python-headless
numpy
sqlalchemy
aiofiles
python-dotenv
```

---

### Step 0.8 — Run it and verify

```bash
cd backend
uvicorn main:app --reload
```

Open `http://localhost:8000/docs` — you should see the Swagger UI with `/health`, `/models`, `/ocr`.
Test `/ocr` by uploading any image — it should return the mock Devanagari text.

**Checkpoint:** frontend can now call `POST /ocr` and get real JSON back. Tell them the server is up.

---

## Phase 1 — Harden the API skeleton

### Step 1.1 — Add request logging middleware

Add this to `main.py` before the routes:

```python
import logging
from fastapi import Request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    ms = round((time.time() - start) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({ms}ms)")
    return response
```

### Step 1.2 — Add consistent JSON error responses

FastAPI already returns JSON errors. Add a custom handler so all errors have the same shape:

```python
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"error": "Validation failed", "detail": str(exc)})

@app.exception_handler(Exception)
async def generic_error_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
```

### Step 1.3 — Verify CORS with the frontend

Ask the frontend developer what port their Vite dev server runs on (usually `5173`).
Add it to the `allow_origins` list in `main.py`.

---

## Phase 2 — Real model integration

> **Wait for this phase until the ML team delivers the model artifact and confirms Contract A.**

### Step 2.1 — Import ML's preprocessing module

The ML team's preprocessing is at `Preprocessing/preprocess.py`. You must use the **exact same steps** — never reimplement them.

Add a helper in `services/ocr.py` to preprocess a single image for inference:

```python
import sys
import cv2
import numpy as np

sys.path.insert(0, "../Preprocessing")  # point to the shared module

IMG_SIZE = 64  # must match training IMG_SIZE in preprocess.py

def preprocess_for_inference(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )
    resized = cv2.resize(thresh, (IMG_SIZE, IMG_SIZE))
    # normalize to [0, 1] and add batch + channel dims: (1, 1, H, W)
    normalized = resized.astype(np.float32) / 255.0
    return normalized[np.newaxis, np.newaxis, :, :]
```

### Step 2.2 — Load the real model at startup

Update `models/loader.py`:

```python
import torch
import logging
from config import CRNN_MODEL_PATH, TRANSFORMER_MODEL_PATH, DEVICE

logger = logging.getLogger(__name__)
loaded_models: dict = {}


def load_all_models():
    device = torch.device(DEVICE)

    try:
        # ML team delivers crnn.pth + a CRNNModel class
        # from ml_team_package import CRNNModel  ← import their class
        # model = CRNNModel(...)
        # model.load_state_dict(torch.load(CRNN_MODEL_PATH, map_location=device))
        # model.eval()
        # loaded_models["crnn"] = model
        logger.info("CRNN model loaded")
    except Exception as e:
        logger.warning(f"CRNN model not loaded: {e}")

    try:
        # loaded_models["transformer"] = ...
        logger.info("Transformer model loaded")
    except Exception as e:
        logger.warning(f"Transformer model not loaded: {e}")
```

Wire the loader into `main.py` using a lifespan event (run once on startup):

```python
from contextlib import asynccontextmanager
from models.loader import load_all_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_all_models()     # runs once when the server starts
    yield
    # cleanup on shutdown (if needed)

app = FastAPI(title="Devanagari OCR API", version="0.1.0", lifespan=lifespan)
```

### Step 2.3 — Replace the mock in `services/ocr.py`

```python
import torch
import unicodedata
from models.loader import loaded_models
from services.preprocessing import preprocess_for_inference


def run_ocr(image_path: str, model_name: str) -> tuple[str, float]:
    if model_name not in loaded_models:
        # fall back to first available model
        model_name = next(iter(loaded_models), None)
        if model_name is None:
            return "नमस्ते (mock — model not loaded)", 0.0

    model = loaded_models[model_name]
    tensor = torch.from_numpy(preprocess_for_inference(image_path))

    with torch.no_grad():
        output = model(tensor)

    # decode output → text (depends on model type; coordinate exact API with ML team)
    raw_text = decode_output(output, model_name)
    text = unicodedata.normalize("NFC", raw_text)
    confidence = float(output.max())  # adjust per model
    return text, confidence


def decode_output(output, model_name: str) -> str:
    # CRNN: CTC beam decode → string
    # Transformer: token IDs → string via tokenizer
    # Fill in once you have the model artifacts from ML
    raise NotImplementedError("Wire up decoding with the ML team")
```

### Step 2.4 — Add PDF support

```bash
pip install pdf2image
# also install Poppler: https://github.com/oschwartz10612/poppler-windows/releases
```

In `services/ocr.py`, add a helper that converts each PDF page to an image before calling `run_ocr`:

```python
from pdf2image import convert_from_path
import tempfile, os

def run_ocr_pdf(pdf_path: str, model_name: str) -> list[dict]:
    pages = convert_from_path(pdf_path)
    results = []
    for i, page_img in enumerate(pages):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            page_img.save(tmp.name)
            text, conf = run_ocr(tmp.name, model_name)
            os.unlink(tmp.name)
        results.append({"page": i + 1, "text": text, "confidence": conf})
    return results
```

Update the `/ocr` route in `main.py` to call `run_ocr_pdf` when the uploaded file is a PDF.

---

## Phase 3 — Persistence, Hardening & Deploy

### Step 3.1 — Write `db.py`

```python
# backend/db.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class DocumentImage(Base):
    __tablename__ = "document_images"
    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String)
    saved_path = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class RecognizedText(Base):
    __tablename__ = "recognized_texts"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer)
    model_used = Column(String)
    text = Column(Text)
    confidence = Column(Float)
    processing_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)
```

Call `create_tables()` inside the lifespan function in `main.py`.

### Step 3.2 — Save results to DB in the `/ocr` route

```python
from db import SessionLocal, DocumentImage, RecognizedText

# inside the /ocr route, after getting result_text:
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
        processing_time_ms=round(elapsed_ms, 2),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    result_id = rec.id
finally:
    db.close()
```

### Step 3.3 — Add `GET /history/{id}`

```python
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
```

### Step 3.4 — Write the Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and test:

```bash
cd backend
docker build -t ocr-backend .
docker run -p 8000:8000 --env-file .env ocr-backend
```

### Step 3.5 — Write tests

Create `backend/tests/test_api.py`:

```python
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_models():
    r = client.get("/models")
    assert r.status_code == 200
    names = [m["name"] for m in r.json()]
    assert "crnn" in names


def test_ocr_mock(tmp_path):
    import numpy as np, cv2
    img = np.ones((64, 64), dtype=np.uint8) * 255
    p = tmp_path / "test.png"
    cv2.imwrite(str(p), img)
    with open(p, "rb") as f:
        r = client.post("/ocr", files={"file": ("test.png", f, "image/png")}, data={"model_name": "crnn"})
    assert r.status_code == 200
    body = r.json()
    assert "recognized_text" in body
    assert "confidence" in body
```

Run with:

```bash
pip install pytest httpx
pytest backend/tests/
```

---

## Checklist — Definition of Done

- [ ] **Phase 0:** folder scaffolded, mock `/ocr` running, schemas shared with frontend
- [ ] **Phase 1:** `/health`, `/ocr`, `/models` working; CORS correct; logging on
- [ ] **Phase 2:** real model loaded at startup; ML preprocessing imported (not copied); PDF support; NFC normalization
- [ ] **Phase 3:** SQLite DB storing every result; `/history/{id}` works; Dockerfile builds; tests pass; `/docs` reviewed with frontend

---

## Coordination checklist

| Who | What you need from them | When |
|-----|-------------------------|------|
| **ML team** | Contract A: `.pth` artifact + `predict()` signature + exact class name | Before Phase 2 |
| **Frontend** | Confirm CORS origin (Vite port) | Before Phase 1 ends |
| **Frontend** | Confirm Contract B JSON shape is enough | After Step 0.3 |
| **Everyone** | Agree on `/ocr` response JSON in week 1 | Now |

---

## Useful commands (run from `backend/`)

| Task | Command |
|------|---------|
| Start dev server | `uvicorn main:app --reload` |
| API docs | open `http://localhost:8000/docs` |
| Run tests | `pytest tests/` |
| Build Docker | `docker build -t ocr-backend .` |
| Run Docker | `docker run -p 8000:8000 --env-file .env ocr-backend` |
