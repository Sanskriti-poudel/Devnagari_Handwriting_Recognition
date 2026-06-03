"""
Prepare dataset: copy from Downloads to local Datasets folder and create split index.
"""
import os
import json
import shutil
from pathlib import Path
from sklearn.model_selection import train_test_split

# Paths
DOWNLOAD_DATA = Path(r"C:\Users\Sanskriti Poudel\Downloads\Devnagari project\Datasets\Preprocessed")
PROJECT_ROOT = Path(__file__).parent.parent
DATASET_ROOT = PROJECT_ROOT / "Datasets"
SPLIT_INDEX_FILE = PROJECT_ROOT / "data" / "split_index.json"
CHARSET_FILE = PROJECT_ROOT / "data" / "charset.json"

print(f"[Download data] {DOWNLOAD_DATA}")
print(f"[Project root] {PROJECT_ROOT}")
print(f"[Dataset target] {DATASET_ROOT}")

# Step 1: Copy dataset from Downloads to project folder
print("\n[Step 1] Copying dataset...")
DATASET_ROOT.mkdir(exist_ok=True)

for split in ["train", "test"]:
    src = DOWNLOAD_DATA / split
    dst = DATASET_ROOT / split

    if src.exists() and not dst.exists():
        print(f"  Copying {split}/ ...")
        shutil.copytree(src, dst)
    elif dst.exists():
        print(f"  {split}/ already exists, skipping")
    else:
        print(f"  ERROR: {src} not found!")

# Step 2: Collect all image paths and create split
print("\n[Step 2] Creating train/val/test split...")

all_images = []
all_labels = []

# Load from existing train/test split
for split in ["train", "test"]:
    split_dir = DATASET_ROOT / split
    if not split_dir.exists():
        print(f"  WARNING: {split_dir} not found")
        continue

    for class_dir in split_dir.iterdir():
        if not class_dir.is_dir():
            continue

        class_name = class_dir.name
        for img_file in class_dir.glob("*.[pP][nN][gG]"):
            # store path RELATIVE to DATASET_ROOT (portable across machines/Colab),
            # using forward slashes so it works on both Windows and Linux
            rel = img_file.relative_to(DATASET_ROOT).as_posix()
            all_images.append(rel)
            all_labels.append(class_name)

print(f"  Total images: {len(all_images)}")
print(f"  Unique classes: {len(set(all_labels))}")

# Create reproducible 80/10/10 split
train_imgs, test_imgs, train_lbls, test_lbls = train_test_split(
    all_images, all_labels, test_size=0.1, random_state=42, stratify=all_labels
)

train_imgs, val_imgs, train_lbls, val_lbls = train_test_split(
    train_imgs, train_lbls, test_size=0.111, random_state=42, stratify=train_lbls
)

print(f"  Train: {len(train_imgs)} | Val: {len(val_imgs)} | Test: {len(test_imgs)}")

split_index = {
    "train": train_imgs,
    "val": val_imgs,
    "test": test_imgs
}

SPLIT_INDEX_FILE.parent.mkdir(exist_ok=True)
with open(SPLIT_INDEX_FILE, "w") as f:
    json.dump(split_index, f)
print(f"[OK] Split saved to: {SPLIT_INDEX_FILE}")

# Step 3: Create charset.json from actual classes in the data
print("\n[Step 3] Creating charset.json...")

# Since dataset contains Newari + Devanagari + digits, use class names as labels
# This is more practical than trying to map to Unicode characters
unique_classes = sorted(set(all_labels))

# Exclude 'test' if it accidentally got in there
unique_classes = [c for c in unique_classes if c != 'test']

print(f"  Found {len(unique_classes)} unique character classes")

charset = {
    "chars": unique_classes,
    "blank_idx": len(unique_classes),
    "num_classes": len(unique_classes) + 1  # +1 for CTC blank
}

with open(CHARSET_FILE, "w", encoding="utf-8") as f:
    json.dump(charset, f, ensure_ascii=False, indent=2)
print(f"[OK] Charset saved to: {CHARSET_FILE}")
print(f"  Total characters: {len(charset['chars'])}")

print("\n[DONE] Dataset preparation complete!")
print(f"   Ready for CRNN training at: {PROJECT_ROOT / 'models/crnn/train.py'}")
