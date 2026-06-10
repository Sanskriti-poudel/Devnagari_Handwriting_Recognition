# ML — Task Plan

**Owned by:** **Sanskriti (S)** — ML lead — and **Chandan (C)**, working as a pair.
**Deliverable:** data pipeline → two OCR models (CNN–RNN–CTC and Transformer) → evaluation
& comparative analysis. This is the core research deliverable (Objectives i & ii of the proposal).

**Prereqs:** read [`.claude/skills.md`](../.claude/skills.md) §1 and §0b (compute). Framework:
**PyTorch** recommended.

**Compute (CPU vs GPU):** Most work runs on a plain CPU. The **CRNN baseline trains on CPU**
(slow but fine), and **all inference runs on CPU**. Only **Transformer/TrOCR fine-tuning needs
a GPU** — use **Google Colab** (free T4, proposal §3.8) or **Kaggle** (~30 free GPU-hrs/week).
If GPU time is tight: use `trocr-small-handwritten`, fewer epochs, smaller batch, or a data
subset. See `skills.md` §0b for the full breakdown.

**Owner split** — tags on each task: **S** = Sanskriti, **C** = Chandan, **S + C** = both.
- **Sanskriti** owns the **CRNN baseline** + the **evaluation / comparative analysis** (lead).
- **Chandan** owns the **Transformer (TrOCR) pipeline** + **EDA / augmentation**.
- **Shared** (S + C): integration contracts, dataset split, charset, model export.

> The repo already has `Preprocessing/preprocess.py` doing **character-level** preprocessing
> (grayscale → Gaussian blur → adaptive threshold → resize 64×64, class-folder layout).
> Your job extends this into full OCR with two comparable models.

---

## Phase 0 — Setup & contracts (week 1)
- [ ] Create `requirements.txt` (torch, torchvision, opencv-python, numpy, pillow, pandas, matplotlib, tqdm, jiwer/torchmetrics, transformers, datasets). — **C**
- [ ] Document the **model-artifact contract** with backend/Savyata (see `README.md` → Contract A): a `predict(image) -> {"text","confidence"}` function + exact preprocessing steps, decoupled from training code. — **S**
- [ ] Confirm dataset inventory: the Google-Drive preprocessed data, **DHCD** (46 classes), and the custom collected handwritten samples. Note which are *character-level* vs *word/line-level*. — **S + C**

## Phase 1 — Data & CRNN baseline
- [ ] **Audit & finalize preprocessing** (`Preprocessing/`): keep grayscale/denoise/threshold/resize; add **skew correction** and **pixel normalization** (proposal §3.2.2). Make the pipeline a reusable importable function so the backend can run the *exact* same steps. — **S**
- [ ] **EDA:** class counts, image-size distribution, sample grids, class imbalance check. — **C**
- [ ] **Data augmentation** (proposal §3.2.3): rotation, scaling, translation, slight distortion — train-set only. — **C**
- [ ] **Dataset split:** train/val/test (e.g. 80/10/10 or DHCD's 85/15). Persist the split so it is reproducible across both models. — **S + C**
- [ ] **Charset:** build `charset.json` (all Devanagari characters/labels + CTC blank). Shared by training, decoding, and the backend. — **S + C**
- [ ] **CRNN baseline (character-level first):** start with a CNN classifier on DHCD to validate data + tooling, then move to **CNN → BiLSTM → CTC** for sequence (word/line) recognition. — **S**
  - [ ] Optimizer Adam + LR scheduling; dropout; early stopping; checkpoint best val. — **S**
  - [ ] Implement **CTC decoding** (best-path; optionally beam search). — **S**
- [ ] Log training curves; save baseline metrics. — **S**

## Phase 2 — Transformer pipeline
- [ ] **Transformer OCR** (proposal §3.3.2 / §3.4.3): CNN/ViT backbone → encoder–decoder, cross-entropy + teacher forcing. — **C**
  - Practical path: **fine-tune TrOCR** (`microsoft/trocr-base-handwritten`) via HuggingFace `VisionEncoderDecoderModel` on the Devanagari word/line data. Reference: NielsRogge Transformers-Tutorials.
  - [ ] AdamW optimizer; use pretrained weights; resize inputs to processor spec (384×384 for TrOCR). — **C**
- [ ] Keep the **same train/val/test split** as CRNN for a fair comparison. — **C**
- [ ] **Export both models** per Contract A (`.pth` + TorchScript/ONNX where feasible) and write `predict.py` for each. Hand off to backend/Savyata. — **S + C**

## Phase 3 — Evaluation & comparative analysis
- [ ] Implement metrics (proposal §3.7): **Accuracy**, **CER = (S+D+I)/N**, **WER** (use `jiwer`). — **S**
- [ ] Run both models on the held-out test set; record accuracy, CER, WER, **training time, inference latency, param count, robustness to handwriting variation**. — **S + C**
- [ ] **Qualitative analysis:** error cases for matras/modifiers, compound/conjunct characters, *shirorekha* connections; confusion between similar characters. — **C**
- [ ] Produce the **comparison table + plots** (CNN–RNN–CTC vs Transformer) for the report (Ch. 3.6 & Ch. 4). — **S**
- [ ] Write a short `models/README.md`: how to retrain, how to run inference, known limitations. — **S + C**

## Definition of done
- Two trained, exported models with a documented `predict()` interface.
- Reproducible preprocessing + split + charset.
- A comparison report (Accuracy/CER/WER + qualitative findings) ready to drop into the thesis.

## Watch-outs
- **Train/serve skew:** backend must run the *identical* preprocessing — export it as one importable module, don't reimplement.
- Character-level (current data) ≠ sequence OCR. Be explicit which data trains which model; you may need word/line-segmented + transcribed data for true document OCR.
- Keep weights out of git (already in `.gitignore`); share via Drive/releases.
