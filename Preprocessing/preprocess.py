import os
import cv2
import numpy as np
from tqdm import tqdm

INPUT_DIR = "../Datasets/Test"
OUTPUT_DIR = "../Datasets/Preprocessed/test"

IMG_SIZE = 64

os.makedirs(OUTPUT_DIR, exist_ok=True)

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
            img = cv2.imread(img_path)

            if img is None:
                continue  # skip broken images

            # grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # light blur (optional)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)

            # adaptive threshold
            thresh = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                11,
                2
            )

            # resize
            resized = cv2.resize(thresh, (IMG_SIZE, IMG_SIZE))

            # save directly (NO normalization needed for images)
            save_path = os.path.join(output_label_path, img_name)
            cv2.imwrite(save_path, resized)

        except Exception as e:
            print(f"Error: {img_path} -> {e}")

print("Preprocessing Completed!")