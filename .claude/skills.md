# Skills & Technology Reference — Devanagari Handwritten Document Recognition (OCR)

This document lists the **skills, tools, and knowledge** each team member needs for this
project. It is derived from the project proposal (*Devanagari Handwritten Document
Recognition Using OCR*, United Technical College, 2026) and current best-practice
references from the OCR/deep-learning community (see **Sources** at the bottom).

The system has three deliverables that map to three roles:

| Role | Owns | Core deliverable |
|------|------|------------------|
| **ML Developer** | Data → models → evaluation | Two trained OCR pipelines (CNN–RNN–CTC and Transformer) + comparison report |
| **Backend Developer** | Inference serving, API, storage | A REST API that wraps the trained model and persists results |
| **Frontend Developer** | User-facing web app | Upload → preview → recognized Unicode Nepali text → download |

> Team: Bipin Jung Thapa, Chandan Dhakal, Sanskriti Poudel, Savyata Poudel.
> Three roles, four people → one role is shared/paired (recommended: ML, since it is the heaviest).

---

## 0. Shared skills (everyone)

- **Git & GitHub** — branching per feature (`ml/...`, `backend/...`, `frontend/...`), pull requests, code review. The repo already uses feature branches (`data_preprocessing`).
- **Python 3.10+** — virtual environments (`venv`/`conda`), `requirements.txt`, type hints.
- **Project hygiene** — `.gitignore` for datasets/weights (already set: `Datasets/`, `*.pth`, `*.pt`, `*.h5`), never commit large binaries or secrets.
- **Unicode & Devanagari basics** — UTF-8, NFC normalization, the *shirorekha* (header line), matras/modifiers, conjuncts. All text I/O must be Unicode-safe.
- **Reading the proposal** — the methodology (Ch. 3), the DFD/Use-Case/ER/Sequence diagrams (§3.10), and the evaluation metrics (Accuracy, CER, WER).

---

## 0b. Compute requirements (CPU vs GPU)

You do **not** need a personal GPU for most of the project. Only **Transformer training**
genuinely requires one.

| Task | Single CPU? | Notes |
|------|-------------|-------|
| **Frontend (React)** | ✅ Yes | No model runs here — browser/Node only. |
| **Backend API + inference** | ✅ Yes | Loading a trained model and running OCR works on CPU. CRNN inference is fast (ms); Transformer/TrOCR inference is slower (~1–5 s/image) but fine for a demo. |
| **CRNN baseline training** | ⚠️ Feasible, slow | Small CNN on DHCD (32×32, 46 classes) trains on CPU — minutes per epoch. Sequence CTC is heavier but still doable with patience. |
| **Transformer / TrOCR fine-tuning** | ❌ Not realistic | ~330M params → hours-to-days per epoch on CPU. **Use a GPU.** |

**Recommended setup**
- **Develop, serve (backend), and run the frontend on your CPU** — no GPU needed.
- **Train on a free cloud GPU:**
  - **Google Colab** (free T4) — the proposal's choice (§3.8).
  - **Kaggle Notebooks** (~30 free GPU-hrs/week) — good backup.
- **If you must lean toward CPU:** use `microsoft/trocr-small-handwritten` (≈5× fewer params than base), fewer epochs, smaller batch size, and train on a subset first. The **CNN/CRNN side of the comparison is fully CPU-trainable** — the Transformer is what pushes you to Colab/Kaggle.

---

## 1. ML Developer skills

**Goal:** build and compare a baseline deep-learning OCR (CNN–RNN–CTC / CRNN) against a
Transformer-based OCR for Nepali Devanagari text.

### Foundations
- Python data stack: **NumPy, OpenCV, Pillow, pandas, matplotlib**.
- **Deep learning framework:** PyTorch (recommended — most OCR reference code is PyTorch) or TensorFlow/Keras.
- CNN fundamentals (conv/pool/batchnorm), RNN/BiLSTM, attention & the Transformer encoder–decoder.

### OCR-specific
- **Image preprocessing** (already started in `Preprocessing/preprocess.py`): grayscale, Gaussian/median denoise, adaptive thresholding, skew correction, resize, normalization, augmentation (rotation/scale/translation/distortion).
- **Two architectures the proposal requires:**
  1. **CNN–RNN–CTC (CRNN):** CNN feature extractor → BiLSTM → **CTC loss** (no explicit character segmentation). Know best-path vs beam-search CTC decoding.
  2. **Transformer OCR:** CNN/ViT backbone → patch embeddings → encoder–decoder with attention; cross-entropy + teacher forcing. **TrOCR** (`microsoft/trocr-base-handwritten`, HuggingFace `VisionEncoderDecoderModel`) is the practical starting point — fine-tune on Devanagari.
