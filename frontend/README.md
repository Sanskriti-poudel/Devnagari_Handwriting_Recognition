# Devnagari OCR — Frontend

A premium, production-styled React SaaS frontend for the Devanagari Handwritten Document
Recognition project. Talks to the FastAPI backend (`wt_backend/backend/`) over REST.

## Stack

React 18 · Vite · TypeScript · Tailwind CSS · Framer Motion · React Router · Axios ·
React Hook Form + Zod · TanStack Query · Zustand · Radix UI primitives · Recharts

## Getting started

```bash
npm install
npm run dev          # http://localhost:5173
```

Sign up with any email, or use the seeded demo account shown on the login page
(`savyata@example.com` / `password123`).

## How this talks to the backend

Set `VITE_USE_MOCK_API=false` (default for production) to talk to the real Render backend.
The Axios service layer (`src/services/*.service.ts`) calls the FastAPI endpoints exactly.

With `VITE_USE_MOCK_API=true`, auth, history, and dashboard are backed by in-browser
`localStorage` (see `src/services/mock/mockDb.ts`) — OCR uploads still hit the real
backend but with mock model responses.

## API integration

The frontend connects to the FastAPI backend at `https://devnagari-ocr-backend.onrender.com`.

**Vercel rewrite** (`vercel.json`): `/api/*` → `https://devnagari-ocr-backend.onrender.com/api/*`

Key endpoints used:
- `POST /api/document` — OCR upload (image or PDF)
- `POST /api/document/pages` — multi-page PDF OCR
- `POST /api/export` — download as TXT / DOCX / PDF
- `POST /signup`, `POST /login` — auth
- `GET /history` — paginated history
- `GET /dashboard/stats`, `GET /dashboard/activity` — dashboard
- `GET /models`, `GET /health` — model & health status

## Project structure

```
src/
├── components/
│   ├── ui/           # Design system primitives (Button, Input, Card, etc.)
│   ├── layout/       # Navbar, Sidebar, Footer
│   ├── ocr/          # UploadZone, ResultDisplay, ModelSelector
│   ├── auth/         # LoginForm, SignupForm
│   ├── dashboard/    # StatsCards, ConfidenceChart, ActivityFeed
│   └── history/      # HistoryTable, HistoryFilters, Pagination
├── pages/
│   ├── Home.tsx
│   ├── Login.tsx / Signup.tsx
│   ├── Dashboard.tsx
│   ├── OCRPage.tsx       # Main recognition page
│   ├── HistoryPage.tsx
│   └── About.tsx
├── hooks/            # TanStack Query hooks per domain
├── services/
│   ├── api.ts        # Axios instance
│   ├── auth.service.ts
│   ├── ocr.service.ts
│   ├── history.service.ts
│   └── dashboard.service.ts
├── stores/           # Zustand stores (theme, auth)
├── types/            # Shared TypeScript domain types
└── lib/              # cn(), formatters, export utilities
```

## Notes

- Dark/light theme persists to `localStorage` and respects `prefers-system-color-scheme`.
- PDF export rasterizes the recognized text with the Devanagari font applied via
  `html2canvas` embedded in a `jsPDF` document — both lazy-loaded on first PDF download.
- `npm run build` runs a full `tsc -b` type check before bundling.
- `VITE_USE_MOCK_API=false` in production — the app expects the real backend.
