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

**4. (Recommended)** Before training, bump batch size for GPU: in
`models/crnn/train.py` `__main__`, change `batch_size=16` → `batch_size=64`.

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