- **Datasets:** the **DHCD** (Devanagari Handwritten Character Dataset — 92k images, 46 classes: 36 consonants + 10 numerals, 32×32 PNG) for character-level baseline; custom collected handwritten samples + word/line-level data for sequence OCR.
- **Character vs sequence framing:** the current preprocessing is *character-level* (class-folder images). For full-document OCR you also need **word/line segmentation** (zone-based: upper/middle/lower) and labeled text strings.
- **Training craft:** dataset split (train/val/test), Adam/AdamW, LR scheduling, dropout, early stopping, mixed precision, checkpointing. Use **Google Colab GPU** (per proposal §3.8).
- **Evaluation:** Accuracy, **CER = (S+D+I)/N**, **WER**; libraries like `jiwer`/`torchmetrics`; confusion analysis for similar-looking characters; qualitative inspection of matras/conjuncts/shirorekha.
- **Model export:** save weights (`.pth`), export a clean `predict(image) -> text` function and ideally **TorchScript/ONNX** so the backend can load without the full training code.

### Key references
- CRNN PyTorch: `Holmeyoung/crnn-pytorch`, `bes-dev/crnn-pytorch`.
- TrOCR fine-tuning notebook: NielsRogge `Transformers-Tutorials` (IAM Seq2SeqTrainer).
- HTR best practices: arXiv 2404.11339 (max-pool count matters; keep CNN+LSTM simple).

---

## 2. Backend Developer skills

**Goal:** expose the trained model as a service and persist documents/results (matches the
DFD data stores: *Annotated Dataset*, *Trained OCR Models*, *Final Unicode Text*, and the ER entities).

