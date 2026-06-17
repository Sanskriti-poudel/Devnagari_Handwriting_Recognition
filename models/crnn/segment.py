"""
Character segmentation for document-mode OCR (Path C).

The CRNN is a single-character classifier, so to read a whole page we first
split the page into individual character blobs with classical computer vision,
then run each crop through the CRNN and stitch the predictions back into lines
of text.

IMPORTANT limitations (be honest about these in the UI / defense):
  * Works well ONLY on neatly written, well-spaced Devanagari where characters
    are separated by whitespace. In connected/cursive writing the शिरोरेखा
    (headline) joins letters into a whole word, so a word gets segmented as one
    blob and recognized as a single (wrong) character.
  * The model's alphabet is just the 46 DHCD classes (36 consonants/conjuncts +
    10 digits). It has NO vowel signs (matras), independent vowels, or
    punctuation, so the reconstructed text is a sequence of base glyphs, not
    fully composed syllables.
"""
import cv2
import numpy as np


def _binarize(gray):
    """Otsu inverse threshold + speck removal: ink -> white (255) on black (0)."""
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # drop single-pixel noise that would create spurious projection peaks
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    return bw


def _runs(profile, on_thresh, merge_gap):
    """Return [start, end] index runs where profile > on_thresh, merging runs
    separated by a gap smaller than merge_gap."""
    on = profile > on_thresh
    runs, start = [], None
    for i, v in enumerate(on):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append([start, i - 1])
            start = None
    if start is not None:
        runs.append([start, len(on) - 1])
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] - 1 < merge_gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return merged


def segment_lines(bgr, min_height_frac=0.25, char_merge_frac=0.22):
    """
    Split a page into character boxes grouped into reading order, using
    projection profiles (robust to Devanagari's disconnected strokes — a single
    character is often several connected components, so we group all ink in a
    column-range into one glyph and split only at whitespace).

    Args:
        bgr: page image, BGR (H,W,3) or grayscale (H,W).
        min_height_frac: drop detected lines shorter than this fraction of the
            median line height (kills stray noise bands).
        char_merge_frac: column gaps smaller than this fraction of the line
            height are treated as intra-character (strokes of one glyph); larger
            gaps split characters.

    Returns:
        list of lines; each line is a list of (x, y, w, h) boxes sorted
        left-to-right; lines themselves sorted top-to-bottom.
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) if bgr.ndim == 3 else bgr
    bw = _binarize(gray)
    ink = (bw > 0).astype(np.int32)
    H, W = ink.shape

    # --- line segmentation: horizontal projection (ink per row) ---
    row_profile = ink.sum(axis=1)
    line_bands = _runs(row_profile, on_thresh=max(1, int(0.005 * W)),
                       merge_gap=max(2, int(0.01 * H)))
    if not line_bands:
        return []
    med_lh = float(np.median([b[1] - b[0] + 1 for b in line_bands]))
    line_bands = [b for b in line_bands if (b[1] - b[0] + 1) >= min_height_frac * med_lh]

    lines = []
    for (y0, y1) in line_bands:
        lh = y1 - y0 + 1
        strip = ink[y0:y1 + 1, :]
        # --- character segmentation within the line: vertical projection ---
        col_profile = strip.sum(axis=0)
        char_runs = _runs(col_profile, on_thresh=0,
                          merge_gap=max(2, int(char_merge_frac * lh)))
        char_runs = [r for r in char_runs if (r[1] - r[0] + 1) >= 0.05 * lh]
        boxes = []
        for (x0, x1) in char_runs:
            # tighten the vertical extent to the ink actually in this column range
            sub = ink[y0:y1 + 1, x0:x1 + 1]
            rows = np.where(sub.sum(axis=1) > 0)[0]
            if rows.size == 0:
                continue
            ty0, ty1 = y0 + int(rows[0]), y0 + int(rows[-1])
            boxes.append((x0, ty0, x1 - x0 + 1, ty1 - ty0 + 1))
        if boxes:
            lines.append(boxes)
    return lines


def segment_line_boxes(bgr, **kwargs):
    """Whole-LINE bounding boxes for word/line-level OCR (e.g. word-level TrOCR).

    The CRNN path needs per-character boxes (segment_lines), but a sequence model
    like word-level TrOCR reads a whole line at once and does its own internal
    character/matra handling — so it wants ONE crop per text line, not per glyph.
    This collapses each line's character boxes into their union bounding box.

    Crucially this avoids the headline (शिरोरेखा) problem that breaks per-character
    segmentation on joined writing: we never try to split letters within a word,
    we just isolate the line and let the model read it.

    Returns: list of (x, y, w, h) line boxes, top-to-bottom.
    """
    boxes = []
    for line in segment_lines(bgr, **kwargs):
        x0 = min(b[0] for b in line)
        y0 = min(b[1] for b in line)
        x1 = max(b[0] + b[2] for b in line)
        y1 = max(b[1] + b[3] for b in line)
        boxes.append((x0, y0, x1 - x0, y1 - y0))
    return boxes


def crop_glyph(gray_or_bgr, box, pad_frac=0.0):
    """Crop one character box for the CRNN.

    DHCD glyphs fill the frame (almost no margin), and the model is sensitive to
    extra whitespace — empirically a TIGHT crop to the ink bounding box scores
    best (adding even ~5% padding drops accuracy sharply), so pad_frac defaults
    to 0. The kwarg is kept for experimentation."""
    x, y, w, h = box
    crop = gray_or_bgr[y:y + h, x:x + w]
    if pad_frac <= 0:
        return crop
    pad = int(round(max(w, h) * pad_frac))
    border = 255 if crop.ndim == 2 else (255, 255, 255)
    return cv2.copyMakeBorder(crop, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=border)


def annotate(bgr, lines):
    """Draw the detected character boxes on a copy of the page (for the UI)."""
    vis = bgr.copy() if bgr.ndim == 3 else cv2.cvtColor(bgr, cv2.COLOR_GRAY2BGR)
    for line in lines:
        for (x, y, w, h) in line:
            cv2.rectangle(vis, (x, y), (x + w, y + h), (80, 70, 230), 2)
    return vis
