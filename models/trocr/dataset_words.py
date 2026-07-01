"""
Word/line-level dataset for TrOCR (Phase 2).

Unlike dataset.py (one isolated DHCD glyph per item, label = single character),
this reads (image -> FULL text string) pairs from a labels.csv produced by
data/generate_synth.py:

    image_path,text
    images/synth_000001.png,मेरो नाम
    ...

Key differences from the single-character dataset, and WHY:
  * No `preprocess_image` / 64x64 / contrast inversion. The single-char pipeline
    forced every crop to a 64x64 white-on-black DHCD glyph; word images are
    variable-size, multi-glyph, and already dark-ink-on-light-paper (the domain
    TrOCR-base-handwritten expects). We hand the PIL image straight to the
    processor — same path used at inference (predict_words.py) so there's no
    train/serve skew.
  * MAX_TARGET_LENGTH is large (a phrase tokenizes into many subword tokens),
    not 8 — that 8 was sized for a single glyph.

The train/val/test split is derived deterministically from the CSV (seeded
shuffle), so there's no separate split file to maintain for synthetic data.
"""

import os
import csv
import random

import torch
from PIL import Image
from torch.utils.data import Dataset, DataLoader

# A long document-style line (5-12 tokens, mixed Devanagari/Latin) tokenizes
# into many subword tokens; 160 gives headroom so labels aren't silently
# truncated. (Short phrases use far fewer — the cap only bounds the long lines.)
MAX_TARGET_LENGTH = 160


def _read_rows(labels_csv):
    with open(labels_csv, encoding="utf-8") as f:
        return [(r["image_path"], r["text"]) for r in csv.DictReader(f)]


def split_rows(rows, val_frac=0.1, test_frac=0.1, seed=42):
    """Deterministic train/val/test split of (path, text) rows."""
    rows = list(rows)
    random.Random(seed).shuffle(rows)
    n = len(rows)
    n_test = int(n * test_frac)
    n_val = int(n * val_frac)
    return {
        "test": rows[:n_test],
        "val": rows[n_test:n_test + n_val],
        "train": rows[n_test + n_val:],
    }


class WordLineDataset(Dataset):
    def __init__(self, rows, processor, root, augment=None, max_len=MAX_TARGET_LENGTH):
        """
        Args:
            rows: list of (image_path, text); image_path is relative to `root`.
            processor: a TrOCRProcessor.
            root: directory the image_path values are relative to.
            augment: optional callable PIL(RGB)->PIL(RGB), train-side only.
            max_len: tokenizer truncation length for the label.
        """
        self.rows = rows
        self.processor = processor
        self.root = root
        self.augment = augment
        self.max_len = max_len
        print(f"[WordLineDataset] {len(rows)} items{' (augmented)' if augment else ''}")

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        # Skip transiently-unreadable files rather than crash a long run.
        n = len(self.rows)
        for offset in range(min(50, n)):
            rel, text = self.rows[(idx + offset) % n]
            try:
                img = Image.open(os.path.join(self.root, rel)).convert("RGB")
            except (IOError, OSError) as e:
                print(f"[WordLineDataset] WARN skip {rel}: {e}")
                continue

            if self.augment is not None:
                img = self.augment(img)

            pixel_values = self.processor(images=img, return_tensors="pt").pixel_values[0]
            labels = self.processor.tokenizer(
                text, max_length=self.max_len, padding=False, truncation=True
            ).input_ids
            return {"pixel_values": pixel_values,
                    "labels": torch.tensor(labels, dtype=torch.long)}

        raise RuntimeError(f"No readable image within 50 of idx {idx} under {self.root}")


def build_word_augment():
    """Mild affine jitter for word images. fill=255 (WHITE) because these are
    dark-ink-on-LIGHT-paper — the single-char augment used fill=0 since DHCD was
    white-on-black; using black here would paint dark borders the model reads as
    ink. Kept mild so the headline/matras aren't distorted into other glyphs."""
    from torchvision import transforms
    return transforms.RandomAffine(
        degrees=3, translate=(0.03, 0.03), scale=(0.95, 1.05), shear=4, fill=255,
    )


def make_collate(pad_token_id):
    def collate(batch):
        pixel_values = torch.stack([b["pixel_values"] for b in batch])
        max_len = max(b["labels"].size(0) for b in batch)
        labels = torch.full((len(batch), max_len), pad_token_id, dtype=torch.long)
        for i, b in enumerate(batch):
            labels[i, : b["labels"].size(0)] = b["labels"]
        labels[labels == pad_token_id] = -100  # ignore pad in the loss
        return {"pixel_values": pixel_values, "labels": labels}
    return collate


def get_word_dataloaders(labels_csv, processor, batch_size=8, num_workers=0,
                         augment_train=True, val_frac=0.1, test_frac=0.1, seed=42):
    root = os.path.dirname(os.path.abspath(labels_csv))
    splits = split_rows(_read_rows(labels_csv), val_frac, test_frac, seed)
    collate = make_collate(processor.tokenizer.pad_token_id)
    loaders = {}
    for split, rows in splits.items():
        aug = build_word_augment() if (split == "train" and augment_train) else None
        ds = WordLineDataset(rows, processor, root, augment=aug)
        loaders[split] = DataLoader(
            ds, batch_size=batch_size, shuffle=(split == "train"),
            collate_fn=collate, num_workers=num_workers,
        )
    return loaders
