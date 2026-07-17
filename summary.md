# Project Progress Summary — Frontend

> **This summary is stale.** The authoritative, up-to-date summary lives in the
> **main monorepo** at `Devnagari_Handwriting_Recognition/summary.md`.
> This file is kept for reference only.

_Last updated: 2026-06-17._

---

## Frontend (React + Vite)

### Current state (2026-07-03)
The React frontend is **fully deployed** at: `https://devnagari-ocr.vercel.app`

Key features:
- Auth: signup/login/logout (JWT in localStorage)
- OCR upload: drag-and-drop, model selector (CRNN / Transformer), confidence display
- History: paginated, searchable, filterable by model/status, sortable by date/confidence
- Dashboard: total docs, avg confidence, character count, confidence trend chart, recent activity
- Export: TXT, DOCX, searchable PDF (lazy-loaded html2canvas + jsPDF)
- Dark/light theme (persists to localStorage, respects `prefers-system-color-scheme`)

### Tech stack
React 18 · Vite · TypeScript · Tailwind CSS · Framer Motion · React Router · Axios ·
React Hook Form + Zod · TanStack Query · Zustand · Radix UI primitives · Recharts

### How it talks to backend
`VITE_USE_MOCK_API=false` (production default) → real FastAPI backend at
`https://devnagari-ocr-backend.onrender.com`. Vercel rewrites `/api/*` to the backend
automatically via `vercel.json`.

### For full history, see
`Devnagari_Handwriting_Recognition/summary.md` — Section 5 "React + FastAPI web app"
