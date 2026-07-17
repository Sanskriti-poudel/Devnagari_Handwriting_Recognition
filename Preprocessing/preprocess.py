import os
import cv2
import numpy as np
from tqdm import tqdm

INPUT_DIR = "../Datasets/Test"
OUTPUT_DIR = "../Datasets/Preprocessed/test"
IMG_SIZE = 64


def preprocess_image(image_path: str) -> np.ndarray:
    """Preprocess a single image for CRNN inference."""
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
    resized = cv2.resize(thresh, (IMG_SIZE, IMG_SIZE))
    return resized


def preprocess_array(gray: np.ndarray) -> np.ndarray:
    """Preprocess a grayscale numpy array for CRNN inference."""
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2,
    )
    resized = cv2.resize(thresh, (IMG_SIZE, IMG_SIZE))
    return resized


if __name__ == "__main__":
    # Batch preprocessing — only runs when script is executed directly
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.isdir(INPUT_DIR):
        print(f"INPUT_DIR not found: {INPUT_DIR}")
        exit(1)

    for label in os.listdir(INPUT_DIR):
        label_path = os.path.join(INPUT_DIR, label)
        if not os.path.isdir(label_path):
            continue

        output_label_path = os.path.join(OUTPUT_DIR, label)
        os.makedirs(output_label_path, exist_ok=True)

        print(f"Processing class: {label}")

        for img_name in tqdm(os.listdir(label_path)):
            img_path = os.path.join(label_path, img_name)
            try:
                resized = preprocess_image(img_path)
                save_path = os.path.join(output_label_path, img_name)
                cv2.imwrite(save_path, resized)
            except Exception as e:
                print(f"Error: {img_path} -> {e}")

    print("Preprocessing Completed!")
