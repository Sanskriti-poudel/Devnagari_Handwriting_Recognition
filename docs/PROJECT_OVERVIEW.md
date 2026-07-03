# Project Overview — Devanagari Handwritten Document Recognition (OCR)

_A single shared reference so every team member can explain the project the same way
at the mid-defense. Written 2026-06-16; updated 2026-06-22 (document-digitizer web app:
Preeti↔Unicode, romanized typing, txt/docx/searchable-PDF export); updated 2026-07-03
(React/FastAPI backend now has real CRNN+TrOCR wired in; word-level TrOCR synth improved
for long/mixed-script lines, retrain in progress)._

---

## 1. What the project is (in one paragraph)

We are building a **deep-learning OCR system for handwritten Nepali (Devanagari)
text** — software that reads an image of handwriting and turns it into editable,
searchable **Unicode** text. The motivation is national: a huge amount of Nepali
government, legal, and archival records exist only on paper or as scanned images,
which can't be searched, edited, or preserved digitally. Existing OCR works well for
printed English but is unreliable for handwritten Devanagari because the script is
hard — it has modifiers (matras), compound/conjunct characters, the connecting top
line (*shirorekha*), and many look-alike characters. We tackle this with **two model
families and compare them**: a traditional deep-learning model (**CRNN: CNN → BiLSTM
→ CTC**) and a modern **Transformer** model (**TrOCR**).

**College / program:** United Technical College (Pokhara University), BE Computer Engineering.
**Team:** Bipin Jung Thapa, Chandan Dhakal, Sanskriti Poudel, Savyata Poudel.

---

## 2. What the proposal said (our commitments)

**Two objectives:**
1. Build an **end-to-end OCR system** for Devanagari Nepali using deep learning + a Transformer model.
2. Do a **comparative analysis**: traditional deep-learning OCR **vs** Transformer OCR.

**Methodology (proposal Ch. 3):**
- **Data:** collect/various handwritten Nepali samples; split into train / validation / test.
- **Preprocessing:** grayscale → noise removal → contrast/adaptive threshold → **skew correction**
  → resize → pixel **normalization**; plus **data augmentation** (rotation, scaling, translation, slight distortion) on the training set only.
- **Two model pipelines:**
  - **CNN–RNN–CTC (CRNN)** — CNN extracts visual features, BiLSTM models sequence, **CTC loss** aligns
    output to text without needing per-character segmentation. *(Baseline.)*
  - **Transformer OCR** — CNN/ViT backbone → Transformer encoder–decoder with attention; trained with
    cross-entropy + teacher forcing; **fine-tune pretrained weights** (AdamW). *(The "modern" model.)*
- **Training:** Adam (CRNN) / AdamW (Transformer), learning-rate scheduling, dropout, early stopping.
- **Evaluation:** **Accuracy, CER (Character Error Rate), WER**, plus training time, inference latency,
  model size, and robustness; **qualitative** error analysis of matras / compounds / *shirorekha* / look-alikes.
- **Interface:** a **simple web interface** (proposal mentioned Streamlit) — upload → recognize → view → download.
- **System design:** Context diagram, DFD, Use-Case, **ER diagram** (entities: Document Image, Text Region,
  Recognized Text, OCR Model, Evaluation Results), Sequence diagram.
- **Tools:** Python, OpenCV, PyTorch, CRNN + Transformer, Streamlit.

---

## 3. What we have done so far (status)

> **Headline for the panel:** the full pipeline works end to end on **isolated Devanagari
> characters** — preprocessing → trained CRNN → **98.67% test accuracy** → evaluation →
> a live demo. The Transformer (TrOCR) comparison model is built and a training bug has
> been fixed; it needs one more GPU run to report its numbers.

### 3.1 Dataset & preprocessing — ✅ done
- **~92,000 images, 46 classes** (36 consonants + 10 digits), all **64×64 grayscale**, perfectly
  **balanced** (2,000/class). Standard **DHCD** (Devanagari Handwritten Character Dataset).
