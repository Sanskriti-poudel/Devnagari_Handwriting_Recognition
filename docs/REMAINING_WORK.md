# Remaining Work — Backend & Frontend (+ ML status)

_Grounded in the actual code on each branch as of 2026-06-16, not the aspirational
task-plan checklists. Status legend: ✅ done · 🟡 partial · ❌ not started._

> **Where the code lives (important):** the work is split across branches.
> - `ml` — data pipeline, CRNN, TrOCR, evaluation, comparison, error analysis. **No** `backend/` or `frontend/`.
> - `backend` — full `backend/` + `frontend/` scaffold (Savyata). **Deletes** `data/`, `models/`, `eda/`, `logs/`.
>
> Nothing integrates until these are merged (or the backend is given access to the
> ML package). See **§0 Integration** — it is the real blocker, not any single feature.

---

## §0 — Integration / cross-cutting (the actual blocker) ❌

- [ ] **Merge `ml` + `backend` branches** (or vendor the ML code into the backend). The
      backend needs, at minimum: `Preprocessing/preprocess.py`, `models/crnn/predict.py`
      (+ `model.py`), `models/trocr/predict.py`, `data/charset.json`, `data/devanagari_labels.py`.
      Today they only exist on `ml`; `backend` deleted them.
- [ ] **Lock Contract A artifact layout** and where weights live (weights stay out of git):
      ```
      artifacts/
        crnn/         best_model.pth, charset.json
        transformer/  model/ (HF dir)
      ```
      Backend `config.py` currently points at `../models/crnn.pth` / `../models/transformer.pth`,
      which **do not exist** — the real CRNN weights are `kaggle_output/artifacts/best_model.pth`.
- [ ] **End-to-end smoke test:** upload a real character image → CRNN → correct Devanagari glyph,
      Unicode intact, persisted in DB, rendered in the UI.

---

## §1 — Backend (Savyata) · FastAPI

**Done**
- ✅ Phase 0: project layout, `schemas.py`, `config.py`, `db.py`, mock `/ocr`.
- ✅ Phase 1: `GET /health`, `POST /ocr` (file-type + 10 MB size validation), `GET /models`,
  CORS (localhost:5173/3000), request-timing logging middleware, JSON error handlers.
- ✅ Persistence: SQLite via SQLAlchemy (`DocumentImage`, `RecognizedText`), `GET /history`,
  `GET /history/{id}`.
- ✅ `tests/test_api.py` (health/models/ocr-mock/bad-ext/history), `Dockerfile`, `.env.example`.

**Remaining**
- [ ] **Phase 2 — real model integration (biggest gap).**
  - [ ] `models/loader.py`: actually load CRNN (and TrOCR) at startup — body is still commented out;
        `loaded_models` is empty, so `/models` reports both as `available: false`.
  - [ ] `services/ocr.py`: replace `_MOCK_TEXT` with real inference. Import ML's `predict()`
        (`{"text","confidence"}`) and the **shared** `Preprocessing.preprocess` — do **not**
        reimplement preprocessing (train/serve skew).
  - [ ] Fix `config.py` model paths to the real Contract-A artifact locations.
- [ ] **Post-processing:** Unicode **NFC** normalization, whitespace/line reconstruction,
      confidence aggregation across regions/pages.
- [ ] **PDF:** `run_ocr_pdf` currently falls back to mock if `pdf2image`/Poppler missing — wire the
      real per-page path and document the Poppler dependency (or bundle it in the Docker image).
- [ ] **ER model:** only 2 of 5 proposal entities exist. Add `OCR_Model` and `Evaluation_Result`
      if the thesis needs them persisted; `Text_Region` only matters for document/line OCR (see note).
- [ ] **Integration test** hitting `/ocr` with a **real** model (current test is mock-only).
- [ ] **Deploy:** Dockerfile must also bring in the ML package + mount weights; add the deployed
      frontend origin to CORS; document the `uvicorn`/`gunicorn` run command + env vars.

---

## §2 — Frontend (shared) · React 18 + Vite

**Done**
- ✅ Phase 0: Vite scaffold, `api/client.js` (axios, `VITE_API_URL`), `.env.example`, `README.md`.
- ✅ Phase 1: drag-and-drop upload (`react-dropzone`, type/size validation), image/PDF preview,
  Recognize button with spinner + disabled-in-flight, `ResultPanel` (copyable textarea + download
  `.txt`), error toasts (`<Toaster/>` mounted in `main.jsx`).
- ✅ Phase 2 (partial): `ModelSelector` populated from `GET /models`; confidence + processing-time
  badges; download `.txt`. Noto Sans Devanagari referenced in `index.html`/`App.css`.

**Remaining**
- [ ] **Point at the real backend** (`VITE_API_URL`) and verify Unicode round-trips end-to-end
      (blocked on Backend §1 Phase 2).
- [ ] **Side-by-side input↔text view** and, if the API ever returns `regions`, a `<canvas>`
      bounding-box overlay. _Note: the current backend schema has **no** `regions` field and the
      dataset is single-character, so this is out of scope unless word/line data is added._
- [ ] **Phase 3 polish:** "try an example" sample-image button; optional per-sample **CER** display
      when the user supplies ground truth; responsive-layout pass; app branding.
- [ ] **Deploy:** `npm run build` → Vercel/Netlify/Nginx; set `VITE_API_URL` per environment;
      confirm backend CORS allows the deployed origin.
- [ ] Verify the bundled Noto font actually loads offline (don't rely on a CDN at runtime).

---

## §3 — ML status (for context; see `summary.md` for detail)

- ✅ CRNN baseline trained + evaluated (98.67% acc) + qualitative error analysis.
- ✅ TrOCR pipeline; **0%-accuracy bug root-caused and fixed** (decoder-start token + image polarity)
  on `ml` 2026-06-16.
- ❌ **Only remaining ML step:** re-run `notebooks/kaggle_train_trocr.ipynb` on a Kaggle T4 with the
  fixes (needs GPU). It then auto-produces `trocr_eval.json`, the filled comparison, and the TrOCR
  error analysis.

---

## Suggested order

1. **§0** merge/integrate branches + lock artifact layout (unblocks everything).
2. **Backend §1 Phase 2** real CRNN inference (TrOCR can follow after its GPU re-run).
3. **Frontend §2** point at real backend, verify Unicode end-to-end.
4. Post-processing, PDF, deploy, polish.
