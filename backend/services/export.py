"""
Export helpers for document-mode OCR results: turn recognized Nepali text +
the original scanned page(s) into downloadable files.

Ported near-verbatim from webapp/export.py (the Flask document digitizer)
so both UIs produce identical output.

  * build_docx(text)            -> editable .docx (opens in Word / Google Docs)
  * build_searchable_pdf(pages) -> a PDF that *looks* like the original scan but
                                    carries an invisible Unicode text layer, so
                                    the page becomes selectable / copyable /
                                    Ctrl+F-able.
"""
import os

import cv2

from ml_models.loader import REPO_ROOT
import sys

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from data.generate_synth import default_font_paths
except Exception:  # pragma: no cover - generate_synth import should not fail
    def default_font_paths():
        return []


def _devanagari_font_file():
    for p in default_font_paths():
        if os.path.exists(p):
            return p
    return None


def build_docx(text):
    """Recognized text -> .docx bytes, one paragraph per line."""
    import io
    from docx import Document
    from docx.shared import Pt
    from docx.oxml.ns import qn

    doc = Document()
    for raw_line in (text or "").split("\n"):
        para = doc.add_paragraph()
        run = para.add_run(raw_line)
        run.font.size = Pt(14)
        rpr = run._element.get_or_add_rPr()
        rfonts = rpr.get_or_add_rFonts()
        rfonts.set(qn("w:ascii"), "Noto Sans Devanagari")
        rfonts.set(qn("w:hAnsi"), "Noto Sans Devanagari")
        rfonts.set(qn("w:cs"), "Mangal")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def build_searchable_pdf(pages):
    """`pages`: list of {"bgr": np.ndarray (H,W,3), "lines": [{"box": (x,y,w,h), "text": str}, ...]}."""
    import fitz  # PyMuPDF

    fontfile = _devanagari_font_file()
    doc = fitz.open()
    try:
        for pg in pages:
            bgr = pg["bgr"]
            h, w = bgr.shape[:2]
            page = doc.new_page(width=w, height=h)

            ok, buf = cv2.imencode(".png", bgr)
            if ok:
                page.insert_image(fitz.Rect(0, 0, w, h), stream=buf.tobytes())

            fontname = "deva" if fontfile else "helv"
            for ln in pg.get("lines", []):
                txt = (ln.get("text") or "").strip()
                if not txt:
                    continue
                x, y, bw, bh = ln["box"]
                rect = fitz.Rect(x, y, x + bw, y + bh)
                fontsize = max(6.0, min(float(bh) * 0.6, 48.0))
                placed = False
                try:
                    rc = page.insert_textbox(
                        rect, txt,
                        fontsize=fontsize, fontname=fontname, fontfile=fontfile,
                        render_mode=3,
                    )
                    placed = rc >= 0
                except Exception:
                    placed = False
                if not placed:
                    try:
                        page.insert_text(
                            (x, y + fontsize), txt,
                            fontsize=fontsize, fontname=fontname, fontfile=fontfile,
                            render_mode=3,
                        )
                    except Exception:
                        pass
        return doc.tobytes()
    finally:
        doc.close()
