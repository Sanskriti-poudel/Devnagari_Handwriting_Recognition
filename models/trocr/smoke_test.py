"""
Fast, network-free sanity check for the TrOCR data path (run from repo root):

    python models/trocr/smoke_test.py

Validates the parts most likely to break BEFORE spending GPU time on Kaggle:
  - the Devanagari label map covers every class in the dataset
  - preprocessing -> RGB PIL conversion produces a valid image
  - the train-only augmentation runs and preserves image size

It does NOT download the 1.4 GB TrOCR weights or run the model — that is
exercised on the GPU notebook. Prints PASS/FAIL.
"""

import os
import sys
import json

# Windows consoles default to cp1252 and can't print Devanagari glyphs.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
sys.path.insert(0, THIS_DIR)
sys.path.insert(0, PROJECT_ROOT)

from data.devanagari_labels import CLASS_TO_DEVANAGARI, class_to_glyph
from dataset import array_to_rgb_pil, DATA_ROOT, DEFAULT_SPLIT
from augment import build_train_augment
from Preprocessing.preprocess import preprocess_image


def main():
    ok = True

    # 1. label map covers all classes in the charset
    charset = json.load(open(os.path.join(PROJECT_ROOT, "data", "charset.json"), encoding="utf-8"))["chars"]
    missing = [c for c in charset if c not in CLASS_TO_DEVANAGARI]
    if missing:
        print(f"[FAIL] label map missing {len(missing)} classes: {missing[:5]}")
        ok = False
    else:
        print(f"[ok] label map covers all {len(charset)} classes "
              f"(e.g. {charset[0]} -> {class_to_glyph(charset[0])})")

    # 2. preprocessing -> RGB PIL on a real sample
    split = json.load(open(DEFAULT_SPLIT))
    sample_rel = split["train"][0]
    sample_path = os.path.join(DATA_ROOT, sample_rel)
    if not os.path.exists(sample_path):
        print(f"[skip] sample image not found ({sample_path}); "
              f"set DEVNAGARI_DATA_ROOT to test image loading.")
    else:
        arr = preprocess_image(sample_path)
        img = array_to_rgb_pil(arr)
        if img.size == (64, 64) and img.mode == "RGB":
            print(f"[ok] preprocess -> RGB PIL {img.size} {img.mode}")
        else:
            print(f"[FAIL] unexpected PIL image {img.size} {img.mode}")
            ok = False

        # 3. augmentation runs and preserves size
        aug = build_train_augment()
        aug_img = aug(img)
        if aug_img.size == img.size:
            print(f"[ok] augmentation runs, size preserved {aug_img.size}")
        else:
            print(f"[FAIL] augmentation changed size: {aug_img.size}")
            ok = False

    print("\nPASS" if ok else "\nFAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
