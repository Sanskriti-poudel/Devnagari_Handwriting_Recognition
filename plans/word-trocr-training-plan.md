# Plan: get real recognized text into the document digitizer

**Date:** 2026-06-23
**Branch:** `ml`
**Goal:** Replace the gibberish OCR text layer with real Devanagari, for **both
printed and handwritten** Nepali pages.

## Context / root cause (confirmed)

Testing the digitizer produced `recognized.docx` / `recognized.pdf` /
`recognized.txt`. The export plumbing works — the searchable PDF correctly
preserves the original scan and all three formats generate. But the OCR **text
layer is gibberish** (`झ२ ८ ८ ज४`, `५णण४`, `गचण नगग`…).

Reason: no `models/trocr/checkpoints_words/` exists, so `/api/document`
(`webapp/server.py:219`) falls back to the 46-class single-character CRNN
(`_ocr_page_charlevel`). That path chops the page into blobs and maps each to one
of 46 DHCD base glyphs — no matras, no punctuation, no real digits — so a dense
document comes out as one nonsense character per blob.

The fix is to produce the word-level TrOCR checkpoint and drop it in. The full
pipeline (line segmentation → word-TrOCR → docx/pdf/txt export) is already built
and wired; the trained weights are the only missing piece.

Verified state:
- Code is already on `origin/ml` (in sync) → the Kaggle clone pulls current code.
- `notebooks/kaggle_train_trocr_words.ipynb` is ready: generates synth data
  in-notebook, trains, sanity-checks, zips the checkpoint for download.
- No local synth data and no checkpoint — both produced by the GPU run.

---

## Phase 0 — Local pre-flight (small edits)

1. **Pin the GPU to T4** in `notebooks/kernel-metadata-words.json`. It currently
   sets `enable_gpu` but not `"machine_shape": "NvidiaTeslaT4"`. Without the pin,
   Kaggle sometimes assigns a Tesla P100 (sm_60) the image's PyTorch can't run →
   `cudaErrorNoKernelImageForDevice` on the first forward pass.
2. **Tune the synth mix for "both equally."** The generator defaults to
   `--clean-ratio 0.25` (75% handwriting-distorted, 25% crisp/printed). For equal
   printed + handwritten handling, set the notebook's generate cell to
   `--clean-ratio 0.5` and raise `--n` to ~12k so each domain gets enough samples.
3. *(Optional, for dense forms)* add a longer-line variant to the synth so the
   model sees full printed lines, not just 1–4-token phrases — the tested form
   has long lines.

## Phase 1 — Train on Kaggle (run yourself; ~30–60 min on a T4)

4. Open `kaggle_train_trocr_words.ipynb` in your Kaggle account →
   **Accelerator = GPU T4**, **Internet = ON** → **Run All**.
5. Watch the two sanity cells:
   - **4b** — generated glyphs must render as real Devanagari, not tofu boxes
     (confirms Devanagari fonts installed).
   - **7b** — predictions on held-out synth must be real multi-glyph text close to
     ground truth (not empty/garbage).
6. Download **`checkpoints_words.zip`** from the Output panel.

## Phase 2 — Integrate locally

7. Unzip into `models/trocr/checkpoints_words/` (kept out of git — large binary;
   matches how the CRNN/TrOCR weights are shared via Kaggle).
8. Confirm `_word_model_available()` returns true, then run
   `python models/trocr/predict_words.py <test_page> --mode page` on the actual
   test page and verify `engine=word-trocr` with real text — **before** touching
   the web app.

## Phase 3 — Re-test end-to-end

9. Restart the web app, re-run document mode on the same page, re-export
   `.docx` / `.pdf` / `.txt`. The searchable-PDF text layer should now read real
   Nepali instead of `झ२ ८ ८ ज४`.

## Phase 4 — Quality iteration (only if needed)

10. If printed forms still read poorly: regenerate synth with more fonts + longer
    lines and retrain. If segmentation misses lines on dense layouts, tune
    `segment_lines` thresholds in `models/crnn/segment.py`.

---

## Honest expectation

Trained on synthetic data, the model reads clean printed and reasonably neat
handwritten **lines** well. A dense bureaucratic form with mixed
Devanagari/Latin, checkboxes, dotted fill-in lines, and tables (like the one
tested) will still be imperfect — that's a layout/domain gap, not a model-loading
bug. Phase 4 narrows it.

## Key files

- `webapp/server.py` — `/api/document` (engine switch), `/api/export`
- `data/generate_synth.py` — synthetic word-image generator
- `models/trocr/dataset_words.py`, `train_words.py`, `predict_words.py`
- `models/crnn/segment.py` — `segment_line_boxes()` (whole-line boxes)
- `notebooks/kaggle_train_trocr_words.ipynb`, `notebooks/kernel-metadata-words.json`
