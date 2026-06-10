# Frontend — Task Plan (shared) · React

**Owned by all three active members**, picked up after their primary deliverables
(ML / backend) are on track. Implements the Use-Case flow from the proposal
(upload → preprocess/preview → perform OCR → view Devanagari text → download).

**Stack:** **React 18 + Vite** (JS or TS), **axios** for API calls. (Proposal mentioned
Streamlit; the team chose React — it calls the same backend API.)

**Owner tags:** **S** = Sanskriti, **C** = Chandan, **Sv** = Savyata.
- **Savyata** owns API wiring / integration / deploy (she built the backend).
- **Sanskriti** owns upload, preview, layout & branding.
- **Chandan** owns the result/download components and error handling.

**Prereqs:** read [`.claude/skills.md`](../.claude/skills.md) §3. Node.js 18+.

---

## Phase 0 — Setup & contracts (week 1)
- [ ] Scaffold the app: `npm create vite@latest frontend -- --template react` (or `react-ts`), then:
  ```
  frontend/
    src/
      App.jsx
      api/client.js        # axios instance, baseURL = import.meta.env.VITE_API_URL
      components/
        UploadZone.jsx     # file picker + drag-and-drop
        ImagePreview.jsx
        ResultPanel.jsx    # recognized text + download
        ModelSelector.jsx
      assets/              # sample images, Noto Sans Devanagari font
    .env                   # VITE_API_URL=http://localhost:8000
    package.json
  ```
  — **C**
- [ ] Agree **Contract B** (`/ocr` JSON response) with backend — see `README.md`. — **Sv**
- [ ] Set `VITE_API_URL` to the backend **mock** so the full UI can be built before the model is ready; create the axios client. — **Sv**

## Phase 1 — Core UI (against mock API)
- [ ] **Upload:** `<input type="file">` + drag-and-drop (`react-dropzone`) for image (PNG/JPG) and PDF; validate file type/size; build `FormData`. — **S**
- [ ] **Preview:** show the selected image via an object URL (`URL.createObjectURL`). — **S**
- [ ] **Recognize button** → `POST /ocr` (multipart) via the axios client; show a loading spinner and disable the button while the request is in flight. — **Sv**
- [ ] **Result panel:** render recognized **Unicode Nepali text** in a copyable `<textarea>`; load Noto Sans Devanagari so matras/conjuncts render correctly. — **C**
- [ ] **Error states:** toast/inline messages for unsupported files, backend down, empty result. — **C**

## Phase 2 — Connect to the real backend & richer UX
- [ ] Switch `VITE_API_URL` to the real backend; verify Unicode round-trips correctly end-to-end. — **Sv**
- [ ] **Model selector** (dropdown: CRNN vs Transformer) populated from `GET /models` — lets the demo show the proposal's comparative analysis. — **Sv**
- [ ] **Side-by-side view:** input image ↔ recognized text; if the backend returns `regions`, overlay bounding boxes on a `<canvas>`. — **S**
- [ ] **Download:** save output as `.txt` via a UTF-8 `Blob` + download link, and/or PDF (`jspdf` with a Unicode font). — **C**
- [ ] Show **confidence** and **processing time** returned by the API. — **C**

## Phase 3 — Polish & deploy
- [ ] Sample images / "try an example" button so reviewers can demo without their own files. — **S**
- [ ] Optional: if a user supplies ground-truth text, display **CER** for that sample (great for the comparison demo). — **C**
- [ ] Responsive layout (component library: MUI/Chakra/Tailwind), clear instructions, app title/branding. — **S**
- [ ] **Deploy:** `npm run build` → static bundle on Vercel / Netlify / Nginx / Docker; set `VITE_API_URL` per environment at build time. Confirm backend **CORS** allows the deployed origin. — **Sv**
- [ ] Write `frontend/README.md`: how to run locally (`npm install && npm run dev`), env vars, how to point at the backend. — **Sv**

## Definition of done
- Upload → recognize → view → download works end-to-end against the real backend.
- Unicode Devanagari renders and downloads correctly.
- Model selector + confidence/timing shown; deployed and demoable.

## Watch-outs
- **CORS:** the backend must allow the frontend origin — coordinate with Savyata early.
- **Unicode rendering:** test with real Devanagari output early; bundle Noto Sans Devanagari rather than relying on system fonts.
- Never hardcode the backend URL — read it from `import.meta.env.VITE_API_URL` (dev vs deployed).
- Keep the UI usable while the backend is slow (spinners, disabled button during request).
- Build against the **mock** first so you are never blocked waiting on the model.
