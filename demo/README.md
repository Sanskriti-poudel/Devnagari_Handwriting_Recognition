# Demo — Mid-Defense

A simple Streamlit app over the **real** trained CRNN (no mock). Upload or pick a
handwritten Devanagari character and see the prediction, plus the project's
evaluation results.

## Run (from the repo root)

```bash
pip install streamlit          # if not already installed
streamlit run demo/app.py
```

Opens at <http://localhost:8501>. CPU is fine (~5 ms/image).

## What it shows

- **Try it** — upload a character image *or* "Pick a random test image"; see the
  preprocessed 64×64 the model is fed, the predicted Devanagari glyph + transliteration,
  and the confidence.
- **Results** — CRNN test metrics (98.67% accuracy), the CRNN-vs-TrOCR comparison, and
  the qualitative confusion heatmap / error-analysis report.

## Requirements

- CRNN weights at `kaggle_output/artifacts/best_model.pth` (already in the repo's
  Kaggle output), and `data/charset.json`.
- `Datasets/test/<class>/*.png` for the "random sample" button.
- Reuses `Preprocessing/preprocess.py` and `models/crnn/predict.py` — same code path as
  training, so there is no train/serve skew.

> TrOCR is intentionally omitted from the live demo until its GPU re-run produces a
> working checkpoint (see `docs/REMAINING_WORK.md`). The **Results** tab already shows
> the comparison scaffolding.
