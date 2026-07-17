# Devnagari Handwriting Recognition — Project Handover

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Git Repos & Branches](#3-git-repos--branches)
4. [Tech Stack](#4-tech-stack)
5. [Project Structure](#5-project-structure)
6. [Deployment](#6-deployment)
7. [Environment Variables](#7-environment-variables)
8. [ML Models](#8-ml-models)
9. [API Reference](#9-api-reference)
10. [Key Features](#10-key-features)
11. [Known Issues & Limitations](#11-known-issues--limitations)
12. [Common Tasks](#12-common-tasks)

---

## 1. Project Overview

**Project Name:** Devnagari Handwriting Recognition
**Type:** Full-stack web application with OCR/ML backend
**Description:** A web app that recognizes Devanagari handwritten text from uploaded images and PDFs using CRNN (CNN+RNN+CTC) and TrOCR (Transformer) models. Supports user accounts, history, document export, and a dashboard.

**Live URLs:**
| Service | URL |
|---------|-----|
| Frontend (Vercel) | https://devnagari-ocr.vercel.app |
| Backend (Render) | https://devnagari-ocr-backend.onrender.com |
| API Base | https://devnagari-ocr-backend.onrender.com/api |

---

## 2. Repository Structure

```
Devnagari_Handwriting_Recognition/          ← Main monorepo (this repo)
├── wt_backend/                             ← Git submodule → devnagari-ocr-backend
│   └── backend/                            ← FastAPI application (THE backend)
│       ├── main.py                         ← FastAPI entry point
│       ├── config.py                       ← Configuration & env vars
│       ├── schemas.py                      ← Pydantic request/response models
│       ├── security.py                     ← JWT auth, password hashing
│       ├── db.py                           ← SQLAlchemy models & session
│       ├── deps.py                         ← FastAPI dependencies (get_db, get_current_user)
│       ├── ml_models/                      ← Model loading & inference
│       ├── services/                       ← Business logic (OCR, document, export)
│       ├── tests/                          ← Unit tests
│       ├── requirements.txt
│       └── uploads/                        ← Uploaded files (gitignored)
├── wt_frontend/                            ← Git submodule → Devnagari_Handwriting_Recognition
│   └── frontend/                           ← React application (THE frontend)
│       ├── src/
│       │   ├── components/
│       │   ├── pages/
│       │   ├── hooks/
│       │   ├── services/                   ← API client
│       │   └── store/                     ← Zustand state
│       ├── vercel.json                     ← Vercel rewrite config
│       └── package.json
├── models/                                 ← ML model weights (not on Git)
│   ├── crnn/checkpoints/best_model.pth
│   └── trocr/checkpoints/model.safetensors
├── data/                                   ← Labels, charset, datasets
├── DEPLOYMENT_GUIDE.md                     ← Deployment instructions
├── DEPLOYMENT_ENV_VARS.md                  ← All env vars documented
└── HANDOVER.md                             ← This file
```

---

## 3. Git Repos & Branches

### 3.1 Main Monorepo
**URL:** `https://github.com/Sanskriti-poudel/Devnagari_Handwriting_Recognition`

| Branch | Purpose |
|--------|---------|
| `main` | Primary branch — synced with frontend/backend submodules |
| `master` | Parallel branch |
| `backend` | Backend work |
| `frontend` | Frontend work |
| `data_preprocessing` | Data prep scripts |
| `ml` | ML experiments |

### 3.2 Submodules

| Submodule | Local Path | Remote Repo |
|----------|-----------|-------------|
| `wt_backend` | `wt_backend/` | `https://github.com/Sanskriti-poudel/devnagari-ocr-backend` |
| `wt_frontend` | `wt_frontend/` | `https://github.com/Sanskriti-poudel/Devnagari_Handwriting_Recognition` |

**Important:** The `wt_frontend` submodule is actually the **same repo** as the parent (circular submodule). It points to the `frontend/` subdirectory of the monorepo.

### 3.3 Updating Submodules
```bash
# In the main repo:
cd wt_backend && git pull origin backend && cd ..
git add wt_backend wt_frontend
git commit -m "Update submodules"
git push origin main
```

---

## 4. Tech Stack

### Backend
| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| Language | Python 3.11 |
| Database | SQLite (`ocr_results.db`) |
| Auth | JWT (PyJWT) |
| Password Hashing | bcrypt via `security.py` |
| File Uploads | `python-multipart`, `aiofiles` |
| PDF Processing | `pymupdf`, `pdf2image` |
| Image Processing | `Pillow`, `opencv-python-headless` |
| ML | `torch`, `torchvision`, `transformers` (TrOCR) |
| Server | Uvicorn |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | React 18/19 + TypeScript |
| Build Tool | Vite |
| Styling | Tailwind CSS |
| Animations | Framer Motion |
| Routing | React Router |
| HTTP Client | Axios |
| Forms | React Hook Form + Zod |
| State | Zustand + TanStack Query |
| Charts | Recharts |
| UI Primitives | Radix UI |
| Deployment | Vercel |

### ML Models
| Model | Architecture | Purpose |
|-------|-------------|---------|
| CRNN | CNN + RNN + CTC | Character-level recognition |
| TrOCR | VisionEncoderDecoder (Transformer) | Word & line recognition |

---

## 5. Project Structure

### 5.1 Backend (`wt_backend/backend/`)

```
backend/
├── main.py              ← FastAPI app, all routes, lifespan (model loading)
├── config.py            ← Env var loading, CORS_ORIGINS, JWT_SECRET, model paths
├── schemas.py           ← Pydantic models for all request/response bodies
├── security.py          ← hash_password, verify_password, create_access_token
├── db.py                ← SQLAlchemy engine, SessionLocal, all ORM models
├── deps.py              ← get_db, get_current_user, get_optional_user
├── ml_models/
│   └── loader.py        ← load_all_models(), loaded_models dict, model inference
├── services/
│   ├── ocr.py           ← run_ocr(), run_ocr_pdf() — main OCR logic
│   ├── document.py      ← read_upload_to_pages(), run_document_ocr()
│   └── export.py        ← build_docx(), build_searchable_pdf()
├── tests/
│   └── test_api.py      ← pytest API tests
├── requirements.txt     ← Python dependencies
├── uploads/             ← Temp uploaded files (auto-cleaned on restart)
└── ocr_results.db       ← SQLite database file
```

### 5.2 Frontend (`wt_frontend/frontend/src/`)

```
src/
├── main.tsx
├── App.tsx
├── components/
│   ├── ui/              ← Reusable UI primitives (Button, Input, Card, etc.)
│   ├── layout/          ← Navbar, Sidebar, Footer
│   ├── ocr/             ← UploadZone, ResultDisplay, ModelSelector
│   ├── auth/            ← LoginForm, SignupForm
│   ├── dashboard/       ← StatsCards, ConfidenceChart, ActivityFeed
│   └── history/         ← HistoryTable, HistoryFilters, Pagination
├── pages/
│   ├── Home.tsx
│   ├── Login.tsx / Signup.tsx
│   ├── Dashboard.tsx
│   ├── OCRPage.tsx      ← Main recognition page
│   ├── HistoryPage.tsx
│   └── About.tsx
├── hooks/
│   ├── useAuth.ts
│   ├── useOCR.ts
│   └── useHistory.ts
├── services/
│   └── api.ts           ← Axios instance, all API call functions
├── store/
│   └── authStore.ts     ← Zustand store for auth state
└── types/
    └── index.ts         ← TypeScript interfaces
```

---

## 6. Deployment

### 6.1 Frontend — Vercel

**Build Command:** `npm run build`
**Output Directory:** `dist`
**Framework:** Vite

```bash
cd wt_frontend/frontend
npx vercel --prod --yes
```

**Auto-deploys on push** to `origin/main` (or whichever branch is linked).

**Rewrite Rule (`vercel.json`):** All `/api/*` requests are forwarded to the backend:
```json
"rewrites": [
  { "source": "/api/:path*", "destination": "https://devnagari-ocr-backend.onrender.com/api/:path*" }
]
```

### 6.2 Backend — Render

**Start Command (CRITICAL):**
```
cd wt_backend/backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```
> ⚠️ Without the `cd wt_backend/backend &&` prefix, Render throws `Could not import module "main"`.

**Build Command:** `pip install -r wt_backend/backend/requirements.txt`

**Environment Variables:** See Section 7 below.

**Cold Start:** Free tier spins down after 15 min. First request after idle takes 30–60s.

---

## 7. Environment Variables

### 7.1 Backend (Render)

| Variable | Value | Notes |
|----------|-------|-------|
| `DEVICE` | `cpu` | CPU inference |
| `CRNN_MODEL_PATH` | *(empty)* | Leave empty for mock mode |
| `TRANSFORMER_MODEL_PATH` | *(empty)* | Leave empty for mock mode |
| `DATABASE_URL` | `sqlite:///./ocr_results.db` | SQLite database |
| `MAX_FILE_SIZE_MB` | `20` | Max upload size in MB |
| `UPLOAD_DIR` | `./uploads` | Temp file directory |
| `JWT_SECRET` | `dev-only-insecure-secret-change-me` | ⚠️ Change in production |
| `JWT_EXPIRES_MINUTES` | `10080` | 7 days |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:5174,http://localhost:3000,https://devnagari-ocr.vercel.app` | Comma-separated |

### 7.2 Frontend (.env for local, Vercel Dashboard for production)

| Variable | Local Value | Production Value |
|----------|-------------|-----------------|
| `VITE_API_URL` | `http://localhost:8000` | *(not needed — vercel.json rewrites)* |
| `VITE_USE_MOCK_API` | `false` | `false` |

---

## 8. ML Models

### Model Weights (NOT on Git — stored locally)

| Model | Local Path |
|-------|-----------|
| CRNN | `C:/Users/Sanskriti Poudel/OneDrive/Desktop/Devnagari recognition/Devnagari_Handwriting_Recognition/kaggle_output/artifacts/best_model.pth` |
| TrOCR Words | `C:/Users/Sanskriti Poudel/OneDrive/Desktop/Devnagari recognition/Devnagari_Handwriting_Recognition/models/trocr/checkpoints_words` |

### Mock Mode
When `CRNN_MODEL_PATH` and `TRANSFORMER_MODEL_PATH` are **empty**, the backend runs in mock mode — all OCR calls return fake/hardcoded responses. The app flow (upload, history, dashboard, export) still works fully.

### Full OCR on Cloud
To enable real inference on Render:
1. Upload model weights to cloud storage (S3, GCS, or Render persistent disk)
2. Set `CRNN_MODEL_PATH` and `TRANSFORMER_MODEL_PATH` to the cloud URLs/paths
3. Consider switching `DEVICE` to `cuda` if GPU is available

---

## 9. API Reference

Base URL: `https://devnagari-ocr-backend.onrender.com`

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/signup` | Register new user |
| POST | `/login` | Login, returns JWT |
| POST | `/logout` | No-op (stateless JWT) |
| POST | `/refresh-token` | Refresh JWT |
| POST | `/forgot-password` | Logged (no real email) |
| POST | `/reset-password` | No-op |

### OCR

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/document` | Upload image/PDF for OCR (main endpoint) |
| POST | `/api/document/pages` | Multi-page OCR with per-line boxes |
| POST | `/api/export` | Export result as txt/docx/pdf |
| POST | `/ocr` | Legacy endpoint (Contract B) |

### History & Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/history` | Paginated, filterable history |
| GET | `/history/{id}` | Single history item |
| DELETE | `/history/{id}` | Delete history item |
| GET | `/dashboard/stats` | Dashboard aggregates |
| GET | `/dashboard/activity` | Recent activity |
| GET | `/models` | Available OCR models |
| GET | `/health` | Service health |

**Interactive docs:** `https://devnagari-ocr-backend.onrender.com/docs`

---

## 10. Key Features

1. **OCR Recognition** — Upload images (JPG, PNG, BMP, TIFF) or PDFs; choose CRNN or Transformer model; get Devanagari text with confidence scores
2. **User Authentication** — JWT-based signup/login; persistent history per user
3. **History** — Paginated, searchable, filterable by model/status, sortable by date/confidence/name
4. **Dashboard** — Total documents, avg confidence, character count, confidence trend chart, recent activity
5. **Export** — Download as TXT, DOCX (layout-preserving), or searchable PDF
6. **Multi-page PDF OCR** — Full document processing with per-page results
7. **Model Switching** — CRNN (character-level) vs Transformer (word/line-level)
8. **Mock Mode** — Full UI without model weights loaded

---

## 11. Known Issues & Limitations

1. **No real model inference in cloud** — `CRNN_MODEL_PATH` and `TRANSFORMER_MODEL_PATH` are empty on Render, so OCR runs in mock mode. Only the upload/history/export UI flow is functional.

2. **Cold start latency** — Render free tier spins down after 15 min idle; first request after idle takes 30–60s.

3. **SQLite not persistent on free tier** — `ocr_results.db` resets when Render restarts (free tier has ephemeral disk).

4. **Nested git repo** — `Devnagari_Handwriting_Recognition/` in the root is a separate git repo, not part of the monorepo. It's ignored via `.gitignore`.

5. **JWT_SECRET is insecure** — Change `JWT_SECRET` env var in production to a random string.

6. **Circular submodule** — `wt_frontend` points to the same repo as the parent monorepo (just a subdirectory). Be careful when updating submodules to avoid circular conflicts.

7. **Model paths use Windows absolute paths** — Local development only. Cloud deployment requires updating these paths.

---

## 12. Common Tasks

### Update Frontend
```bash
cd wt_frontend/frontend
# Make changes
git add -A && git commit -m "description" && git push origin frontend
# Vercel auto-deploys on push
```

### Update Backend
```bash
cd wt_backend
# Make changes
git add -A && git commit -m "description" && git push origin backend
# Render auto-deploys (if GitHub integration is enabled)
# Or manually redeploy in Render Dashboard
```

### Update Main Repo + Sync Submodules
```bash
cd Devnagari_Handwriting_Recognition  # main repo
# Update submodules
cd wt_backend && git pull origin backend && cd ..
cd wt_frontend && git pull origin frontend && cd ..
# Commit submodule updates
git add wt_backend wt_frontend
git commit -m "Sync submodules"
git push origin main
```

### Redeploy Without Code Changes
- **Vercel:** `npx vercel --prod --yes` from `wt_frontend/frontend/`
- **Render:** Dashboard → Service → Redeploy button

### Check Deployment Status
- **Vercel:** https://vercel.com/dashboard
- **Render:** https://render.com/dashboard

### Fix "Could not import module 'main'" on Render
1. Go to Render Dashboard → Backend Service → Settings
2. Set **Start Command** to: `cd wt_backend/backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Redeploy

### Add a New Environment Variable
1. **Backend:** Render Dashboard → Service → Environment → Add variable → Redeploy
2. **Frontend:** Vercel Dashboard → Project → Settings → Environment Variables

### Run Backend Locally
```bash
cd wt_backend/backend
pip install -r requirements.txt
cp .env.example .env  # edit paths if needed
uvicorn main:app --reload
# Open http://localhost:8000/docs
```

### Run Frontend Locally
```bash
cd wt_frontend/frontend
npm install
npm run dev
# Open http://localhost:5173
```

### Run Tests
```bash
# Backend
cd wt_backend/backend
pytest

# Frontend
cd wt_frontend/frontend
npm test
```

---

*Last updated: 2026-07-17*
