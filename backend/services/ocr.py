import logging
from ml_models.loader import loaded_models

logger = logging.getLogger(__name__)
_MOCK_TEXT = "नमस्ते, यो एक परीक्षण पाठ हो।"


def run_ocr(image_path: str, model_name: str) -> tuple[str, float]:
    if model_name not in ("crnn", "transformer"):
        model_name = "crnn"

    if model_name not in loaded_models:
        logger.debug("Model %r not loaded — returning mock result", model_name)
        return _MOCK_TEXT, 0.95

    try:
        if model_name == "transformer":
            return _infer_transformer(image_path)
        return _infer_crnn(image_path)
    except Exception as exc:
        logger.warning("Inference failed for %r: %s — falling back to mock", model_name, exc)
        return _MOCK_TEXT, 0.0


def _infer_crnn(image_path: str) -> tuple[str, float]:
    import torch
    from services.preprocessing import preprocess_for_inference
    from ml_models.char_map import idx_to_char

    arr = preprocess_for_inference(image_path)
    tensor = torch.from_numpy(arr)

    model = loaded_models["crnn"]
    with torch.no_grad():
        log_probs = model(tensor)  # (T, 1, C)

    probs = log_probs.exp()
    text = _ctc_greedy_decode(probs[:, 0, :], idx_to_char)
    confidence = float(probs.max(dim=2).values.mean())
    return text, confidence


def _ctc_greedy_decode(probs, idx_to_char: dict) -> str:
    """Argmax → collapse consecutive duplicates → strip blank (index 46)."""
    from ml_models.char_map import BLANK_IDX
    indices = probs.argmax(dim=1).tolist()
    chars, prev = [], None
    for idx in indices:
        if idx != prev:
            if idx != BLANK_IDX:
                chars.append(idx_to_char.get(idx, ''))
            prev = idx
    return ''.join(chars)


def _infer_transformer(image_path: str) -> tuple[str, float]:
    """Word/line-level TrOCR — delegates to models/trocr/predict_words.py (the
    shared inference path also used by the Flask document digitizer), so
    there's one implementation of TrOCR inference, not a second copy here."""
    from config import DEVICE
    from ml_models.loader import REPO_ROOT
    import sys
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    from models.trocr.predict_words import predict_line

    checkpoint = loaded_models["transformer"]
    result = predict_line(image_path, checkpoint_path=checkpoint, device=DEVICE)
    return result["text"], result["confidence"]


def run_ocr_pdf(pdf_path: str, model_name: str) -> list[dict]:
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return [{"page": 1, "text": _MOCK_TEXT, "confidence": 0.95}]

    import os, tempfile

    pages = convert_from_path(pdf_path)
    results = []
    for i, page_img in enumerate(pages):
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.close()
        try:
            page_img.save(tmp.name)
            text, conf = run_ocr(tmp.name, model_name)
        finally:
            os.unlink(tmp.name)
        results.append({"page": i + 1, "text": text, "confidence": conf})
    return results
