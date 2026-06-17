"""
Synthetic Nepali word-image generator for word-level TrOCR training (Phase 1).

The DHCD data this project ships with is single isolated characters, so a model
trained on it can only ever read one base glyph at a time — it has no matras
(vowel signs), no punctuation, and it cannot read joined/cursive words. To train
a TrOCR model that reads whole words/lines (the actual goal), we need
(image -> full text string) pairs. Real handwritten word datasets are scarce and
need manual transcription, so we BOOTSTRAP with synthetic data: render Nepali
text from Devanagari fonts and apply handwriting-like distortion. This is the
standard "synthetic pretrain -> fine-tune on a little real data" OCR recipe.

Vocabulary is a MIX (per the project decision):
  * real Nepali words   -> realistic spellings, matra usage, conjuncts
  * random syllables     -> broad glyph/matra coverage the word list misses

Output layout (consumed by the word-level dataset in Phase 2):
    <out>/images/synth_000001.png ...
    <out>/labels.csv              # columns: image_path,text   (path is relative to <out>)

Usage:
    python data/generate_synth.py --out Datasets/synth --n 5000
    python data/generate_synth.py --out Datasets/synth --n 200 --seed 0   # quick smoke set

Fonts: defaults to the Windows-bundled Nirmala UI family (regular/bold/semilight),
which renders Devanagari correctly. Add more .ttf paths via --fonts for variety
(e.g. Mangal, Noto Sans Devanagari) — more fonts => better generalization.
"""

import os
import csv
import glob
import math
import random
import argparse

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter


# --- Devanagari building blocks (Unicode) ---------------------------------

# Consonants (base, no inherent-vowel suppression). Mirrors DHCD's 36 plus a
# few common ones the dataset folds together, so coverage is a bit broader.
CONSONANTS = list("कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह")

# Dependent vowel signs (matras) — the thing the single-char model can't produce.
# "" = bare consonant (keeps the inherent 'a').
MATRAS = ["", "ा", "ि", "ी", "ु", "ू", "े", "ै", "ो", "ौ", "ृ", "ं", "ः", "ँ"]

# Independent vowels (word-initial).
VOWELS = list("अआइईउऊएऐओऔ")

DIGITS = list("०१२३४५६७८९")

HALANT = "्"  # virama: joins two consonants into a conjunct (क् + ष -> क्ष)

DANDA = "।"   # Devanagari full stop / sentence terminator
PUNCT = ["।", ",", "?", "-"]


# A small seed list of common Nepali words. Not exhaustive — it just anchors the
# synthetic set in real spellings (matra placement, conjuncts) that random
# syllables don't reproduce. Extend freely or pass --wordfile for a bigger list.
NEPALI_WORDS = [
    "नमस्ते", "धन्यवाद", "नेपाल", "काठमाडौं", "मेरो", "नाम", "हो", "तिमी",
    "हामी", "तपाईं", "घर", "पानी", "खाना", "किताब", "विद्यालय", "शिक्षक",
    "विद्यार्थी", "देश", "भाषा", "संस्कृति", "मानिस", "समय", "आज", "भोलि",
    "हिजो", "बिहान", "बेलुका", "राम्रो", "नराम्रो", "ठूलो", "सानो", "नयाँ",
    "पुरानो", "रातो", "कालो", "सेतो", "हरियो", "फूल", "रूख", "बाटो",
    "गाउँ", "शहर", "सडक", "मन", "माया", "साथी", "परिवार", "आमा", "बुबा",
    "दाजु", "भाइ", "दिदी", "बहिनी", "छोरा", "छोरी", "काम", "पैसा", "बजार",
    "दिन", "रात", "हप्ता", "महिना", "वर्ष", "घाम", "जून", "तारा", "आकाश",
    "धर्ती", "नदी", "पहाड", "हिमाल", "जंगल", "पशु", "पंक्षी", "माछा",
    "सपना", "खुसी", "दुख", "जीवन", "मृत्यु", "सत्य", "ज्ञान", "विज्ञान",
]


# --- text sampling ---------------------------------------------------------

def random_syllable(rng):
    """A single (usually) valid akshara: maybe a conjunct, plus an optional matra."""
    # ~15% conjunct (consonant + halant + consonant), else a single consonant.
    if rng.random() < 0.15:
        base = rng.choice(CONSONANTS) + HALANT + rng.choice(CONSONANTS)
    else:
        base = rng.choice(CONSONANTS)
    return base + rng.choice(MATRAS)


