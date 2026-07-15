# Running the Project Locally

This repo splits work across branches: `frontend` (Savyata's premium React UI),
`backend` (matching FastAPI service), `ml` (models/training), `data_preprocessing`
(default/main branch). To run the full app, you need the `frontend` and `backend`
branches checked out **at the same time** — use git worktrees so you don't have to
keep switching branches in your main working copy.

## 1. One-time setup: create worktrees

From the main repo directory:

```bash
git worktree add ../wt_backend heads/backend
git worktree add ../wt_frontend heads/frontend
```

This creates two sibling folders next to the repo:
- `../wt_backend` — backend branch checked out
- `../wt_frontend` — frontend branch checked out

(Run `git worktree list` any time to see what's active; `git worktree remove <path>`
to clean one up later.)

## 2. Backend setup (FastAPI)

```bash
cd ../wt_backend/backend
python -m venv venv
source venv/Scripts/activate      # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` — because this is a **worktree** (a sibling folder, not the main repo),
relative paths like `../kaggle_output/...` won't resolve to the real trained model.
Point `CRNN_MODEL_PATH` at the **absolute path** to the real weights in the main repo:

```
CRNN_MODEL_PATH=C:/Users/<you>/.../Devnagari_Handwriting_Recognition/kaggle_output/artifacts/best_model.pth
```

Leave `TRANSFORMER_MODEL_PATH` as-is — this backend branch doesn't have the
word-TrOCR integration wired in yet, so it will report the transformer model as
"degraded" (expected, not an error).

Start it:

```bash
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Verify: `curl http://127.0.0.1:8000/health` should return
`"status":"operational"` with `crnn` → `active`.

## 3. Frontend setup (React + Vite)

```bash
cd ../wt_frontend/frontend
npm install
```

Create `frontend/.env`:

```
VITE_API_URL=http://localhost:8000
VITE_USE_MOCK_API=false
```

(The branch's `.env.example` defaults `VITE_USE_MOCK_API` to `true` — set it to
`false` to hit the real backend above instead of the in-browser mock.)

Start it:

```bash
npm run dev
```

Open **http://localhost:5173**.

## 4. Using the app

- This backend has real auth (JWT) — sign up / log in before OCR features work.
- Upload a Devanagari handwriting image and run recognition — it hits the real
  trained CRNN model.
- TrOCR/transformer model will show as "degraded" — that's expected on this
  branch; CRNN is the only real model wired in here.

## Troubleshooting

- **"This site can't be reached" on :5173** — the Vite dev server isn't running
  or was killed. Check with `netstat`/`Get-NetTCPConnection -LocalPort 5173` and
  restart `npm run dev` from `../wt_frontend/frontend`.
- **Network error when clicking "Recognize Text"** — usually means the backend
  isn't running, `VITE_API_URL` doesn't match where it's listening, or
  `VITE_USE_MOCK_API` is still `true`.
- **CRNN shows "mock mode active" in backend logs** — `CRNN_MODEL_PATH` didn't
  resolve. Since you're in a worktree, use an absolute path (see step 2).
- Both servers log to stdout — redirect to a file
  (`... > server.log 2>&1 &`) if running in the background, so you can `tail`/
  `Read` it to debug startup issues.
