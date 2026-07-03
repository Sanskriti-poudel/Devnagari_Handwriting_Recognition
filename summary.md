# Project Progress Summary

Running log of what's been done and how, so anyone can pick up where we left off.
Project: **Devanagari Handwritten Character Recognition (OCR)** — two comparable
models (CRNN baseline vs TrOCR) + evaluation. Plans in [`plans/ml-developer-tasks.md`](plans/ml-developer-tasks.md).

_Last updated: 2026-07-03._

---

## Dataset (done)
- **92,000** preprocessed images, **46 classes** (36 consonants + 10 digits), all **64×64** grayscale.
- Perfectly **balanced**: 2,000 images/class (EDA confirmed — no resampling needed).
- Reproducible **80/10/10 split** persisted in `data/split_index.json`
  (train 73,609 / val 9,191 / test 9,200), built by `data/prepare_dataset.py` (stratified, seed 42).
- Class list + CTC blank in `data/charset.json`.
- Preprocessing pipeline `Preprocessing/preprocess.py`: grayscale → Gaussian blur →
  adaptive threshold → deskew → resize 64×64 → normalize [0,1]. **Single source of truth** —
  both training and inference import it so there's no train/serve skew.
  - *Refactor (2026-06-10):* split into `preprocess_array(img)` (in-memory) + `preprocess_image(path)`
    (reads file then calls it), so the backend can preprocess uploaded bytes without a temp file.

## CRNN baseline (done + trained + evaluated)
CNN → BiLSTM → CTC. Owned by **Sanskriti**. Code in `models/crnn/`.
- **Architecture:** `model.py` (`CRNN`, log_softmax output) + `decode_ctc_greedy()`.
- **Training:** `train.py` — Adam, StepLR, gradient clipping, early stopping, best-checkpoint on
  val loss, CSV logging. Auto-detects CUDA; batch 64 on GPU / 16 on CPU.
- **Trained on Kaggle T4** on 2026-06-09 (`kernel-metadata.json`, dataset `sanskritipoudel/devnagari-preprocessed`).
  22 epochs, early-stopped; **best val loss 0.0448 (epoch 12)**.
  Curves in `kaggle_output/artifacts/crnn_training.csv`; weights `kaggle_output/artifacts/best_model.pth`.
- **Evaluation (2026-06-10):** `models/crnn/evaluate.py` on the held-out **test** split → `logs/crnn_eval.json`:

  | Metric | Value |
  |---|---|
  | Accuracy | **98.67%** |
  | CER | 0.0003 |
  | WER | 0.0018 |
  | Parameters | 6,712,559 |
  | Inference latency | ~5 ms/image (CPU) |

