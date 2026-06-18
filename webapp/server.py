"""
Lightweight web app for the Devanagari OCR demo (HTML/CSS/JS frontend, Flask backend).

Serves one attractive page and a small JSON API backed by the REAL trained CRNN
(no mock). Self-contained: no npm, no separate backend, no branch merge.

Run from the repo root:
    python webapp/server.py
Then open http://localhost:8000

Endpoints:
    GET  /              -> the web page
    POST /api/predict   -> multipart "image" (image OR PDF; first page rendered) -> {glyph, translit, class, confidence, time_ms, processed}
    GET  /api/random    -> a random held-out test image + its prediction (for the demo)
"""
import os
import sys
import time
import glob
import base64
import random

import cv2
import numpy as np
from flask import Flask, request, jsonify, render_template

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "models", "crnn"))

from Preprocessing.preprocess import preprocess_array
from data.devanagari_labels import class_to_glyph, class_to_translit

TEST_DIR = os.path.join(PROJECT_ROOT, "Datasets", "test")

# Word-level TrOCR weights (the real document-OCR model). When this dir exists
# with a saved checkpoint, document mode reads whole lines with the word model;
# otherwise it falls back to the honest CRNN character-segmentation path.
WORDS_CHECKPOINT = os.environ.get(
    "TROCR_WORDS_CHECKPOINT",
    os.path.join(PROJECT_ROOT, "models", "trocr", "checkpoints_words"),
)

app = Flask(__name__, template_folder="templates", static_folder="static")

# import the real CRNN predictor (loads + caches the model on first call)
from models.crnn.predict import predict as crnn_predict


def _word_model_available():
    """True iff a saved word-level TrOCR checkpoint is present (config + weights)."""
    if not os.path.isdir(WORDS_CHECKPOINT):
        return False
    has_cfg = os.path.exists(os.path.join(WORDS_CHECKPOINT, "config.json"))
    has_weights = any(
        os.path.exists(os.path.join(WORDS_CHECKPOINT, f))
        for f in ("model.safetensors", "pytorch_model.bin")
    )
    return has_cfg and has_weights


def _to_data_uri(bgr_or_gray):
    ok, buf = cv2.imencode(".png", bgr_or_gray)
    return "data:image/png;base64," + base64.b64encode(buf).decode() if ok else None


def _recognize(bgr):
    """ndarray (BGR/gray) -> result dict with prediction + 'what the model sees'."""
    t0 = time.perf_counter()
    proc = preprocess_array(bgr)                  # (64,64) float [0,1]
    res = crnn_predict(proc, device="cpu")        # real CRNN
    ms = (time.perf_counter() - t0) * 1000.0
    cls = res["text"]
    return {
        "glyph": class_to_glyph(cls) if cls else "—",
        "translit": class_to_translit(cls) if cls else "",
        "class_name": cls or "(blank)",
        "confidence": res["confidence"],
        "time_ms": round(ms, 1),
        "processed": _to_data_uri((proc * 255).astype(np.uint8)),
    }


@app.route("/")
def index():
    return render_template("index.html", word_model=_word_model_available())


