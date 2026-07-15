# Devanagari fonts for synthetic data generation

Bundled here so `data/generate_synth.py` gets font diversity on every platform
(Kaggle/Colab included) without depending on `apt-get install fonts-deva` or
whatever happens to be preinstalled. Previously the generator only had access
to Windows' Nirmala/Mangal — one typeface family — which meant every
synthetic training image looked like the same font, wide from what a model
needs to generalize to real handwriting/print.

All fonts are from [Google Fonts](https://fonts.google.com) and licensed
under the SIL Open Font License 1.1 (free to use, modify, and redistribute).

- Noto Sans Devanagari
- Noto Serif Devanagari
- Hind (Regular, Medium)
- Mukta
- Tiro Devanagari Hindi
- Baloo 2
- Khand
