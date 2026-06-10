from models.loader import loaded_models

# Mock Devanagari text returned until real model artifacts are wired in (Phase 2)
_MOCK_TEXT = "नमस्ते, यो एक परीक्षण पाठ हो।"


def run_ocr(image_path: str, model_name: str) -> tuple[str, float]:
    """
    Returns (recognized_text, confidence).
    Phase 1: returns mock output so the frontend can develop against a real response.
    Phase 2: replace the body with real preprocessing + model inference.
    """
    if model_name not in ("crnn", "transformer"):
        model_name = "crnn"

    # TODO Phase 2: preprocess image and run loaded_models[model_name]
    return _MOCK_TEXT, 0.95


def run_ocr_pdf(pdf_path: str, model_name: str) -> list[dict]:
    """
    Convert each PDF page to an image and run OCR on each page.
    Returns a list of per-page dicts: {"page": int, "text": str, "confidence": float}.
    Requires pdf2image + Poppler; falls back to mock if not available.
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return [{"page": 1, "text": _MOCK_TEXT, "confidence": 0.95}]

    import os
    import tempfile

    pages = convert_from_path(pdf_path)
    results = []
    for i, page_img in enumerate(pages):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            page_img.save(tmp.name)
            text, conf = run_ocr(tmp.name, model_name)
            os.unlink(tmp.name)
        results.append({"page": i + 1, "text": text, "confidence": conf})
    return results