### Core
- **Web framework:** **FastAPI** (recommended — async, auto OpenAPI docs, Pydantic validation). Flask is acceptable for a simpler POC.
- **ASGI serving:** `uvicorn` (dev) / `uvicorn` workers under `gunicorn` (prod).
- **Model loading:** load weights **once at startup** (not per request); always call `model.eval()`; run inference under `torch.no_grad()`; pick CPU/GPU via config.
- **API design:**
  - `POST /ocr` — accept an uploaded image/PDF, return recognized Unicode text + confidence + which model was used.
  - `GET /health` — readiness/liveness (required by any deployment/monitor).
  - `GET /models` — list available models (CRNN vs Transformer) so the frontend can offer a choice (supports the proposal's *comparative analysis*).
  - Optional: `GET /history/{id}` for stored results.
- **Service layer separation:** keep preprocessing → model selection → inference → post-processing → logging **out of the route handlers** (modular, testable).
- **File handling:** validate file type/size, handle multi-page PDF (`pdf2image`/`PyMuPDF`), reuse the **same preprocessing pipeline** as training (consistency is critical for accuracy).
- **Post-processing:** Unicode NFC normalization, whitespace/line reconstruction.
- **Persistence:** SQLite/PostgreSQL via SQLAlchemy for the ER-diagram entities (`Document_Image`, `Text_Region`, `Recognized_Text`, `OCR_Model`, `Evaluation_Result`); store uploaded files on disk or object storage, paths in DB.
- **CORS** configured so the React frontend can call the API.
- **Config & secrets:** `config.py` + environment variables; separate dev/prod settings.
- **Logging & errors:** structured logging, consistent JSON error responses, request timing.
- **Packaging:** `Dockerfile` (CUDA base if GPU); optionally TorchServe later if many models.

### Key references
- PyImageSearch "FastAPI for MLOps" (project structure, health endpoint, service layer).
- Medium "Serving a torch model using FastAPI"; Anyscale FastAPI + Ray Serve.

---

## 3. Frontend Developer skills

**Goal:** a **React** single-page web app implementing the Use-Case flow:
upload → preprocess/preview → perform OCR → view Devanagari text → download.
(The proposal mentioned Streamlit; the team has chosen **React** instead — it talks to the
same backend API, so nothing else changes.)

### Core
- **JavaScript/TypeScript + React 18** (function components, hooks: `useState`, `useEffect`).
- **Build tooling:** **Vite** (`npm create vite@latest`) — fast dev server + build. Node.js 18+.
- **HTTP client:** **axios** (or `fetch`) to call the backend `POST /ocr`, `GET /models`, `GET /health`.
- **File upload:** `<input type="file">` / drag-and-drop (e.g. `react-dropzone`), build `FormData` for multipart upload; validate file type/size client-side.
- **State & data:** local component state for upload/result; optionally TanStack Query for request/loading/error handling.
- **Styling:** a component library (MUI / Chakra / Tailwind + shadcn) for quick, clean UI.
- **Image handling:** preview uploaded image via object URL; optionally overlay bounding boxes (`regions`) on a `<canvas>`.
- **Unicode rendering:** browsers render Devanagari natively; bundle a font (e.g. Noto Sans Devanagari) for consistency. Show recognized text in a copyable `<textarea>`; offer **download as `.txt`** (UTF-8 Blob) and/or PDF (`jspdf` with a Unicode font).
- **UX details:** loading spinners, disabled button during request, error toasts, sample images, file-type/size hints, side-by-side "input image ↔ recognized text", model selector (CRNN vs Transformer), optional CER display when ground truth is provided.
- **API config:** read the backend base URL from a Vite env var (`VITE_API_URL`) — never hardcode it.
- **CORS:** backend must allow the frontend origin (coordinate with backend/Savyata).
- **Deployment:** `npm run build` → static bundle on Vercel / Netlify / Nginx / Docker; set `VITE_API_URL` at build time per environment.

### Key references
- [Vite — Getting Started](https://vitejs.dev/guide/), [React docs](https://react.dev/learn)
- [axios](https://axios-http.com/docs/intro), [react-dropzone](https://react-dropzone.js.org/), [Noto Sans Devanagari](https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari)

---

## 4. How the three roles connect (integration contract)

```
[Frontend]  --upload image/PDF-->  [Backend /ocr]  --preprocess+infer-->  [ML model artifact]
[Frontend]  <--Unicode text + confidence + model name--  [Backend]  --persist-->  [DB / storage]
```

- **ML → Backend boundary:** ML delivers a versioned model artifact (`.pth`/TorchScript/ONNX) **plus** a documented `predict(image_array) -> {"text": str, "confidence": float}` function and the exact preprocessing steps. Backend must not depend on training code.
- **Backend → Frontend boundary:** a stable JSON schema for `/ocr` responses, agreed early so both sides can build against a mock.
- **Everyone:** agree on the request/response JSON and the model-artifact format **in week 1** so work proceeds in parallel.

---

## Sources

- CRNN / CTC: [Holmeyoung/crnn-pytorch](https://github.com/Holmeyoung/crnn-pytorch), [bes-dev/crnn-pytorch](https://github.com/bes-dev/crnn-pytorch), [HTR best practices (arXiv 2404.11339)](https://arxiv.org/pdf/2404.11339)
- TrOCR: [microsoft/trocr-base-handwritten](https://huggingface.co/microsoft/trocr-base-handwritten), [TrOCR docs](https://huggingface.co/docs/transformers/model_doc/trocr), [Transformers-Tutorials TrOCR fine-tuning](https://github.com/NielsRogge/Transformers-Tutorials/blob/master/TrOCR/Fine_tune_TrOCR_on_IAM_Handwriting_Database_using_Seq2SeqTrainer.ipynb), [LearnOpenCV TrOCR](https://learnopencv.com/trocr-getting-started-with-transformer-based-ocr/)
- Dataset: [DHCD on UCI ML Repository](https://archive.ics.uci.edu/dataset/389/devanagari+handwritten+character+dataset)
- Backend: [FastAPI for MLOps (PyImageSearch)](https://pyimagesearch.com/2026/04/13/fastapi-for-mlops-python-project-structure-and-api-best-practices/), [Serving a torch model with FastAPI](https://medium.com/swlh/serving-a-torch-model-using-fastapi-37a56220ea3f), [PyTorch + FastAPI in Docker](https://medium.com/@mingc.me/deploying-pytorch-model-to-production-with-fastapi-in-cuda-supported-docker-c161cca68bb8)
- Frontend (React): [Vite Getting Started](https://vitejs.dev/guide/), [React docs](https://react.dev/learn), [axios](https://axios-http.com/docs/intro), [react-dropzone](https://react-dropzone.js.org/), [Noto Sans Devanagari](https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari)
