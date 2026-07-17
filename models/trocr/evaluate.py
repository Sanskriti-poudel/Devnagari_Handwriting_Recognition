"""
Evaluate the fine-tuned TrOCR model on the held-out TEST split.

Reports the same Phase 3 metrics as the CRNN evaluator (Accuracy / CER / WER via
jiwer) plus param count and inference latency, so the two models drop straight
into the comparison table. Writes logs/trocr_eval.json.

Usage:
    python models/trocr/evaluate.py
    python models/trocr/evaluate.py --checkpoint models/trocr/checkpoints
"""

import os
import sys
import json
import time
import argparse

import torch

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
sys.path.insert(0, THIS_DIR)
sys.path.insert(0, PROJECT_ROOT)

from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from torch.utils.data import DataLoader
from dataset import TrOCRDataset, make_collate


def evaluate(checkpoint, device="cpu", batch_size=8):
    import jiwer

    processor = TrOCRProcessor.from_pretrained(checkpoint)
    model = VisionEncoderDecoderModel.from_pretrained(checkpoint).to(device)
    model.eval()
    param_count = sum(p.numel() for p in model.parameters())
    print(f"[eval] loaded {checkpoint} | {param_count:,} params | device={device}")

    ds = TrOCRDataset("test", processor, augment=None)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False,
                        collate_fn=make_collate(processor.tokenizer.pad_token_id))

    correct = total = 0
    refs, hyps = [], []
    infer_time = 0.0
    pad_id = processor.tokenizer.pad_token_id

    with torch.no_grad():
        for batch in loader:
            pixel_values = batch["pixel_values"].to(device)
            labels = batch["labels"].clone()
            labels[labels == -100] = pad_id

            t0 = time.perf_counter()
            generated = model.generate(pixel_values, max_length=8)
            if device == "cuda":
                torch.cuda.synchronize()
            infer_time += time.perf_counter() - t0

            pred_text = processor.batch_decode(generated, skip_special_tokens=True)
            gt_text = processor.batch_decode(labels, skip_special_tokens=True)

            for pred, gt in zip(pred_text, gt_text):
                pred, gt = pred.strip(), gt.strip()
                total += 1
                correct += int(pred == gt)
                refs.append(gt)
                hyps.append(pred)

    accuracy = correct / total if total else 0.0
    # glyph strings are short; concatenate with spaces so each sample is one "word"
    cer = jiwer.cer(" ".join(refs), " ".join(hyps))
    wer = jiwer.wer(" ".join(refs), " ".join(hyps))
    latency_ms = (infer_time / total * 1000) if total else 0.0

    results = {
        "checkpoint": checkpoint,
        "test_samples": total,
        "accuracy": round(accuracy, 4),
        "cer": round(cer, 4),
        "wer": round(wer, 4),
        "param_count": param_count,
        "avg_inference_latency_ms": round(latency_ms, 3),
        "device": device,
    }

    print("\n=== TrOCR — TEST set ===")
    print(f"  Samples            : {total}")
    print(f"  Accuracy           : {accuracy * 100:.2f}%")
    print(f"  CER                : {cer:.4f}")
    print(f"  WER                : {wer:.4f}")
    print(f"  Parameters         : {param_count:,}")
    print(f"  Inference latency  : {latency_ms:.3f} ms/image ({device})")

    out = os.path.join(PROJECT_ROOT, "logs", "trocr_eval.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[eval] wrote metrics -> {out}")
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Evaluate fine-tuned TrOCR on the test split.")
    p.add_argument("--checkpoint", default=os.path.join(PROJECT_ROOT, "models", "trocr", "checkpoints"))
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu",
                   choices=["cpu", "cuda"])
    p.add_argument("--batch-size", type=int, default=8)
    args = p.parse_args()

    if not os.path.isdir(args.checkpoint):
        sys.exit(f"[eval] checkpoint dir not found: {args.checkpoint}\n"
                 f"       Train first (models/trocr/train.py) or pass --checkpoint.")
    evaluate(args.checkpoint, device=args.device, batch_size=args.batch_size)
