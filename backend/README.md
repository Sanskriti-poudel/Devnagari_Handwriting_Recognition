# Devanagari OCR — Backend

FastAPI service that runs the trained CRNN/Transformer models and persists results. This
extends the original "Contract B" scaffold (see `plans/savyata-backend-guide.md`) with
auth, dashboard stats, and a paginated/filterable history — the full contract the
`frontend/` app expects when `VITE_USE_MOCK_API=false`.

## Running locally

```bash
cd backend
pip install -r requirements.txt   # torch/torchvision only needed once you have real model weights
cp .env.example .env
uvicorn main:app --reload
```

Open `http://localhost:8000/docs` for interactive API docs. Without model weights present
at `CRNN_MODEL_PATH` / `TRANSFORMER_MODEL_PATH`, every recognition falls back to a fixed
mock response — the server is fully usable end-to-end without them.

## Tests

```bash
pytest tests/
```

## API surface

### Auth
`POST /signup`, `POST /login` → `{user, accessToken}`. `POST /logout`, `POST /refresh-token`,
`POST /forgot-password`, `POST /reset-password`. Passwords are hashed with PBKDF2-SHA256
(stdlib `hashlib`, no native deps); sessions are stateless JWTs (`Authorization: Bearer <token>`).
`forgot-password` / `reset-password` don't send real email yet — see the `TODO` in `main.py`.

### OCR
`POST /api/document` — multipart `image` + `model` (`crnn`|`transformer`). Runs OCR, saves a
row (see `RecognizedText` in `db.py`), and returns
`{text, num_chars, num_lines, avg_confidence, time_ms, model_simulated}`. `model_simulated`
is `true` whenever the requested model has no real weights loaded (currently always true for
`transformer`, since that inference path isn't wired up yet — see `services/ocr.py`).

The legacy `POST /ocr` (Contract B) endpoint is kept working for backwards compatibility but
isn't used by the current frontend.

### History (requires auth, scoped to the logged-in user)
`GET /history?search=&model=&status=&sortBy=&sortDir=&page=&pageSize=` →
`{items, total, page, pageSize}`. `DELETE /history/{id}`.

### Dashboard (requires auth)
`GET /dashboard/stats`, `GET /dashboard/activity` — aggregated from the same
`recognized_texts` table as history.

### Models & health (public)
`GET /models` → `[{id, name, description, status}]`. `GET /health` →
`{status, message, models, checkedAt}`. Status reflects whether real model weights are
loaded (`active`) or the mock fallback is in use (`degraded`).

## Response shape convention

Everything the frontend consumes directly (`UserOut`, `HistoryItemOut`, `DashboardStatsOut`,
etc. in `schemas.py`) is a `CamelModel` — fields are declared snake_case in Python but
serialize as camelCase JSON, matching the TypeScript types in `frontend/src/types`. The one
exception is `/api/document`, which intentionally stays snake_case to match
`ocr.service.ts`'s `DocumentApiResponse` (inherited from the original Flask `webapp/`).

## Known gaps / next steps

- **Transformer inference isn't wired up** (`models/loader.py._load_transformer` is a
  placeholder) — `/api/document` with `model=transformer` still runs CRNN and reports
  `model_simulated: true`.
- **No real email delivery** for forgot/reset password.
- **No DB migrations** — schema changes require deleting the dev SQLite file
  (`ocr_results.db`, gitignored) and letting `create_tables()` recreate it.
