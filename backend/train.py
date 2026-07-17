"""
Training script for the CRNN model on Devanagari handwriting data.

Dataset layout expected:
    <DATA_DIR>/
        <label_1>/   ← Unicode character name or codepoint
            img001.png
            ...
        <label_2>/
            ...

Each subfolder name is used as the ground-truth label (single character).
Images are preprocessed, then assembled into fixed-height strips for CRNN.

Usage:
    python train.py --data ../Datasets/Preprocessed/train --epochs 30
"""

import argparse
import os
import logging
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class DevanagariDataset(Dataset):
    """
    Loads character images organised in class directories.
    Each sample is (image_tensor, label_tensor, input_length, label_length).
    """

    def __init__(self, root: str, img_height: int = 32):
        from ml_models.char_map import char_to_idx
        self.img_height = img_height
        self.samples: list[tuple[str, int]] = []

        for label_dir in sorted(Path(root).iterdir()):
            if not label_dir.is_dir():
                continue
            char = label_dir.name
            if char not in char_to_idx:
                logger.warning("Label %r not in char_map — skipping", char)
                continue
            idx = char_to_idx[char]
            for img_path in label_dir.glob("*.png"):
                self.samples.append((str(img_path), idx))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, i):
        path, label_idx = self.samples[i]
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise RuntimeError(f"Cannot read {path!r}")

        img = cv2.GaussianBlur(img, (3, 3), 0)
        img = cv2.adaptiveThreshold(
            img, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11, 2,
        )
        h, w = img.shape
        new_w = max(1, int(w * self.img_height / h))
        img = cv2.resize(img, (new_w, self.img_height), interpolation=cv2.INTER_AREA)

        tensor = torch.from_numpy(img.astype(np.float32) / 255.0).unsqueeze(0)  # (1, H, W)
        label = torch.tensor([label_idx], dtype=torch.long)
        return tensor, label


def collate_fn(batch):
    """Pads images in a batch to the same width."""
    images, labels = zip(*batch)
    max_w = max(img.shape[2] for img in images)
    padded = torch.zeros(len(images), 1, images[0].shape[1], max_w)
    for i, img in enumerate(images):
        padded[i, :, :, : img.shape[2]] = img
    labels_cat = torch.cat(labels)
    input_lengths = torch.full((len(images),), max_w // 4, dtype=torch.long)
    label_lengths = torch.ones(len(images), dtype=torch.long)
    return padded, labels_cat, input_lengths, label_lengths


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def train(args):
    import sys
    sys.path.insert(0, os.path.dirname(__file__))

    from ml_models.crnn import CRNN
    from ml_models.char_map import NUM_CLASSES

    device = torch.device(args.device)
    model = CRNN(num_classes=NUM_CLASSES).to(device)
    criterion = nn.CTCLoss(blank=0, zero_infinity=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

    dataset = DevanagariDataset(args.data, img_height=32)
    if len(dataset) == 0:
        logger.error("No samples found in %s", args.data)
        return

    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True,
                        collate_fn=collate_fn, num_workers=0)
    logger.info("Training on %d samples, %d epochs", len(dataset), args.epochs)

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for images, labels, input_lengths, label_lengths in loader:
            images = images.to(device)
            log_probs = model(images)  # (T, B, C)
            loss = criterion(log_probs, labels, input_lengths, label_lengths)
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            total_loss += loss.item()

        scheduler.step()
        avg = total_loss / len(loader)
        logger.info("Epoch %d/%d  loss=%.4f", epoch, args.epochs, avg)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), args.output)
    logger.info("Model saved to %s", args.output)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train CRNN on Devanagari dataset")
    parser.add_argument("--data", required=True, help="Path to dataset root with class dirs")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--device", default="cpu", help="cpu or cuda")
    parser.add_argument("--output", default="../models/crnn.pth",
                        help="Where to save the trained weights")
    train(parser.parse_args())
