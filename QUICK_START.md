# Devanagari OCR Quick Start Guide

**For demonstrations, handoffs, and quick reference**
_Last updated: 2026-07-16 — React + FastAPI stack is the primary deployment._

---

## 🚀 5-Minute Demo Setup

### FastAPI Backend
```bash
cd backend
pip install -r requirements.txt
# Run the API server
KMP_DUPLICATE_LIB_OK=TRUE uvicorn main:app --host 0.0.0.0 --port 8000
```

### React Frontend
```bash
cd frontend
npm install
npm run dev
# Open browser to: http://localhost:5173
```

**Or use the Flask demo app (standalone, no setup needed):**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python webapp/server.py
# Open browser to: http://localhost:8000
```

---

## 📊 Key Numbers

| Metric | CRNN | Word-level TrOCR |
|--------|------|------------------|
| **Test Accuracy** | **98.67%** | Synthetic-trained |
| **CER** | 0.0003 | — |
| **WER** | 0.0018 | — |
| **Parameters** | ~6.7M | ~124M |
| **Inference** | ~5 ms/img (CPU) | ~50 ms/img (CPU) |
| **Training** | 22 epochs (T4 GPU) | 6–8 epochs (T4 GPU) |

**Dataset:** 92,000 images, 46 classes (36 consonants + 10 digits), 80/10/10 split

---

## 🎯 API Endpoints (FastAPI)

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/health` | Server health + loaded models |
| `GET` | `/models` | Available OCR models |
| `POST` | `/ocr` | Character-level OCR (CRNN or Transformer) |
| `POST` | `/document` | Document-level OCR with word-level TrOCR |
| `GET` | `/random` | Random test image + prediction verdict |
| `POST` | `/export` | Download as TXT / DOCX / searchable PDF |
| `GET` | `/history` | Past OCR results |

---

## 🧪 Quick Verify

```bash
# Backend health
curl http://localhost:8000/health
# → {"status":"ok","models_loaded":["crnn","transformer"]}

# Run OCR on a test image
curl -X POST http://localhost:8000/ocr \
  -F "file=@Datasets/test/character_1_ka/10963.png" \
  -F "model_name=crnn"
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `OMP: Error #15` | Set `KMP_DUPLICATE_LIB_OK=TRUE` before running |
| `UnicodeEncodeError` in Windows shell | Use `PYTHONIOENCODING=utf-8` when running Python scripts |
| Model not loading | Check `../kaggle_output/artifacts/best_model.pth` exists |
| Port in use | Kill existing process: `taskkill //F //IM uvicorn.exe` |

---

## 📁 Key Files

- `backend/main.py` — FastAPI app + all routes
- `frontend/src/App.jsx` — React application
- `models/crnn/predict.py` — CRNN inference
- `models/trocr/predict_words.py` — Word-level TrOCR inference
- `Preprocessing/preprocess.py` — Shared preprocessing (no train/serve skew)
- `data/charset.json` — 46-class label mapping

---

## 🎓 For the Thesis/Report

**Key results to cite:**
- CRNN: 98.67% accuracy (9,200 held-out test images), CER=0.0003, WER=0.0018
- Full preprocessing pipeline validated (no train/serve skew)
- End-to-end system architecture documented
- Comparative analysis framework ready

**Next steps if continuing:**
- TrOCR character-level GPU re-run for comparison metrics
- Real handwriting fine-tuning for word-level TrOCR
- Production deployment (Docker, Vercel/Netlify)
