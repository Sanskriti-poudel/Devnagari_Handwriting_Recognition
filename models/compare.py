"""
Phase 3 — CRNN vs TrOCR comparative analysis.

Reads the two evaluation JSONs produced by the per-model evaluators
(logs/crnn_eval.json, logs/trocr_eval.json), builds a side-by-side metrics
table (Markdown) for the thesis, and renders grouped bar charts comparing
Accuracy / CER / WER, parameter count, and inference latency.

Outputs:
    logs/comparison.md          — Markdown table + headline takeaways
    logs/comparison_metrics.png — Accuracy / CER / WER grouped bars
    logs/comparison_size.png    — params + latency (log-scaled, dual panel)

Usage:
    python models/compare.py
    python models/compare.py --crnn logs/crnn_eval.json --trocr logs/trocr_eval.json

TrOCR is optional: if logs/trocr_eval.json is missing, the script still emits
the CRNN-only table and tells you to run the TrOCR evaluator first.
"""

import os
import sys
import json
import argparse

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Display order + human labels for the metrics we report.
ROWS = [
    ("accuracy", "Accuracy", lambda v: f"{v * 100:.2f}%"),
    ("cer", "CER", lambda v: f"{v:.4f}"),
    ("wer", "WER", lambda v: f"{v:.4f}"),
    ("param_count", "Parameters", lambda v: f"{v:,}"),
    ("avg_inference_latency_ms", "Inference latency", lambda v: f"{v:.3f} ms/img"),
    ("test_samples", "Test samples", lambda v: f"{v:,}"),
]


def load(path):
    if not path or not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_table(crnn, trocr):
    """Return a Markdown table string for whichever models are present."""
    models = [("CRNN", crnn)]
    if trocr is not None:
        models.append(("TrOCR", trocr))

    header = "| Metric | " + " | ".join(name for name, _ in models) + " |"
    sep = "|---|" + "|".join("---" for _ in models) + "|"
    lines = [header, sep]
    for key, label, fmt in ROWS:
        cells = []
        for _, data in models:
            v = data.get(key) if data else None
            cells.append(fmt(v) if v is not None else "—")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def takeaways(crnn, trocr):
    """A few auto-generated comparison sentences for the thesis."""
    if trocr is None:
        return ("> _TrOCR metrics not yet available._ Run "
                "`python models/trocr/evaluate.py` after fine-tuning to populate "
                "`logs/trocr_eval.json`, then re-run this script.")

    out = []

    def cmp(key, label, higher_is_better):
        c, t = crnn.get(key), trocr.get(key)
        if c is None or t is None:
            return
        if c == t:
            out.append(f"- **{label}:** tied ({c}).")
            return
        crnn_better = (c > t) if higher_is_better else (c < t)
        winner, w, l = ("CRNN", c, t) if crnn_better else ("TrOCR", t, c)
        out.append(f"- **{label}:** {winner} wins ({w} vs {l}).")

    cmp("accuracy", "Accuracy", higher_is_better=True)
    cmp("cer", "CER", higher_is_better=False)
    cmp("wer", "WER", higher_is_better=False)
    cmp("param_count", "Model size", higher_is_better=False)
    cmp("avg_inference_latency_ms", "Inference latency", higher_is_better=False)
    return "\n".join(out)


def plot_metrics(crnn, trocr, out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    keys = [("accuracy", "Accuracy"), ("cer", "CER"), ("wer", "WER")]
    labels = [lbl for _, lbl in keys]
    crnn_vals = [crnn.get(k, 0) or 0 for k, _ in keys]
    x = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(7, 4))
    width = 0.35 if trocr is not None else 0.5
    if trocr is not None:
        trocr_vals = [trocr.get(k, 0) or 0 for k, _ in keys]
        ax.bar(x - width / 2, crnn_vals, width, label="CRNN")
        ax.bar(x + width / 2, trocr_vals, width, label="TrOCR")
    else:
        ax.bar(x, crnn_vals, width, label="CRNN")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Value")
    ax.set_title("CRNN vs TrOCR — accuracy / error rates (test split)")
    ax.legend()
    for container in ax.containers:
        ax.bar_label(container, fmt="%.4f", padding=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_size(crnn, trocr, out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    names = ["CRNN"] + (["TrOCR"] if trocr is not None else [])
    datasets = [crnn] + ([trocr] if trocr is not None else [])
    params = [d.get("param_count", 0) or 0 for d in datasets]
    latency = [d.get("avg_inference_latency_ms", 0) or 0 for d in datasets]
    x = np.arange(len(names))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    ax1.bar(x, params, color="#4C72B0")
    ax1.set_xticks(x); ax1.set_xticklabels(names)
    ax1.set_ylabel("Parameters")
    ax1.set_title("Model size")
    if len(params) > 1 and max(params) / max(min(params), 1) > 20:
        ax1.set_yscale("log")
    ax1.bar_label(ax1.containers[0], fmt="%d", padding=2, fontsize=8)

    ax2.bar(x, latency, color="#DD8452")
    ax2.set_xticks(x); ax2.set_xticklabels(names)
    ax2.set_ylabel("ms / image")
    ax2.set_title("Inference latency")
    ax2.bar_label(ax2.containers[0], fmt="%.2f", padding=2, fontsize=8)

    fig.suptitle("CRNN vs TrOCR — cost", y=1.02)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description="CRNN vs TrOCR comparative analysis.")
    p.add_argument("--crnn", default=os.path.join(LOGS_DIR, "crnn_eval.json"))
    p.add_argument("--trocr", default=os.path.join(LOGS_DIR, "trocr_eval.json"))
    p.add_argument("--no-plots", action="store_true",
                   help="Skip PNG generation (table only).")
    args = p.parse_args()

    crnn = load(args.crnn)
    if crnn is None:
        sys.exit(f"[compare] CRNN metrics not found: {args.crnn}\n"
                 f"          Run `python models/crnn/evaluate.py` first.")
    trocr = load(args.trocr)

    os.makedirs(LOGS_DIR, exist_ok=True)
    table = build_table(crnn, trocr)
    notes = takeaways(crnn, trocr)

    md = (
        "# CRNN vs TrOCR — Comparative Analysis\n\n"
        "Devanagari handwritten character recognition, evaluated on the held-out "
        "test split (46 balanced classes). Generated by `models/compare.py`.\n\n"
        "## Metrics\n\n"
        f"{table}\n\n"
        "## Takeaways\n\n"
        f"{notes}\n"
    )
    if not args.no_plots and trocr is not None:
        md += ("\n## Figures\n\n"
               "![Accuracy / CER / WER](comparison_metrics.png)\n\n"
               "![Model size & latency](comparison_size.png)\n")

    out_md = os.path.join(LOGS_DIR, "comparison.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[compare] wrote table -> {out_md}")
    print("\n" + table + "\n")

    if args.no_plots:
        return
    try:
        plot_metrics(crnn, trocr, os.path.join(LOGS_DIR, "comparison_metrics.png"))
        plot_size(crnn, trocr, os.path.join(LOGS_DIR, "comparison_size.png"))
        print(f"[compare] wrote plots -> {LOGS_DIR}")
    except ImportError as e:
        print(f"[compare] plotting skipped (missing dependency: {e}).")

    if trocr is None:
        print("\n[compare] NOTE: TrOCR metrics absent — CRNN-only report written. "
              "Run `python models/trocr/evaluate.py` after fine-tuning, then re-run.")


if __name__ == "__main__":
    main()