- Reproducible **80/10/10 split** (train 73,609 / val 9,191 / test 9,200), saved so both models use the *same* split.
- **Preprocessing pipeline** implemented exactly as the proposal describes (grayscale → Gaussian blur →
  adaptive threshold → **deskew** → resize 64×64 → normalize). It is **one shared module** used by both
  training and inference, so there is no "train/serve skew."
- **EDA** done (class counts, image-size distribution, sample grids — confirmed the data is balanced).

### 3.2 Model 1 — CRNN baseline — ✅ trained & evaluated
- Architecture: **CNN → BiLSTM → CTC**, with greedy CTC decoding.
- Trained on a **Kaggle T4 GPU**; early-stopped; best validation loss at epoch 12.
- **Test-set results (held-out 9,200 images):**

  | Metric | Value |
  |---|---|
  | **Accuracy** | **98.67%** |
  | CER | 0.0003 |
  | WER | 0.0018 |
  | Parameters | ~6.7M |
  | Inference | ~5 ms/image (CPU) |

- **Qualitative error analysis** done: hardest character थ (*tha*, ~95%); most errors are between
  visually similar consonants (e.g. घ↔ध, द↔ढ) — exactly the look-alike problem the proposal predicted.

### 3.3 Model 2 — TrOCR (Transformer) — 🟡 built, bug fixed, needs a re-run
- Full fine-tuning pipeline for `microsoft/trocr-base-handwritten` (ViT encoder → Transformer decoder),
  using the **same split + same preprocessing** as CRNN for a fair comparison, with train-only augmentation.
- First GPU run scored **0%** — we **root-caused two bugs and fixed them**: (1) the decoder start-token was
  set wrong, making the model output empty text; (2) image colour polarity was inverted relative to what the
  pretrained model expects. **Remaining ML work = one Kaggle GPU re-run** to produce its Accuracy/CER/WER.

### 3.4 Comparison & evaluation tooling — ✅ ready
- A script produces the **CRNN-vs-TrOCR comparison table + plots** automatically; another produces the
  **qualitative error analysis** (per-class accuracy, most-confused pairs, confusion heatmap) for **both** models.
  These fill in the moment TrOCR's numbers exist.

### 3.5 Backend (inference API) — ✅ real CRNN + TrOCR wired in and verified (updated 2026-07-03)
- **FastAPI** service with `/health`, `/ocr` (upload + file validation), `/models`, `/history`, request
  logging, error handling, a **SQLite database** (stores documents + recognized text), tests, and a Dockerfile.
- Both models now run **real inference**, verified live (not just unit tests): `GET /health` reports
  `models_loaded: ['crnn', 'transformer']`, and `POST /ocr` with `model_name=transformer` returns real
  Devanagari text from the word-level TrOCR checkpoint. Only falls back to mock text if a checkpoint is
  genuinely missing.
- Along the way: fixed a train/serve-skew risk (backend was duplicating the shared preprocessing
  logic instead of calling it), resolved a package-name collision (`backend/models` → `backend/ml_models`)
  that was blocking the TrOCR import, and fixed a test-harness bug so all 6 backend tests pass.
- **Remaining:** TrOCR only covers single-image `/ocr` calls — the PDF-page pipeline and the
  document-mode features (Preeti↔Unicode, TXT/DOCX/searchable-PDF export) that `webapp/` already has
  haven't been ported here. See §5.

### 3.6 Frontend (web app) — 🟡 built against the mock; backend is real now
- **React + Vite** app: drag-and-drop upload, image/PDF preview, "Recognize" button, result panel with
  **copy / download .txt**, a **model selector** (CRNN vs Transformer), and confidence/time display.
- Built against the mock API. The backend (§3.5) now serves real CRNN + TrOCR results, so this just
  needs pointing at it (`VITE_API_URL`) and a pass to verify Unicode renders correctly end-to-end.

