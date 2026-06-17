"""
Quick end-to-end smoke test of the CRNN pipeline.
Validates: data loading -> preprocessing -> model forward -> CTC loss -> backprop.
Runs on a tiny subset so it finishes in seconds, BEFORE the full training run.
"""
import torch
import torch.nn as nn

from model import CRNN, decode_ctc_greedy
from dataset import CRNNDataset, collate_crnn
from torch.utils.data import DataLoader, Subset


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[smoke] device = {device}")

    # Load a tiny slice of the train split (first 32 images)
    full = CRNNDataset(split="train")
    charset = full.get_charset()
    num_classes = len(charset) + 1  # +1 for CTC blank
    print(f"[smoke] num_classes = {num_classes} (46 chars + 1 blank)")

    subset = Subset(full, list(range(32)))
    loader = DataLoader(subset, batch_size=8, collate_fn=collate_crnn)

    # Build model
    model = CRNN(num_classes=num_classes, hidden_size=256).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[smoke] model params = {n_params:,}")

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CTCLoss(blank=num_classes - 1, reduction="mean")

    # Run a few training steps and confirm loss is finite and decreasing-ish
    model.train()
    losses = []
    for step, (images, labels_flat, label_lengths) in enumerate(loader):
        images = images.to(device)
        labels_flat = labels_flat.to(device)
        label_lengths = label_lengths.to(device)

        # Sanity-check shapes on the first batch
        if step == 0:
            print(f"[smoke] image batch shape  = {tuple(images.shape)}  (B, 1, 64, 64)")

        optimizer.zero_grad()
        logits = model(images)  # (T, B, num_classes)
        if step == 0:
            print(f"[smoke] logits shape       = {tuple(logits.shape)}  (T, B, num_classes)")

        input_lengths = torch.full((images.size(0),), logits.size(0), dtype=torch.long, device=device)
        loss = criterion(logits, labels_flat, input_lengths, label_lengths)
        loss.backward()
        optimizer.step()

        losses.append(loss.item())
        print(f"[smoke] step {step}: loss = {loss.item():.4f}")

    # Decode one batch to confirm decoding works
    model.eval()
    with torch.no_grad():
        images, labels_flat, label_lengths = next(iter(loader))
        logits = model(images.to(device))
        decoded = decode_ctc_greedy(logits, charset, blank_idx=num_classes - 1)
    print(f"[smoke] sample decoded predictions: {decoded[:3]}")

    assert all(torch.isfinite(torch.tensor(l)) for l in losses), "Loss became non-finite!"
    print("\n[smoke] PASS - pipeline works end-to-end. Ready for full training.")


if __name__ == "__main__":
    main()
