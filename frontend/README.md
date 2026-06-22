# Devanagari OCR — Frontend

React 18 + Vite web app for the Devanagari handwritten document recognition system.

## Running locally

**Prerequisites:** Node.js 18+, backend running at `http://localhost:8000`

```bash
cd frontend
npm install
cp .env.example .env     # sets VITE_API_URL=http://localhost:8000
npm run dev              # opens at http://localhost:5173
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |

Always read the backend URL from this variable — never hardcode it.

## Build for production

```bash
npm run build       # outputs to dist/
npm run preview     # preview the built bundle locally
```

Deploy `dist/` to Vercel / Netlify / Nginx.  
Set `VITE_API_URL` to your deployed backend URL at build time:

```bash
VITE_API_URL=https://your-backend.example.com npm run build
```

## Project structure

```
src/
  api/client.js          # axios instance — all API calls go here
  components/
    UploadZone.jsx        # drag-and-drop file picker (react-dropzone)
    ImagePreview.jsx      # preview for uploaded image / PDF indicator
    ModelSelector.jsx     # dropdown populated from GET /models
    ResultPanel.jsx       # text output, copy, download .txt
  App.jsx                 # main layout and state
  App.css                 # all styles
  index.css               # global reset
```

## API contract (Contract B)

`POST /ocr` response the UI expects:

```json
{
  "id": 1,
  "filename": "sample.png",
  "model_used": "crnn",
  "recognized_text": "नमस्ते, यो एक परीक्षण पाठ हो।",
  "confidence": 0.95,
  "processing_time_ms": 12.4,
  "created_at": "2026-06-10T10:00:00"
}
```
