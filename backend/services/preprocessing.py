"""
Single-image preprocessing for CRNN inference.

Mirrors the pipeline in Preprocessing/preprocess.py but:
- operates on one file at a time
- preserves the original aspect ratio (scales to fixed height, variable width)
- returns a float32 numpy array ready for torch.from_numpy()
"""

import cv2
import numpy as np

IMG_HEIGHT = 32  # must match models/crnn.py


def preprocess_for_inference(image_path: str) -> np.ndarray:
    """
    Loads, binarises, and resizes one image for CRNN inference.

    Returns: float32 array of shape (1, 1, IMG_HEIGHT, W), values in [0, 1].
    Raises: ValueError if the file cannot be read.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path!r}")

    img = cv2.GaussianBlur(img, (3, 3), 0)

    img = cv2.adaptiveThreshold(
        img, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2,
    )

    h, w = img.shape
    new_w = max(1, int(w * IMG_HEIGHT / h))
    img = cv2.resize(img, (new_w, IMG_HEIGHT), interpolation=cv2.INTER_AREA)

    tensor = (img.astype(np.float32) / 255.0)[np.newaxis, np.newaxis, :, :]
    return tensor  # (1, 1, H, W)
