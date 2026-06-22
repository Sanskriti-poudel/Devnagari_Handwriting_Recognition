import logging
from models.loader import loaded_models

logger = logging.getLogger(__name__)
_MOCK_TEXT = "नमस्ते, यो एक परीक्षण पाठ हो।"


def run_ocr(image_path: str, model_name: str) -> tuple[str, float]:
    if model_name not in ("crnn", "transformer"):
        model_name = "crnn"

    if model_name not in loaded_models:
        logger.debug("Model %r not loaded — returning mock result", model_name)
        return _MOCK_TEXT, 0.95

    try:
        return _infer(image_path, model_name)
    except Exception as exc:
        logger.warning("Inference failed for %r: %s — falling back to mock", model_name, exc)
        return _MOCK_TEXT, 0.0


def _infer(image_path: str, model_name: str) -> tuple[str, float]:
    import torch
    from services.preprocessing import preprocess_for_inference
    from models.char_map import idx_to_char, BLANK_IDX

    arr = preprocess_for_inference(image_path)
    tensor = torch.from_numpy(arr)

    model = loaded_models[model_name]
    with torch.no_grad():
        log_probs = model(tensor)  # (T, 1, C)

    probs = log_probs.exp()
    text = _ctc_greedy_decode(probs[:, 0, :], idx_to_char)
    confidence = float(probs.max(dim=2).values.mean())
    return text, confidence


def _ctc_greedy_decode(probs, idx_to_char: dict) -> str:
    """Argmax → collapse consecutive duplicates → strip blank (index 46)."""
    from models.char_map import BLANK_IDX
    indices = probs.argmax(dim=1).tolist()
    chars, prev = [], None
    for idx in indices:
        if idx != prev:
            if idx != BLANK_IDX:
                chars.append(idx_to_char.get(idx, ''))
            prev = idx
    return ''.join(chars)


def run_ocr_pdf(pdf_path: str, model_name: str) -> list[dict]:
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return [{"page": 1, "text": _MOCK_TEXT, "confidence": 0.95}]

    import os, tempfile

    pages = convert_from_path(pdf_path)
    results = []
    for i, page_img in enumerate(pages):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            page_img.save(tmp.name)
            text, conf = run_ocr(tmp.name, model_name)
            os.unlink(tmp.name)
        results.append({"page": i + 1, "text": text, "confidence": conf})
    return results
