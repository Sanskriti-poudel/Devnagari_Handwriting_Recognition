"""
Scan the dataset for unreadable / corrupt images.

Reads the same split_index.json + DEVNAGARI_DATA_ROOT that CRNN training uses,
then attempts to decode every listed image. Reports (and optionally writes out)
the list of files that fail to load, so they can be re-preprocessed or pruned.

Usage (local):
    python Preprocessing/verify_dataset.py

Usage (Colab/Kaggle), pointing at mounted data:
    DEVNAGARI_DATA_ROOT="/content/drive/MyDrive/Devnagari project/Datasets/Preprocessed" \
        python Preprocessing/verify_dataset.py --out corrupt_images.txt
"""

import os
import sys
import json
import argparse

import cv2
from tqdm import tqdm

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_SPLIT = os.path.join(PROJECT_ROOT, "data", "split_index.json")
DATA_ROOT = os.environ.get("DEVNAGARI_DATA_ROOT", os.path.join(PROJECT_ROOT, "Datasets"))


def verify(split_index_path: str, splits, out_path: str | None):
    with open(split_index_path, "r") as f:
        split_data = json.load(f)

    corrupt = []
    for split in splits:
        paths = split_data.get(split, [])
        print(f"[verify] scanning split '{split}': {len(paths)} images")
        for rel_path in tqdm(paths):
            img_path = os.path.join(DATA_ROOT, rel_path)
            ok = False
            reason = "missing"
            if os.path.exists(img_path):
                if os.path.getsize(img_path) == 0:
                    reason = "zero-byte"
                else:
                    try:
                        ok = cv2.imread(img_path) is not None
                        reason = "undecodable" if not ok else ""
                    except cv2.error as e:
                        reason = f"cv2-error: {e}"
            if not ok:
                corrupt.append((rel_path, reason))

    print(f"\n[verify] total corrupt/unreadable: {len(corrupt)}")
    for rel_path, reason in corrupt[:50]:
        print(f"  {reason:12s}  {rel_path}")
    if len(corrupt) > 50:
        print(f"  ... and {len(corrupt) - 50} more")

    if out_path and corrupt:
        with open(out_path, "w", encoding="utf-8") as f:
            for rel_path, reason in corrupt:
                f.write(f"{rel_path}\t{reason}\n")
        print(f"[verify] wrote full list to {out_path}")

    return corrupt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split-index", default=DEFAULT_SPLIT)
    parser.add_argument("--splits", nargs="+", default=["train", "val", "test"])
    parser.add_argument("--out", default=None, help="write tab-separated list of bad files here")
    args = parser.parse_args()

    print(f"[verify] DATA_ROOT = {DATA_ROOT}")
    corrupt = verify(args.split_index, args.splits, args.out)
    sys.exit(1 if corrupt else 0)
