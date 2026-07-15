# Devanagari Handwriting Recognition — Project Guide

One-stop reference: what this project is, how the branches fit together, how
to run and test it, and a troubleshooting playbook for the failure modes
we've actually hit. Written from a full end-to-end testing pass (2026-07-15)
that exercised every endpoint, the browser UI on two separate branch pairs,
and found/fixed several real bugs — the details below are what that pass
uncovered, not speculation.

---

## 1. What this project is

A Devanagari (Nepali) handwriting OCR system with two recognition models:

- **CRNN** (CNN + RNN + CTC) — character-level, trained on the DHCD dataset
  (real handwritten single characters, isolated). Fast, high accuracy on
  clean single-character crops; cannot read matras/conjuncts/joined words on
  its own — a segmentation step chops a line into per-character boxes first.
- **Transformer (TrOCR)** — word/line-level, `microsoft/trocr-base-handwritten`
  fine-tuned on **synthetic** Devanagari word/line images (see §6 — this is
  the model's main current limitation). Reads whole lines including matras,
  conjuncts, and punctuation in one shot; the intended path for real
  documents.

Two product surfaces exist across four branches (see §2): a "document
digitizer" (scan → editable text → docx/searchable-PDF/txt, plus Preeti↔Unicode
conversion) and a "premium" auth'd dashboard app with OCR history and stats.

## 2. Branch layout — read this before touching anything

```
data_preprocessing / main   — default branches, dataset + preprocessing code
ml                          — models/training + a full, self-contained
                               document-digitizer app (backend/ + frontend/
                               both live directly in this branch)
backend                     — FastAPI service for the "premium" dashboard app
                               (auth, history, stats) — pairs with ↓
frontend                    — React "premium" dashboard UI — pairs with ↑
```

