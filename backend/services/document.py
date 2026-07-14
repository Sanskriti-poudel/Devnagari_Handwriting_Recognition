"""
Document-mode OCR: a page or multi-page PDF -> editable Devanagari Unicode text.

Ports the logic from webapp/server.py (the Flask document digitizer) so both
UIs share the same behavior: uses the real word-level TrOCR (reads whole
lines, including matras/conjuncts/punctuation) when a trained checkpoint is
loaded; otherwise falls back to the honest CRNN character-segmentation path.
"""
import base64
import logging
import time
import unicodedata
import uuid
from collections import OrderedDict

import cv2
import numpy as np

from ml_models.loader import loaded_models, REPO_ROOT
import sys

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

logger = logging.getLogger(__name__)

# In-memory store of recent OCR runs, keyed by a doc_id handed to the client.
# Holds the original page images + per-line boxes/text so export_service can
# build a searchable PDF later. Bounded so a long-running server doesn't grow.
_DOC_CACHE = OrderedDict()
_DOC_CACHE_MAX = 24


def _cache_doc(pages):
    doc_id = uuid.uuid4().hex
    _DOC_CACHE[doc_id] = pages
    while len(_DOC_CACHE) > _DOC_CACHE_MAX:
        _DOC_CACHE.popitem(last=False)
    return doc_id


def get_cached_doc(doc_id):
    return _DOC_CACHE.get(doc_id)


def _nfc(text):
    return unicodedata.normalize("NFC", text or "")


def _to_data_uri(bgr_or_gray):
    ok, buf = cv2.imencode(".png", bgr_or_gray)
    return "data:image/png;base64," + base64.b64encode(buf).decode() if ok else None


def _pixmap_to_bgr(pix):
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    if pix.n == 3:
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
            pix = doc.load_page(i).get_pixmap(matrix=fitz.Matrix(2, 2))
            pages.append(_pixmap_to_bgr(pix))
        return pages
    except Exception:
        return None


def read_upload_to_pages(filename, raw):
    """(filename, raw bytes) -> (pages: list[np.ndarray] | None, error_message: str | None)."""
    name = (filename or "").lower()
    is_pdf = name.endswith(".pdf") or raw[:5] == b"%PDF-"
    if is_pdf:
        pages = _pdf_to_bgr_pages(raw)
        if not pages:
            return None, "Could not read that PDF (or PyMuPDF is not installed)."
        return pages, None
    data = np.frombuffer(raw, np.uint8)
    bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if bgr is None:
        return None, "Could not read that file. Upload an image or PDF."
    return [bgr], None


def _ocr_page_wordlevel(bgr):
    from config import DEVICE
    from models.trocr.predict_words import predict_page

    checkpoint = loaded_models["transformer"]
    out = predict_page(bgr, checkpoint_path=checkpoint, device=DEVICE)
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
    from config import DEVICE
    from data.devanagari_labels import class_to_glyph
    from models.crnn.predict import predict as crnn_predict
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
                parts.append(" ")
            crop = crop_glyph(gray, box)
            res = crnn_predict(crop, device=DEVICE)
            cls = res["text"]
            parts.append(class_to_glyph(cls) if cls else "")
            conf_sum += res["confidence"]
            n_chars += 1
            prev_right = x + w
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


def run_document_ocr(pages):
    """list[np.ndarray] (BGR pages) -> (response_dict, error_message_or_None)."""
    ocr_page = _ocr_page_wordlevel if "transformer" in loaded_models else _ocr_page_charlevel
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
        return None, msg

    doc_id = _cache_doc(cache_pages)
    engine = page_results[0]["engine"]
    combined_text = _nfc("\n\n".join(r["text"] for r in page_results))
    total_lines = sum(r["num_lines"] for r in page_results)
    total_chars = sum(r["num_chars"] for r in page_results)
    confs = [r["avg_confidence"] for r in page_results if r["num_lines"]]

    response = {
        "doc_id": doc_id,
        "engine": engine,
        "text": combined_text,
        "num_chars": total_chars,
        "num_lines": total_lines,
        "num_pages": len(page_results),
        "avg_confidence": round(float(np.mean(confs)), 4) if confs else 0.0,
        "time_ms": round((time.perf_counter() - t0) * 1000.0, 1),
        "annotated": page_results[0]["annotated_uri"],
        "pages": [{
            "annotated": r["annotated_uri"],
            "text": r["text"],
            "num_lines": r["num_lines"],
            "num_chars": r["num_chars"],
            "avg_confidence": r["avg_confidence"],
        } for r in page_results],
    }
    return response, None
