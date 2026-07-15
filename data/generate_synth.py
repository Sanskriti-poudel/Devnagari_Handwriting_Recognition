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
    # extra common words — broaden matra/conjunct coverage for the demo vocabulary
    "नेपाली", "हस्तलेख", "अक्षर", "शब्द", "वाक्य", "लेख", "पढाइ", "स्कूल",
    "कलेज", "प्रश्न", "उत्तर", "सरकार", "देशभक्त", "स्वतन्त्रता", "गणतन्त्र",
    "प्रजातन्त्र", "अधिकार", "कर्तव्य", "समाज", "संसार", "प्रकृति", "वातावरण",
    "स्वास्थ्य", "शिक्षा", "रोजगार", "विकास", "प्रविधि", "कम्प्युटर", "इन्टरनेट",
    "मोबाइल", "सञ्चार", "यातायात", "व्यापार", "अर्थतन्त्र", "किसान", "मजदुर",
    "डाक्टर", "इन्जिनियर", "वकिल", "नर्स", "पुलिस", "सैनिक", "नेता", "जनता",
    "गोरखा", "पोखरा", "विराटनगर", "धरान", "भक्तपुर", "ललितपुर", "चितवन",
    "एक", "दुई", "तीन", "चार", "पाँच", "छ", "सात", "आठ", "नौ", "दश",
    # document / official-form vocabulary — the real target is printed Nepali
    # forms (complaints, applications), which the earlier synth never covered.
    "श्रीमान्", "कार्यालय", "प्रमुखज्यू", "प्रहरी", "विषय", "महोदय", "निवेदक",
    "निवेदिका", "निवेदन", "सम्बन्धमा", "सम्बन्धी", "बमोजिम", "देहाय", "उपरोक्त",
    "घटना", "कारवाही", "कानून", "पेश", "साइबर", "अपराध", "विद्युतीय", "माध्यम",
    "ठगी", "सामाजिक", "सञ्जाल", "संलग्न", "कागजात", "आवश्यक", "स्क्रिनसट",
    "नागरिकता", "प्रतिलिपि", "राहदानी", "पासपोर्ट", "राष्ट्रिय", "परिचयपत्र",
    "कर्मचारी", "विवरण", "नामथर", "लिङ्ग", "जन्म", "मिति", "ठेगाना", "दस्तखत",
    "व्यक्तिगत", "सम्पर्क", "नम्बर", "अभिभावक", "संस्था", "मैले", "जानेसम्म",
    "उल्लिखित", "व्यहोरा", "साँचो", "झुट्टा", "ठहरे", "सहुँला", "गते", "पेज",
]

# Latin tokens that appear verbatim on real Nepali forms (mixed-script lines).
# The earlier synth was pure Devanagari, so the model had never seen Latin and
# collapsed on lines like "निवेदकको Original ID/URL:-".
LATIN_TOKENS = [
    "ID", "URL", "FB", "Messenger", "Insta", "WhatsApp", "Tiktok", "Focal",
    "Person", "Email", "Original", "No", "OK", "Facebook", "Viber", "Imo",
]

# Label prefixes / fragments that pattern real form lines.
LIST_PREFIXES = ["१.", "२.", "३.", "४.", "५.", "६.", "७.", "८.", "९.", "•", "✓"]
LABEL_SUFFIX = ":-"  # "नामथरः-", "Original ID/URL:-" style trailing marker


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


def sample_line(rng, real_ratio):
    """A LONG, document-style line (6–16 tokens), optionally mixing Latin tokens,
    a leading list prefix (१. / • / ✓), slashes, and a ":-" label marker.

    The earlier synth only produced 1–4-token phrases, so the model collapsed on
    the long printed lines of a real form. This samples the missing regime."""
    n_tokens = rng.randint(5, 12)
    tokens = []
    # ~40% of long lines start like a numbered/bulleted form item
    if rng.random() < 0.40:
        tokens.append(rng.choice(LIST_PREFIXES))
    for _ in range(n_tokens):
        r = rng.random()
        if r < 0.12:                       # occasional Latin token (mixed script)
            tokens.append(rng.choice(LATIN_TOKENS))
        elif r < 0.85:                     # real Nepali / form word — long lines are
            tokens.append(rng.choice(NEPALI_WORDS))  # prose/form text, mostly real
        else:                              # a little short-syllable filler for coverage
            tokens.append(random_syllable(rng) + rng.choice(MATRAS))
    # sprinkle slashes between a few adjacent tokens ("निवेदक / निवेदिका", "ID/URL")
    for i in range(1, len(tokens)):
        if rng.random() < 0.10:
            tokens[i] = "/" + tokens[i] if rng.random() < 0.5 else tokens[i] + "/"
    text = " ".join(tokens)
    tail = rng.random()
    if tail < 0.35:
        text += LABEL_SUFFIX               # form field label ("...:-")
    elif tail < 0.70:
        text += DANDA                      # sentence terminator
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


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BUNDLED_FONT_DIR = os.path.abspath(os.path.join(THIS_DIR, "..", "assets", "fonts_devanagari"))


