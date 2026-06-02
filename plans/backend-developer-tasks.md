# Backend — Task Plan

**Owned by:** **Savyata** (sole owner — all tasks below).
**Deliverable:** the inference service that wraps the trained model(s), plus persistence of
documents and results. Implements the DFD processes (preprocess → recognize → post-process)
and the ER data stores.

**Prereqs:** read [`.claude/skills.md`](../.claude/skills.md) §2. Framework: **FastAPI**
recommended; `uvicorn` for serving.

---

## Phase 0 — Setup & contracts (week 1)
- [ ] Scaffold `backend/` with a clean layout:
  ```
  backend/
    main.py            # FastAPI app + routes
    config.py          # env-based settings (dev/prod, device, model paths)
    services/ocr.py    # preprocess -> model -> postprocess (NO logic in routes)
    models/loader.py   # load artifacts once at startup
    schemas.py         # Pydantic request/response models
    db.py              # SQLAlchemy models + session
    requirements.txt
    Dockerfile
  ```
- [ ] Agree **Contract A** (model artifact, with ML) and **Contract B** (`/ocr` JSON, with frontend) — see `README.md`. Lock the response schema so frontend can build against a mock.
- [ ] Build a **mock `/ocr`** that returns canned Devanagari text so frontend isn't blocked.

## Phase 1 — API skeleton (against mock model)
- [ ] `GET /health` — liveness/readiness (needed by any deployment/monitor).
- [ ] `POST /ocr` — accept uploaded image (multipart), validate **file type + size**, return Contract-B JSON. Use the mock model for now.
- [ ] `GET /models` — list available models (`crnn`, `transformer`) so the frontend can let the user pick (supports the proposal's comparative analysis).
- [ ] **CORS** middleware so the React frontend (dev server + deployed origin) can call the API.
- [ ] Structured **logging** + consistent JSON error responses; log request timing.

## Phase 2 — Real model integration
- [ ] **Load the real artifact** from ML (Contract A) **once at startup**; call `model.eval()`; run inference under `torch.no_grad()`; select CPU/GPU from `config.py`.
- [ ] Import ML's **exact preprocessing module** (do not reimplement — avoid train/serve skew).
- [ ] **PDF support:** convert pages to images (`pdf2image`/PyMuPDF) and run OCR per page.
- [ ] **Post-processing:** Unicode **NFC normalization**, line/whitespace reconstruction, confidence aggregation.
- [ ] Optionally run **both models** and return each result so the frontend can show the comparison.

## Phase 3 — Persistence, hardening, deploy
- [ ] **Database** (SQLite for dev, optionally PostgreSQL) via SQLAlchemy, modeling the ER entities:
  `Document_Image`, `Text_Region`, `Recognized_Text`, `OCR_Model`, `Evaluation_Result`.
  Store files on disk/object storage; keep paths in DB.
- [ ] `GET /history/{id}` (and/or list) to retrieve past results.
- [ ] **Error handling** for corrupt images, unsupported formats, oversized files, model failure.
- [ ] **Tests:** unit tests for the service layer; an integration test hitting `/ocr` with a sample image.
- [ ] **Dockerfile** (CUDA base if GPU); document `uvicorn`/`gunicorn` run command and env vars.
- [ ] Auto-generated **OpenAPI docs** (`/docs`) reviewed and shared with the frontend dev.

## Definition of done
- `/health`, `/ocr`, `/models` (+ history) working against the real model.
- Same preprocessing as training; Unicode-correct output; results persisted.
- Dockerized, documented, and demoable end-to-end with the frontend.

## Watch-outs
- Keep preprocessing/inference logic in `services/`, **not** in route handlers (testability).
- Never load the model per-request; preload at startup.
- Validate and bound inputs (file size/type, `max_length` on generation) — protects the service.
- Don't commit model weights; load them from a configured path / mounted volume.
