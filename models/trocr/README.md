# TrOCR Pipeline — How to Run

Fine-tuned Transformer OCR (ViT encoder → Transformer decoder) as the
comparison model against the CRNN baseline. Owned by **Chandan**.

## Files
- `dataset.py` — `TrOCRDataset` (reads the shared `data/split_index.json`, runs
  the same `Preprocessing.preprocess`, maps class → **Devanagari glyph**, applies
  train-only augmentation) + collate.
- `augment.py` — mild train-only affine augmentation (rotation/scale/translate/shear).
- `train.py` — AdamW fine-tuning of `microsoft/trocr-base-handwritten`, best-checkpoint
  on val loss, early stopping, CSV logging.
- `evaluate.py` — Accuracy / CER / WER (jiwer) on the **test** split → `logs/trocr_eval.json`.
- `predict.py` — Contract A: `predict(image) -> {"text", "confidence"}` (text = glyph).
- `smoke_test.py` — fast, **network-free** data-path check (run first).

## Labels
Unlike CRNN (opaque class ids for CTC), TrOCR emits text, so targets are the real
Devanagari glyphs from `data/devanagari_labels.py` (e.g. `character_1_ka` → `क`).

## 1. Validate the data path (seconds, CPU, no download)
```bash
python models/trocr/smoke_test.py    # expect PASS
```

## 2. Train on GPU (Kaggle T4 — recommended)
Full fine-tuning needs a GPU. Use `notebooks/kaggle_train_trocr.ipynb`, or run
directly once the dataset is mounted and `DEVNAGARI_DATA_ROOT` points at the
folder containing `train/` and `test/`:
```bash
python models/trocr/train.py
```
Env overrides: `TROCR_MODEL` (use `microsoft/trocr-small-handwritten` if GPU time
is tight), `TROCR_BATCH_SIZE`, `TROCR_EPOCHS`, `TROCR_MAX_TRAIN` (cap train size
for a quick run), `TROCR_LR`. Outputs → `models/trocr/checkpoints/` (HF dir:
weights + processor), log → `logs/trocr_training.csv`.

## 3. Evaluate
```bash
python models/trocr/evaluate.py --checkpoint models/trocr/checkpoints
```

## Notes
- **Same split as CRNN** (`data/split_index.json`) for a fair comparison.
- **Train/serve consistency:** both training and `predict.py` call
  `Preprocessing.preprocess` then the TrOCR processor — don't reimplement.
- Checkpoints are git-ignored — share via Drive/Kaggle output, like the CRNN weights.
- TrOCR is heavy (~334M params for base) and was pretrained on Latin handwriting;
  on single Devanagari characters it is the comparison model, not the production
  recommendation — expect the CRNN baseline to be far faster at inference.
