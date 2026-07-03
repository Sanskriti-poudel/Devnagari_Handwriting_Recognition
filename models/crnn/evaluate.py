"""
Evaluate the trained CRNN baseline on the held-out TEST split.

Reports the proposal's Phase 3 metrics (section 3.7):
  - Accuracy   : exact-match class accuracy (the primary metric for this
                 character-level dataset)
  - CER        : Character Error Rate = (S + D + I) / N  (via jiwer)
  - WER        : Word Error Rate                          (via jiwer)
plus parameter count and average inference latency for the comparison table.

Each test image is a single Devanagari character, so the model emits one class
per image. For CER/WER each class is mapped to a unique single symbol so the
metrics are well-defined at the per-sample level; with single-character samples
these reduce to (1 - Accuracy), but the code generalizes to true sequence data.

Usage:
    python models/crnn/evaluate.py
    python models/crnn/evaluate.py --checkpoint kaggle_output/artifacts/best_model.pth
"""

import os
import sys
import json
import time
import argparse

import torch

# Allow running as a script from anywhere: add this dir (for model/dataset
# imports) and the repo root (for Preprocessing).
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
sys.path.insert(0, THIS_DIR)
sys.path.insert(0, PROJECT_ROOT)

from model import CRNN, decode_ctc_greedy
from dataset import get_crnn_dataloaders


def _default_checkpoint():
    """Prefer the local checkpoint, fall back to the Kaggle run artifact."""
    candidates = [
        os.path.join(PROJECT_ROOT, "models", "crnn", "checkpoints", "best_model.pth"),
        os.path.join(PROJECT_ROOT, "kaggle_output", "artifacts", "best_model.pth"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


def reconstruct_ground_truth(labels_flat, label_lengths, charset):
    """Split the flat label tensor back into per-sample class-name strings."""
    gts = []
    cursor = 0
    for length in label_lengths.tolist():
        idxs = labels_flat[cursor:cursor + length].tolist()
        gts.append("_".join(charset[i] for i in idxs))
        cursor += length
    return gts


def evaluate(checkpoint_path, device="cpu", batch_size=64):
    import jiwer

    # --- data ---
    loaders = get_crnn_dataloaders(batch_size=batch_size)
    test_loader = loaders["test"]
    charset = test_loader.dataset.get_charset()
    blank_idx = test_loader.dataset.get_blank_idx()
    num_classes = test_loader.dataset.num_classes

    # --- model ---
    model = CRNN(num_classes=num_classes, hidden_size=256).to(device)
    state = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state)
    model.eval()
    param_count = sum(p.numel() for p in model.parameters())
    print(f"[eval] Loaded {checkpoint_path}")
    print(f"[eval] {num_classes} classes | {param_count:,} parameters | device={device}")

    # one unique symbol per class so jiwer treats each class as one token
    sym = {c: chr(0xE000 + i) for i, c in enumerate(charset)}

    def to_symbols(class_str):
        # a predicted string may hold 0, 1 or several "_"-joined class tokens
        if not class_str:
            return ""
        return "".join(sym.get(tok, "￿") for tok in class_str.split("_"))

    correct = 0
    total = 0
    ref_chars, hyp_chars = [], []   # for CER (concatenated symbols)
    ref_words, hyp_words = [], []   # for WER (space-separated per sample)
    infer_time = 0.0

    with torch.no_grad():
        for images, labels_flat, label_lengths in test_loader:
            images = images.to(device)

            t0 = time.perf_counter()
            log_probs = model(images)  # (T, B, num_classes)
            if device == "cuda":
                torch.cuda.synchronize()
            infer_time += time.perf_counter() - t0

            preds = decode_ctc_greedy(log_probs, charset, blank_idx=blank_idx)
            gts = reconstruct_ground_truth(labels_flat, label_lengths, charset)

            for pred, gt in zip(preds, gts):
                total += 1
                if pred == gt:
                    correct += 1
                ref_chars.append(to_symbols(gt))
                hyp_chars.append(to_symbols(pred))
                ref_words.append(to_symbols(gt))
                hyp_words.append(to_symbols(pred))

    accuracy = correct / total if total else 0.0
    cer = jiwer.cer("".join(ref_chars), "".join(hyp_chars))
    wer = jiwer.wer(" ".join(ref_words), " ".join(hyp_words))
    latency_ms = (infer_time / total * 1000) if total else 0.0

    results = {
        "checkpoint": checkpoint_path,
        "test_samples": total,
        "accuracy": round(accuracy, 4),
        "cer": round(cer, 4),
        "wer": round(wer, 4),
        "param_count": param_count,
        "avg_inference_latency_ms": round(latency_ms, 3),
        "device": device,
    }

    print("\n=== CRNN baseline — TEST set ===")
    print(f"  Samples            : {total}")
    print(f"  Accuracy           : {accuracy * 100:.2f}%")
    print(f"  CER                : {cer:.4f}")
    print(f"  WER                : {wer:.4f}")
    print(f"  Parameters         : {param_count:,}")
    print(f"  Inference latency  : {latency_ms:.3f} ms/image ({device})")

    out_path = os.path.join(PROJECT_ROOT, "logs", "crnn_eval.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[eval] Wrote metrics -> {out_path}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the CRNN baseline on the test split.")
    parser.add_argument("--checkpoint", default=_default_checkpoint(),
                        help="Path to best_model.pth")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu",
                        choices=["cpu", "cuda"])
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()

    if not os.path.exists(args.checkpoint):
        sys.exit(f"[eval] Checkpoint not found: {args.checkpoint}\n"
                 f"       Pass --checkpoint <path to best_model.pth>.")

    evaluate(args.checkpoint, device=args.device, batch_size=args.batch_size)
