"""Stub CRNN predictor — returns mock result when no model weights are loaded."""

_MOCK_CONFIDENCE = 0.95
# Return a valid class name that class_to_glyph can map
_MOCK_CLASS = "character_1_ka"


def predict(image_or_path, *, device: str = "cpu") -> dict:
    """Returns mock OCR result in the format expected by document.py."""
    return {"text": _MOCK_CLASS, "confidence": _MOCK_CONFIDENCE}
