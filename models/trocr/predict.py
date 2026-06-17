"""
Contract A — TrOCR inference interface for the backend.

Exposes `predict(image) -> {"text": str, "confidence": float}`, matching the
CRNN `predict()` signature so the backend can swap models behind one interface.
Runs the SAME preprocessing as training (`Preprocessing.preprocess`) → RGB → the
TrOCR processor, so there is no train/serve skew. `text` is the Devanagari glyph.

The model/processor are loaded once and cached.

Example:
    from models.trocr.predict import predict
    predict("/path/to/char.png")   # {"text": "क", "confidence": 0.97}
"""

import os
import sys
from functools import lru_cache

import cv2
import numpy as np
import torch

try:  # Windows consoles can't print Devanagari glyphs without this
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
sys.path.insert(0, THIS_DIR)
sys.path.insert(0, PROJECT_ROOT)

from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from Preprocessing.preprocess import preprocess_image, preprocess_array
from dataset import array_to_rgb_pil

DEFAULT_CHECKPOINT = os.path.join(PROJECT_ROOT, "models", "trocr", "checkpoints")


def _resolve_checkpoint(path=None):
    path = path or os.environ.get("TROCR_CHECKPOINT") or DEFAULT_CHECKPOINT
    if not os.path.isdir(path):
        raise FileNotFoundError(
            f"No TrOCR checkpoint at {path}. Train (models/trocr/train.py), "
            f"set TROCR_CHECKPOINT, or pass checkpoint_path."
        )
    return path


@lru_cache(maxsize=2)
def _load(checkpoint_path, device):
    processor = TrOCRProcessor.from_pretrained(checkpoint_path)
    model = VisionEncoderDecoderModel.from_pretrained(checkpoint_path).to(device)
    model.eval()
    return processor, model


def _to_rgb_pil(image):
    """path | OpenCV ndarray | pre-normalized (64,64) float -> RGB PIL image."""
    if isinstance(image, str):
        arr = preprocess_image(image)
    elif isinstance(image, np.ndarray):
        if image.dtype in (np.float32, np.float64) and image.shape == (64, 64):
            arr = image.astype(np.float32)
        else:
            arr = preprocess_array(image)
    else:
        raise TypeError(f"Unsupported image type: {type(image)}")
    return array_to_rgb_pil(arr)


def predict(image, checkpoint_path=None, device=None):
    """
    Recognize the character in a single image.

    Returns {"text": str, "confidence": float}, where confidence is the mean
    softmax probability of the generated tokens in [0, 1].
    """
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    processor, model = _load(_resolve_checkpoint(checkpoint_path), device)

    img = _to_rgb_pil(image)
    pixel_values = processor(images=img, return_tensors="pt").pixel_values.to(device)

    with torch.no_grad():
        out = model.generate(
            pixel_values, max_length=8,
            output_scores=True, return_dict_in_generate=True,
        )
    text = processor.batch_decode(out.sequences, skip_special_tokens=True)[0].strip()

    # mean per-step max-softmax probability over the generated steps
    if out.scores:
        step_probs = [torch.softmax(s[0], dim=-1).max().item() for s in out.scores]
        confidence = float(np.mean(step_probs)) if step_probs else 0.0
    else:
        confidence = 0.0

    return {"text": text, "confidence": round(confidence, 4)}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Run TrOCR inference on one image.")
    p.add_argument("image")
    p.add_argument("--checkpoint", default=None)
    args = p.parse_args()
    print(predict(args.image, checkpoint_path=args.checkpoint))
