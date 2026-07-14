import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

loaded_models: dict = {}

# The ML package (models/trocr, models/crnn) lives at the repo root, a sibling
# of backend/ — add it to sys.path so `models.trocr.predict_words` resolves.
# Safe because this backend package is `ml_models`, not `models` (no name clash).
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_all_models():
    from config import CRNN_MODEL_PATH, TRANSFORMER_MODEL_PATH, DEVICE
    _load_crnn(CRNN_MODEL_PATH, DEVICE)
    _load_transformer(TRANSFORMER_MODEL_PATH, DEVICE)


def _load_crnn(model_path: str, device: str):
    if not Path(model_path).exists():
        logger.info("CRNN artifact not found at %s — mock mode active", model_path)
        return
    try:
        import torch
        from ml_models.crnn import CRNN
        from ml_models.char_map import NUM_CLASSES

        model = CRNN(num_classes=NUM_CLASSES)
        model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
        model.eval()
        loaded_models["crnn"] = model
        logger.info("CRNN loaded from %s on device=%s", model_path, device)
    except Exception as exc:
        logger.warning("CRNN failed to load: %s", exc)


def _load_transformer(model_path: str, device: str):
    """Word-level TrOCR (models/trocr/predict_words.py) — the only TrOCR
    checkpoint with real trained weights; models/trocr/checkpoints (single-char)
    is untrained. Loading is delegated to predict_words' own cached `_load`,
    so this just validates the checkpoint and warms that cache."""
    if not Path(model_path).is_dir():
        logger.info("Transformer checkpoint not found at %s — mock mode active", model_path)
        return
    try:
        if REPO_ROOT not in sys.path:
            sys.path.insert(0, REPO_ROOT)
        from models.trocr.predict_words import _load as _load_trocr, _resolve_checkpoint

        checkpoint = _resolve_checkpoint(model_path)
        _load_trocr(checkpoint, device)  # warms the lru_cache
        loaded_models["transformer"] = checkpoint
        logger.info("Transformer (word-TrOCR) loaded from %s on device=%s", checkpoint, device)
    except Exception as exc:
        logger.warning("Transformer failed to load: %s", exc)
