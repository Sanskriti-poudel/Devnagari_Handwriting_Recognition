# Kaggle TrOCR Quicktest — Debug Log (2026-07-15)

Chronological record of debugging the word-level TrOCR "quick sanity check"
kernel (`sanskritipoudel/devnagari-trocr-words-quicktest`). Kept separate from
`docs/PROJECT_GUIDE.md`'s troubleshooting playbook because this is a detailed
case log of one specific debugging session, not general reference — but
every fix below is also folded into `PROJECT_GUIDE.md` §5 for future
reference. Read this if you want the full story of *why*; read
`PROJECT_GUIDE.md` if you just want the fix.

## Objective

Before committing to the full production retrain (12k synthetic images, 8
epochs, ~8-16h on a Kaggle T4), run a cheap sanity check (2k images, 2
epochs, ~15-30 min) to confirm two untested changes actually help real-world
accuracy:
- 8 newly bundled open-license Devanagari fonts (`assets/fonts_devanagari/`)
- a new numpy-only sinusoidal "wave warp" augmentation in
  `data/generate_synth.py`'s `augment()`

Baseline to beat: the current production checkpoint scores ~67% avg
confidence on the real test document (`financial-fraud_2083_02_04.pdf`),
with heavy repeated-character garbling (`र्र्र्र्र...`, `य्य्य्य्य...`).

## Setup

Pushed to a **separate** Kaggle kernel (`devnagari-trocr-words-quicktest`),
not the production `devnagari-trocr-words` kernel, so failed attempts can't
disturb anything. A local copy of `notebooks/kaggle_train_trocr_words.ipynb`
was patched (`--n 12000` → `--n 2000`, `TROCR_EPOCHS='8'` → `'2'`) and pushed
via `kaggle kernels push`.

## Timeline — four real, unrelated bugs found and fixed

### v1 — `OSError: ... preprocessor_config.json`
Crashed ~113s in, post-"training", when the notebook's own sanity-check cell
tried to reload the just-trained checkpoint. Hypothesis at the time: Kaggle's
base container image had silently upgraded `transformers` to a version with a
processor save/reload naming regression.
**Fix applied:** pinned `transformers==5.13.1` (the version verified all
session to correctly load the existing production checkpoint) in the
notebook. → `ml` commit `50778406`.

### v2 — same `OSError`, despite the pin
Confirmed via the log that `transformers version: 5.13.1` printed correctly
— the pin worked, but the exact same error recurred. **This ruled out the
version-mismatch theory.** Inspected the existing (working) checkpoint's
`processor_config.json` — turned out its image-processor config is nested
*inside* `processor_config.json`, a newer consolidated format. Hypothesis:
`processor.save_pretrained()` on a freshly-built (not previously-reloaded)
processor doesn't reliably write a standalone `preprocessor_config.json`.
**Fix applied:** explicitly call `processor.image_processor.save_pretrained(CHECKPOINT_DIR)`
right after `processor.save_pretrained(CHECKPOINT_DIR)` in `train_words.py`,
to guarantee the exact file the error complains about missing actually
exists. → `ml` commit `d548ba54`.

### v3 — same `OSError` yet again — turned out to be a red herring
Scrolling *up* in the log (not just the tail) revealed the REAL first error,
~5 seconds before the familiar OSError:
```
ValueError: Couldn't instantiate the backend tokenizer from one of: ...
You need to have sentencepiece or tiktoken installed to convert a slow
tokenizer to a fast one.
```
This was present in v1 and v2 too — missed both times because only the log
*tail* was checked. **Root cause:** `train_words.py`'s very first
operational line, `TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')`
(loading the base model from HF Hub to start fine-tuning), crashed
immediately. Since `processor` never got created, training never started —
the `checkpoints_words/` directory the sanity-check cell later tried to load
was leftover/nonexistent, and the "missing preprocessor_config.json" error
was just a downstream symptom of loading nothing.

