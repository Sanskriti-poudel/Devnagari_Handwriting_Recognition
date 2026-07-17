"""Stub TrOCR word-level predictor — returns mock result when no model weights are loaded."""

import numpy as np
import cv2

_MOCK_LINES = [
    {"box": [10, 20, 200, 60], "text": "नमस्ते, यो एक परीक्षण पाठ हो।", "confidence": 0.95},
]


def predict_page(bgr_image, *, checkpoint_path: str = None, device: str = "cpu", include_confidence: bool = True) -> dict:
    """Return mock annotated page with one line."""
    h, w = bgr_image.shape[:2]
    annotated = bgr_image.copy() if bgr_image.ndim == 3 else cv2.cvtColor(bgr_image, cv2.COLOR_GRAY2BGR)
    return {"annotated": annotated, "lines": _MOCK_LINES}


def predict_line(image_path: str, *, checkpoint_path: str = None, device: str = "cpu") -> dict:
    """Return mock single-line result."""
    return {"text": "नमस्ते, यो एक परीक्षण पाठ हो।", "confidence": 0.95}
