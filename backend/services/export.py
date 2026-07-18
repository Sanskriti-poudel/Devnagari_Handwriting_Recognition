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


def build_docx(text, line_data=None, page_image=None):
    """Recognized text -> .docx bytes.

    When line_data is provided (list of {box: [x,y,w,h], text: str}), creates
    a layout-preserving document with the original page image as background
    and OCR text overlaid at the detected positions.

    If page_image is provided (numpy BGR array), embeds it as a full-page
    background image and places text boxes at the detected line positions,
    preserving the original document's visual appearance.

    Falls back to simple paragraph-per-line format if no line_data.
    """
    import io
    import numpy as np
    from docx import Document
    from docx.shared import Pt, Twips as Twip, Inches, RGBColor, Emu
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn, nsmap
    from docx.oxml import OxmlElement
    import base64

    doc = Document()

    # Set page to exact dimensions for the page image
    if page_image is not None:
        h, w = page_image.shape[:2]
        # Set page size to match image dimensions (in inches, 1 inch = 96 pixels at 96dpi)
        page_w_inches = w / 96.0
        page_h_inches = h / 96.0
        for section in doc.sections:
            section.page_width = Inches(page_w_inches)
            section.page_height = Inches(page_h_inches)
            section.left_margin = Inches(0)
            section.right_margin = Inches(0)
            section.top_margin = Inches(0)
            section.bottom_margin = Inches(0)

        # Encode image
        rgb = page_image if page_image.ndim == 3 else cv2.cvtColor(page_image, cv2.COLOR_GRAY2BGR)
        ok, buf = cv2.imencode(".png", rgb)
        if not ok:
            page_image = None
        else:
            img_bytes = buf.tobytes()

    if not line_data:
        # Fallback: simple paragraphs
        for raw_line in (text or "").split("\n"):
            para = doc.add_paragraph(raw_line)
            para.paragraph_format.space_before = Pt(0)
            para.paragraph_format.space_after = Pt(0)
            run = para.runs[0] if para.runs else para.add_run(raw_line)
            run.font.size = Pt(11)
            _set_devanagari_font(run)
        bio = io.BytesIO()
        doc.save(bio)
        return bio.getvalue()

    # Group lines by vertical proximity (within 10 pixels = same line)
    def group_lines_by_y(lines):
        if not lines:
            return []
        sorted_lines = sorted(lines, key=lambda l: l["box"][1] if l.get("box") else 0)
        groups = []
        current_group = [sorted_lines[0]]
        last_y = sorted_lines[0]["box"][1] if sorted_lines[0].get("box") else 0
        for ln in sorted_lines[1:]:
            y = ln["box"][1] if ln.get("box") else 0
            if abs(y - last_y) <= 10:
                current_group.append(ln)
            else:
                groups.append(sorted(current_group, key=lambda l: l["box"][0]))
                current_group = [ln]
            last_y = y
        if current_group:
            groups.append(sorted(current_group, key=lambda l: l["box"][0]))
        return groups

    line_groups = group_lines_by_y([ln for ln in line_data if ln.get("box")])

    if page_image is not None:
        # Add page image as the first paragraph (full page background)
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
        run = para.add_run()
        run.add_picture(io.BytesIO(img_bytes), width=Inches(page_w_inches))

        # Now add each line as a positioned text box
        # We use a table with invisible borders to position text
        dpi = 96.0  # screen dpi

        for group in line_groups:
            for ln in group:
                box = ln.get("box")
                if not box:
                    continue
                x, y, w, h = box
                txt = ln.get("text") or ""

                # Create a new paragraph with explicit positioning
                # DOCX doesn't support true absolute positioning,
                # but we can use a table with 1 cell to approximate
                para = doc.add_paragraph()
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.line_spacing = 1.0

                # Estimate font size from box height (pixels -> points, ~0.75 factor)
                fontsize = max(6.0, min(h * 0.45, 12.0))
                run = para.add_run(txt)
                run.font.size = Pt(fontsize)
                _set_devanagari_font(run)
                # Make text subtle so image shows through
                run.font.color.rgb = RGBColor(128, 128, 128)
    else:
        # No image: use table layout with grouped lines
        table = doc.add_table(rows=len(line_groups), cols=1)
        table.style = "Table Grid"

        for i, group in enumerate(line_groups):
            row = table.rows[i]
            # Set row height
            max_h = max((ln["box"][3] for ln in group if ln.get("box")), default=20)
            row.height = Twip(int(max_h * 15 * 0.5))  # Convert to twips

            cell = row.cells[0]
            # Build text from all lines in this group
            group_text = " ".join(ln.get("text", "") for ln in group)
            para = cell.paragraphs[0]
            para.paragraph_format.space_before = Pt(0)
            para.paragraph_format.space_after = Pt(0)
            para.paragraph_format.line_spacing = 1.0
            run = para.add_run(group_text)
            run.font.size = Pt(max(8.0, min(max_h * 0.4, 12.0)))
            _set_devanagari_font(run)

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