### 3.7 Live demo + document digitizer — web app — ✅ ready now (updated 2026-06-22)
The live interface is now a small **Flask + HTML/CSS/vanilla-JS web app** (`webapp/`) backed by the
**real trained CRNN** (the earlier Streamlit demo was retired). It runs **offline**, CPU is fine
(`KMP_DUPLICATE_LIB_OK=TRUE python webapp/server.py` → http://localhost:8000), and it covers both the
character demo and the start of the proposal's real goal — turning a scan into editable Unicode:
- **Character mode:** upload or pick a random test image → preprocessed input, predicted **Devanagari
  glyph**, transliteration, confidence, and a ✓/✗ verdict against the true label.
- **Document mode:** upload a page **or multi-page PDF** → editable Devanagari Unicode (word-level
  TrOCR when its checkpoint is present, else the honest CRNN character-segmentation fallback), then
  **download as TXT, DOCX, or a searchable PDF** (the original scan with an invisible, selectable
  Unicode text layer — so the page becomes Ctrl+F-able).
- **Nepali text tools (all client-side, offline):** a **Preeti↔Unicode** converter (digitize legacy
  Preeti-font documents and back), and **romanized typing** (type `namaste` → नमस्ते) so a non-Nepali
  typist can correct the OCR text.

### 3.8 Word/line-level OCR — document recognition — 🟡 built & verified on CPU, training pending (started 2026-06-17)
This is the move from single characters toward the proposal's real goal: reading **whole handwritten
lines** of Nepali, **with matras, conjuncts and punctuation**.
- **Why it was needed:** the demo's "Document → text" mode garbled real handwriting (a photo of
  `मेरो नाम संस्कृति हो।` came out as `त्रगल३४ ज`). This is **structural, not a bug**: the models are
  single-character classifiers, and character-segmentation can only cut at whitespace — but the
  **शिरोरेखा (top headline) joins the letters of a word**, so each *word* became one blob handed to a
  model that can only output one base glyph. The fix is a **sequence model trained on word/line images**.
- **Approach (standard OCR recipe):** **synthetic pretraining** — generate word images from Devanagari
  fonts with handwriting-like distortion (labelled handwritten word datasets are scarce) — then optionally
  fine-tune on a little real handwriting. Vocabulary is a **mix** of real Nepali words + random syllables.
- **Built this session (all new files — the single-char tracks are untouched):**
  - a **synthetic word-image generator** (`data/generate_synth.py`) producing matras/conjuncts/digits/
    punctuation that the single-char model can't, with image + text-label pairs;
  - **line segmentation** (`segment_line_boxes`) that crops whole lines instead of characters;
  - a **word-level TrOCR dataset + trainer + page-inference** path (`dataset_words.py`,
    `train_words.py`, `predict_words.py`) reusing the existing TrOCR architecture.
- **Verified on CPU** (no GPU/weights needed): generator output is correct, the data path produces the right
  tensors, and Devanagari phrases round-trip through the tokenizer.
- **Trained once (2026-07-01):** real weights exist at `models/trocr/checkpoints_words/` and are already
  wired into `webapp/server.py`'s document mode. Testing against a real printed form exposed a **long-line
  failure mode** (6+ token lines, mixed Devanagari/Latin, list markers) the original short-phrase-only synth
  never covered.
- **Synth improved (2026-07-02)** with a long-line generator, official-form vocabulary, and a raised
  tokenizer length cap to match. A retrain on the improved data got to **best val loss 1.8006 (8 epochs)**
  before **Kaggle's GPU quota cut the session before the checkpoint was exported** — that run's weights
  were lost, so the 2026-07-01 checkpoint remains the one in production pending a re-run once quota resets.

---

## 4. Honest scope note (be ready for this question)

The proposal's end goal is **document / word-level** recognition of handwritten Nepali. What we have trained
and measured so far is **isolated character** recognition (the 46-class DHCD dataset) — a deliberate,
sensible first milestone that validates the whole pipeline, both model architectures, and the
evaluation/comparison framework on clean data. As of **2026-06-17 we have started the word/line phase**:
the full word-level pipeline (synthetic data generator → line segmentation → word-level TrOCR dataset,
trainer, and page inference) is **built and verified on CPU**; what remains is the **GPU training run**.
If asked "is this full document OCR yet?", the honest answer is: *"At the character level it's trained and
measured (98.67%); for word/line OCR the full pipeline is built and the data path is verified — we just
haven't run the GPU training yet."*

