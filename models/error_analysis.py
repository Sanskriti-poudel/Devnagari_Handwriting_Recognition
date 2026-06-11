"""
Phase 3 — qualitative error analysis for the Devanagari recognisers.

Goes beyond the headline Accuracy/CER/WER (see models/compare.py) to ask *where*
a model fails: which characters are hardest, which pairs get confused, and
whether errors cluster in visually-similar glyphs (matras, conjuncts, look-alike
consonants/digits). Produces thesis-ready tables + a confusion heatmap.

Currently wired for the CRNN (local checkpoint). The analysis core works on plain
(true, predicted) class-name lists, so a TrOCR adapter — map emitted glyphs back
to class names via data.devanagari_labels.GLYPH_TO_CLASS — can feed the same
functions once TrOCR predictions exist.

Outputs (logs/):
    crnn_error_analysis.md      — per-class accuracy, top confused pairs, group stats
    crnn_confusion_pairs.csv    — every (true -> pred) error with counts
    crnn_confusion_heatmap.png  — confusions among the classes that have errors

Usage:
    python models/error_analysis.py
    python models/error_analysis.py --checkpoint kaggle_output/artifacts/best_model.pth
"""

import os
import sys
import csv
import json
import argparse
from collections import Counter, defaultdict

import torch

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
sys.path.insert(0, os.path.join(THIS_DIR, "crnn"))
sys.path.insert(0, PROJECT_ROOT)

from data.devanagari_labels import CLASS_TO_DEVANAGARI

LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
NONE_TOKEN = "<none>"  # model emitted nothing / an undecodable string


def glyph(cls):
    return CLASS_TO_DEVANAGARI.get(cls, (cls, cls))[0]


def translit(cls):
    return CLASS_TO_DEVANAGARI.get(cls, (cls, cls))[1]


def is_digit(cls):
    return cls.startswith("digit_")


def label(cls):
    """Readable label, e.g. 'क (ka)' — falls back to the raw name if unmapped."""
    if cls == NONE_TOKEN:
        return NONE_TOKEN
    if cls in CLASS_TO_DEVANAGARI:
        return f"{glyph(cls)} ({translit(cls)})"
    return cls


# --------------------------------------------------------------------------- #
# Prediction gathering (CRNN)
# --------------------------------------------------------------------------- #
def gather_crnn_predictions(checkpoint_path, device="cpu", batch_size=64):
    """Run the CRNN over the test split; return (true_classes, pred_classes)."""
    from model import CRNN, decode_ctc_greedy
    from dataset import get_crnn_dataloaders
    from evaluate import reconstruct_ground_truth

    loaders = get_crnn_dataloaders(batch_size=batch_size)
    test_loader = loaders["test"]
    charset = test_loader.dataset.get_charset()
    blank_idx = test_loader.dataset.get_blank_idx()
    num_classes = test_loader.dataset.num_classes

    model = CRNN(num_classes=num_classes, hidden_size=256).to(device)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()
    print(f"[error-analysis] loaded {checkpoint_path} | {num_classes} classes | device={device}")

    trues, preds = [], []
    with torch.no_grad():
        for images, labels_flat, label_lengths in test_loader:
            images = images.to(device)
            log_probs = model(images)
            batch_preds = decode_ctc_greedy(log_probs, charset, blank_idx=blank_idx)
            batch_gts = reconstruct_ground_truth(labels_flat, label_lengths, charset)
            for pred, gt in zip(batch_preds, batch_gts):
                # single-character samples -> one class token; guard empties
                trues.append(gt)
                preds.append(pred if pred else NONE_TOKEN)
    return trues, preds


