"""
Dataset for fine-tuning TrOCR on the Devanagari character data.

Mirrors the CRNN dataset (same split_index.json, same DATA_ROOT, same
`preprocess_image` so there is no train/serve skew) but produces TrOCR-shaped
items:
  - pixel_values: (3, 384, 384) float tensor from the TrOCR processor
  - labels:       token ids of the Devanagari glyph string (e.g. "क")

Targets are the REAL Devanagari glyphs (via data/devanagari_labels.py), because
TrOCR's decoder emits Unicode text — unlike CTC, which only needs class ids.
"""

import os
import sys
import json

import cv2
import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset, DataLoader

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
sys.path.insert(0, THIS_DIR)
sys.path.insert(0, PROJECT_ROOT)

from Preprocessing.preprocess import preprocess_image
from data.devanagari_labels import class_to_glyph

DEFAULT_SPLIT = os.path.join(PROJECT_ROOT, "data", "split_index.json")
DATA_ROOT = os.environ.get("DEVNAGARI_DATA_ROOT", os.path.join(PROJECT_ROOT, "Datasets"))

MAX_TARGET_LENGTH = 8  # glyphs are 1–3 tokens; 8 is comfortable headroom


def _label_of(rel_path):
    return os.path.basename(os.path.dirname(rel_path))


def array_to_rgb_pil(arr01):
    """(64,64) float [0,1] -> 3-channel uint8 PIL image for the TrOCR processor.

    Our preprocessing (THRESH_BINARY_INV) yields a WHITE character on a BLACK
    background. TrOCR-base-handwritten was pretrained on natural handwriting —
    DARK ink on LIGHT paper — so we invert here to match that domain. Feeding the
    pretrained ViT encoder inverted-contrast images wrecks its features (near-random
    val loss). CRNN is trained from scratch, so it is unaffected and keeps the
    original polarity; this inversion is TrOCR-only.
    """
    gray = ((1.0 - arr01) * 255).astype(np.uint8)
    rgb = np.stack([gray, gray, gray], axis=-1)
    return Image.fromarray(rgb)


class TrOCRDataset(Dataset):
    def __init__(self, split, processor, augment=None, split_index_path=DEFAULT_SPLIT):
        """
        Args:
            split: "train" | "val" | "test"
            processor: a TrOCRProcessor (feature extractor + tokenizer)
            augment: optional callable PIL->PIL, applied train-side only
            split_index_path: path to split_index.json
        """
        self.split = split
        self.processor = processor
        self.augment = augment
        with open(split_index_path) as f:
            self.image_paths = json.load(f)[split]
        print(f"[TrOCRDataset] {len(self.image_paths)} images for split '{split}'"
              f"{' (augmented)' if augment else ''}")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        # Skip transiently-unreadable / corrupt files rather than crash a long run
        # (same robustness contract as the CRNN dataset).
        n = len(self.image_paths)
        for offset in range(min(50, n)):
            rel = self.image_paths[(idx + offset) % n]
            try:
                arr = preprocess_image(os.path.join(DATA_ROOT, rel))
            except (IOError, OSError, cv2.error) as e:
                print(f"[TrOCRDataset] WARN skip {rel}: {e}")
                continue

            img = array_to_rgb_pil(arr)
            if self.augment is not None:
                img = self.augment(img)

            pixel_values = self.processor(images=img, return_tensors="pt").pixel_values[0]

            text = class_to_glyph(_label_of(rel))
            labels = self.processor.tokenizer(
                text, max_length=MAX_TARGET_LENGTH, padding=False, truncation=True
            ).input_ids
            return {"pixel_values": pixel_values, "labels": torch.tensor(labels, dtype=torch.long)}

        raise RuntimeError(f"No readable image within 50 of idx {idx} under {DATA_ROOT}")


def make_collate(pad_token_id):
    def collate(batch):
        pixel_values = torch.stack([b["pixel_values"] for b in batch])
        max_len = max(b["labels"].size(0) for b in batch)
        labels = torch.full((len(batch), max_len), pad_token_id, dtype=torch.long)
        for i, b in enumerate(batch):
            labels[i, : b["labels"].size(0)] = b["labels"]
        # ignore pad positions in the loss
        labels[labels == pad_token_id] = -100
        return {"pixel_values": pixel_values, "labels": labels}
    return collate


def get_trocr_dataloaders(processor, batch_size=8, num_workers=0, augment_train=True):
    from augment import build_train_augment

    loaders = {}
    for split in ["train", "val", "test"]:
        aug = build_train_augment() if (split == "train" and augment_train) else None
        ds = TrOCRDataset(split, processor, augment=aug)
        loaders[split] = DataLoader(
            ds,
            batch_size=batch_size,
            shuffle=(split == "train"),
            collate_fn=make_collate(processor.tokenizer.pad_token_id),
            num_workers=num_workers,
        )
    return loaders