def _pdf_first_page_to_bgr(raw):
    """Render the first page of a PDF (bytes) to a BGR ndarray, or None on failure."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None
    try:
        doc = fitz.open(stream=raw, filetype="pdf")
        if doc.page_count == 0:
            return None
        # render at 2x so thin strokes survive the downscale to 64x64
        pix = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(2, 2))
        img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:        # RGBA -> BGR
            return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        if pix.n == 3:        # RGB -> BGR
            return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    except Exception:
        return None


@app.route("/api/predict", methods=["POST"])
def api_predict():
    bgr, is_pdf, err = _read_upload_to_bgr(request.files.get("image"))
    if err is not None:
        return err
    out = _recognize(bgr)
    if is_pdf:
        # the browser can't preview a PDF blob in an <img>, so send back
        # the rendered first page as the input preview
        out["original"] = _to_data_uri(bgr)
    return jsonify(out)


def _read_upload_to_bgr(file):
    """Shared upload reader. Returns (bgr, is_pdf, error_response_or_None)."""
    if file is None:
        return None, False, (jsonify({"error": "No file uploaded."}), 400)
    raw = file.read()
    name = (file.filename or "").lower()
    is_pdf = name.endswith(".pdf") or raw[:5] == b"%PDF-"
    if is_pdf:
        bgr = _pdf_first_page_to_bgr(raw)
        if bgr is None:
            return None, True, (jsonify({"error": "Could not read that PDF (or PyMuPDF is not installed)."}), 400)
    else:
        data = np.frombuffer(raw, np.uint8)
        bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if bgr is None:
            return None, False, (jsonify({"error": "Could not read that file. Upload an image or PDF."}), 400)
    return bgr, is_pdf, None


@app.route("/api/document", methods=["POST"])
def api_document():
    """
    Document mode: page (image or PDF) -> editable Devanagari Unicode text.

    Uses the REAL word-level TrOCR (reads whole lines, including matras /
    conjuncts / punctuation) when a trained checkpoint is present; otherwise
    falls back to the honest CRNN character-segmentation path (base glyphs only).
    """
    bgr, _is_pdf, err = _read_upload_to_bgr(request.files.get("image"))
    if err is not None:
        return err
    if _word_model_available():
        return _document_wordlevel(bgr)
    return _document_charlevel(bgr)


def _document_wordlevel(bgr):
    """Word/line-level TrOCR: segment the page into LINES and read each end-to-end.
    This is the model that actually reads joined handwriting with matras."""
    from models.trocr.predict_words import predict_page

    t0 = time.perf_counter()
    out = predict_page(bgr, checkpoint_path=WORDS_CHECKPOINT, device="cpu")
    lines = out["lines"]
    if not lines:
        return jsonify({"error": "No text lines detected. Try a clearer, higher-contrast scan."}), 400

    confs = [ln["confidence"] for ln in lines if ln.get("confidence")]
    text = out["text"]
    return jsonify({
        "engine": "word-trocr",
        "text": text,
        "num_chars": len(text.replace("\n", "").replace(" ", "")),
        "num_lines": len(lines),
        "avg_confidence": round(float(np.mean(confs)), 4) if confs else 0.0,
        "time_ms": round((time.perf_counter() - t0) * 1000.0, 1),
        "annotated": _to_data_uri(out["annotated"]),
    })


def _document_charlevel(bgr):
    """Fallback: segment a page into characters and run each through the CRNN.

    The CRNN knows only the 46 DHCD classes (no vowel signs / matras /
    punctuation) and segmentation only works on neatly spaced writing, so the
    output is base glyphs, not fully composed syllables. See models/crnn/segment.py.
    """
    from models.crnn.segment import segment_lines, crop_glyph, annotate

    t0 = time.perf_counter()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    lines = segment_lines(bgr)
    if not lines:
        return jsonify({"error": "No characters detected. Try a clearer, higher-contrast scan."}), 400

    text_lines, n_chars, conf_sum = [], 0, 0.0
    for line in lines:
        widths = [w for (_x, _y, w, _h) in line]
        med_w = float(np.median(widths)) if widths else 0.0
        parts, prev_right = [], None
        for box in line:
            x, _y, w, _h = box
            if prev_right is not None and (x - prev_right) > 0.8 * med_w:
                parts.append(" ")                      # large gap -> word space
            crop = crop_glyph(gray, box)
            res = crnn_predict(crop, device="cpu")
            cls = res["text"]
            parts.append(class_to_glyph(cls) if cls else "")
            conf_sum += res["confidence"]
            n_chars += 1
            prev_right = x + w
        text_lines.append("".join(parts))

    return jsonify({
        "engine": "crnn-chars",
        "text": "\n".join(text_lines),
        "num_chars": n_chars,
        "num_lines": len(lines),
        "avg_confidence": round(conf_sum / n_chars, 4) if n_chars else 0.0,
        "time_ms": round((time.perf_counter() - t0) * 1000.0, 1),
        "annotated": _to_data_uri(annotate(bgr, lines)),
    })


@app.route("/api/random")
def api_random():
    paths = glob.glob(os.path.join(TEST_DIR, "*", "*.png"))
    if not paths:
        return jsonify({"error": f"No test images under {TEST_DIR}."}), 404
    p = random.choice(paths)
    bgr = cv2.imread(p)
    true_cls = os.path.basename(os.path.dirname(p))
    out = _recognize(bgr)
    out["original"] = _to_data_uri(bgr)
    out["true_glyph"] = class_to_glyph(true_cls)
    out["true_translit"] = class_to_translit(true_cls)
    out["correct"] = (out["class_name"] == true_cls)
    return jsonify(out)


if __name__ == "__main__":
    print("Devanagari OCR web app -> http://localhost:8000")
    app.run(host="0.0.0.0", port=8000, debug=False)
