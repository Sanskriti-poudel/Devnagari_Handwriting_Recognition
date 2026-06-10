# Project Progress Summary

Running log of what's been done and how, so anyone can pick up where we left off.
Project: **Devanagari Handwritten Character Recognition (OCR)** — two comparable
models (CRNN baseline vs TrOCR) + evaluation. Plans in [`plans/ml-developer-tasks.md`](plans/ml-developer-tasks.md).

_Last updated: 2026-06-10._

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

## TrOCR comparison model (pipeline built; needs GPU run)
Fine-tuned ViT-encoder → Transformer-decoder (`microsoft/trocr-base-handwritten`).
Owned by **Chandan**. Code in `models/trocr/`. Built 2026-06-10, structurally validated on CPU
(`smoke_test.py` PASSes); **full fine-tuning still needs a GPU run on Kaggle**.
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

# TrOCR: validate data path, then train on Kaggle GPU (notebooks/kaggle_train_trocr.ipynb)
python models/trocr/smoke_test.py
python models/trocr/evaluate.py --checkpoint models/trocr/checkpoints   # after training
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
1. **Run `notebooks/kaggle_train_trocr.ipynb` on a Kaggle T4** to produce TrOCR weights + `logs/trocr_eval.json`
   (manual GPU step). Then re-run `python models/compare.py` to populate the comparison.
2. **Qualitative error analysis (Phase 3):** matras, conjuncts, similar-character confusion —
   not yet built; needs the TrOCR predictions.
3. Hand `predict.py` (both models) to backend/Savyata.
