import logging
from pathlib import Path

logger = logging.getLogger(__name__)

loaded_models: dict = {}


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
        from models.crnn import CRNN
        from models.char_map import NUM_CLASSES

        model = CRNN(num_classes=NUM_CLASSES)
        model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
        model.eval()
        loaded_models["crnn"] = model
        logger.info("CRNN loaded from %s on device=%s", model_path, device)
    except Exception as exc:
        logger.warning("CRNN failed to load: %s", exc)


def _load_transformer(model_path: str, device: str):
    if not Path(model_path).exists():
        logger.info("Transformer artifact not found at %s — mock mode active", model_path)
        return
    try:
        import torch
        # Placeholder — replace with the real Transformer class when available
        logger.info("Transformer loading not yet implemented; artifact found at %s", model_path)
    except Exception as exc:
        logger.warning("Transformer failed to load: %s", exc)
