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
import uuid
import unicodedata
from collections import OrderedDict
from io import BytesIO

import cv2
import numpy as np
from flask import Flask, request, jsonify, render_template, send_file

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

# In-memory store of recent OCR runs, keyed by a doc_id we hand to the client.
# Holds the original page images + per-line boxes/text so /api/export can build
# a searchable PDF later. Bounded so a long-running server doesn't grow forever.
_DOC_CACHE = OrderedDict()
_DOC_CACHE_MAX = 24


def _cache_doc(pages):
    """Store OCR pages, return a new doc_id. Evicts the oldest when full."""
    doc_id = uuid.uuid4().hex
    _DOC_CACHE[doc_id] = pages
    while len(_DOC_CACHE) > _DOC_CACHE_MAX:
        _DOC_CACHE.popitem(last=False)
    return doc_id


def _nfc(text):
    """Normalize to Unicode NFC so composed Devanagari compares/renders consistently."""
    return unicodedata.normalize("NFC", text or "")


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


def _pixmap_to_bgr(pix):
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:        # RGBA -> BGR
        return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    if pix.n == 3:        # RGB -> BGR
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)


def _pdf_to_bgr_pages(raw):
    """Render EVERY page of a PDF (bytes) to a list of BGR ndarrays, or None on failure."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None
    try:
        doc = fitz.open(stream=raw, filetype="pdf")
        if doc.page_count == 0:
            return None
        pages = []
        for i in range(doc.page_count):
            # render at 2x so thin strokes survive the downscale to 64x64
            pix = doc.load_page(i).get_pixmap(matrix=fitz.Matrix(2, 2))
            pages.append(_pixmap_to_bgr(pix))
        return pages
    except Exception:
        return None


def _pdf_first_page_to_bgr(raw):
    """Render only the first page of a PDF (bytes) to a BGR ndarray, or None on failure."""
    pages = _pdf_to_bgr_pages(raw)
    return pages[0] if pages else None


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


def _read_upload_to_pages(file):
    """Like _read_upload_to_bgr but returns ALL pages. Returns (pages, error_or_None).

    Images yield a single-element list; multi-page PDFs yield one BGR ndarray per page.
    """
    if file is None:
        return None, (jsonify({"error": "No file uploaded."}), 400)
    raw = file.read()
    name = (file.filename or "").lower()
    is_pdf = name.endswith(".pdf") or raw[:5] == b"%PDF-"
    if is_pdf:
        pages = _pdf_to_bgr_pages(raw)
        if not pages:
            return None, (jsonify({"error": "Could not read that PDF (or PyMuPDF is not installed)."}), 400)
        return pages, None
    data = np.frombuffer(raw, np.uint8)
    bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if bgr is None:
        return None, (jsonify({"error": "Could not read that file. Upload an image or PDF."}), 400)
    return [bgr], None


@app.route("/api/document", methods=["POST"])
def api_document():
    """
    Document mode: a page or multi-page PDF -> editable Devanagari Unicode text.

    Uses the REAL word-level TrOCR (reads whole lines, including matras /
    conjuncts / punctuation) when a trained checkpoint is present; otherwise
    falls back to the honest CRNN character-segmentation path (base glyphs only).

    Returns one entry per page plus a combined text, and a `doc_id` the client
    can hand back to /api/export to download a searchable PDF.
    """
    pages, err = _read_upload_to_pages(request.files.get("image"))
    if err is not None:
        return err

    ocr_page = _ocr_page_wordlevel if _word_model_available() else _ocr_page_charlevel
    t0 = time.perf_counter()

    page_results, cache_pages = [], []
    any_lines = False
    for bgr in pages:
        res = ocr_page(bgr)
        if res["lines"]:
            any_lines = True
        page_results.append(res)
        cache_pages.append({
            "bgr": bgr,
            "lines": [{"box": ln["box"], "text": ln["text"]} for ln in res["lines"]],
        })

    if not any_lines:
        msg = ("No text lines detected. Try a clearer, higher-contrast scan."
               if ocr_page is _ocr_page_wordlevel
               else "No characters detected. Try a clearer, higher-contrast scan.")
        return jsonify({"error": msg}), 400

    doc_id = _cache_doc(cache_pages)
    engine = page_results[0]["engine"]
    combined_text = _nfc("\n\n".join(r["text"] for r in page_results))
    total_lines = sum(r["num_lines"] for r in page_results)
    total_chars = sum(r["num_chars"] for r in page_results)
    confs = [r["avg_confidence"] for r in page_results if r["num_lines"]]

    return jsonify({
        "doc_id": doc_id,
        "engine": engine,
        "text": combined_text,
        "num_chars": total_chars,
        "num_lines": total_lines,
        "num_pages": len(page_results),
        "avg_confidence": round(float(np.mean(confs)), 4) if confs else 0.0,
        "time_ms": round((time.perf_counter() - t0) * 1000.0, 1),
        # first page kept at top level for backward compatibility
        "annotated": page_results[0]["annotated_uri"],
        "pages": [{
            "annotated": r["annotated_uri"],
            "text": r["text"],
            "num_lines": r["num_lines"],
            "num_chars": r["num_chars"],
            "avg_confidence": r["avg_confidence"],
        } for r in page_results],
    })


def _ocr_page_wordlevel(bgr):
    """Word/line-level TrOCR: segment a page into LINES and read each end-to-end.
    This is the model that actually reads joined handwriting with matras.
    Returns a structured dict (text NFC-normalized, per-line boxes, annotated image)."""
    from models.trocr.predict_words import predict_page

    out = predict_page(bgr, checkpoint_path=WORDS_CHECKPOINT, device="cpu")
    lines = []
    for ln in out["lines"]:
        lines.append({
            "box": tuple(int(v) for v in ln["box"]),
            "text": _nfc(ln.get("text", "")),
            "confidence": float(ln.get("confidence") or 0.0),
        })
    text = _nfc(out["text"])
    confs = [ln["confidence"] for ln in lines if ln["confidence"]]
    return {
        "engine": "word-trocr",
        "text": text,
        "lines": lines,
        "annotated_uri": _to_data_uri(out["annotated"]),
        "num_chars": len(text.replace("\n", "").replace(" ", "")),
        "num_lines": len(lines),
        "avg_confidence": round(float(np.mean(confs)), 4) if confs else 0.0,
    }


def _ocr_page_charlevel(bgr):
    """Fallback: segment a page into characters and run each through the CRNN.

    The CRNN knows only the 46 DHCD classes (no vowel signs / matras /
    punctuation) and segmentation only works on neatly spaced writing, so the
    output is base glyphs, not fully composed syllables. See models/crnn/segment.py.
    Returns the same structured dict shape as _ocr_page_wordlevel (one box per line,
    the union of the line's character boxes, for the searchable-PDF layer)."""
    from models.crnn.segment import segment_lines, crop_glyph, annotate

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    seg_lines = segment_lines(bgr)
    if not seg_lines:
        return {
            "engine": "crnn-chars", "text": "", "lines": [],
            "annotated_uri": _to_data_uri(bgr),
            "num_chars": 0, "num_lines": 0, "avg_confidence": 0.0,
        }

    out_lines, n_chars, conf_sum = [], 0, 0.0
    for line in seg_lines:
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
        # union box of this line's character boxes (for the searchable-PDF text layer)
        xs = [b[0] for b in line]; ys = [b[1] for b in line]
        xe = [b[0] + b[2] for b in line]; ye = [b[1] + b[3] for b in line]
        union = (min(xs), min(ys), max(xe) - min(xs), max(ye) - min(ys))
        out_lines.append({
            "box": tuple(int(v) for v in union),
            "text": _nfc("".join(parts)),
            "confidence": 0.0,
        })

    return {
        "engine": "crnn-chars",
        "text": _nfc("\n".join(ln["text"] for ln in out_lines)),
        "lines": out_lines,
        "annotated_uri": _to_data_uri(annotate(bgr, seg_lines)),
        "num_chars": n_chars,
        "num_lines": len(out_lines),
        "avg_confidence": round(conf_sum / n_chars, 4) if n_chars else 0.0,
    }


@app.route("/api/export", methods=["POST"])
def api_export():
    """Download the recognized text as txt | docx | (searchable) pdf.

    Body JSON: {"format": "txt"|"docx"|"pdf", "text": <edited text>, "doc_id": <id>}
    - txt / docx use the (possibly user-edited) `text`.
    - pdf rebuilds a searchable PDF from the cached page images + OCR line boxes
      for `doc_id` (so the scan is preserved with an invisible, searchable text layer).
    """
    body = request.get_json(silent=True) or {}
    fmt = (body.get("format") or "").lower()
    text = _nfc(body.get("text") or "")

    if fmt == "txt":
        return send_file(
            BytesIO(text.encode("utf-8")),
            mimetype="text/plain; charset=utf-8",
            as_attachment=True, download_name="recognized.txt",
        )

    if fmt == "docx":
        from webapp.export import build_docx
        data = build_docx(text)
        return send_file(
            BytesIO(data),
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True, download_name="recognized.docx",
        )

    if fmt == "pdf":
        doc_id = body.get("doc_id")
        pages = _DOC_CACHE.get(doc_id) if doc_id else None
        if not pages:
            return jsonify({"error": "This document expired — re-run the scan, then export."}), 410
        from webapp.export import build_searchable_pdf
        data = build_searchable_pdf(pages)
        return send_file(
            BytesIO(data),
            mimetype="application/pdf",
            as_attachment=True, download_name="recognized.pdf",
        )

    return jsonify({"error": "Unknown export format. Use txt, docx or pdf."}), 400


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
