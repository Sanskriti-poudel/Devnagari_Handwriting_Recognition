# CRNN Baseline — How to Run

CNN → BiLSTM → CTC character recognizer. Owned by **Sanskriti**.

## Files
- `model.py` — `CRNN` architecture (log_softmax output) + `decode_ctc_greedy()`
- `dataset.py` — `CRNNDataset` + `collate_crnn` (imports `Preprocessing.preprocess.preprocess_image`)
- `train.py` — training loop: Adam, StepLR, early stopping, best-checkpoint, CSV logging
- `smoke_test.py` — fast end-to-end sanity check (run this first)

## Prereqs
- `data/charset.json` and `data/split_index.json` exist (run `python data/prepare_dataset.py`)
- Deps installed: `pip install -r requirements.txt`

## 1. Validate the pipeline (seconds, CPU)
Run from the **repo root**:
```bash
python models/crnn/smoke_test.py
```
Expect: positive, decreasing loss and a `PASS` line.

## 2a. Train locally (slow on CPU)
```bash
python models/crnn/train.py
```
Outputs → `models/crnn/checkpoints/best_model.pth`, log → `logs/crnn_training.csv`.

## 2b. Train on GPU (Colab — recommended)
`train.py` auto-detects CUDA, so it runs unchanged. `split_index.json` stores
**relative** paths; point `DEVNAGARI_DATA_ROOT` at the folder that contains
`train/` and `test/` (e.g. the Drive "Preprocessed" folder). In a Colab notebook
(Runtime → Change runtime type → **T4 GPU** first):
```python
# 1. GPU check
import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))

# 2. Get the code (clone your GitHub repo)
!git clone https://github.com/<your-username>/Devnagari_Handwriting_Recognition.git
%cd Devnagari_Handwriting_Recognition
!pip install -q torch torchvision opencv-python numpy pillow tqdm scikit-learn

# 3. Mount Drive for the dataset (Datasets/ is git-ignored, lives on Drive)
from google.colab import drive; drive.mount('/content/drive')
import os
os.environ["DEVNAGARI_DATA_ROOT"] = "/content/drive/MyDrive/Devnagari project/Datasets/Preprocessed"

# 4. Train (data/charset.json + data/split_index.json are committed, so no prep needed)
!python models/crnn/train.py

# 5. Copy the trained weights back to Drive so they persist
!cp models/crnn/checkpoints/best_model.pth "/content/drive/MyDrive/"
```
For GPU, bump batch size in `train.py`'s `__main__` (16 → 64 or 128) for much faster epochs.

## Notes
- **Train/serve consistency:** both training and the backend MUST call the same
  `preprocess_image()` in `Preprocessing/preprocess.py`. Don't reimplement preprocessing.
- Labels are class-folder names (e.g. `character_1_ka`); 46 classes + 1 CTC blank = 47 outputs.
- Checkpoints/weights are git-ignored — share via Drive.