def default_font_paths():
    """Find Devanagari fonts to render from. Always includes the fonts bundled
    in assets/fonts_devanagari (checked into the repo — Noto Sans/Serif
    Devanagari, Hind, Mukta, Tiro Devanagari Hindi, Baloo 2, Khand — 8 distinct
    typefaces so the model doesn't overfit to a couple of Windows system
    fonts), plus whatever the OS already has installed (Windows -> Nirmala/
    Mangal; Linux/mac -> any installed Devanagari/Lohit/Noto-Devanagari
    .ttf/.otf, e.g. after `apt-get install fonts-deva fonts-lohit-deva`)."""
    paths = []
    if os.path.isdir(_BUNDLED_FONT_DIR):
        paths += sorted(glob.glob(os.path.join(_BUNDLED_FONT_DIR, "*.ttf")))
        paths += sorted(glob.glob(os.path.join(_BUNDLED_FONT_DIR, "*.otf")))

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


def _wave_warp(img, rng, axis, amp_range=(1.0, 3.5), freq_range=(1.2, 3.5)):
    """Sinusoidal per-line displacement (numpy only, no scipy) — mimics the
    wavering baseline and uneven stroke height of real handwriting, which a
    perfectly-rasterized font never has. axis='row' shifts each row
    horizontally (wavy baseline); axis='col' shifts each column vertically
    (letters bouncing above/below the line)."""
    arr = np.asarray(img).astype(np.uint8)
    H, W = arr.shape
    out = np.full_like(arr, 255)
    amp = rng.uniform(*amp_range)
    freq = rng.uniform(*freq_range)
    phase = rng.uniform(0, 2 * math.pi)
    n = H if axis == "row" else W
    for i in range(n):
        shift = int(round(amp * math.sin(2 * math.pi * freq * i / n + phase)))
        if shift == 0:
            line = arr[i, :] if axis == "row" else arr[:, i]
            (out[i, :] if axis == "row" else out[:, i])[:] = line
            continue
        if axis == "row":
            if shift > 0:
                out[i, shift:] = arr[i, :W - shift]
            else:
                out[i, :W + shift] = arr[i, -shift:]
        else:
            if shift > 0:
                out[shift:, i] = arr[:H - shift, i]
            else:
                out[:H + shift, i] = arr[-shift:, i]
    return Image.fromarray(out)


def augment(img, rng):
    """Geometric + photometric distortion to look less font-perfect —
    approximates real pen-stroke variation (wavy baseline, jittery stroke
    height, slant, blur, sensor/paper noise) instead of a crisp rasterized
    font, which is most of the train/real-photo domain gap."""
    if rng.random() < 0.7:
        img = _shear(img, rng)
    if rng.random() < 0.7:
        img = img.rotate(rng.uniform(-4, 4), resample=Image.BILINEAR,
                         expand=True, fillcolor=255)
    if rng.random() < 0.6:
        img = _wave_warp(img, rng, axis="row")
    if rng.random() < 0.5:
        img = _wave_warp(img, rng, axis="col")
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

def generate(out_dir, n, fonts, rng, real_ratio, clean_ratio=0.25, long_ratio=0.0):
    img_dir = os.path.join(out_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    rows = []
    for i in range(1, n + 1):
        # `long_ratio` of the set are long document-style lines; the rest are
        # short 1–4-token phrases (both regimes appear on real pages).
        text = (sample_line(rng, real_ratio) if rng.random() < long_ratio
                else sample_text(rng, real_ratio))
        font = rng.choice(fonts)
        base = render_text(text, font, rng)
        # `clean_ratio` of the set is left crisp (printed-style), the rest gets
        # handwriting-like distortion. The demo input is a MIX of printed and
        # handwritten pages, so the model needs to see both domains.
        img = base if rng.random() < clean_ratio else augment(base, rng)
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
    ap.add_argument("--sizes", nargs="*", type=int, default=[28, 34, 40, 52, 64, 80],
                    help="font pixel sizes to sample from (small sizes matter: "
                         "real printed forms have small body text)")
    ap.add_argument("--real-ratio", type=float, default=0.5,
                    help="per-token probability of a real word vs random syllables")
    ap.add_argument("--clean-ratio", type=float, default=0.25,
                    help="fraction rendered crisp/printed (no handwriting distortion)")
    ap.add_argument("--long-ratio", type=float, default=0.0,
                    help="fraction generated as long document-style lines "
                         "(6-16 tokens, mixed Latin/form punctuation)")
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
    print(f"[gen] {args.n} images, real_ratio={args.real_ratio}, "
          f"clean_ratio={args.clean_ratio}, long_ratio={args.long_ratio}, seed={args.seed}")
    generate(args.out, args.n, fonts, rng, args.real_ratio, args.clean_ratio,
             args.long_ratio)


if __name__ == "__main__":
    main()
