# Devnagari Handwriting Recognition — Project Handover

## Quick Start

```bash
# Backend (Terminal 1)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (Terminal 2)
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Project Structure

```
Devnagari_Handwriting_Recognition/
├── backend/                 # FastAPI OCR service
│   ├── main.py             # FastAPI app entry point
│   ├── config.py           # Environment variables
│   ├── services/           # Business logic (OCR, document, export)
│   ├── ml_models/          # Model loading
│   ├── requirements.txt    # Python dependencies
│   └── uploads/            # Uploaded files (gitignored)
├── frontend/               # React + Vite frontend
│   ├── src/
│   │   ├── pages/         # Page components
│   │   ├── services/      # API clients
│   │   └── stores/        # Zustand state
│   └── package.json
└── LOCAL_DEV.md           # Detailed local development guide
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, Zustand |
| Backend | FastAPI, SQLAlchemy, JWT |
| ML | PyTorch (CRNN + TrOCR), Transformers |
| Database | SQLite (file-based) |

---

## Key Features

- **OCR**: Upload images/PDFs, get Devanagari text via CRNN or TrOCR models
- **Auth**: JWT-based registration/login
- **History**: Paginated, searchable OCR history
- **Dashboard**: Statistics and activity feed
- **Export**: Download results as TXT, DOCX, or searchable PDF
- **Mock Mode**: Works without ML model weights (simulated OCR results)

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/signup` | No | Register user |
| `POST` | `/login` | No | Login, returns JWT |
| `POST` | `/api/document` | Yes | Upload image/PDF for OCR |
| `POST` | `/api/document/pages` | Yes | Multi-page PDF OCR |
| `POST` | `/api/export` | Yes | Export as TXT/DOCX/PDF |
| `GET` | `/history` | Yes | Paginated history |
| `GET` | `/dashboard/stats` | Yes | User statistics |
| `GET` | `/models` | No | Model status |
| `GET` | `/health` | No | Service health |

Full docs at **http://localhost:8000/docs**

---

## Environment Variables

### Backend (`backend/.env`)

```env
DEVICE=cpu
CRNN_MODEL_PATH=                    # Path to CRNN .pth file (optional)
TRANSFORMER_MODEL_PATH=             # Path to TrOCR checkpoint (optional)
DATABASE_URL=sqlite:///./ocr_results.db
JWT_SECRET=dev-only-insecure-secret-change-me
CORS_ORIGINS=http://localhost:5173
MAX_FILE_SIZE_MB=20
```

### Frontend (`frontend/.env.local`)

```env
VITE_API_URL=http://localhost:8000
VITE_USE_MOCK_API=false
```

---

## Mock Mode

Without ML model weights, the backend runs in **mock mode**:
- OCR returns simulated results
- All other features (auth, history, export) work fully
- No errors — just "CRNN failed to load" warning in logs

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "CRNN failed to load" | Normal — mock mode is active |
| CORS errors | Ensure backend `CORS_ORIGINS` includes `localhost:5173` |
| Port in use | Kill process: `netstat -ano \| findstr :8000` then `taskkill /PID <id> /F` |
| Mock mode stuck | Clear browser localStorage, restart frontend |

---

## Demo Account

```
Email: savyata@example.com
Password: password123
```

---

## See Also

- [LOCAL_DEV.md](./LOCAL_DEV.md) — Detailed development guide
