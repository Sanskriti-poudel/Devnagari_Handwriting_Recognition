import os
import cv2
import numpy as np
from tqdm import tqdm

IMG_SIZE = 64


def deskew(image):
    """Apply skew correction using the minimum-area bounding box of foreground pixels."""
    if image is None or image.size == 0:
        return image
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
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), borderValue=0)
    return rotated


def preprocess_image(img_path: str) -> np.ndarray:
    """
    Preprocess a single image: grayscale -> denoise -> adaptive threshold ->
    skew correction -> resize -> normalize to [0, 1].

    This is the SINGLE source of truth for preprocessing. Both CRNN training
    and the backend inference API import this function so train/serve stay
    consistent (proposal section 3.2.2).

    Args:
        img_path: absolute or relative path to an image file

    Returns:
        np.ndarray: preprocessed image, shape (64, 64), float32 in [0, 1]

    Raises:
        IOError: if the image cannot be read
    """
    img = cv2.imread(img_path)
    if img is None:
        raise IOError(f"Cannot read image: {img_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )

    # skew correction on the binarized image (foreground = white)
    thresh = deskew(thresh)

    resized = cv2.resize(thresh, (IMG_SIZE, IMG_SIZE))
    normalized = resized.astype(np.float32) / 255.0

    return normalized


def _batch_preprocess(input_dir: str, output_dir: str):
    """Batch-preprocess a class-folder dataset (kept for the original CLI use)."""
    os.makedirs(output_dir, exist_ok=True)

    for label in os.listdir(input_dir):
        label_path = os.path.join(input_dir, label)
        if not os.path.isdir(label_path):
            continue

        output_label_path = os.path.join(output_dir, label)
        os.makedirs(output_label_path, exist_ok=True)
        print(f"Processing class: {label}")

        for img_name in tqdm(os.listdir(label_path)):
            img_path = os.path.join(label_path, img_name)
            try:
                normalized = preprocess_image(img_path)
                save_path = os.path.join(output_label_path, img_name)
                cv2.imwrite(save_path, (normalized * 255).astype(np.uint8))
            except Exception as e:
                print(f"Error: {img_path} -> {e}")

    print("Preprocessing Completed!")


if __name__ == "__main__":
    INPUT_DIR = "../Datasets/Test"
    OUTPUT_DIR = "../Datasets/Preprocessed/test"
    _batch_preprocess(INPUT_DIR, OUTPUT_DIR)
