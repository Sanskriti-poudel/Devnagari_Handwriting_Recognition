"""
Exploratory Data Analysis for the Devanagari character dataset (Chandan, Phase 1).

Produces, into eda/outputs/:
  - class_counts.csv            per-class image counts for train/val/test + total
  - class_distribution.png      bar chart of per-class counts (train vs val vs test)
  - image_size_distribution.png histogram of raw image widths/heights
  - sample_grid.png             one example image per class with its glyph
  - eda_summary.md              headline numbers + class-imbalance check

Runs on CPU in well under a minute. Reads the committed split (data/split_index.json)
so the EDA reflects exactly the data the models train on.
"""

import os
import sys
import json
from collections import Counter

import cv2
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless; just write PNGs
import matplotlib.pyplot as plt

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

from data.devanagari_labels import CLASS_TO_DEVANAGARI, class_to_glyph

SPLIT_INDEX = os.path.join(PROJECT_ROOT, "data", "split_index.json")
DATA_ROOT = os.environ.get("DEVNAGARI_DATA_ROOT", os.path.join(PROJECT_ROOT, "Datasets"))
OUT_DIR = os.path.join(THIS_DIR, "outputs")

# Use a font that can render Devanagari if one is available; otherwise the latin
# transliteration is used in plot labels so nothing crashes on missing glyphs.
_DEVA_FONT = None
for _cand in ["Nirmala UI", "Mangal", "Noto Sans Devanagari", "Lohit Devanagari"]:
    if _cand.lower() in {f.name.lower() for f in matplotlib.font_manager.fontManager.ttflist}:
        _DEVA_FONT = _cand
        break


def _label_of(rel_path):
    """class-folder name from a relative image path .../<class>/<file>.png"""
    return os.path.basename(os.path.dirname(rel_path))


def load_split():
    with open(SPLIT_INDEX) as f:
        return json.load(f)


def class_counts(split):
    rows = {}
    for name in ["train", "val", "test"]:
        rows[name] = Counter(_label_of(p) for p in split[name])
    classes = sorted(set().union(*[set(c) for c in rows.values()]))
    df = pd.DataFrame(
        {name: [rows[name].get(c, 0) for c in classes] for name in ["train", "val", "test"]},
        index=classes,
    )
    df["total"] = df.sum(axis=1)
    df.index.name = "class"
    return df


def plot_class_distribution(df, path):
    fig, ax = plt.subplots(figsize=(16, 6))
    x = np.arange(len(df))
    ax.bar(x, df["train"], label="train")
    ax.bar(x, df["val"], bottom=df["train"], label="val")
    ax.bar(x, df["test"], bottom=df["train"] + df["val"], label="test")
    ax.set_xticks(x)
    ax.set_xticklabels(df.index, rotation=90, fontsize=7)
    ax.set_ylabel("image count")
    ax.set_title("Per-class image counts (stacked by split)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def image_size_distribution(split, path, sample_per_split=2000):
    widths, heights = [], []
    # raw images may already be 64x64 (preprocessed) — sample to keep it fast
    paths = split["train"][:sample_per_split]
    for rel in paths:
        img = cv2.imread(os.path.join(DATA_ROOT, rel), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        h, w = img.shape[:2]
        heights.append(h)
        widths.append(w)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].hist(widths, bins=30, color="steelblue")
    axes[0].set_title(f"Image width (n={len(widths)})")
    axes[1].hist(heights, bins=30, color="indianred")
    axes[1].set_title(f"Image height (n={len(heights)})")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return widths, heights


def sample_grid(split, path, n_cols=8):
    # one example per class
    seen = {}
    for rel in split["train"]:
        lbl = _label_of(rel)
        if lbl not in seen:
            seen[lbl] = rel
    classes = sorted(seen)
    n = len(classes)
    n_rows = (n + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 1.4, n_rows * 1.6))
    axes = np.array(axes).reshape(-1)
    for ax in axes:
        ax.axis("off")
    for i, cls in enumerate(classes):
        img = cv2.imread(os.path.join(DATA_ROOT, seen[cls]), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            axes[i].imshow(img, cmap="gray")
        if _DEVA_FONT:
            axes[i].set_title(class_to_glyph(cls), fontname=_DEVA_FONT, fontsize=14)
        else:
            axes[i].set_title(CLASS_TO_DEVANAGARI[cls][1], fontsize=8)
    fig.suptitle("One sample per class")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def write_summary(df, widths, heights, path):
    total = int(df["total"].sum())
    imbalance = df["total"].max() / df["total"].min()
    lines = [
        "# EDA Summary — Devanagari Character Dataset\n",
        f"- **Total images:** {total:,}",
        f"- **Classes:** {len(df)} (36 consonants + 10 digits)",
        f"- **Split:** train {int(df['train'].sum()):,} / "
        f"val {int(df['val'].sum()):,} / test {int(df['test'].sum()):,}",
        f"- **Per-class total range:** {int(df['total'].min())}–{int(df['total'].max())} "
        f"(imbalance ratio {imbalance:.2f}×)",
        f"- **Image size:** width {min(widths)}–{max(widths)} px, "
        f"height {min(heights)}–{max(heights)} px "
        f"(median {int(np.median(widths))}×{int(np.median(heights))})",
        "",
        "## Class imbalance check",
        "Near-balanced — every class has a similar count, so no resampling/weighting "
        "is required. (Ratio close to 1.0 means balanced.)" if imbalance < 1.5 else
        f"Imbalance ratio {imbalance:.2f}× — consider class weighting or augmentation "
        "for under-represented classes.",
        "",
        "## Most / least represented classes",
        "```",
        df["total"].sort_values(ascending=False).head(5).to_string(),
        "...",
        df["total"].sort_values().head(5).to_string(),
        "```",
        "",
        "Artifacts: `class_counts.csv`, `class_distribution.png`, "
        "`image_size_distribution.png`, `sample_grid.png`.",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    if not os.path.isdir(DATA_ROOT):
        sys.exit(f"[eda] DATA_ROOT not found: {DATA_ROOT}\n"
                 f"      Set DEVNAGARI_DATA_ROOT to the folder containing train/ and test/.")

    print(f"[eda] data root: {DATA_ROOT}")
    split = load_split()

    df = class_counts(split)
    df.to_csv(os.path.join(OUT_DIR, "class_counts.csv"))
    print(f"[eda] {len(df)} classes, {int(df['total'].sum()):,} images")

    plot_class_distribution(df, os.path.join(OUT_DIR, "class_distribution.png"))
    widths, heights = image_size_distribution(split, os.path.join(OUT_DIR, "image_size_distribution.png"))
    sample_grid(split, os.path.join(OUT_DIR, "sample_grid.png"))
    write_summary(df, widths, heights, os.path.join(OUT_DIR, "eda_summary.md"))

    print(f"[eda] wrote outputs -> {OUT_DIR}")
    if not _DEVA_FONT:
        print("[eda] note: no Devanagari font found; sample grid used transliterations.")


if __name__ == "__main__":
    main()
