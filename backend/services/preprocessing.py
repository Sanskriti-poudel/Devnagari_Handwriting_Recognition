import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from Preprocessing.preprocess import preprocess_image


def preprocess_for_inference(image_path: str) -> np.ndarray:
    """
    Returns float32 array of shape (1, 1, 64, 64) in [0, 1].
    Delegates to Preprocessing.preprocess_image, the single source of truth
    also used at training time, so train/serve stay in sync.
    """
    arr = preprocess_image(image_path)  # (64, 64)
    return arr[np.newaxis, np.newaxis, :, :]  # (1, 1, 64, 64)
