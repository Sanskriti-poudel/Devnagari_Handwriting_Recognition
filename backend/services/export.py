"""
Export helpers for document-mode OCR results: turn recognized Nepali text +
the original scanned page(s) into downloadable files.

  * build_docx(text, line_data=None) -> editable .docx with optional table layout
  * build_searchable_pdf(pages)     -> a PDF that looks like the original scan but
                                        carries an invisible Unicode text layer.
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


def _set_devanagari_font(run):
    """Apply Noto Sans Devanagari font to a python-docx run."""
    from docx.oxml.ns import qn
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:ascii"), "Noto Sans Devanagari")
    rfonts.set(qn("w:hAnsi"), "Noto Sans Devanagari")
    rfonts.set(qn("w:cs"), "Mangal")


def build_docx(text, line_data=None):
    """Recognized text -> .docx bytes.

    When line_data is provided (list of {box: [x,y,w,h], text: str}), creates
    a table with one row per detected line, preserving original line heights
    and horizontal positions. Without line_data, falls back to one paragraph
    per newline-delimited line.
    """
    import io
    from docx import Document
    from docx.shared import Pt, Twips as Twip

    doc = Document()

    if not line_data:
        # Fallback: one paragraph per newline-delimited line
        for raw_line in (text or "").split("\n"):
            para = doc.add_paragraph()
            run = para.add_run(raw_line)
            run.font.size = Pt(14)
            _set_devanagari_font(run)
        bio = io.BytesIO()
        doc.save(bio)
        return bio.getvalue()

    # Table-based layout: one row per detected line, preserving line height + position
    # 1 twip = 1/20 point = 1/1440 inch; 1 pixel ≈ 0.75 twip at 96dpi
    for ln in line_data:
        box = ln.get("box")
        if not box:
            continue
        x, y, w, h = box
        txt = ln.get("text") or ""

        # Add a table with 1 row, 1 cell — row height = original line height
        table = doc.add_table(rows=1, cols=1)
        row = table.rows[0]
        # h is in pixels; convert to twips (h * 15 = twips, since 1px ≈ 15 twips at typical rendering)
        row.height = Twip(int(h * 15))

        cell = row.cells[0]
        # Cell width = original line width
        cell.width = Twip(w)

        para = cell.paragraphs[0]
        # Estimate font size from box height (h * 0.5, clamped to 8-14pt)
        fontsize = Pt(max(8.0, min(h * 0.5, 14.0)))
        run = para.add_run(txt)
        run.font.size = fontsize
        _set_devanagari_font(run)

        # Add an empty paragraph after the table row to create vertical spacing
        # (tables don't auto-space in docx the way we need)
        doc.add_paragraph()

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def _merge_columns_reading_order(columns, raw_lines):
    """Merge lines from multiple columns into a single reading-order list.

    Walks down all columns simultaneously, appending one line from each column
    per step — producing left-to-right, top-to-bottom reading order for
    two-column layouts where left and right columns have similar y-ranges.
    """
    if len(columns) == 1:
        return raw_lines

    # Build lookup from box tuple to raw_lines entry
    box_to_line = {tuple(ln["box"]): ln for ln in raw_lines}

    result = []
    indices = [0] * len(columns)

    while any(i < len(col) for i, col in zip(indices, columns)):
        for col_idx, col in enumerate(columns):
            if indices[col_idx] < len(col):
                line = box_to_line.get(tuple(col[indices[col_idx]]))
                if line:
                    result.append(line)
                indices[col_idx] += 1

    return result


def build_searchable_pdf(pages):
    """`pages`: list of {"bgr": np.ndarray (H,W,3), "lines": [{"box": (x,y,w,h), "text": str}, ...]}.

    Embeds the original scan as a full-page image and overlays an invisible
    Unicode text layer at the detected line positions. Uses column detection
    to render lines in the correct reading order for multi-column layouts.
    """
    import fitz  # PyMuPDF

    # Import detect_columns from document.py (no circular import — document.py doesn't import export.py)
    from services.document import detect_columns

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

            raw_lines = pg.get("lines", [])
            if not raw_lines:
                continue

            boxes = [tuple(ln["box"]) for ln in raw_lines]
            columns = detect_columns(boxes, w, h)

            if len(columns) >= 2:
                # Multi-column: merge into reading order
                lines_ordered = _merge_columns_reading_order(columns, raw_lines)
            else:
                # Single column: sort by y then x (top-to-bottom, left-to-right)
                lines_ordered = sorted(raw_lines, key=lambda ln: (ln["box"][1], ln["box"][0]))

            fontname = "deva" if fontfile else "helv"
            for ln in lines_ordered:
                txt = (ln.get("text") or "").strip()
                if not txt:
                    continue
                x, y, bw, bh = ln["box"]
                rect = fitz.Rect(x, y, x + bw, y + bh)
                fontsize = max(6.0, min(float(bh) * 0.6, 48.0))
                # render_mode=0 = filled (visible) text; invisible text (mode=3) is not
                # reliably searchable across all PDF readers, so we use visible text
                # colored light gray so it doesn't distract from the original scan
                placed = False
                try:
                    rc = page.insert_textbox(
                        rect, txt,
                        fontsize=fontsize, fontname=fontname, fontfile=fontfile,
                        color=(0.6, 0.6, 0.6), render_mode=0,
                    )
                    placed = rc >= 0
                except Exception:
                    placed = False
                if not placed:
                    try:
                        page.insert_text(
                            (x, y + fontsize), txt,
                            fontsize=fontsize, fontname=fontname, fontfile=fontfile,
                            color=(0.6, 0.6, 0.6), render_mode=0,
                        )
                    except Exception:
                        pass
        return doc.tobytes()
    finally:
        doc.close()