def random_word(rng):
    """A pseudo-word of 1–4 aksharas. May start with an independent vowel/digit."""
    r = rng.random()
    if r < 0.08:
        return "".join(rng.choice(DIGITS) for _ in range(rng.randint(1, 4)))
    parts = []
    if r < 0.18:
        parts.append(rng.choice(VOWELS))
    parts += [random_syllable(rng) for _ in range(rng.randint(1, 4))]
    return "".join(parts)


def sample_text(rng, real_ratio):
    """One label string: a short phrase of 1–4 tokens, mixing real words and
    random syllables. `real_ratio` is the per-token probability of a real word."""
    n_tokens = rng.choices([1, 2, 3, 4], weights=[5, 4, 2, 1])[0]
    tokens = []
    for _ in range(n_tokens):
        if rng.random() < real_ratio:
            tokens.append(rng.choice(NEPALI_WORDS))
        else:
            tokens.append(random_word(rng))
    text = " ".join(tokens)
    # occasionally terminate with a danda / punctuation, like real writing
    if rng.random() < 0.25:
        text += rng.choice(PUNCT) if rng.random() < 0.5 else DANDA
    return text


# --- rendering + augmentation ----------------------------------------------

# Filename keywords that identify a Devanagari-capable font on Linux/mac (Kaggle,
# Colab). Windows ships Nirmala/Mangal; Linux usually needs `apt-get install
# fonts-deva fonts-lohit-deva fonts-noto-core`, which drop files matching these.
_DEVA_FONT_KEYS = [
    "devanagari", "lohit-deva", "lohit_deva", "gargi", "samanata", "kalimati",
    "nakula", "sahadeva", "mukti", "annapurna", "kokila", "aparajita", "utsaah",
    "sarai", "chandas", "mangal", "nirmala",
]


def default_font_paths():
    """Find Devanagari fonts on the current OS (Windows -> Nirmala/Mangal;
    Linux/mac -> any installed Devanagari/Lohit/Noto-Devanagari .ttf/.otf)."""
    paths = []
    if os.name == "nt":  # Windows
        win = "C:/Windows/Fonts"
        for p in ("Nirmala.ttf", "NirmalaB.ttf", "NirmalaS.ttf", "mangal.ttf", "Mangal.ttf"):
            fp = os.path.join(win, p)
            if os.path.exists(fp):
                paths.append(fp)
        for pat in ("Mangal*.ttf", "*Devanagari*.ttf", "Aparajita*.ttf",
                    "Kokila*.ttf", "utsaah*.ttf"):
            paths += glob.glob(os.path.join(win, pat))
    else:  # Linux / mac (Kaggle, Colab)
        roots = ["/usr/share/fonts", "/usr/local/share/fonts",
                 os.path.expanduser("~/.fonts"),
                 "/Library/Fonts", "/System/Library/Fonts"]
        for root in roots:
            if not os.path.isdir(root):
                continue
            for ext in ("*.ttf", "*.otf"):
                for f in glob.glob(os.path.join(root, "**", ext), recursive=True):
                    if any(k in os.path.basename(f).lower() for k in _DEVA_FONT_KEYS):
                        paths.append(f)
    # de-dup, preserve order
    seen, out = set(), []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def load_fonts(font_paths, sizes):
    """Pre-load (path, size) -> ImageFont so we don't re-open per image."""
    fonts = []
    for p in font_paths:
        for s in sizes:
            try:
                fonts.append(ImageFont.truetype(p, s))
            except (OSError, IOError) as e:
                print(f"[fonts] WARN could not load {p}@{s}: {e}")
    if not fonts:
        raise SystemExit(
            "No usable Devanagari fonts found.\n"
            "  Windows: pass --fonts C:/Windows/Fonts/Nirmala.ttf\n"
            "  Linux/Kaggle/Colab: install some first, e.g.\n"
            "    apt-get update && apt-get install -y fonts-deva fonts-lohit-deva fonts-noto-core\n"
            "  then re-run (auto-detected), or pass --fonts /path/to/font.ttf"
        )
    return fonts


