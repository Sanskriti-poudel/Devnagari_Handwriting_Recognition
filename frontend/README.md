# Devanagari OCR — Frontend

A premium, production-styled React SaaS frontend for the Devanagari Handwritten Document
Recognition project. Talks to the real CRNN backend in `../webapp/server.py` over REST.

## Stack

React 18 · Vite · TypeScript · Tailwind CSS · Framer Motion · React Router · Axios ·
React Hook Form + Zod · TanStack Query · Zustand · Radix UI primitives · Recharts

## Getting started

```bash
npm install
cp .env.example .env   # already done; edit VITE_API_URL if your Flask backend runs elsewhere
npm run dev
```

Open http://localhost:5173. Sign up with any email, or use the seeded demo account shown on
the login page (`savyata@example.com` / `password123`).

## How this talks to the backend

The Flask app in `../webapp/server.py` only implements three endpoints today:
`POST /api/predict`, `POST /api/document`, `GET /api/random`. It has no auth, history, models,
or health endpoints yet.

To keep the UI fully usable in the meantime, `VITE_USE_MOCK_API=true` (the default, see `.env`)
backs auth, OCR history, dashboard stats, and model/health status with an in-browser mock
(`localStorage`, see `src/services/mock/mockDb.ts`). The **OCR recognition itself is real** —
`src/services/ocr.service.ts` uploads to `POST /api/document` on the backend and shows the
actual CRNN's output. Selecting "Transformer" in the model picker still calls the same real
CRNN endpoint (the backend doesn't expose a second model yet) and the result is flagged
`modelSimulated` so the UI says so instead of pretending.

Once the backend grows real `/login`, `/signup`, `/history`, `/models`, `/health` endpoints,
flip `VITE_USE_MOCK_API=false` — the Axios service layer (`src/services/*.service.ts`) already
calls those exact paths.

## Project structure

```
src/
  components/   ui/ (design system), layout/ (shell), common/ (empty/error states, animations)
  features/     auth/ dashboard/ ocr/ history/ profile/ settings/ — feature-scoped UI
  pages/        route-level components (lazy loaded)
  layouts/      AppLayout (sidebar+topbar shell), AuthLayout (split-screen)
  routes/       route guards
  services/     Axios instance + one service per domain + the mock backing store
  stores/       Zustand stores (theme, auth, settings)
  hooks/        TanStack Query hooks per domain
  lib/          cn(), formatters, TXT/PDF export
  types/        shared domain types
```

## Notes

- Dark/light theme persists to `localStorage` and respects `prefers-system-color-scheme`.
- PDF export rasterizes the recognized text (with the Devanagari font actually applied) via
  `html2canvas` and embeds it into a `jsPDF` document, since jsPDF's built-in fonts can't render
  Devanagari glyphs. Both libraries are lazy-loaded on first PDF download.
- `npm run build` runs a full `tsc -b` type check before bundling.
