import os
import json
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.optim.lr_scheduler import StepLR
import csv
from datetime import datetime

from model import CRNN, decode_ctc_greedy
from dataset import get_crnn_dataloaders


def train_epoch(model, train_loader, optimizer, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    num_batches = 0

    for images, labels_flat, label_lengths in train_loader:
        images = images.to(device)
        labels_flat = labels_flat.to(device)
        label_lengths = label_lengths.to(device)

        optimizer.zero_grad()

        # Forward pass
        logits = model(images)  # (T, B, num_classes)

        # Prepare for CTC loss
        # CTC expects: logits (T, B, C), targets, input_lengths (B,), target_lengths (B,)
        input_lengths = torch.full((images.size(0),), logits.size(0), dtype=torch.long, device=device)

        # CTC loss (blank_idx = last index)
        criterion = nn.CTCLoss(blank=model.num_classes - 1, reduction='mean')
        loss = criterion(logits, labels_flat, input_lengths, label_lengths)

        # Backward
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item()
        num_batches += 1

    return total_loss / num_batches


def validate(model, val_loader, charset, device):
    """Validate and compute metrics."""
    model.eval()
    total_loss = 0.0
    num_batches = 0

    criterion = nn.CTCLoss(blank=model.num_classes - 1, reduction='mean')

    with torch.no_grad():
        for images, labels_flat, label_lengths in val_loader:
            images = images.to(device)
            labels_flat = labels_flat.to(device)
            label_lengths = label_lengths.to(device)

            logits = model(images)  # (T, B, num_classes)

            input_lengths = torch.full((images.size(0),), logits.size(0), dtype=torch.long, device=device)
            loss = criterion(logits, labels_flat, input_lengths, label_lengths)

            total_loss += loss.item()
            num_batches += 1

    avg_loss = total_loss / num_batches

    return avg_loss


def train_crnn(
    num_epochs=50,
    batch_size=32,
    learning_rate=0.001,
    device="cpu",
    checkpoint_dir="models/crnn/checkpoints",
    log_file="logs/crnn_training.csv"
):
    """
    Main training function for CRNN.

    Args:
        num_epochs: number of training epochs
        batch_size: batch size
        learning_rate: initial learning rate
        device: "cpu" or "cuda"
        checkpoint_dir: where to save model checkpoints
        log_file: where to save training log
    """
    os.makedirs(checkpoint_dir, exist_ok=True)
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Load dataloaders
    dataloaders = get_crnn_dataloaders(batch_size=batch_size)
    train_loader = dataloaders["train"]
    val_loader = dataloaders["val"]
    charset = train_loader.dataset.get_charset()
    num_classes = len(charset) + 1  # +1 for CTC blank

    # Model
    model = CRNN(num_classes=num_classes, hidden_size=256).to(device)
    print(f"[CRNN] Model created with {num_classes} classes")
    print(f"[CRNN] Total parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Optimizer & scheduler
    optimizer = Adam(model.parameters(), lr=learning_rate)
    scheduler = StepLR(optimizer, step_size=10, gamma=0.5)

    # Training loop
    best_val_loss = float('inf')
    patience = 10
    patience_counter = 0

    with open(log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_loss", "val_loss", "timestamp"])

        for epoch in range(1, num_epochs + 1):
            train_loss = train_epoch(model, train_loader, optimizer, device)
            val_loss = validate(model, val_loader, charset, device)
            scheduler.step()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"Epoch {epoch:3d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | {timestamp}"
            )
            writer.writerow([epoch, train_loss, val_loss, timestamp])
            f.flush()

            # Save checkpoint if val loss improves
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                checkpoint_path = os.path.join(checkpoint_dir, "best_model.pth")
                torch.save(model.state_dict(), checkpoint_path)
                print(f"  [CHECKPOINT] {checkpoint_path}")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"[EARLY STOP] Early stopping after {epoch} epochs")
                    break

    print(f"[DONE] Training complete. Best model: {os.path.join(checkpoint_dir, 'best_model.pth')}")
    return model, checkpoint_dir


if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[Device] Using: {device}")

    # Larger batches on GPU (Colab T4); override either default with CRNN_BATCH_SIZE.
    batch_size = int(os.environ.get("CRNN_BATCH_SIZE", 64 if device == "cuda" else 16))
    print(f"[Config] batch_size = {batch_size}")

    model, checkpoint_dir = train_crnn(
        num_epochs=50,
        batch_size=batch_size,
        learning_rate=0.001,
        device=device,
        checkpoint_dir="models/crnn/checkpoints",
        log_file="logs/crnn_training.csv"
    )