Reproduced locally to confirm: installing `sentencepiece` (confirmed
present, v0.2.2) did **not** fix it — the error message is misleading.
`transformers` 5.x has dropped legacy slow-tokenizer support entirely, and
`microsoft/trocr-base-handwritten` (a 2021-era HF Hub upload) has no fast
`tokenizer.json`, so the Auto-dispatch path can never load it, locally or on
Kaggle, with or without sentencepiece/tiktoken.

**Fix applied:** bypass the broken dispatch — load `RobertaTokenizer` and
`ViTImageProcessor` directly (both still load this old checkpoint format
fine when instantiated directly, verified locally) and assemble the
`TrOCRProcessor` manually:
```python
tokenizer = RobertaTokenizer.from_pretrained(DEFAULT_MODEL)
image_processor = ViTImageProcessor.from_pretrained(DEFAULT_MODEL)
processor = TrOCRProcessor(image_processor=image_processor, tokenizer=tokenizer)
```
→ `ml` commit `da188ff1`. **Verified locally**: model loads, dataset builds,
a full training epoch runs (previously crashed before any of that).

### v4 — new error: `CUDA error: no kernel image is available for execution on the device`
Progress — training actually started this time (past the tokenizer bug).
Crashed instead on the first real GPU op:
```
Tesla P100-PCIE-16GB with CUDA capability sm_60 is not compatible with the
current PyTorch installation. The current PyTorch install supports CUDA
capabilities sm_70 sm_75 sm_80 sm_86 sm_90 sm_100 sm_120.
```
Kaggle assigned a Pascal-generation P100 instead of the requested T4; the
preinstalled PyTorch build has dropped Pascal (`sm_60`) kernel support
entirely. `torch.cuda.is_available()` returns `True` regardless (driver/
runtime present) — it doesn't check kernel availability for the specific
architecture, so this only surfaces on the first real op, deep inside
training.

### v5 — retried, same P100 assignment, same crash
A plain retry landed on another P100 — not random bad luck, more likely
Kaggle's T4 pool being unavailable/exhausted for this account at the time.
Blind retries alone weren't a reliable fix.

**Fix applied:** probe for a *usable* CUDA device up front (try a trivial op,
not just check `is_available()`), and fall back to CPU if it fails, so a
GPU-incompatibility degrades gracefully instead of crashing mid-training:
```python
def _usable_cuda_device():
    if not torch.cuda.is_available():
        return False
    try:
        torch.zeros(1, device="cuda") + 1
        return True
    except RuntimeError:
        return False  # falls back to CPU
```
→ `ml` commit `89ad3492`. Verified locally the guard correctly returns
`False` (no GPU here) with no regression to the existing CPU path.

### v6 — in progress as of this writing
Pushed with all four fixes in place. Should now complete regardless of which
GPU (or lack of one) Kaggle assigns — fast if a compatible GPU, slower
(potentially 30-90+ min) but bounded if it falls back to CPU.

## Status / what's still open

- [ ] Confirm v6 completes (either on GPU or CPU fallback)
- [ ] Download the resulting checkpoint, run it against the real test
      document (`financial-fraud_2083_02_04.pdf`), compare confidence and
      output quality against the ~67%-confidence baseline
- [ ] Decide, based on that comparison, whether to commit to the full
      12k-image / 8-epoch production run

## Lessons for next time

1. **Always read the full log, not just the tail.** The real first error in
   v1-v3 was scrolled past three separate times before being caught.
2. **A pin "working" (version printed correctly) doesn't mean the pin was
   the actual fix** — verify the hypothesis against the NEW error, don't
   assume success just because the intended change took effect.
3. **`torch.cuda.is_available()` is not sufficient** to confirm a GPU will
   actually work — Kaggle's GPU pool includes older hardware that current
   PyTorch builds may have dropped support for.
4. **Reproduce locally when possible** before spending more remote GPU/CPU
   minutes — the tokenizer bug (the real root cause) was confirmed
   definitively via a local repro before touching Kaggle again, which
   avoided at least one more wasted round-trip.
