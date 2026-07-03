# Web App — Devanagari OCR (HTML/CSS/JS + Flask)

A small, attractive web frontend backed by the **real trained CRNN** (no mock,
no npm, no separate backend). Plain HTML/CSS/JS served by a tiny Flask server.

## Run (from the repo root)

```bash
pip install flask          # if not already installed
python webapp/server.py
```

Open <http://localhost:8000>. CPU is fine (~5–50 ms/image).

## What it does

- **Drag & drop** or **browse** a single handwritten Devanagari character image, or click
  **🎲 Random sample** to pull one from the held-out test set.
- Shows the **input**, **what the model sees** (preprocessed 64×64), and the **prediction**:
  the Devanagari glyph, transliteration, class name, a **confidence bar**, and timing.
  For random samples it also shows the true label and a ✓/✗ verdict.

## Files

```
webapp/
  server.py            # Flask: serves the page + /api/predict, /api/random (real CRNN)
  templates/index.html # markup
  static/style.css     # styling
  static/app.js         # upload / drag-drop / fetch logic
```

## How it stays consistent with training

`server.py` imports the shared `Preprocessing/preprocess.py` and `models/crnn/predict.py`,
so the web app runs the **exact same** preprocessing + model as evaluation — no train/serve skew.

## Requirements

- CRNN weights at `kaggle_output/artifacts/best_model.pth` and `data/charset.json`.
- `Datasets/test/<class>/*.png` for the "Random sample" button.
- Internet is only used to load the Devanagari web font; it falls back to a system font offline.

> This is the simple demo frontend. The fuller **React + FastAPI** app (model selector,
> history, PDF) lives on the `backend` branch and needs the real-model wiring described in
> `docs/REMAINING_WORK.md`.
