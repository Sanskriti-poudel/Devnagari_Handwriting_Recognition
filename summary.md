# Project Progress Summary — Backend

> **This summary is stale.** The authoritative, up-to-date summary lives in the
> **main monorepo** at `Devnagari_Handwriting_Recognition/summary.md`.
> This file is kept for reference only.

_Last updated: 2026-06-17._

---

## Backend (Flask → FastAPI migration)

### Current state (2026-07-03)
The `wt_backend/backend/` FastAPI service is **fully deployed** at:
`https://devnagari-ocr-backend.onrender.com`

Key features wired up:
- `POST /api/document` — image/PDF OCR (real CRNN + TrOCR, or mock if no weights)
- `POST /api/document/pages` — multi-page PDF OCR with per-line boxes
- `POST /api/export` — TXT / DOCX / searchable PDF
- Auth: `/signup`, `/login`, `/logout`, JWT refresh
- History: paginated, searchable, filterable, sortable
- Dashboard: stats + activity feed
- `GET /models`, `GET /health`

### Important deployment note
**Render Start Command (required):**
```
cd wt_backend/backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```
Without the `cd wt_backend/backend &&` prefix, Render throws `Could not import module "main"`.

### Mock mode
`CRNN_MODEL_PATH` and `TRANSFORMER_MODEL_PATH` are empty on Render → OCR runs in mock mode.
The upload/history/dashboard/export flows work end-to-end.

### For full history, see
`Devnagari_Handwriting_Recognition/summary.md` — Section 5 "React + FastAPI web app"
