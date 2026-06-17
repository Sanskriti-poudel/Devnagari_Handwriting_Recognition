"""
Fine-tune TrOCR on the Devanagari character data (Chandan, Phase 2).

CNN/ViT encoder + Transformer decoder (microsoft/trocr-base-handwritten by
default), fine-tuned with AdamW and teacher forcing (cross-entropy is computed
internally when `labels` are passed). Mirrors the CRNN trainer: best-checkpoint
on val loss, early stopping, CSV logging.

NEEDS A GPU for a full run (Kaggle T4 / Colab). On CPU it works but is far too
slow for the whole set — use a small CRNN_*-style subset for a sanity run.

Usage (GPU):
    python models/trocr/train.py
Env overrides:
    TROCR_MODEL        hub id (default microsoft/trocr-base-handwritten;
                       use microsoft/trocr-small-handwritten if GPU time is tight)
    TROCR_BATCH_SIZE   default 8 (GPU) / 2 (CPU)
    TROCR_EPOCHS       default 5
    TROCR_MAX_TRAIN    cap #train samples (for quick runs); 0 = all
"""

import os
import sys
import csv
import math
from datetime import datetime

import torch
from torch.optim import AdamW
from torch.utils.data import Subset, DataLoader

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
sys.path.insert(0, THIS_DIR)
sys.path.insert(0, PROJECT_ROOT)

from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from dataset import TrOCRDataset, make_collate
from augment import build_train_augment

DEFAULT_MODEL = os.environ.get("TROCR_MODEL", "microsoft/trocr-base-handwritten")
CHECKPOINT_DIR = os.path.join(PROJECT_ROOT, "models", "trocr", "checkpoints")
LOG_FILE = os.path.join(PROJECT_ROOT, "logs", "trocr_training.csv")


def configure_model(model, processor):
    """Standard TrOCR fine-tuning config (special tokens + generation).

    Training needs decoder_start_token_id / pad_token_id / vocab_size on
    model.config (used to build decoder_input_ids + mask the loss). Generation
    params (eos, max_length) must live on model.generation_config — newer
    transformers raises on save_pretrained if they're left on model.config.

    CRITICAL: TrOCR's pretrained decoder starts decoding from the </s>/sep token
    (id 2), NOT <s>/cls (id 0) — see microsoft/trocr-base-handwritten's own
    generation_config (decoder_start_token_id=2). A previous version overrode this
    to cls_token_id, so at inference the model started from an out-of-distribution
    token and emitted an immediate EOS -> empty string -> 0% accuracy / CER 1.0 on
    the whole test set, even though teacher-forced training loss looked fine. Keep
    decoder_start aligned with the pretrained model.
    """
    tok = processor.tokenizer
    model.config.decoder_start_token_id = tok.sep_token_id
    model.config.pad_token_id = tok.pad_token_id
    model.config.eos_token_id = tok.sep_token_id
    model.config.vocab_size = model.config.decoder.vocab_size

    model.generation_config.decoder_start_token_id = tok.sep_token_id
    model.generation_config.pad_token_id = tok.pad_token_id
    model.generation_config.eos_token_id = tok.sep_token_id
    model.generation_config.max_length = 8
    return model


def run_epoch(model, loader, device, optimizer=None):
    train = optimizer is not None
    model.train() if train else model.eval()
    total, n = 0.0, 0
    torch.set_grad_enabled(train)
    for batch in loader:
        pixel_values = batch["pixel_values"].to(device)
        labels = batch["labels"].to(device)
        outputs = model(pixel_values=pixel_values, labels=labels)
        loss = outputs.loss
        if train:
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        total += loss.item()
        n += 1
    torch.set_grad_enabled(True)
    return total / max(n, 1)


def train_trocr():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    batch_size = int(os.environ.get("TROCR_BATCH_SIZE", 8 if device == "cuda" else 2))
    epochs = int(os.environ.get("TROCR_EPOCHS", 5))
    max_train = int(os.environ.get("TROCR_MAX_TRAIN", 0))
    lr = float(os.environ.get("TROCR_LR", 5e-5))
    # num_workers>0 parallelises the per-image cv2 preprocessing so it doesn't
    # starve the GPU (the main bottleneck at num_workers=0). 2 is safe on Kaggle.
    num_workers = int(os.environ.get("TROCR_NUM_WORKERS", 2 if device == "cuda" else 0))

    print(f"[trocr] device={device} model={DEFAULT_MODEL} batch={batch_size} epochs={epochs}")
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    processor = TrOCRProcessor.from_pretrained(DEFAULT_MODEL)
    model = VisionEncoderDecoderModel.from_pretrained(DEFAULT_MODEL).to(device)
    model = configure_model(model, processor)
    print(f"[trocr] parameters: {sum(p.numel() for p in model.parameters()):,}")

    collate = make_collate(processor.tokenizer.pad_token_id)
    train_ds = TrOCRDataset("train", processor, augment=build_train_augment())
    val_ds = TrOCRDataset("val", processor, augment=None)
    if max_train > 0:
        train_ds = Subset(train_ds, range(min(max_train, len(train_ds))))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              collate_fn=collate, num_workers=num_workers)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                            collate_fn=collate, num_workers=num_workers)
    print(f"[trocr] num_workers={num_workers}")

    optimizer = AdamW(model.parameters(), lr=lr)

    best_val = math.inf
    patience, bad = 3, 0
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_loss", "val_loss", "timestamp"])
        for epoch in range(1, epochs + 1):
            tr = run_epoch(model, train_loader, device, optimizer)
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


if __name__ == "__main__":
    train_trocr()
