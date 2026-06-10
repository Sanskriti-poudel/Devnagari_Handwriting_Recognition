"""
Contract A — CRNN inference interface for the backend.

Exposes a `predict(image) -> {"text": str, "confidence": float}` function,
decoupled from training. It runs the EXACT same preprocessing the model was
trained with (`Preprocessing.preprocess`) so there is no train/serve skew.

The model and charset are loaded once and cached, so repeated calls are cheap.

Example (backend):
    from models.crnn.predict import predict
    result = predict("/path/to/char.png")
    # {"text": "character_1_ka", "confidence": 0.98}

    # or with an already-decoded upload (OpenCV BGR/grayscale ndarray):
    import cv2
    img = cv2.imdecode(np.frombuffer(upload_bytes, np.uint8), cv2.IMREAD_COLOR)
    result = predict(img)
"""

import os
import sys
import json
from functools import lru_cache

import cv2
import numpy as np
import torch

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
sys.path.insert(0, THIS_DIR)
sys.path.insert(0, PROJECT_ROOT)

from model import CRNN, decode_ctc_greedy
from Preprocessing.preprocess import preprocess_image, preprocess_array

DEFAULT_CHARSET = os.path.join(PROJECT_ROOT, "data", "charset.json")


def _resolve_checkpoint(path=None):
    if path:
        return path
    env = os.environ.get("CRNN_CHECKPOINT")
    if env:
        return env
    for c in [
        os.path.join(PROJECT_ROOT, "models", "crnn", "checkpoints", "best_model.pth"),
        os.path.join(PROJECT_ROOT, "kaggle_output", "artifacts", "best_model.pth"),
    ]:
        if os.path.exists(c):
            return c
    raise FileNotFoundError(
        "No CRNN checkpoint found. Set CRNN_CHECKPOINT or pass checkpoint_path."
    )


@lru_cache(maxsize=4)
def _load(checkpoint_path, charset_path, device):
    """Load and cache (model, charset, blank_idx) for a given config."""
    with open(charset_path, "r", encoding="utf-8") as f:
        charset_data = json.load(f)
    charset = charset_data["chars"]
    blank_idx = charset_data.get("blank_idx", len(charset))
    num_classes = charset_data.get("num_classes", len(charset) + 1)

    model = CRNN(num_classes=num_classes, hidden_size=256).to(device)
    state = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state)
    model.eval()
    return model, tuple(charset), blank_idx


def _to_processed_tensor(image):
    """Accept a path, an OpenCV ndarray, or an already-preprocessed (64,64)
    float array; return a (1, 1, 64, 64) tensor."""
    if isinstance(image, str):
        arr = preprocess_image(image)
    elif isinstance(image, np.ndarray):
        if image.dtype in (np.float32, np.float64) and image.shape == (64, 64):
            arr = image.astype(np.float32)          # already preprocessed
        else:
            arr = preprocess_array(image)           # raw upload -> preprocess
    else:
        raise TypeError(f"Unsupported image type: {type(image)}")
    return torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)  # (1,1,64,64)


def predict(image, checkpoint_path=None, charset_path=DEFAULT_CHARSET, device=None):
    """
    Recognize the character(s) in a single image.

    Args:
        image: file path (str), OpenCV image (BGR or grayscale ndarray), or a
               pre-normalized (64, 64) float array.
        checkpoint_path: optional override for the model weights.
        charset_path: charset.json (defaults to the repo's).
        device: "cpu" / "cuda" (defaults to cuda if available).

    Returns:
        {"text": str, "confidence": float}
        - text: predicted class name (e.g. "character_1_ka"); empty string if
          the model emits only blanks.
        - confidence: mean per-timestep max softmax probability in [0, 1].
    """
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint_path = _resolve_checkpoint(checkpoint_path)
    model, charset, blank_idx = _load(checkpoint_path, charset_path, device)
    charset = list(charset)

    x = _to_processed_tensor(image).to(device)

    with torch.no_grad():
        log_probs = model(x)                       # (T, 1, num_classes)
        probs = log_probs.exp()
        per_step_conf = probs.max(dim=2).values    # (T, 1)
        confidence = float(per_step_conf.mean().item())
        text = decode_ctc_greedy(log_probs, charset, blank_idx=blank_idx)[0]

    return {"text": text, "confidence": round(confidence, 4)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run CRNN inference on one image.")
    parser.add_argument("image", help="Path to an image file")
    parser.add_argument("--checkpoint", default=None)
    args = parser.parse_args()

    print(predict(args.image, checkpoint_path=args.checkpoint))
