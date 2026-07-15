"""
Word/line-level TrOCR inference (Phase 2).

Two entry points:
  * predict_line(image)  -> recognize ONE line/word crop -> {"text", "confidence"}
  * predict_page(image)  -> segment a whole page into LINES, read each line, and
                            stitch into multi-line text.

This is the path that replaces character-segmentation document mode: instead of
splitting a line into per-character blobs (which fails on joined writing — the
शिरोरेखा glues letters together), we crop whole LINES and let TrOCR read each one
end-to-end, including matras and conjuncts.

Images are fed to the TrOCR processor as dark-ink-on-light RGB — the SAME path as
dataset_words.py training, so no train/serve skew. Real page photos are already
in that domain; we do not run the 64x64 single-char preprocessing.

Default checkpoint: models/trocr/checkpoints_words (override via TROCR_WORDS_CHECKPOINT).
"""

import os
import sys

import cv2
import numpy as np
import torch
from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
sys.path.insert(0, THIS_DIR)
sys.path.insert(0, PROJECT_ROOT)

from predict import _load  # cached (processor, model) loader, reused as-is
from dataset_words import MAX_TARGET_LENGTH
from models.crnn.segment import segment_line_boxes, annotate

DEFAULT_CHECKPOINT = os.path.join(PROJECT_ROOT, "models", "trocr", "checkpoints_words")


def _resolve_checkpoint(path=None):
    path = path or os.environ.get("TROCR_WORDS_CHECKPOINT") or DEFAULT_CHECKPOINT
    if not os.path.isdir(path):
        raise FileNotFoundError(
            f"No word-level TrOCR checkpoint at {path}. Train with "
            f"models/trocr/train_words.py, set TROCR_WORDS_CHECKPOINT, or pass checkpoint_path."
        )
    return path


def _to_rgb_pil(image):
    """path | BGR/gray ndarray | RGB PIL -> RGB PIL, WITHOUT 64x64 single-char
    preprocessing (word/line crops are variable-size and already dark-on-light)."""
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, str):
        bgr = cv2.imread(image, cv2.IMREAD_COLOR)
        if bgr is None:
            raise IOError(f"Could not read image: {image}")
        return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    if isinstance(image, np.ndarray):
        if image.ndim == 2:
            return Image.fromarray(image).convert("RGB")
        return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    raise TypeError(f"Unsupported image type: {type(image)}")


def predict_lines(images, checkpoint_path=None, device=None):
    """Recognize a BATCH of line/word images in one model.generate() call.

    Sequential per-line generate() calls each pay the same fixed model
    forward-pass overhead; batching lets a CPU use multiple threads across
    the batch dimension, which matters a lot for multi-line CPU inference
    (the common case here — no GPU). Returns a list of
    {"text": str, "confidence": float}, one per input image, same order.
    """
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    processor, model = _load(_resolve_checkpoint(checkpoint_path), device)

    if not images:
        return []

    imgs = [_to_rgb_pil(im) for im in images]
    pixel_values = processor(images=imgs, return_tensors="pt").pixel_values.to(device)
    with torch.no_grad():
        out = model.generate(
            pixel_values, max_length=MAX_TARGET_LENGTH,
            output_scores=True, return_dict_in_generate=True, use_cache=True,
        )
    texts = [t.strip() for t in processor.batch_decode(out.sequences, skip_special_tokens=True)]

    if out.scores:
        # out.scores: one (batch, vocab) tensor per generated step.
        per_step_max = [torch.softmax(step, dim=-1).max(dim=-1).values for step in out.scores]
        confidences = torch.stack(per_step_max, dim=1).mean(dim=1).tolist()
    else:
        confidences = [0.0] * len(imgs)

    return [{"text": text, "confidence": round(float(conf), 4)} for text, conf in zip(texts, confidences)]


def predict_line(image, checkpoint_path=None, device=None):
    """Recognize the text in a single line/word image.

    Returns {"text": str, "confidence": float}; confidence is the mean per-step
    max-softmax probability over the generated tokens.
    """
    return predict_lines([image], checkpoint_path=checkpoint_path, device=device)[0]


def predict_page(image, checkpoint_path=None, device=None):
    """Read a whole page: segment into lines, recognize each, stitch into text.

    Returns {
        "text": str,                       # lines joined by newlines
        "lines": [{"box": (x,y,w,h), "text": str, "confidence": float}, ...],
        "annotated": ndarray (BGR),        # page with line boxes drawn
    }
    """
    if isinstance(image, str):
        bgr = cv2.imread(image, cv2.IMREAD_COLOR)
        if bgr is None:
            raise IOError(f"Could not read image: {image}")
    elif isinstance(image, np.ndarray):
        bgr = image if image.ndim == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        raise TypeError(f"Unsupported image type: {type(image)}")

    boxes = segment_line_boxes(bgr)
    crops = [bgr[y:y + h, x:x + w] for (x, y, w, h) in boxes]
    line_results = predict_lines(crops, checkpoint_path=checkpoint_path, device=device)
    results = [
        {"box": box, "text": r["text"], "confidence": r["confidence"]}
        for box, r in zip(boxes, line_results)
    ]

    # annotate() expects a list-of-lines-of-boxes; wrap each line box as its own line
    annotated = annotate(bgr, [[b] for b in boxes])
    return {
        "text": "\n".join(r["text"] for r in results),
        "lines": results,
        "annotated": annotated,
    }


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Word/line-level TrOCR inference.")
    p.add_argument("image")
    p.add_argument("--mode", choices=["line", "page"], default="page")
    p.add_argument("--checkpoint", default=None)
    args = p.parse_args()
    if args.mode == "line":
        print(predict_line(args.image, checkpoint_path=args.checkpoint))
    else:
        out = predict_page(args.image, checkpoint_path=args.checkpoint)
        print(out["text"])
        print(f"\n[{len(out['lines'])} lines]")
