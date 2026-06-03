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
