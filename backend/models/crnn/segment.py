"""Stub CRNN segmentation — used by services/document.py in mock mode."""

import numpy as np
import cv2


def segment_lines(bgr_image) -> list[list[list[int]]]:
    """Return a single mock line covering the whole image."""
    h, w = bgr_image.shape[:2]
    return [[[0, 0, w, h]]]  # [line [box [x,y,w,h]]]


def crop_glyph(gray_image, box: list) -> np.ndarray:
    """Return a tiny white patch as stub glyph crop."""
    x, y, w, h = box
    return np.ones((h, w), dtype=np.uint8) * 255


def annotate(bgr, lines, font_path=None) -> np.ndarray:
    """Return the image unchanged as the annotated version."""
    return bgr