def render_text(text, font, rng):
    """Render `text` as dark ink on a light paper-ish background.

    Polarity matters: TrOCR-base-handwritten was pretrained on dark-ink-on-light
    paper, so we render in that domain directly (the OLD single-char pipeline had
    to invert white-on-black DHCD crops; here we avoid that mismatch at source).
    """
    # measure
    tmp = Image.new("L", (8, 8), 255)
    d = ImageDraw.Draw(tmp)
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    tw, th = max(1, r - l), max(1, b - t)

    pad_x = rng.randint(int(th * 0.3), int(th * 0.8))
    pad_y = rng.randint(int(th * 0.3), int(th * 0.8))
    W, H = tw + 2 * pad_x, th + 2 * pad_y

    # light, slightly off-white background; dark (not pure-black) ink
    bg = rng.randint(238, 255)
    ink = rng.randint(0, 60)
    img = Image.new("L", (W, H), bg)
    d = ImageDraw.Draw(img)
    d.text((pad_x - l, pad_y - t), text, font=font, fill=ink)
    return img


def _shear(img, rng, max_shear=0.18):
    """Horizontal shear to mimic slanted handwriting."""
    s = rng.uniform(-max_shear, max_shear)
    W, H = img.size
    # expand width so the slant isn't clipped
    new_W = W + int(abs(s) * H)
    return img.transform(
        (new_W, H), Image.AFFINE, (1, s, -s * H if s > 0 else 0, 0, 1, 0),
        resample=Image.BILINEAR, fillcolor=255,
    )


def augment(img, rng):
    """Light geometric + photometric distortion to look less font-perfect."""
    if rng.random() < 0.7:
        img = _shear(img, rng)
    if rng.random() < 0.7:
        img = img.rotate(rng.uniform(-4, 4), resample=Image.BILINEAR,
                         expand=True, fillcolor=255)
    if rng.random() < 0.5:
        img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.4, 1.1)))

    arr = np.asarray(img).astype(np.float32)
    if rng.random() < 0.7:  # speckle / sensor noise
        arr += rng.uniform(4, 14) * np.random.randn(*arr.shape)
    if rng.random() < 0.4:  # gentle contrast/brightness jitter
        arr = arr * rng.uniform(0.85, 1.1) + rng.uniform(-10, 10)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


# --- driver ----------------------------------------------------------------

def generate(out_dir, n, fonts, rng, real_ratio):
    img_dir = os.path.join(out_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    rows = []
    for i in range(1, n + 1):
        text = sample_text(rng, real_ratio)
        font = rng.choice(fonts)
        img = augment(render_text(text, font, rng), rng)
        rel = os.path.join("images", f"synth_{i:06d}.png")
        img.convert("L").save(os.path.join(out_dir, rel))
        rows.append((rel.replace("\\", "/"), text))
        if i % 500 == 0:
            print(f"  {i}/{n}")

    labels_path = os.path.join(out_dir, "labels.csv")
    with open(labels_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["image_path", "text"])
        w.writerows(rows)
    print(f"[done] {n} images -> {img_dir}")
    print(f"[done] labels -> {labels_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join("Datasets", "synth"),
                    help="output dir (gets images/ and labels.csv)")
    ap.add_argument("--n", type=int, default=5000, help="number of images")
    ap.add_argument("--fonts", nargs="*", default=None,
                    help="Devanagari .ttf paths; default = Windows Nirmala family")
    ap.add_argument("--sizes", nargs="*", type=int, default=[40, 52, 64, 80],
                    help="font pixel sizes to sample from")
    ap.add_argument("--real-ratio", type=float, default=0.5,
                    help="per-token probability of a real word vs random syllables")
    ap.add_argument("--wordfile", default=None,
                    help="optional newline-separated word list to ADD to the built-in one")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    np.random.seed(args.seed)

    if args.wordfile:
        with open(args.wordfile, encoding="utf-8") as f:
            NEPALI_WORDS.extend(w.strip() for w in f if w.strip())

    font_paths = args.fonts if args.fonts else default_font_paths()

    print(f"[fonts] {len(font_paths)} font file(s): {font_paths}")
    fonts = load_fonts(font_paths, args.sizes)
    print(f"[fonts] {len(fonts)} (font,size) variants")
    print(f"[gen] {args.n} images, real_ratio={args.real_ratio}, seed={args.seed}")
    generate(args.out, args.n, fonts, rng, args.real_ratio)


if __name__ == "__main__":
    main()