# --------------------------------------------------------------------------- #
# Analysis core — operates on plain (true, pred) class-name lists
# --------------------------------------------------------------------------- #
def analyse(trues, preds):
    total = len(trues)
    correct = sum(t == p for t, p in zip(trues, preds))

    per_class_total = Counter(trues)
    per_class_correct = Counter(t for t, p in zip(trues, preds) if t == p)
    confusions = Counter((t, p) for t, p in zip(trues, preds) if t != p)

    per_class_acc = {
        c: per_class_correct[c] / per_class_total[c]
        for c in per_class_total
    }

    # group accuracy: consonants vs digits
    groups = defaultdict(lambda: [0, 0])  # name -> [correct, total]
    for t, p in zip(trues, preds):
        g = "digit" if is_digit(t) else "consonant"
        groups[g][1] += 1
        groups[g][0] += int(t == p)

    return {
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "per_class_acc": per_class_acc,
        "per_class_total": per_class_total,
        "confusions": confusions,
        "groups": groups,
    }


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def write_report(stats, model_name="CRNN"):
    os.makedirs(LOGS_DIR, exist_ok=True)
    slug = model_name.lower()

    # ---- confusion pairs CSV ----
    csv_path = os.path.join(LOGS_DIR, f"{slug}_confusion_pairs.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["true_class", "true_glyph", "pred_class", "pred_glyph", "count"])
        for (t, p), n in stats["confusions"].most_common():
            w.writerow([t, glyph(t), p, (glyph(p) if p != NONE_TOKEN else ""), n])

    # ---- worst classes ----
    worst = sorted(stats["per_class_acc"].items(), key=lambda kv: kv[1])

    lines = []
    lines.append(f"# {model_name} — Qualitative Error Analysis\n")
    lines.append(f"Test split, {stats['total']:,} single-character samples · "
                 f"overall accuracy **{stats['accuracy']*100:.2f}%** "
                 f"({stats['total'] - stats['correct']} errors).\n")

    # group stats
    lines.append("## Accuracy by group\n")
    lines.append("| Group | Accuracy | Correct / Total |")
    lines.append("|---|---|---|")
    for g, (c, t) in sorted(stats["groups"].items()):
        lines.append(f"| {g} | {c/t*100:.2f}% | {c} / {t} |")
    lines.append("")

    # worst classes (only those below 100%)
    imperfect = [(c, a) for c, a in worst if a < 1.0]
    lines.append("## Hardest characters (accuracy < 100%)\n")
    if not imperfect:
        lines.append("_Every class scored 100% — no per-class errors._\n")
    else:
        lines.append("| Character | Accuracy | Correct / Total |")
        lines.append("|---|---|---|")
        for c, a in imperfect:
            tot = stats["per_class_total"][c]
            cor = round(a * tot)
            lines.append(f"| {label(c)} | {a*100:.1f}% | {cor} / {tot} |")
        lines.append("")

    # top confused pairs
    lines.append("## Most-confused pairs (true → predicted)\n")
    top = stats["confusions"].most_common(25)
    if not top:
        lines.append("_No confusions._\n")
    else:
        lines.append("| True | → | Predicted | Count |")
        lines.append("|---|---|---|---|")
        for (t, p), n in top:
            lines.append(f"| {label(t)} | → | {label(p)} | {n} |")
        lines.append("")

    md_path = os.path.join(LOGS_DIR, f"{slug}_error_analysis.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[error-analysis] wrote {md_path}")
    print(f"[error-analysis] wrote {csv_path}")
    return md_path, worst, imperfect


def write_heatmap(stats, model_name="CRNN"):
    """Confusion heatmap restricted to classes involved in any error (translit
    axis labels — matplotlib's default font can't render Devanagari)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        print(f"[error-analysis] heatmap skipped (missing {e})")
        return None

    involved = set()
    for (t, p), _ in stats["confusions"].items():
        involved.add(t)
        if p != NONE_TOKEN:
            involved.add(p)
    if not involved:
        print("[error-analysis] no errors -> no heatmap")
        return None

    classes = sorted(involved, key=lambda c: (is_digit(c), translit(c)))
    idx = {c: i for i, c in enumerate(classes)}
    m = np.zeros((len(classes), len(classes)), dtype=int)
    for (t, p), n in stats["confusions"].items():
        if t in idx and p in idx:
            m[idx[t], idx[p]] = n

    labels = [translit(c) for c in classes]
    fig, ax = plt.subplots(figsize=(max(6, len(classes) * 0.5),) * 2)
    im = ax.imshow(m, cmap="Reds")
    ax.set_xticks(range(len(classes))); ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_yticks(range(len(classes))); ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("predicted"); ax.set_ylabel("true")
    ax.set_title(f"{model_name} — confusions among error-involved classes")
    for i in range(len(classes)):
        for j in range(len(classes)):
            if m[i, j]:
                ax.text(j, i, m[i, j], ha="center", va="center", fontsize=7)
    fig.colorbar(im, fraction=0.046, pad=0.04)
    fig.tight_layout()
    out = os.path.join(LOGS_DIR, f"{model_name.lower()}_confusion_heatmap.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"[error-analysis] wrote {out}")
    return out


def _default_checkpoint():
    for c in [os.path.join(PROJECT_ROOT, "models", "crnn", "checkpoints", "best_model.pth"),
              os.path.join(PROJECT_ROOT, "kaggle_output", "artifacts", "best_model.pth")]:
        if os.path.exists(c):
            return c
    return c


def main():
    p = argparse.ArgumentParser(description="Qualitative error analysis for the CRNN.")
    p.add_argument("--checkpoint", default=_default_checkpoint())
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu",
                   choices=["cpu", "cuda"])
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--no-heatmap", action="store_true")
    args = p.parse_args()

    if not os.path.exists(args.checkpoint):
        sys.exit(f"[error-analysis] checkpoint not found: {args.checkpoint}")

    trues, preds = gather_crnn_predictions(args.checkpoint, args.device, args.batch_size)
    stats = analyse(trues, preds)
    _, _, imperfect = write_report(stats, "CRNN")
    if not args.no_heatmap:
        write_heatmap(stats, "CRNN")

    print(f"\n[error-analysis] overall accuracy {stats['accuracy']*100:.2f}% "
          f"| {len(imperfect)} classes below 100% "
          f"| {sum(stats['confusions'].values())} total errors")


if __name__ == "__main__":
    main()
