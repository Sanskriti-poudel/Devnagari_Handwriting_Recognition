import cv2
import numpy as np

IMG_SIZE = 64


def _deskew(image: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(image > 0))
    if coords.shape[0] == 0:
        return image
    angle = cv2.minAreaRect(coords)[2]
    if angle < -45:
        angle = 90 + angle
    elif angle > 45:
        angle = angle - 90
    if abs(angle) < 1:
        return image
    h, w = image.shape
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), borderValue=0)


def preprocess_for_inference(image_path: str) -> np.ndarray:
    """
    Returns float32 array of shape (1, 1, 64, 64) in [0, 1].
    Matches the pipeline in Preprocessing/preprocess.py used during training.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise IOError(f"Cannot read image: {image_path!r}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2,
    )
    thresh = _deskew(thresh)
    resized = cv2.resize(thresh, (IMG_SIZE, IMG_SIZE))
    arr = resized.astype(np.float32) / 255.0
    return arr[np.newaxis, np.newaxis, :, :]  # (1, 1, 64, 64)
