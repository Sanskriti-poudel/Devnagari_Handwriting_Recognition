# GPU Training Guide (Google Colab)

How to train the CRNN baseline (and later TrOCR) on a free GPU. The repo is set up
so the **same code + split files** run unchanged locally and on Colab.

---

## One-time prep (on your Windows machine)

**1. Push the repo to GitHub** so Colab can pull the code:
```powershell
git add -A
git commit -m "CRNN baseline + portable dataset split"
git push
```
> `data/charset.json` and `data/split_index.json` **are committed** (only `Datasets/`
> and `*.pth` weights are git-ignored). The dataset stays on Drive — already at
> `Devnagari project/Datasets/Preprocessed`.

---

## Each Colab session

**2.** Open https://colab.research.google.com → New notebook →
**Runtime → Change runtime type → T4 GPU**.

**3.** Run these cells:

```python
# Confirm GPU is on
import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))
```
```python
# Get the code
!git clone https://github.com/<your-username>/Devnagari_Handwriting_Recognition.git
%cd Devnagari_Handwriting_Recognition
!pip install -q torch torchvision opencv-python numpy pillow tqdm scikit-learn
```
```python
# Mount Drive for the dataset, point the loader at it
from google.colab import drive; drive.mount('/content/drive')
import os
os.environ["DEVNAGARI_DATA_ROOT"] = "/content/drive/MyDrive/Devnagari project/Datasets/Preprocessed"
```
```python
# Train
!python models/crnn/train.py
```
```python
# Save trained weights back to Drive (Colab wipes local files on disconnect!)
!cp models/crnn/checkpoints/best_model.pth "/content/drive/MyDrive/"
```

**4.** Batch size auto-scales: 64 on GPU, 16 on CPU. Override with the
`CRNN_BATCH_SIZE` env var if needed (e.g. on out-of-memory).

> **Shortcut:** instead of typing the cells above, open the ready-made notebook
> `notebooks/colab_train_crnn.ipynb` in Colab (File → Open notebook → GitHub).

---

## Plan B: Kaggle (when Colab says "Cannot connect to a GPU backend")

Colab's free GPUs are a shared pool with per-account usage limits — when you hit the
limit, it resets on its own (usually within 12–24 h). **Don't dodge it with a second
Google account** (against Colab's ToS). Use **Kaggle** instead: a guaranteed
**~30 GPU-hours/week**, and the training run only needs 1–2 of them.

### One-time prep

**1. Account:** register at https://www.kaggle.com (Google sign-in works), then
**verify your phone**: avatar → Settings → Phone verification. This unlocks GPU +
Internet access for notebooks.

**2. Zip the dataset** (zip the *contents* of `Datasets/` so `train/` + `test/` sit at
the zip root — ~80 MB):
```powershell
Compress-Archive -Path Datasets\* -DestinationPath ..\devnagari_preprocessed.zip
```

**3. Upload it as a Kaggle Dataset:** kaggle.com → **Create → New Dataset** → drag the
zip in → title it `devnagari-preprocessed` → **Create** (keep it Private). Kaggle
auto-extracts the zip; the data lands at `/kaggle/input/devnagari-preprocessed/`.

### Each Kaggle session

**4. Import the ready-made notebook:** kaggle.com → **Create → New Notebook** →
**File → Import Notebook → GitHub tab** → paste
`https://github.com/Sanskriti-poudel/Devnagari_Handwriting_Recognition/blob/ml/notebooks/kaggle_train_crnn.ipynb`.

**5. Configure the session** (right sidebar):
- **Session options → Accelerator → GPU T4 x2** (or P100)
- **Session options → Internet → On** (needed for `git clone`)
- **Input → Add Input** → search *your* datasets → attach `devnagari-preprocessed`

**6. Run all cells.** Same code, same split, same outputs as Colab — the notebook
auto-detects the dataset path under `/kaggle/input/`.

**7. Get the outputs:** cell 6 copies `best_model.pth` + `crnn_training.csv` to
`/kaggle/working/` — download them from the **Output** panel (right sidebar), or
**Save Version → Save & Run All** to persist them with the notebook.

### Kaggle vs Colab differences

| | Colab | Kaggle |
|---|---|---|
| GPU quota | unpredictable pool | ~30 hrs/week, guaranteed |
| Data access | Drive mount (FUSE — slow, flaky) | attached dataset on local disk (fast) |
| Idle timeout | ~90 min | ~20 min interactive (use *Save & Run All* for unattended runs) |
| Outputs | copy to Drive manually | Output panel / saved with version |

---

## Why each step matters

| Step | Why it's needed |
|------|-----------------|
| `DEVNAGARI_DATA_ROOT` env var | `split_index.json` uses **relative** paths — this tells the loader where `train/` + `test/` live on Colab |
| Save weights to Drive | Colab **deletes everything** when the session disconnects (~90 min idle) |
| Commit `data/*.json` | Same split is reproducible on Colab → fair CRNN-vs-Transformer comparison |
| T4 GPU runtime | ~minutes/epoch vs ~30+ min/epoch on local CPU |

---

## Alternative: all-on-Drive (no GitHub)
Upload the whole repo folder to Drive, then in Colab:
```python
from google.colab import drive; drive.mount('/content/drive')
%cd "/content/drive/MyDrive/Devnagari_Handwriting_Recognition"
import os; os.environ["DEVNAGARI_DATA_ROOT"] = os.path.abspath("Datasets")
!pip install -q torch torchvision opencv-python numpy pillow tqdm scikit-learn
!python models/crnn/train.py
```

---

## Outputs
- Best checkpoint → `models/crnn/checkpoints/best_model.pth`
- Per-epoch loss log → `logs/crnn_training.csv`
- Trains up to 50 epochs with early stopping (auto-detects CUDA)
