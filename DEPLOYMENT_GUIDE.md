# Devnagari OCR - Deployment Guide

## Architecture

```
Frontend (React + Vite)     →  Vercel (https://devnagari-ocr.vercel.app)
Backend (FastAPI + ML)       →  Render (https://devnagari-ocr-backend.onrender.com)
```

---

## Repositories

| Service | Repository | Branch |
|---------|------------|--------|
| Frontend | `Sanskriti-Poudel/Devnagari_Handwriting_Recognition` | `frontend` |
| Backend | `Sanskriti-Poudel/devnagari-ocr-backend` | `backend` |

---

## 1. FRONTEND (Vercel)

### URL
https://devnagari-ocr.vercel.app

### Tech Stack
- React 19 + TypeScript
- Vite (build tool)
- Tailwind CSS
- React Router

### Deploy via CLI
```bash
cd wt_frontend/frontend
npx vercel --prod --yes
```

### Environment Variables
Set in Vercel Dashboard → Project → Settings → Environment Variables:

| Name | Value | Environments |
|------|-------|--------------|
| `VITE_USE_MOCK_API` | `false` | Production |

### Key Files
- `wt_frontend/frontend/vercel.json` — Vercel config (rewrites API requests to backend)
- `wt_frontend/frontend/.env` — Local environment (VITE_API_URL, VITE_USE_MOCK_API)

### Troubleshooting

**Network Error on Signup/Login:**
- `VITE_USE_MOCK_API` must be set to `false` for real backend, or `true` for mock auth
- With mock auth, user data is stored in browser localStorage (no real accounts)

**API Requests Failing:**
- Check `vercel.json` rewrites point to correct backend URL
- Current rewrite: `/api/*` → `https://devnagari-ocr-backend.onrender.com/api/*`

**Build Failures:**
```bash
# Clear cache and rebuild
npx vercel build --force
npx vercel --prod --yes
```

**Update API URL:**
1. Edit `wt_frontend/frontend/vercel.json`
2. Change `destination` in rewrites
3. Commit and push: `git add vercel.json && git commit -m "Update API URL" && git push origin frontend`
4. Vercel auto-deploys on push

---

## 2. BACKEND (Render)

### URL
https://devnagari-ocr-backend.onrender.com

### Tech Stack
- FastAPI (Python)
- PyTorch (CRNN + TrOCR models)
- SQLite (file-based, for ocr_results.db)

### Deploy via CLI
```bash
# Install Railway CLI (alternative to Render)
npm install -g @railway/cli
railway login
cd wt_backend
railway init  # Only if creating new project
railway up
```

### Repository Structure
```
wt_backend/
├── backend/           # FastAPI application (MAIN)
│   ├── main.py        # FastAPI app entry point
│   ├── requirements.txt
│   └── ...
├── models/           # ML model weights
│   ├── crnn/checkpoints/best_model.pth
│   └── trocr/checkpoints/model.safetensors
├── data/             # Charset, labels
└── railway.json      # Railway deployment config
```

### Render Settings (for new deployments)
- **Build Command:** (let Render auto-detect)
- **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Root Directory:** `/` (or blank)

### Requirements (backend/requirements.txt)
```
flask>=2.0
fastapi>=0.100
uvicorn[standard]
python-multipart
pillow
opencv-python-headless
numpy
sqlalchemy
aiofiles
python-dotenv
pymupdf
python-docx
torch
torchvision
transformers>=4.30
scikit-learn
pandas
matplotlib
tqdm
jiwer
```

### Troubleshooting

**ModuleNotFoundError: No module named 'flask':**
- Edit `backend/requirements.txt` on GitHub to include missing packages
- Push changes → Render auto-rebuilds

**Build Timeout:**
- Add `NIXPACKS_PYTHON_VERSION=3.11` to environment variables
- Or use Build Command: `pip install -r backend/requirements.txt`

**App Crashes on Startup:**
- Check Start Command is correct: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- Check logs in Render Dashboard → Logs tab

**Model Files Missing (CRUD):**
- Model weights stored in LFS (Git Large File Storage)
- Large files may fail to push via CLI
- Push via GitHub web interface if CLI times out

**Cold Start Slow:**
- Free tier on Render spins down after 15 min inactivity
- First request after idle may take 30-60 seconds

---

## 3. COMMON WORKFLOWS

### Update Frontend
```bash
cd wt_frontend/frontend
# Make code changes
git add -A
git commit -m "Update description"
git push origin frontend
# Vercel auto-deploys
```

### Update Backend
```bash
cd wt_backend
# Make code changes
git add -A
git commit -m "Update description"
git push origin backend
# Render auto-deploys (if GitHub integration enabled)
# OR manually trigger deploy in Render Dashboard
```

### Redeploy Without Code Changes
- **Vercel:** `npx vercel --prod --yes`
- **Render:** Dashboard → Service → Redeploy button

### Check Deployment Status
- **Vercel:** `npx vercel ls`
- **Render:** Dashboard → Service → status indicator

---

## 4. ENVIRONMENT VARIABLES QUICK REFERENCE

### Frontend (.env)
```bash
VITE_API_URL=https://devnagari-ocr-backend.onrender.com
VITE_USE_MOCK_API=false
```

### Backend (Render Environment)
```bash
FLASK_ENV=production
PORT=8000
```

---

## 5. IMPORTANT NOTES

### Mock API vs Real API
- `VITE_USE_MOCK_API=true`: Uses fake data, no backend needed
- `VITE_USE_MOCK_API=false`: Connects to real Render backend

### Model Weights Location
- CRNN: `models/crnn/checkpoints/best_model.pth`
- TrOCR: `models/trocr/checkpoints/model.safetensors`
- TrOCR Words: `models/trocr/checkpoints_words/model.safetensors`

### Database
- Backend uses SQLite: `backend/ocr_results.db`
- Not persisted on free tier — data resets on cold start

### Git Remotes (Common Issue)
If you push to wrong repo:
```bash
# Check current remote
git remote -v

# Fix frontend remote
cd wt_frontend/frontend
git remote set-url origin https://github.com/Sanskriti-Poudel/Devnagari_Handwriting_Recognition.git

# Fix backend remote
cd wt_backend
git remote set-url origin https://github.com/Sanskriti-Poudel/devnagari-ocr-backend.git
```

---

## 6. EMERGENCY FIXES

### Frontend 500 Error
1. Clear browser cache
2. Check Vercel deployment logs
3. Verify `VITE_USE_MOCK_API` is set correctly
4. Redeploy: `npx vercel --prod --yes`

### Backend Not Responding
1. Check Render dashboard for uptime
2. Check if service is in "Sleep" mode (free tier)
3. Wake it up by visiting the URL
4. Check Render logs for errors

### CORS Errors
Backend CORS is configured for specific origins. If frontend URL changes, update CORS settings in `backend/main.py`.

---

## 7. DEPLOYMENT URLs (Current)

| Service | URL |
|---------|-----|
| Frontend (Vercel) | https://devnagari-ocr.vercel.app |
| Backend (Render) | https://devnagari-ocr-backend.onrender.com |
| API Base | https://devnagari-ocr-backend.onrender.com/api |

---

## 8. MONITORING

- **Vercel:** https://vercel.com/dashboard
- **Render:** https://render.com/dashboard
- **GitHub Repos:**
  - Frontend: https://github.com/Sanskriti-Poudel/Devnagari_Handwriting_Recognition
  - Backend: https://github.com/Sanskriti-Poudel/devnagari-ocr-backend