- **Bug fixed during eval:** `decode_ctc_greedy` used a broken layout heuristic
  (compared the *time* axis to `len(charset)`) that silently collapsed the batch for
  batch size > 1 — it scored ~0% on most of the test set. Replaced with an explicit
  `time_first` arg (default `True` = the model's native `(T, B, C)` output).
- **Backend handoff (Contract A):** `models/crnn/predict.py` — `predict(image) -> {"text", "confidence"}`,
  accepts a path / OpenCV array / pre-normalized array; runs the shared preprocessing; caches the model.

## TrOCR comparison model (trained → debugged → fixed; needs a re-run)
Fine-tuned ViT-encoder → Transformer-decoder (`microsoft/trocr-base-handwritten`).
Owned by **Chandan**. Code in `models/trocr/`. Built 2026-06-10, structurally validated on CPU
(`smoke_test.py` PASSes).

- **First GPU run (Kaggle T4, 2026-06-11, 3 epochs full set):** trained but scored **0% accuracy
  / CER 1.0 / WER 1.0** on test, with a pathological **val loss ~9.8** (≈ random for the ~50k vocab)
  vs train loss 0.40 — i.e. it never generalised and generation produced empty/garbage strings.
- **Root-caused (2026-06-16, Sanskriti covering Chandan's TrOCR) — two bugs:**
  1. **Wrong decoder start token.** `train.py:configure_model` overrode `decoder_start_token_id`
     to `cls`/0; `microsoft/trocr-base-handwritten`'s own config uses **`sep`/2**. Generating from
     the out-of-distribution start token made the model emit an immediate EOS → empty prediction →
     exactly CER 1.0 / 0% even though teacher-forced training loss looked fine. **Fixed** to use
     `sep_token_id` on both `model.config` and `model.generation_config`.
  2. **Inverted image polarity.** Our preprocessing (`THRESH_BINARY_INV`) is **white-on-black**, but
     TrOCR was pretrained on **dark-ink-on-light-paper**. Feeding inverted contrast into the
     pretrained ViT wrecked its features (the near-random val loss from epoch 1). **Fixed** in
     `dataset.py:array_to_rgb_pil` — TrOCR inputs are now inverted to dark-on-light. (CRNN trains
     from scratch, keeps the original polarity, and is unaffected.)
- **Status:** fixes are in `models/trocr/` on branch `ml`. The HF-documented `decoder_start=2` value
  was confirmed by fetching the base model's `generation_config.json`. A full retrain still needs a
  **Kaggle T4** (`notebooks/kaggle_train_trocr.ipynb`, now bumped to 8 epochs and chained to run
  eval → compare → error-analysis in one pass). The 0% `trocr_eval.json` was **not** merged into
  the main repo's comparison.
- **Labels:** unlike CRNN's opaque class ids, TrOCR emits text, so targets are the real
  **Devanagari glyphs** via `data/devanagari_labels.py` (e.g. `character_1_ka` → `क`).
- `dataset.py` — `TrOCRDataset`: same split + same `preprocess` as CRNN → RGB → TrOCR processor.
- `augment.py` — **train-only** mild affine augmentation (rotation 5°, scale 0.9–1.1,
  translate 5%, shear 5°); kept mild because orientation/shirorekha carry identity.
- `train.py` — AdamW fine-tuning, best-checkpoint on val loss, early stopping, CSV logging.
  Env overrides: `TROCR_MODEL`, `TROCR_BATCH_SIZE`, `TROCR_EPOCHS`, `TROCR_MAX_TRAIN`, `TROCR_LR`.
- `evaluate.py` — same Accuracy/CER/WER metrics as CRNN → `logs/trocr_eval.json` (drops into the comparison table).
- `predict.py` — Contract A `predict(image) -> {"text", "confidence"}` (text = glyph).
- `smoke_test.py` — fast, **network-free** check of label map + preprocessing + augmentation.
- **Kaggle notebook:** `notebooks/kaggle_train_trocr.ipynb` (mirrors the working CRNN notebook).

## Word/line-level TrOCR — document OCR (trained once; retrain in progress) — 2026-06-17 → 2026-07-03
**Why this track exists.** The CRNN and the first TrOCR are both **single-character**
models (46 DHCD classes: consonants + digits, *no matras, conjuncts beyond the 3 DHCD
ones, or punctuation*). The document-mode demo therefore garbles real handwriting:
testing a photo of `मेरो नाम संस्कृति हो।` returned `त्रगल३४ ज`. Root cause is structural,
not a bug — character-segmentation cuts only at whitespace, but the **शिरोरेखा (headline)
joins letters within a word**, so each *word* becomes one blob fed to a model that can
only emit one base glyph. Reading joined Nepali with matras needs a **sequence model
trained on word/line images**, not retraining the single-char model on the same data.

Decision (2026-06-17): bootstrap a word-level TrOCR with **synthetic data** (the standard
"synthetic pretrain → fine-tune on a little real data" OCR recipe), since labelled
handwritten word/line corpora are scarce. Vocabulary is a **mix** of real Nepali words +
random valid syllables; training target is **Kaggle/Colab GPU**.

- **`data/generate_synth.py`** — synthetic Nepali word-image generator. Renders text from
  Devanagari fonts (Windows **Nirmala UI** regular/bold/semilight by default; auto-picks up
  Mangal / Noto Devanagari if present) with handwriting-like augmentation (shear/slant,
  rotation, blur, speckle noise, contrast jitter, random margins). Produces **matras,
  conjuncts (via halant), independent vowels, digits, and danda/punctuation** — exactly what
  the single-char model can't. Output: `<out>/images/*.png` + `<out>/labels.csv`
  (`image_path,text`). CLI: `--out --n --real-ratio --fonts --sizes --wordfile --seed`.
- **`models/crnn/segment.py::segment_line_boxes()`** — returns **one box per text line**
  (union of each line's char boxes), instead of per-character. Sidesteps the headline problem
  by never splitting letters within a word — the sequence model reads the whole line.
- **`models/trocr/dataset_words.py`** — `WordLineDataset` reads `(image → full text)` from
  `labels.csv`; **deterministic** train/val/test split (seeded shuffle, no separate split
  file); word-appropriate augmentation (`fill=255` for dark-on-light, unlike the single-char
  `fill=0`); `MAX_TARGET_LENGTH=64` (a phrase tokenizes to many subword tokens, vs 8 for one
  glyph). Feeds the PIL image straight to the TrOCR processor — **no** 64×64 single-char
  preprocessing, and renders dark-ink-on-light to match the processor at both train + serve.
- **`models/trocr/train_words.py`** — word-level fine-tuner. Reuses the proven loop +
  special-token config (`configure_model`, `run_epoch`) from `train.py`; raises generation
  `max_length` to 64; writes to a **separate** `models/trocr/checkpoints_words/` so it never
  clobbers the single-char checkpoint. Same env overrides as `train.py`; `--labels` points at
  the synthetic `labels.csv`.
- **`models/trocr/predict_words.py`** — `predict_line()` (one line/word crop) and
  `predict_page()` (segment page into lines → read each → stitch into multi-line text +
  annotated image). Default checkpoint `checkpoints_words/` (override `TROCR_WORDS_CHECKPOINT`).
- **Verified on CPU (no GPU, no trained weights needed):** all modules compile; generator
  renders correct Devanagari word images with matching labels; CSV read + deterministic split
  (30 → 18/6/6, reproducible); `segment_line_boxes` on a 3-line page → exactly 3 line boxes;
  full data path through the real TrOCR processor → `pixel_values (B,3,384,384)` + multi-token
  Devanagari labels that **round-trip cleanly** (`संस्कृति।`, `शहर विद्यालय-`).
- **Kaggle training prepared** (`notebooks/kaggle_train_trocr_words.ipynb` + `notebooks/kernel-metadata-words.json`):
  clones branch `ml`, **apt-get installs Devanagari fonts** (Kaggle is Linux — no Nirmala/Mangal),
  **generates the synthetic set in-notebook** (no dataset attachment needed), fine-tunes
  `train_words.py` on a T4, runs a sanity generation, and saves weights+log to
  `/kaggle/working/artifacts`. The generator is now **cross-platform** (`default_font_paths()`
  auto-detects Windows Nirmala/Mangal *or* Linux Lohit/Noto-Devanagari).
- **First trained checkpoint (2026-07-01, Kaggle T4):** trained on the original short-phrase-only
  synth (1–4 tokens/line). Real weights landed locally at `models/trocr/checkpoints_words/`
  (1.3 GB) and are already wired into `webapp/server.py` — `_word_model_available()` is true, so
  document mode uses word-TrOCR instead of the CRNN character fallback.
- **Real-form failure mode found:** testing this checkpoint against an actual printed Nepali
  complaint form showed it collapsing on **long lines** (6+ tokens, mixed Devanagari/Latin,
  list markers, `:-` field labels) — the synth never generated anything that long or that mixed.
- **Synth generator improved (2026-07-02, `ml` commit `9ba7e1ca`)** to cover that regime:
  - `sample_line()` — new long-line generator (5–13 tokens; docstring says up to 16, tracked as a
    known doc/impl mismatch to tighten later), optional numbered/bulleted list prefix
    (१./•/✓), occasional Latin tokens (`ID`, `URL`, `Email`, `Facebook`, …), `/`-joined tokens,
    and a `:-` form-label suffix.
  - `NEPALI_WORDS` extended with document/official-form vocabulary (श्रीमान्, निवेदन, प्रहरी,
    सम्बन्धमा, कार्यालय, दस्तखत, …) — the earlier list skewed conversational/general.
  - `--long-ratio` CLI flag mixes long document lines in with the original short phrases.
  - `MAX_TARGET_LENGTH` raised **64 → 160** in `dataset_words.py` so the longer labels aren't
    silently truncated during training (`predict_words.py` imports the same constant, so
    generation stays in sync automatically).
- **Retrain attempt (2026-07-02, Kaggle T4):** 12k images, 8 epochs, best val loss **1.8006**
  (epoch 8) on the improved synth. **Kaggle's GPU quota was exceeded before the checkpoint was
  exported off the session**, so this run's weights were lost — the 2026-07-01 checkpoint above is
  still the one in use pending a re-run once quota resets. Lesson applied going forward:
  zip + download the checkpoint (or commit a notebook version) immediately after training
  finishes, before running any further cells.
- **Remaining:** re-run training on the improved synth once GPU quota resets, verify the
  sanity cell on the longest generated lines (now explicitly sampled, not just a random tail),
  and swap the new checkpoint into `models/trocr/checkpoints_words/`. The single-character
  CRNN/TrOCR tracks are untouched, so they remain available for the mid-defense comparison.

## Nepali Document Digitizer — web app (front+back done & running; OCR uses CRNN fallback) — 2026-06-22
Turned the OCR web app (`webapp/`, plain HTML/CSS/vanilla-JS + Flask — the Streamlit demo was
retired) into a usable **document digitizer**: scan a page → editable Unicode → download. Built
**offline**, no npm, no React. Three areas committed on their own branches per the team workflow
(`frontend`, `backend`), then **both merged into `ml`** and verified running end-to-end.

- **Backend (`backend` branch → `webapp/server.py`, `webapp/export.py`, `requirements.txt`):**
  - `POST /api/document` — image **or multi-page PDF** → editable Devanagari Unicode. Uses the
    word-level TrOCR when a `checkpoints_words/` checkpoint is present, else the honest **CRNN
    character-segmentation fallback** (`_word_model_available()` picks). Returns per-page text +
    per-line boxes + a `doc_id`. NFC-normalized.
  - `POST /api/export` — `{format: txt|docx|pdf, text, doc_id}`. **txt** (UTF-8), **docx**
    (`build_docx`, python-docx, Devanagari complex-script font slot `w:cs`), **searchable PDF**
    (`build_searchable_pdf`, PyMuPDF: original scan + an **invisible, selectable Unicode text
    layer** rebuilt from the cached page images + OCR line boxes for `doc_id`).
  - Bounded in-memory `_DOC_CACHE` keyed by `doc_id` (so a searchable PDF can be rebuilt after edits).
  - **Bug fixed (2026-06-22):** the searchable PDF shipped with **no text layer** —
    `insert_textbox` returns a *negative* (not an exception) on overflow, so the `try/except`
    fallback never fired and `fontsize = bh*0.7` overflowed the box. Now sizes at `bh*0.6`, checks
    the return value, and falls back to `insert_text` (baseline, never clips). Verified: every line
    is extractable (Ctrl+F / copy).
- **Frontend (`frontend` branch → `index.html`, `app.js`, `style.css`, + two new modules):**
  - **`static/preeti.js`** (NEW) — offline **Preeti↔Unicode** converter. `preetiToUnicode` is a
    faithful port of the canonical Shuvayatra char-map + ordered post-rules (short-i `ि` reorder,
    reph `{`→`र्`, matra reordering, split-vowel coalescence `अ+ा→आ`); `unicodeToPreeti` is a
    cluster-aware inverse. Validated in node: **7/7 known forward pairs** (incl. `g]kfn`→नेपाल),
    **26/26 Unicode→Preeti→Unicode round-trips**.
  - **`static/translit.js`** — romanized→Devanagari typing aid (`namaste`→नमस्ते), now loaded.
  - UI: export bar (**TXT / DOCX / Searchable-PDF** → `/api/export`, stores `doc_id`); a
    **romanized-typing toggle** on the editable text (converts each word on space/Enter); and a
    **"Nepali text tools" card** = live Preeti↔Unicode converter with a direction toggle + ⇄ swap.
- **Verified running (`KMP_DUPLICATE_LIB_OK=TRUE python webapp/server.py`, port 8000):** page +
  both JS modules load; `/api/random` real CRNN (predicted ठ, conf 1.0); `/api/document` →
  text + `doc_id`; txt/docx/searchable-PDF all export and the PDF text layer is extractable.
- **Env note:** Anaconda base + `torch` clash on OpenMP (`libiomp5md.dll already initialized`) —
  run with `KMP_DUPLICATE_LIB_OK=TRUE`. Added deps: `opencv-python`, `PyMuPDF`, `python-docx`,
  `tqdm`, `torch` (CPU).
- **Remaining:** OCR *accuracy* on real joined handwriting still needs the **word-level TrOCR GPU
  run** (the export/editor/Preeti/romanized features all work regardless of which engine loads);
  optional `tools/preeti.py` / `POST /api/preeti` were **not** built (kept client-side like translit).

## React + FastAPI backend — real model wiring (done) — 2026-07-03
The `backend` branch's FastAPI service (`backend/`) had a scaffold with mock OCR
(`docs/REMAINING_WORK.md`'s "biggest gap"). Investigating found CRNN inference was
already real (not mock, contrary to the stale doc) — `services/ocr.py` did genuine CTC
decoding. What was actually still missing was the **TrOCR/transformer path** and one
real bug:

- **`backend/services/preprocessing.py`** duplicated `Preprocessing/preprocess.py`'s
  logic instead of calling it — a train/serve-skew risk (same bug class the shared
  module was written to prevent). Now calls `Preprocessing.preprocess_image()` directly.
- **`backend/models/` renamed to `backend/ml_models/`** — it collided by name with the
  repo-root `models/` package, which blocked importing `models.trocr.predict_words`
  from the backend (whichever "models" got imported first into `sys.modules` would win
  for the whole process). All internal imports (`main.py`, `services/ocr.py`,
  `train.py`) updated to match.
- **`config.py`**: `TRANSFORMER_MODEL_PATH` now points at
  `models/trocr/checkpoints_words` (the only TrOCR checkpoint with real trained
  weights — the single-char `checkpoints/` dir's `model.safetensors` is 0 bytes,
  never trained) instead of a nonexistent `models/transformer.pth`.
- **`ml_models/loader.py` / `services/ocr.py`**: `_load_transformer` / `_infer_transformer`
  delegate to `models/trocr/predict_words.py`'s existing cached loader and
  `predict_line()` — no second implementation of TrOCR inference, and the same
  `DEVICE` is used at load-time and call-time so the two hit the same `lru_cache` entry
  instead of double-loading the 1.3 GB model.
- **Verified live**, not just unit tests: `GET /health` → `models_loaded: ['crnn',
  'transformer']`; `POST /ocr` with `model_name=transformer` on a real dataset image →
  200 OK with real Devanagari text (`शः`, confidence 0.91), not the mock fallback string.
- **Test suite**: created a `.venv` for `backend/` (torch/transformers/fastapi were never
  installed there), added `transformers` to `requirements.txt`. Fixed a pre-existing bug
  in `tests/test_api.py` — `TestClient(app)` wasn't used as a context manager, so
  FastAPI's `lifespan` (which calls `create_tables()`) never ran, and `/history` failed
  with "no such table". All **6/6 tests now pass**.
- **Remaining on this track:** TrOCR only handles single-image `/ocr` calls so far — the
  PDF-page pipeline (`run_ocr_pdf`) and the document-mode features the Flask `webapp/`
  already has (Preeti↔Unicode, TXT/DOCX/searchable-PDF export) haven't been ported to
  the React/FastAPI stack. Whether that's worth doing depends on whether `webapp/` or
  the React+FastAPI app is meant to be the shipped frontend — currently two parallel
  UIs exist.

## EDA (done — Chandan, Phase 1)
`eda/run_eda.py`, outputs in `eda/outputs/`:
- `eda_summary.md`, `class_counts.csv`, `class_distribution.png`,
  `image_size_distribution.png`, `sample_grid.png`.
- Headline: 92k images, 46 balanced classes (2,000 each, imbalance ratio 1.00×), all 64×64.

---

## How to run (from repo root)
```bash
# EDA (CPU, seconds)
python eda/run_eda.py

# CRNN: validate, (GPU) train, evaluate
python models/crnn/smoke_test.py
python models/crnn/train.py                                  # GPU recommended
python models/crnn/evaluate.py --checkpoint kaggle_output/artifacts/best_model.pth --device cpu

# TrOCR (single-char): validate data path, then train on Kaggle GPU (notebooks/kaggle_train_trocr.ipynb)
python models/trocr/smoke_test.py
python models/trocr/evaluate.py --checkpoint models/trocr/checkpoints   # after training

# Word/line-level TrOCR (document OCR): generate synthetic data, train on GPU, then read a page
python data/generate_synth.py --out Datasets/synth --n 5000            # synthetic word images + labels.csv
python models/trocr/train_words.py --labels Datasets/synth/labels.csv  # GPU (Kaggle/Colab) — deferred
python models/trocr/predict_words.py path/to/page.jpg --mode page      # after training

# Document digitizer web app (Flask, real CRNN; CPU is fine) -> http://localhost:8000
KMP_DUPLICATE_LIB_OK=TRUE python webapp/server.py                      # KMP flag: Anaconda+torch OpenMP clash
```
Set `DEVNAGARI_DATA_ROOT` to the folder containing `train/`+`test/` when data isn't at `<repo>/Datasets`.
Dependencies pinned in **`requirements.txt`** (`pip install -r requirements.txt`) — incl. `jiwer` for eval.

## Comparative analysis (Phase 3 — scaffolding done, awaiting TrOCR run)
`models/compare.py` reads `logs/crnn_eval.json` + `logs/trocr_eval.json` and emits:
- `logs/comparison.md` — side-by-side metrics table + auto takeaways for the thesis.
- `logs/comparison_metrics.png` (Accuracy/CER/WER) + `logs/comparison_size.png` (params, latency).
TrOCR is optional: with `trocr_eval.json` absent it writes a CRNN-only report and prompts to run the
TrOCR evaluator. Re-run once TrOCR weights exist to fill the table + plots.

## What's next
1. **Re-run `notebooks/kaggle_train_trocr.ipynb` on a Kaggle T4** (the only remaining GPU step for the
   single-char comparison model). With the two fixes above it should now actually learn — watch val
   loss fall well below ~1 and the `5b` sanity cell print real Devanagari glyphs. The notebook now
   chains train → eval → `compare.py` → `error_analysis.py --model trocr` in one pass, so it produces
   `logs/trocr_eval.json`, the filled comparison table/plots, and the TrOCR error-analysis report together.
2. **Re-run `notebooks/kaggle_train_trocr_words.ipynb`** once Kaggle GPU quota resets, on the improved
   synth (long lines + form vocab, §"Word/line-level TrOCR" above). **Zip and download the checkpoint
   immediately after training finishes** — the 2026-07-02 run's weights were lost to a quota cutoff
   before export.
3. **Qualitative error analysis (Phase 3):** `models/error_analysis.py` now supports **both** models
   (`--model crnn|trocr`). CRNN is done → `logs/crnn_error_analysis.md` (+ pairs CSV + heatmap):
   98.67% overall; hardest char थ (tha, 95%); errors cluster in look-alike consonants (घ↔ध, द↔ढ).
   The TrOCR adapter maps emitted glyphs back to class names via `GLYPH_TO_CLASS` and reuses the same
   analysis core; it runs automatically in the notebook once TrOCR weights exist.
4. Decide whether `webapp/` (Flask, has the full document digitizer) or the React+FastAPI app
   (`backend`/`frontend` branches, now has real CRNN+TrOCR wired but no document-mode/export/Preeti
   features) is the app to keep polishing — right now they're two parallel, unequal UIs.
