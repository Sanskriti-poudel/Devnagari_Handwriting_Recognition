"""
Fine-tune TrOCR on WORD/LINE images (Phase 2) — the model that can actually read
joined Devanagari with matras, unlike the single-character CRNN/TrOCR baselines.

Same training loop and checkpoint/early-stop logic as train.py, but:
  * data comes from a labels.csv (data/generate_synth.py output) via
    dataset_words.get_word_dataloaders, not the DHCD single-glyph split.
  * generation max_length is raised to fit a whole phrase (train.py used 8, sized
    for one glyph).

NEEDS A GPU for a real run (Kaggle T4 / Colab). On CPU use --max-train for a
sanity check only.

Usage (GPU):
    python models/trocr/train_words.py --labels Datasets/synth/labels.csv
Env overrides mirror train.py: TROCR_MODEL, TROCR_BATCH_SIZE, TROCR_EPOCHS,
TROCR_LR, TROCR_NUM_WORKERS.
"""

import os
import sys
import csv
import math
import argparse
from datetime import datetime

import torch
from torch.optim import AdamW
from transformers import get_linear_schedule_with_warmup

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
sys.path.insert(0, THIS_DIR)
sys.path.insert(0, PROJECT_ROOT)

from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from train import configure_model, run_epoch  # reuse loop + special-token config
from dataset_words import get_word_dataloaders, MAX_TARGET_LENGTH

DEFAULT_MODEL = os.environ.get("TROCR_MODEL", "microsoft/trocr-base-handwritten")
# separate checkpoint dir so the word model never clobbers the single-char one
CHECKPOINT_DIR = os.path.join(PROJECT_ROOT, "models", "trocr", "checkpoints_words")
LOG_FILE = os.path.join(PROJECT_ROOT, "logs", "trocr_words_training.csv")


def train(labels_csv, epochs, batch_size, lr, num_workers, max_train, grad_accum=1):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[trocr-words] device={device} model={DEFAULT_MODEL} "
          f"batch={batch_size} epochs={epochs} labels={labels_csv}")
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    processor = TrOCRProcessor.from_pretrained(DEFAULT_MODEL)
    model = VisionEncoderDecoderModel.from_pretrained(DEFAULT_MODEL).to(device)
    model = configure_model(model, processor)
    # configure_model sets max_length=8 (single glyph); a phrase needs much more.
    model.generation_config.max_length = MAX_TARGET_LENGTH
    print(f"[trocr-words] parameters: {sum(p.numel() for p in model.parameters()):,}")

    loaders = get_word_dataloaders(
        labels_csv, processor, batch_size=batch_size,
        num_workers=num_workers, augment_train=True,
    )
    train_loader, val_loader = loaders["train"], loaders["val"]
    if max_train > 0:  # quick CPU sanity: cap batches per epoch
        from itertools import islice
        n_batches = max(1, max_train // batch_size)
        base_train, base_val = train_loader, val_loader
        train_loader = list(islice(base_train, n_batches))
        val_loader = list(islice(base_val, max(1, n_batches // 5)))
        print(f"[trocr-words] max_train={max_train}: {len(train_loader)} train batches")

    optimizer = AdamW(model.parameters(), lr=lr)
    steps_per_epoch = math.ceil(len(train_loader) / grad_accum)
    total_steps = steps_per_epoch * epochs
    warmup_steps = max(1, int(0.1 * total_steps))
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)
    print(f"[trocr-words] grad_accum={grad_accum} warmup_steps={warmup_steps} total_steps={total_steps}")
    best_val, patience, bad = math.inf, 3, 0

    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_loss", "val_loss", "timestamp"])
        for epoch in range(1, epochs + 1):
            tr = run_epoch(model, train_loader, device, optimizer, scheduler, grad_accum)
            va = run_epoch(model, val_loader, device, optimizer=None)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Epoch {epoch:2d} | train {tr:.4f} | val {va:.4f} | {ts}")
            writer.writerow([epoch, tr, va, ts]); f.flush()

            if va < best_val:
                best_val, bad = va, 0
                model.save_pretrained(CHECKPOINT_DIR)
                processor.save_pretrained(CHECKPOINT_DIR)
                print(f"  [checkpoint] {CHECKPOINT_DIR}")
            else:
                bad += 1
                if bad >= patience:
                    print(f"[early stop] after {epoch} epochs")
                    break

    print(f"[done] best val loss {best_val:.4f} | weights in {CHECKPOINT_DIR}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default=os.path.join(PROJECT_ROOT, "Datasets", "synth", "labels.csv"),
                    help="labels.csv from data/generate_synth.py")
    ap.add_argument("--epochs", type=int, default=int(os.environ.get("TROCR_EPOCHS", 5)))
    ap.add_argument("--batch-size", type=int,
                    default=int(os.environ.get("TROCR_BATCH_SIZE",
                                               8 if torch.cuda.is_available() else 2)))
    ap.add_argument("--lr", type=float, default=float(os.environ.get("TROCR_LR", 2e-5)))
    ap.add_argument("--num-workers", type=int,
                    default=int(os.environ.get("TROCR_NUM_WORKERS",
                                               2 if torch.cuda.is_available() else 0)))
    ap.add_argument("--max-train", type=int, default=int(os.environ.get("TROCR_MAX_TRAIN", 0)),
                    help="cap #train samples for a quick CPU sanity run; 0 = all")
    ap.add_argument("--grad-accum", type=int, default=int(os.environ.get("TROCR_GRAD_ACCUM", 4)),
                    help="accumulate gradients over N batches to raise the effective batch size "
                         "without more GPU memory (helps stabilize a small physical batch)")
    args = ap.parse_args()
    train(args.labels, args.epochs, args.batch_size, args.lr, args.num_workers, args.max_train,
          args.grad_accum)


if __name__ == "__main__":
    main()
