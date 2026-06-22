# Mid-Defense Demo Runbook — Scan → Editable Nepali Unicode

_Goal of the demo: show the project's **main working** — upload a scanned image/PDF of
handwritten or printed Nepali and get back **editable Unicode text**, read by our own
**word-level TrOCR** model. Last updated 2026-06-18._

This is the presenter's checklist. It has three parts:
1. **Train the word-level model on GPU** (one-time, on Kaggle).
2. **Drop the trained weights into the repo** so the web app uses them.
3. **Run the demo** and what to say.

---

## 0. The architecture in one breath (for the panel)

- **Single-character track (done, 98.67%):** CRNN (CNN→BiLSTM→CTC) reads one isolated
  Devanagari glyph. Proves the pipeline + baseline. This powers the **Single character** tab.
- **Document track (the main working):** a **word-level TrOCR** (ViT encoder → Transformer
  decoder) reads a *whole line* end-to-end — including **matras, conjuncts and punctuation** —
  so it handles **joined** handwriting that a single-character model structurally cannot.
  This powers the **Document → text** tab.

The web app picks the engine automatically: if the trained word-level checkpoint is present
it uses it; if not, it falls back to the honest character-level path and says so in the UI.

---

## 1. Train the word-level TrOCR (Kaggle T4, one-time)

Everything is prepared — you just run the notebook.

1. Push the latest `ml` branch:
   ```bash
   git push origin ml
   ```
2. On Kaggle: **New Notebook → File → Upload** `notebooks/kaggle_train_trocr_words.ipynb`
   (or import from GitHub). In the settings panel set **Accelerator = GPU T4** and
   **Internet = ON**.
3. **Run all cells.** The notebook:
   - clones branch `ml`, installs Devanagari fonts (Linux has none by default),
   - generates ~8,000 synthetic Nepali word images (cell 4) — a **mix of printed + handwriting-style** renders,
   - fine-tunes `microsoft/trocr-base-handwritten` on them (cell 6, ~6 epochs),
   - prints a sanity check (cell 5b) — predictions should be real multi-glyph Devanagari, **not** empty/garbage,
   - saves weights to `/kaggle/working/artifacts/checkpoints_words/` (cell 8).

   > Watch **val loss fall well below ~1**. If cell 5b prints empty strings or boxes,
   > stop and check the font-install cell (4) and the sanity images (4b) first.

4. **Download** the trained weights. Kaggle can't download a *folder* and the large
   `model.safetensors` often stalls as a loose file — so the notebook's **last cell zips
   the checkpoint** into a single `checkpoints_words.zip` under `/kaggle/working/`. Grab
   that one file from the **Output/Data** panel (⋮ → Download). If your session already
   died, "Save Version" to persist the output, or pull it with the Kaggle API:
   `kaggle kernels output <username>/<notebook-slug> -p ./download`.

### Want it to read your real handwriting better?
Synthetic-only training reads **printed/clean** Nepali well and neat handwriting decently.
For best results on genuine handwriting, after the synthetic run optionally fine-tune a few
more epochs on a small folder of your own labelled handwritten word images (same
`labels.csv` format: `image_path,text`) and re-run `train_words.py --labels <that csv>`.

---

## 2. Install the weights locally (so the web app uses the real model)

Unzip/copy the downloaded checkpoint into the repo at exactly this path:

```
models/trocr/checkpoints_words/
    config.json
    generation_config.json
    model.safetensors          (or pytorch_model.bin)
    preprocessor_config.json
    tokenizer.json / vocab files ...
```

(Or put it anywhere and set `TROCR_WORDS_CHECKPOINT=/abs/path/to/checkpoints_words`.)

Verify it's detected:
```bash
python -c "import webapp.server as s; print('word model loaded:', s._word_model_available())"
# -> word model loaded: True
```
If this prints `True`, the **Document → text** tab will now use the word-level TrOCR.
If it prints `False`, the app still runs — it just falls back to the character path and
labels the output as the CRNN fallback (honest, but not the main working).

---

## 3. Run the demo

```bash
pip install -r requirements.txt      # first time only
python webapp/server.py              # -> http://localhost:8000
```

Open **http://localhost:8000** in a browser whose font renders Devanagari (Chrome/Edge are fine).

### Demo script (≈3 minutes)
1. **Single character tab** → click **🎲 Random sample** a few times. Shows the real CRNN at
   98.67%: the input, "what the model sees", the predicted glyph, transliteration, confidence,
   and a ✓/✗ against ground truth. *"This is our trained baseline."*
2. **Document → text tab** → the green banner confirms **Word-level TrOCR** is active.
   - Upload a **printed** Nepali page first (most reliable) → editable Unicode appears in the
     text box; click **📋 Copy text**.
   - Then upload a **handwritten** sample → show it reading joined writing with matras.
   - Point at the per-line boxes on the annotated image and the confidence/line stats.
   *"This is the main working — a scan of Nepali turns into editable, searchable Unicode."*

### Tips for a smooth live demo
- **Inference is on CPU**, so a page with many lines takes a few seconds per line. For the
  live demo prefer **short pages (2–4 lines)** or single-line/word crops — they're near-instant.
- Have **2–3 known-good sample files ready** (one printed, one handwritten) that you tested
  beforehand. Don't improvise with a brand-new messy photo on stage.
- Test the whole flow **once in the actual presentation browser** before you present, so the
  Devanagari font and the model load are already warm.

---

## 4. If something goes wrong (graceful degradation)

- **Word model not downloaded in time?** The app auto-falls back to the character-level CRNN
  and the UI says so. You can still demo the document flow honestly as "base glyphs", and the
  Single-character tab is rock-solid regardless.
- **A photo returns junk?** It's likely segmentation on a low-contrast/skewed scan — switch to
  one of your prepared high-contrast samples.
- **Port 8000 busy?** `PORT` isn't wired; edit the last line of `webapp/server.py` or stop the
  other process.

---

## 5. Honest scope line (have this ready)

> "At the character level the pipeline is trained and measured — 98.67% with a full CER/WER and
> error analysis. For full document OCR we train a word-level TrOCR on synthetic Nepali so it
> reads whole lines with matras and conjuncts; that's the document demo you're seeing. For the
> final defense we'll improve handwriting accuracy with more real data, polish the UI, and
> deploy it on Vercel."
