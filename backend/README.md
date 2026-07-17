# Devnagari OCR — Backend

FastAPI service that runs trained CRNN/Transformer models and persists results.
Provides auth (JWT), paginated/filterable history, dashboard stats, multi-page PDF OCR,
and document export (TXT, DOCX, searchable PDF).

## Running locally

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env       # edit CRNN_MODEL_PATH / TRANSFORMER_MODEL_PATH if you have weights
uvicorn main:app --reload
```

Open `http://localhost:8000/docs` for interactive API docs. Without model weights,
all OCR runs in mock mode — the server is fully usable end-to-end for the upload,
history, and export flows.

## Running tests

```bash
pytest tests/
```

---

## API Surface

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/signup` | Register — returns `{user, accessToken}` |
| POST | `/login` | Login — returns `{user, accessToken}` |
| POST | `/logout` | No-op (stateless JWT) |
| POST | `/refresh-token` | Refresh JWT |
| POST | `/forgot-password` | Logged only (no real email) |
| POST | `/reset-password` | No-op |

Passwords hashed with PBKDF2-SHA256; sessions are stateless JWTs
(`Authorization: Bearer <token>`).

### OCR
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/document` | Main OCR endpoint — multipart image/PDF + model selector |
| POST | `/api/document/pages` | Multi-page PDF OCR with per-line boxes |
| POST | `/api/export` | Export result as TXT / DOCX / searchable PDF |
| POST | `/ocr` | Legacy Contract-B endpoint (kept for backwards compat) |

`POST /api/document` accepts `image` (file) + `model` (`crnn`|`transformer`).
Returns `{text, num_chars, num_lines, avg_confidence, time_ms, model_simulated}`.

### History (requires auth, scoped to user)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/history` | Paginated, searchable, filterable by model/status |
| GET | `/history/{id}` | Single history item |
| DELETE | `/history/{id}` | Delete history item |

### Dashboard (requires auth)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/stats` | Total docs, avg confidence, character count, trend |
| GET | `/dashboard/activity` | Recent 8 recognitions |

### Models & Health (public)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/models` | Available models with status (`active`/`degraded`) |
| GET | `/health` | Service health + per-model status |

---

## Response shape convention

All frontend-facing models (`schemas.py`) are `CamelModel` — fields are declared
snake_case in Python but serialize as camelCase JSON. The exception is `/api/document`,
which intentionally stays snake_case to match the legacy `ocr.service.ts` contract.

---

## Architecture

```
backend/
├── main.py              # FastAPI app, all routes, lifespan (model loading on startup)
├── config.py            # Env vars: model paths, JWT_SECRET, CORS_ORIGINS, upload limits
├── schemas.py           # Pydantic request/response models (CamelModel)
├── security.py          # hash_password, verify_password, create_access_token (JWT)
├── db.py                # SQLAlchemy engine, ORM models (User, DocumentImage, RecognizedText)
├── deps.py              # get_db, get_current_user, get_optional_user
├── ml_models/
│   └── loader.py        # load_all_models(), loaded_models dict; loads CRNN + TrOCR
├── services/
│   ├── ocr.py           # run_ocr(), run_ocr_pdf() — dispatches to CRNN or TrOCR
│   ├── document.py       # read_upload_to_pages(), run_document_ocr() — PDF multi-page
│   └── export.py        # build_docx(), build_searchable_pdf()
└── tests/
    └── test_api.py
```

### Model loading
- **CRNN** loaded from `CRNN_MODEL_PATH` — quantized for faster CPU inference
- **Transformer (word-TrOCR)** loaded from `TRANSFORMER_MODEL_PATH` via
  `models/trocr/predict_words.py`

Both run in mock mode if their weights are absent (env vars empty or paths don't exist).

---

## Known gaps

- **No real email delivery** for forgot/reset password.
- **No DB migrations** — schema changes require deleting `ocr_results.db` and letting
  `create_tables()` recreate it.
- **SQLite resets on Render free tier** — `ocr_results.db` is ephemeral on Render's
  free plan; history is lost on cold start.
