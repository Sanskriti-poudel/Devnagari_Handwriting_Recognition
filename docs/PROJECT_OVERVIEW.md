# Project Overview — Devanagari Handwritten Document Recognition (OCR)

_A single shared reference so every team member can explain the project the same way
at the mid-defense. Written 2026-06-16._

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

### 3.5 Backend (inference API) — 🟡 scaffold done (mock), real model not wired
- **FastAPI** service with `/health`, `/ocr` (upload + file validation), `/models`, `/history`, request
  logging, error handling, a **SQLite database** (stores documents + recognized text), tests, and a Dockerfile.
- It currently returns **mock text** — connecting it to the real trained model is the main backend task left.

### 3.6 Frontend (web app) — 🟡 built against the mock
- **React + Vite** app: drag-and-drop upload, image/PDF preview, "Recognize" button, result panel with
  **copy / download .txt**, a **model selector** (CRNN vs Transformer), and confidence/time display.
- Built against the mock API; needs to be pointed at the real backend once that's wired.

### 3.7 Live demo for the defense — ✅ ready now
- A **Streamlit app** (`demo/app.py`) runs the **real trained CRNN** (not a mock): upload or pick a random
  test image → see the preprocessed input, the predicted **Devanagari glyph**, transliteration, and confidence,
  plus a Results tab with the metrics and error-analysis figures. **One command:** `streamlit run demo/app.py`.

---

## 4. Honest scope note (be ready for this question)

The proposal's end goal is **document / word-level** recognition of handwritten Nepali. What we have trained
and measured so far is **isolated character** recognition (the 46-class DHCD dataset). This is a deliberate,
sensible first milestone — it validates the whole pipeline, both model architectures, and the
evaluation/comparison framework on clean data. **Moving to full document/line OCR** needs word/line-level
images with transcriptions (segmentation + sequence labels); that is the natural next phase after mid-defense.
If asked "is this full document OCR yet?", the honest answer is: *"Not yet — we've proven the pipeline and
both models at the character level; word/line data and segmentation are the next phase."*

---

## 5. What's left (short list)

1. **TrOCR re-run** on Kaggle GPU (bug already fixed) → fills the comparison table.
2. **Backend Phase 2:** load the real CRNN (and TrOCR) and replace the mock; Unicode NFC post-processing; PDF support.
3. **Integrate** the ML code with the backend (they currently live on separate Git branches) and point the frontend at the real API.
4. **Phase 2 (research):** move toward **word/line-level** Nepali data for true document OCR.
5. Polish, deploy, and write up the comparison for the report.

_(Full, code-grounded breakdown in [`docs/REMAINING_WORK.md`](REMAINING_WORK.md).)_

---

## 6. Who did what (for the panel)

| Member | Area | Status of their part |
|---|---|---|
| **Sanskriti Poudel** | ML lead — CRNN baseline + evaluation/comparison; frontend | CRNN trained & evaluated (98.67%), error analysis, demo ✅ |
| **Chandan Dhakal** | ML — TrOCR Transformer + EDA/augmentation; frontend | EDA ✅; TrOCR built + bug fixed, needs GPU re-run 🟡 |
| **Savyata Poudel** | Backend (FastAPI + DB) + frontend integration | API scaffold + DB + tests ✅; real-model wiring left 🟡 |
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
pip install -r requirements.txt        # first time
streamlit run demo/app.py              # opens http://localhost:8501
```
Use **"Try it" → "Pick a random test image"** a few times to show live recognition; open the
**"Results"** tab to show the 98.67% metrics and the confusion heatmap. (Test it once in the
presentation browser beforehand so the Devanagari font renders.)
