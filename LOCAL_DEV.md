# Devnagari OCR — Local Development Guide

This guide explains how to run the frontend and backend on your local machine for development.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | ≥ 3.10 | [python.org](https://python.org) |
| Node.js | ≥ 18 | [nodejs.org](https://nodejs.org) |
| npm | ≥ 9 | Comes with Node.js |
| Git | Any recent | [git-scm.com](https://git-scm.com) |

---

## Quick Start (5 minutes)

### 1. Clone & Navigate

```bash
git clone https://github.com/Sanskriti-Poudel/Devnagari_Handwriting_Recognition.git
cd Devnagari_Handwriting_Recognition
```

### 2. Start Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # optional: edit for real model paths
uvicorn main:app --reload
```

Backend running at: **http://localhost:8000**

### 3. Start Frontend (new terminal)

```bash
cd frontend
npm install                 # only needed once
npm run dev
```

Frontend running at: **http://localhost:5173**

### 4. Open Browser

Visit **http://localhost:5173** — the frontend will connect to the backend at `http://localhost:8000`.

---

## Project Structure

```
Devnagari_Handwriting_Recognition/
├── backend/                # FastAPI OCR service
│   ├── main.py            # FastAPI app entry point
│   ├── config.py          # Environment variable loading
│   ├── services/
│   │   └── ocr.py         # OCR inference logic
│   ├── ml_models/
│   │   └── loader.py      # Model loading
│   └── requirements.txt
├── frontend/              # React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/         # Page components
│   │   ├── services/     # API clients
│   │   └── stores/        # Zustand state management
│   └── package.json
└── LOCAL_DEV.md           # This file
```

---

## Running the Backend

### Basic

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### With Real Model Weights (Optional)

If you have trained model weights, create `backend/.env` and set:

```env
DEVICE=cpu
CRNN_MODEL_PATH=/path/to/your/best_model.pth
TRANSFORMER_MODEL_PATH=/path/to/trocr/checkpoints
```

Without weights, the backend runs in **mock mode** — OCR returns simulated results but all other features (auth, history, export) work fully.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEVICE` | `cpu` | Device for ML inference (`cpu` or `cuda`) |
| `CRNN_MODEL_PATH` | *(empty)* | Path to CRNN `.pth` file |
| `TRANSFORMER_MODEL_PATH` | *(empty)* | Path to TrOCR checkpoint directory |
| `DATABASE_URL` | `sqlite:///./ocr_results.db` | SQLite database path |
| `JWT_SECRET` | `dev-only...` | Secret for JWT signing |
| `CORS_ORIGINS` | `localhost:5173,localhost:3000` | Allowed CORS origins |
| `MAX_FILE_SIZE_MB` | `20` | Max upload file size in MB |

---

## Running the Frontend

### Basic

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create `frontend/.env.local` (not `.env` — that's gitignored):

```env
VITE_API_URL=http://localhost:8000
VITE_USE_MOCK_API=false
```

> **Note:** The frontend also stores `apiBaseUrl` in localStorage via Zustand's persist middleware. If you've previously used mock mode, clear site data or manually set `apiBaseUrl` to `http://localhost:8000` in the Settings page.

### Build for Production

```bash
npm run build    # outputs to frontend/dist/
npm run preview  # preview the production build
```

---

## Mock Mode vs Real Mode

### Mock Mode (`VITE_USE_MOCK_API=true`)
- OCR responses are **simulated** (random text)
- All UI features work end-to-end
- No backend server needed
- Good for: UI/UX development, design work

### Real Mode (`VITE_USE_MOCK_API=false`)
- Connects to FastAPI backend
- Actual OCR inference (CPU-based)
- Auth, history, export all work
- Good for: full-stack development, testing

### Switching Between Modes

1. **Frontend setting:** Go to Settings page → API Settings → toggle mock mode
2. **Or manually:** Set `VITE_USE_MOCK_API=false` in `.env.local`

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/signup` | No | Register user |
| `POST` | `/login` | No | Login, returns JWT |
| `GET` | `/health` | No | Service health check |
| `POST` | `/api/document` | Yes | Upload image/PDF for OCR |
| `GET` | `/history` | Yes | Paginated OCR history |
| `GET` | `/dashboard/stats` | Yes | User statistics |

Full API docs at **http://localhost:8000/docs** (Swagger UI)

---

## Running Tests

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

---

## Troubleshooting

### "Cannot connect to backend" / CORS errors

1. Is the backend running on port 8000?
2. Check `CORS_ORIGINS` in `backend/config.py` includes `localhost:5173`
3. Try: `curl http://localhost:8000/health`

### "CRNN failed to load" warnings

**This is normal** if you don't have model weights. The backend runs in mock mode and returns simulated OCR results.

### Frontend shows "Mock Mode" but I want real OCR

1. Ensure backend is running (`curl http://localhost:8000/health`)
2. Set `VITE_USE_MOCK_API=false` in `frontend/.env.local`
3. Restart the frontend dev server
4. Clear browser localStorage if previously in mock mode

### Port already in use

```bash
# Find and kill process on port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# Or use a different port
uvicorn main:app --reload --port 8001
# Then update frontend .env to VITE_API_URL=http://localhost:8001
```

### Python packages fail to install

```bash
# Use pip instead of pip3
pip install -r requirements.txt

# If torch install fails, install CPU-only version
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### npm install fails on Windows

```bash
# Run as administrator, or:
npm install --legacy-peer-deps
```

---

## Common Workflows

### Full-Stack Development

1. Terminal 1: `cd backend && uvicorn main:app --reload`
2. Terminal 2: `cd frontend && npm run dev`
3. Open **http://localhost:5173**
4. Make code changes — both servers auto-reload

### UI/UX Only (No Backend)

1. Set `VITE_USE_MOCK_API=true` in `frontend/.env.local`
2. `cd frontend && npm run dev`
3. All OCR returns fake data, but UI is fully interactive

### Testing OCR with Real Models

1. Add model paths to `backend/.env`
2. Restart backend
3. Verify with `curl http://localhost:8000/health` — should show models loaded
4. Upload an image via the frontend

---

## Useful Links

- Backend API docs: http://localhost:8000/docs
- Frontend repo: already cloned locally
- Project GitHub: https://github.com/Sanskriti-Poudel/Devnagari_Handwriting_Recognition