`backend` and `frontend` are **separate branches**, not folders — you check
them out as **git worktrees** side by side, never by switching branches in
your main working copy (see `docs/RUN_LOCALLY.md` §1). The `ml` branch's own
`backend/` + `frontend/` are a **different, independent** app (the document
digitizer) — don't confuse the two backend implementations. They share model
code (`models/trocr/`, `models/crnn/`) via `sys.path` tricks
(`ml_models/loader.py`'s `REPO_ROOT`), so a fix to `models/trocr/predict_words.py`
needs to be applied/ported to **both** if both are running.

**When you fix something that lives in `backend/` code, check whether the
same bug exists on the other backend branch too.** We hit this twice today:
the `use_cache` fix and the "OCR blocks the whole server" fix both existed
independently on `ml`'s backend and the `backend` branch, and had to be
applied to each separately (they're not the same file, just structurally
identical logic that was copy/pasted when the branch was forked).

## 3. Running it

Full step-by-step setup (worktrees, `.env`, ports) is in
**`docs/RUN_LOCALLY.md`** — follow that, don't duplicate it here. Quick
summary of what "working" looks like:

```bash
curl http://127.0.0.1:8000/health
# {"status":"operational"/"ok","models":[{"id":"crnn","status":"active"},{"id":"transformer","status":"active"}]}
```

Both models should say `"active"`, not `"degraded"`. If transformer is
degraded, see §5.3.

**Models take ~60-90s to load on startup** (CRNN is instant; TrOCR's
`VisionEncoderDecoderModel.from_pretrained` takes the time) — `/health` will
refuse connections until that finishes. Don't assume a hung server; poll:

```bash
until curl -s http://127.0.0.1:8000/health | grep -q active; do sleep 3; done
```

## 4. Testing checklist (what a full pass covers)

Run this whenever you touch `backend/`, `models/trocr/`, or `models/crnn/`:

1. **Unit tests**: `cd backend && python -m pytest tests/ -v` — needs
   poppler on PATH for PDF tests (see §5.1) and takes ~80s (loads real
   models via `TestClient`'s lifespan).
2. **Direct API smoke test**: `curl` the actual endpoints with a real file,
   not just the mocked test fixtures — the test suite's synthetic images are
   too clean to catch real-world accuracy/timeout issues (see §6).
3. **Browser-driven UI test**: don't stop at curl. Use Playwright (see
   below) to actually click through upload → recognize → export/download,
   and check `console --errors` is empty. A backend that returns 200 doesn't
   guarantee the frontend rendered it correctly — we found a real bug this
   way (§5.4) that curl testing alone would never have caught.

No `chromium-cli` tool was available in this environment; the fallback that
worked:
```bash
npm install playwright && npx playwright install chromium
node your_test_script.js   # see any browser_test*.js this session left behind
```

## 5. Troubleshooting playbook

### 5.1 — `PDFInfoNotInstalledError` / "Is poppler installed and in PATH?"

`pdf2image` (used by `services/ocr.py`'s `run_ocr_pdf`) shells out to
poppler's `pdftoppm`. Installed via winget but not on PATH by default:

```bash
export PATH="/c/Users/<you>/AppData/Local/Microsoft/WinGet/Packages/oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe/poppler-25.07.0/Library/bin:$PATH"
```

Add this to whatever launches uvicorn (or your shell profile) — the server
process needs poppler on ITS PATH, not just the terminal you happen to be
typing in.

### 5.2 — `/document` (or `/api/document`) takes forever / whole server hangs

**Symptom**: uploading a real (non-trivial) document seems to freeze the
entire app — even unrelated pages, `/health`, other tabs — not just a
loading spinner on the upload.

**Root cause #1 (fixed 2026-07-15, `ml` commit `e22c1c08`, `backend` branch
n/a — was a checkpoint config issue, only on `ml`'s checkpoint)**: TrOCR
checkpoints can have `use_cache: false` baked into `config.json` /
`generation_config.json` (a training-time setting for gradient
checkpointing that has no business being in an inference checkpoint).
Without KV-caching, `generate()` recomputes the entire decoded sequence
from scratch every step — quadratic, and on CPU with `max_length=160` this
turned a should-be-seconds request into 25-30+ minutes.
**Check**: `python -c "import json; print(json.load(open('models/trocr/checkpoints_words/generation_config.json'))['use_cache'])"`
**Fix**: force it at load time, don't trust the checkpoint:
```python
model.config.use_cache = True
model.generation_config.use_cache = True
# and pass use_cache=True explicitly in the generate() call too, belt-and-suspenders
```
Already applied in `models/trocr/predict.py`'s `_load()`. If you retrain and
get a new checkpoint, this will still apply (it patches at load time, not
by editing the checkpoint files) — but re-verify with the check above if
you ever see this symptom again.

**Root cause #2 (fixed 2026-07-15, `ml` commit `e23c7b1f`, `backend` commit
`d1ef0ce5`)**: `/document`, `/api/document`, `/api/document/pages`, and
`/ocr` ran CPU-bound model inference **synchronously inside `async def`
handlers**. FastAPI/Starlette is single-event-loop; a synchronous call
inside an `async def` blocks that loop for the ENTIRE request — no other
request (including `/health`) gets scheduled until it returns. This is why
the symptom looks like "the whole server is down," not "one slow request."
**Fix**: wrap the inference call in `starlette.concurrency.run_in_threadpool`:
```python
from starlette.concurrency import run_in_threadpool
result = await run_in_threadpool(run_ocr_pdf, save_path, model_name)
```
**Verify the fix is actually in place** (don't just trust it's still there —
check both backend implementations separately, they're different files):
```bash
grep -n "run_in_threadpool" backend/main.py   # should show 3+ call sites
```
Fire a request, then immediately curl `/health` from another terminal — it
should respond in milliseconds, not queue behind the OCR request.

**Even with both fixes, CPU inference is still genuinely slow and
variable** — anywhere from ~2 minutes to ~15 minutes for a dense 2-page
document, run to run, depending on how many decode steps each line's
generation needs before hitting EOS. This is NOT a bug, it's CPU-only
autoregressive generation on a base-sized transformer. Don't re-diagnose
this as broken if a request takes 10 minutes and still returns 200 — check
the server log for a `→ 200` completion line before assuming it's hung
versus just slow. GPU inference would fix this; it's not currently set up
for serving (only used for training via Kaggle/Colab).

### 5.3 — `/models` (or `/health`) reports transformer as "degraded"

Means `TRANSFORMER_MODEL_PATH` (env var, `backend/.env`) didn't resolve to
a real checkpoint directory — `ml_models/loader.py`'s `_load_transformer`
silently falls back to mock mode (logs "Transformer checkpoint not found at
... — mock mode active", doesn't crash).

**Check**: does the path in `.env` actually exist?
```bash
python -c "from pathlib import Path; import os; print(Path(os.environ.get('TRANSFORMER_MODEL_PATH','')).is_dir())"
```
**Common cause**: you're in a **git worktree** (a sibling checkout of
`backend` or `frontend`), and `.env` has a relative path like
`../models/trocr/checkpoints_words` — that resolves relative to the
worktree's own directory, which doesn't have the (gitignored, large)
checkpoint files. **Fix**: use an ABSOLUTE path into the `ml` branch's
checkout, same fix as `CRNN_MODEL_PATH` needs (see `docs/RUN_LOCALLY.md`):
```
TRANSFORMER_MODEL_PATH=C:/Users/<you>/.../Devnagari_Handwriting_Recognition/models/trocr/checkpoints_words
```
Also check the loaded venv actually has `transformers`/`torch` installed —
worktrees have their own venv, not shared with the main checkout:
```bash
venv/Scripts/python.exe -c "import transformers, torch"
```
(`sentencepiece` is NOT required for this tokenizer, despite what you might
expect — don't waste time chasing that if it's missing.)

Once the checkpoint path resolves and deps are present, restart the
server — `/models` should flip to `"active"`.

### 5.4 — Frontend shows "Simulated"/0% confidence even though the backend is real

**Found and fixed 2026-07-15** (`frontend` branch commit `2994b8fb`). If you
ever see the "Transformer" model selection produce a `Simulated — backend
model endpoint pending` badge or 0.00% confidence, despite `/health`
reporting transformer as `"active"` and a direct `curl -F model=transformer`
request returning real, non-degraded output: **check the frontend service
layer**, not the backend. `ocr.service.ts`'s `recognize()` historically
(a) never sent the user's selected `model` in the upload request at all
(defaulting the backend to `"crnn"` regardless of UI selection), and
(b) hardcoded `modelSimulated: model === 'transformer'` client-side instead
of reading the backend's own `model_simulated` field from the response.
**Fix pattern**: always append the selection to the form data, and trust
whatever the backend says actually happened:
```ts
formData.append('model', model)
// ...
modelSimulated: data.model_simulated   // NOT `model === 'transformer'`
```
If this regresses (e.g. a UI refactor drops the `formData.append('model', ...)`
line again), the symptom is: CRNN and Transformer produce IDENTICAL results
even on documents where they should clearly differ, and Transformer always
shows the same confidence pattern.

### 5.5 — CORS error signing up / any request from the frontend (`Access-Control-Allow-Origin`)

The `backend` branch's CORS config (`CORS_ORIGINS` in `.env`) is a literal
string match against the frontend's actual origin. If Vite's dev server
port 5173 is already taken (e.g. another checkout's frontend is running),
it silently falls back to 5174, 5175, etc. — and then every request 403s on
preflight because `.env` only whitelists `:5173`.
**Fix**: either free up `:5173` (stop whatever else is bound to it) so Vite
binds to the port `.env` expects, or add the actual port Vite chose to
`CORS_ORIGINS`. Don't run two different frontend checkouts' dev servers
simultaneously without checking which port each landed on.

### 5.6 — OCR accuracy is poor / garbled on real (non-test-fixture) documents

**This is a known, unresolved limitation, not a bug to "fix" by more
debugging.** Root cause: the word-level TrOCR checkpoint is trained
**entirely on synthetic, font-rendered images** (`data/generate_synth.py` —
Devanagari fonts + geometric/photometric distortion filters), never on real
photographed/scanned cursive handwriting. That's a genuine train/test domain
gap — a distorted digital font doesn't look like real joined cursive
strokes, pen pressure variation, or scan artifacts. Symptom: repeated-
character garbling (`र्र्र्र्र...`, `य्य्य्य्य...`) on dense real handwriting,
usually with confidence in the 50-70% range rather than a clean failure.

**What WON'T fix it**: training longer on the same synthetic data, or a
bigger/faster GPU for the same recipe — that just gets better at reading
synthetic fonts, not real handwriting.

**What's been tried (2026-07-15, `ml` commit `cb603a5e`, NOT yet retrained
on)**: bundled 8 additional open-license Devanagari fonts
(`assets/fonts_devanagari/`, previously only Nirmala/Mangal existed) and
added a numpy-only sinusoidal "wave warp" augmentation (wavy baseline +
per-column stroke jitter) to `data/generate_synth.py`'s `augment()`, to
reduce the "too font-perfect" look. **This alone changes nothing** until a
new checkpoint is actually trained on the regenerated synthetic set.

**Recommended next steps, in order of effort**:
1. Quick sanity check: regenerate a small synthetic set (~2k images) with
   the new fonts/warp, run a short 2-epoch training job (~15-30 min on a
   Kaggle T4), and compare its output on the same real test document against
   the current checkpoint. Confirms the changes help before committing to
   a full run.
2. If step 1 shows improvement: run the full config (12k images, 8 epochs,
   `notebooks/kaggle_train_trocr_words.ipynb`, ~8-16h on a T4).
3. Higher-leverage but higher-effort: collect a small set of REAL
   handwritten word/line images with transcriptions, and fine-tune the
   synthetic-pretrained checkpoint on top of them (the "synthetic pretrain →
   fine-tune on real data" recipe the generator's own docstring already
   calls out as standard practice). Even a few hundred real examples would
   likely help more than another round of synthetic-only training.

### 5.7 — General "something's broken and I don't know what" checklist

1. Is the server actually running? `curl -m 3 http://127.0.0.1:8000/health`
   — if it hangs (no response, not even an error) rather than erroring
   quickly, that's usually §5.2's blocking-event-loop symptom, not a dead
   process. Check `netstat -ano | grep :8000` for `LISTENING` vs nothing.
2. Read the actual server log, not just the HTTP status the client got.
   Background-launched servers should redirect stdout/stderr to a file —
   `tail` it. Uvicorn logs model-loading progress, per-request timing
   (`GET /health → 200 (2.5ms)`), and swallowed exceptions.
3. If a request seems to hang, check `netstat` for `CLOSE_WAIT` — that
   means a PREVIOUS client gave up (timed out) but the server is still
   processing that same request server-side. Don't kill the server thinking
   it's stuck; check CPU usage first:
   `powershell -Command "Get-Process -Id <pid> | Select CPU"` — if CPU time
   is climbing, it's actively working, not hung.
4. Windows Git Bash path gotchas: `/tmp/foo` is NOT a real Windows path —
   tools that aren't Git-Bash-aware (a separately-installed Python, a
   Windows-native exe) won't find it. Use `cygpath -w /tmp/foo` to get the
   real path when handing a file to a non-MSYS tool.
5. Multiple servers on the same port collide silently in confusing ways
   (whichever bound first wins; the second either errors or, if you're not
   watching, you think you restarted something you didn't). Always
   `netstat -ano | grep :<port>` before relaunching, and stop the old PID
   first.

## 6. Model training reference

- Training happens on **Kaggle** (kernel `devnagari-trocr-training`), not
  locally — no local GPU. Code must be pushed to `origin/ml` first; the
  kernel clones `-b ml`.
- Notebooks: `notebooks/kaggle_train_trocr.ipynb` (single-char TrOCR, mostly
  superseded by CRNN), `notebooks/kaggle_train_trocr_words.ipynb`
  (word/line-level — the one that matters). Has a documented "fast config"
  (4k images, 3 epochs, ~20-30 min — for quick verification) and "full
  config" (12k images, 8 epochs, ~1-2h/epoch — production quality).
- Synthetic data generator: `data/generate_synth.py` — see its docstring
  and §5.6 above for what it does and its current limitations.
- CRNN training: `backend/train.py` / `notebooks/colab_train_crnn.ipynb`,
  on real DHCD data (isolated single characters) — this model's accuracy is
  NOT the current bottleneck; TrOCR's is.

## 7. Git workflow

- One area per branch: frontend / backend / data_preprocessing / ml. Don't
  mix concerns across branches.
- Always create NEW commits; don't amend/force-push shared branches.
- The `ml` branch's `backend/` and `frontend/` (document digitizer) vs. the
  standalone `backend`/`frontend` branches (premium dashboard) are
  independently versioned — a fix on one does not automatically apply to
  the other. Check both when the bug is architectural (see §2).
- `docs/RUN_LOCALLY.md` is the step-by-step setup guide; this file
  (`docs/PROJECT_GUIDE.md`) is the "what is this, and what breaks" reference.
  Keep both updated when either the setup process or a recurring failure
  mode changes.