---

## 5. What's left (short list)

1. **TrOCR re-run** on Kaggle GPU (bug already fixed) → fills the single-char comparison table.
2. **Word/line-level OCR retrain (2026-07-03):** synth generator now covers long, mixed-script,
   form-style lines; the 2026-07-02 training run reached best val loss 1.8006 but its checkpoint was
   lost to a Kaggle quota cutoff before export. Needs a re-run once quota resets — **download/export
   the checkpoint immediately after training**, before running any further cells.
3. **Document digitizer web app — ✅ done & running (2026-06-22):** real CRNN, multi-page PDF, editable Unicode, **TXT/DOCX/searchable-PDF export**, **Preeti↔Unicode**, and **romanized typing**. (This is a self-contained Flask app.)
4. **React+FastAPI backend — ✅ real models wired (2026-07-03):** CRNN and word-level TrOCR both run real
   inference, verified live. Still missing the document-mode features (PDF pages, Preeti, export) that
   `webapp/` has, and the React frontend still needs to be pointed at it. **Decide** whether this stack
   or `webapp/` is the one to keep building on — they're currently two parallel, unequal UIs.
5. Polish, deploy, and write up the comparison for the report.

_(Full, code-grounded breakdown in [`docs/REMAINING_WORK.md`](REMAINING_WORK.md).)_

---

## 6. Who did what (for the panel)

| Member | Area | Status of their part |
|---|---|---|
| **Sanskriti Poudel** | ML lead — CRNN baseline + evaluation/comparison; frontend | CRNN trained & evaluated (98.67%), error analysis, demo ✅ |
| **Chandan Dhakal** | ML — TrOCR Transformer + EDA/augmentation; frontend | EDA ✅; TrOCR built + bug fixed, needs GPU re-run 🟡 |
| **Savyata Poudel** | Backend (FastAPI + DB) + frontend integration | API scaffold + DB + tests ✅; real CRNN+TrOCR wiring ✅ (2026-07-03); frontend still points at mock 🟡 |
| **Bipin Jung Thapa** | (Supporting) | — |

---

## 7. Mid-defense talking points (60-second version)

1. **Problem:** handwritten Nepali government records can't be searched/edited; existing OCR fails on Devanagari.
2. **Goal:** an OCR system that outputs editable Unicode Nepali, comparing a CNN-RNN-CTC model with a Transformer.
3. **Done:** built the full preprocessing pipeline + a balanced 92k / 46-class dataset; trained the **CRNN baseline to 98.67% test accuracy** with CER/WER and a confusion analysis; built the TrOCR Transformer pipeline and a backend API + web app; and we have a **live demo** recognizing characters with the real model.
4. **In progress / next:** one GPU re-run to get the Transformer's numbers and complete the comparison; then move from single characters toward full word/line document OCR, and connect the web app to the real model.
5. **Why it matters:** supports e-governance, digital archiving, and preservation of Nepali records.

## 8. How to run the demo (presenter)

```bash
# from the repo root
pip install -r requirements.txt                 # first time
KMP_DUPLICATE_LIB_OK=TRUE python webapp/server.py   # opens http://localhost:8000
```
(The `KMP_DUPLICATE_LIB_OK=TRUE` flag avoids an Anaconda+torch OpenMP clash; harmless elsewhere.)
Show **Single-character** mode with **🎲 Random sample** a few times for live recognition (✓/✗ vs the
true label), then **Document → text** to scan a page and **download a searchable PDF / DOCX**, and the
**Nepali text tools** card for the Preeti↔Unicode converter and romanized typing. (Test it once in the
presentation browser beforehand so the Devanagari font renders.)
