# Devnagari OCR — Frontend

A premium, production-styled React frontend for the Devnagari Handwritten Document
Recognition project. Talks to the FastAPI backend over REST.

## Stack

React 19 · Vite · TypeScript · Tailwind CSS · Framer Motion · React Router · Axios ·
React Hook Form + Zod · TanStack Query · Zustand · Radix UI primitives · Recharts

## Getting Started

```bash
npm install
npm run dev          # http://localhost:5173
```

Sign up with any email, or use the seeded demo account shown on the login page
(`savyata@example.com` / `password123`).

## How This Talks to the Backend

Set `VITE_USE_MOCK_API=false` to talk to the real FastAPI backend.
The Axios service layer (`src/services/*.service.ts`) calls the FastAPI endpoints exactly.

With `VITE_USE_MOCK_API=true`, auth, history, and dashboard are backed by in-browser
`localStorage` (see `src/services/mock/mockDb.ts`) — OCR uploads still hit the real
backend but with mock model responses.

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000` by default.

Create `src/.env.local` to override:

```env
VITE_API_URL=http://localhost:8000
VITE_USE_MOCK_API=false
```

Key endpoints used:
- `POST /api/document` — OCR upload (image or PDF)
- `POST /api/document/pages` — multi-page PDF OCR
- `POST /api/export` — download as TXT / DOCX / PDF
- `POST /signup`, `POST /login` — auth
- `GET /history` — paginated history
- `GET /dashboard/stats`, `GET /dashboard/activity` — dashboard
- `GET /models`, `GET /health` — model & health status

## Project Structure

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
- Without model weights, OCR runs in mock mode — all UI works but results are simulated.
