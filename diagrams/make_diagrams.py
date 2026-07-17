"""
Black-and-white system-design diagrams for the Devanagari OCR Final Defense Report (Section 3.13).

Notation matches the project PROPOSAL (Figures 3-4 .. 3-8):
  * plain single-border rectangles for external entities / terminators
  * a circle for the system process (context / DFD level 0)
  * rounded-rectangle numbered processes + DB-cylinder data stores (DFD level 1)
  * stick-figure actors
  * Chen-style ER: entity rectangles with a title bar + bulleted attribute list,
    joined by diamonds carrying the relationship name and 1 : N cardinality
  * sequence diagram with activation boxes straddling the lifelines

Generates (pure black-on-white, print-safe):
  1. context_diagram.png      (Fig 3-1)
  2. dfd_level0.png           (Fig 3-2)
  3. dfd_level1.png           (Fig 3-3)
  4. use_case_diagram.png     (Fig 3-4)
  5. er_diagram.png           (Fig 3-5)
  6. sequence_diagram.png     (Fig 3-6)

Run:  python make_diagrams.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Ellipse, FancyArrowPatch, Circle, Arc, Polygon
from matplotlib.lines import Line2D
import os

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "text.color": "black",
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
})
BLACK = "black"
WHITE = "white"
OUT = os.path.dirname(os.path.abspath(__file__))


def canvas(xlim, ylim, scale=11.0):
    fig, ax = plt.subplots(figsize=(xlim / scale, ylim / scale), dpi=200)
    ax.set_xlim(0, xlim)
    ax.set_ylim(0, ylim)
    ax.axis("off")
    ax.set_aspect("equal", adjustable="box")
    return fig, ax


# ---------- primitive shapes ----------
def box(ax, cx, cy, w, h, text, fs=10, lw=1.4):
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, ec=BLACK, fc=WHITE, lw=lw))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs)


def rbox(ax, cx, cy, w, h, text, fs=9, lw=1.4):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.02,rounding_size=1.6",
                                ec=BLACK, fc=WHITE, lw=lw))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs)


def circ(ax, cx, cy, r, text, fs=9, lw=1.4):
    ax.add_patch(Circle((cx, cy), r, ec=BLACK, fc=WHITE, lw=lw))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs)


def _rrect(ax, cx, cy, w, h, lw=1.4):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.02,rounding_size=1.4",
                                ec=BLACK, fc=WHITE, lw=lw))


def pbox(ax, cx, cy, w, h, title, sub=None, tfs=8.5):
    """Plain pipeline box: bold title, optional smaller sub-line."""
    _rrect(ax, cx, cy, w, h)
    if sub:
        ax.text(cx, cy + 2, title, ha="center", va="center", fontsize=tfs, fontweight="bold")
        ax.text(cx, cy - 3.2, sub, ha="center", va="center", fontsize=tfs - 1.8)
    else:
        ax.text(cx, cy, title, ha="center", va="center", fontsize=tfs, fontweight="bold")


def dbox(ax, cx, cy, w, h, title, bullets, tfs=8.5, bfs=7):
    """Detail box: bold title, divider rule, left-aligned bulleted list."""
    _rrect(ax, cx, cy, w, h)
    top = cy + h / 2
    ax.text(cx, top - 3.2, title, ha="center", va="center", fontsize=tfs, fontweight="bold")
    ax.add_line(Line2D([cx - w / 2 + 2.5, cx + w / 2 - 2.5], [top - 6, top - 6],
                       color="#555555", lw=0.8))
    yb = top - 9.8
    for b in bullets:
        ax.text(cx - w / 2 + 3, yb, "• " + b, ha="left", va="center", fontsize=bfs)
        yb -= 4.6


def pipe(ax, cy, items, x0=6, gap=4):
    """Draw a left-to-right box pipeline; items carry their own kind/size."""
    x = x0
    prev_r = None
    for it in items:
        w, h = it["w"], it["h"]
        cx = x + w / 2
        if prev_r is not None:
            arrow(ax, (prev_r, cy), (x, cy))
        if it["kind"] == "plain":
            pbox(ax, cx, cy, w, h, it["title"], it.get("sub"), tfs=it.get("tfs", 8.5))
        else:
            dbox(ax, cx, cy, w, h, it["title"], it["bullets"], bfs=it.get("bfs", 7))
        prev_r = x + w
        x = prev_r + gap
    return x


def cylinder(ax, cx, cy, w, h, dlabel, caption, fs=8):
    rx, eh = w / 2, h * 0.22
    top, bot = cy + h / 2 - eh / 2, cy - h / 2 + eh / 2
    ax.add_line(Line2D([cx - rx, cx - rx], [bot, top], color=BLACK, lw=1.3))
    ax.add_line(Line2D([cx + rx, cx + rx], [bot, top], color=BLACK, lw=1.3))
    ax.add_patch(Arc((cx, bot), w, eh, theta1=180, theta2=360, ec=BLACK, lw=1.3))
    ax.add_patch(Ellipse((cx, top), w, eh, ec=BLACK, fc=WHITE, lw=1.3))
    ax.text(cx, cy - eh * 0.3, dlabel, ha="center", va="center", fontsize=fs, fontweight="bold")
    if caption:
        ax.text(cx, bot - eh - 2.5, caption, ha="center", va="top", fontsize=7)


def actor(ax, cx, cy, label, s=1.0):
    ax.add_patch(Circle((cx, cy + 6 * s), 2.1 * s, ec=BLACK, fc=WHITE, lw=1.3))
    ax.add_line(Line2D([cx, cx], [cy + 3.9 * s, cy - 2 * s], color=BLACK, lw=1.3))
    ax.add_line(Line2D([cx - 4 * s, cx + 4 * s], [cy + 1.5 * s, cy + 1.5 * s], color=BLACK, lw=1.3))
    ax.add_line(Line2D([cx, cx - 3.5 * s], [cy - 2 * s, cy - 8 * s], color=BLACK, lw=1.3))
    ax.add_line(Line2D([cx, cx + 3.5 * s], [cy - 2 * s, cy - 8 * s], color=BLACK, lw=1.3))
    ax.text(cx, cy - 11.5 * s, label, ha="center", va="center", fontsize=9)


def arrow(ax, p0, p1, text=None, fs=8, dashed=False, lw=1.3, above=2.2, ha="center"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=12, color=BLACK,
                                 lw=lw, shrinkA=1, shrinkB=1,
                                 linestyle=("dashed" if dashed else "solid")))
    if text:
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + above
        ax.text(mx, my, text, ha=ha, va="center", fontsize=fs)


def line(ax, p0, p1, lw=1.2, dashed=False):
    ax.add_line(Line2D([p0[0], p1[0]], [p0[1], p1[1]], color=BLACK, lw=lw,
                       linestyle=((0, (4, 3)) if dashed else "solid")))


def caption(ax, x, y, t):
    ax.text(x, y, t, ha="center", va="top", fontsize=11, fontstyle="italic")


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, bbox_inches="tight", pad_inches=0.2, facecolor="white")
    plt.close(fig)
    print("wrote", p)


# ------------------------------------------------------------------ 1. CONTEXT
def context_diagram():
    fig, ax = canvas(150, 56)
    box(ax, 20, 32, 24, 14, "User", fs=11)
    circ(ax, 76, 32, 14, "OCR\nSystem", fs=10)
    box(ax, 126, 32, 28, 15, "Unicode\nDevanagari Text", fs=9)
    arrow(ax, (32.5, 32), (61.5, 32), "Scanned document / PDF", fs=8, above=3.5)
    arrow(ax, (90.5, 32), (111.5, 32), "Unicode text", fs=8, above=3.5)
    caption(ax, 75, 9, "Figure 3-1: Context Diagram")
    save(fig, "context_diagram.png")


# ------------------------------------------------------------------ 2. DFD L0
def dfd_level0():
    fig, ax = canvas(135, 90)
    box(ax, 20, 64, 24, 14, "User", fs=11)
    circ(ax, 78, 64, 14, "0\nDevanagari\nOCR System", fs=9)
    cylinder(ax, 78, 27, 36, 15, "", "Model checkpoints / recognized-text store", fs=8)
    arrow(ax, (32.5, 68), (63.5, 68), "Document (image / PDF)", fs=8, above=3.5)
    arrow(ax, (63.5, 60), (32.5, 60), "Unicode text", fs=8, above=3.5)
    # process <-> store (read / write)
    ax.add_patch(FancyArrowPatch((78, 50), (78, 35.5), arrowstyle="<|-|>", mutation_scale=12, color=BLACK, lw=1.3))
    ax.text(80.5, 43, "read / write", fontsize=8, ha="left")
    caption(ax, 67, 8, "Figure 3-2: Data Flow Diagram — Level 0")
    save(fig, "dfd_level0.png")


# ------------------------------------------------------------------ 3. DFD L1
def dfd_level1():
    fig, ax = canvas(152, 90)
    ys = 62
    actor(ax, 9, ys, "User")
    procs = [(36, "1.0\nPre-process"), (64, "2.0\nLine\nSegmentation"),
             (92, "3.0\nText\nRecognition"), (120, "4.0\nUnicode\nPost-processing")]
    for x, t in procs:
        rbox(ax, x, ys, 20, 15, t, fs=8.5)
    # input + pipeline flows (labels centred over each arrow, clear of the boxes)
    arrow(ax, (13.5, ys), (25.5, ys), "scanned\ndocument", fs=7, above=4)
    arrow(ax, (46.5, ys), (53.5, ys), "clean\nimage", fs=7, above=4)
    arrow(ax, (74.5, ys), (81.5, ys), "line\ncrops", fs=7, above=4)
    arrow(ax, (102.5, ys), (109.5, ys), "raw\ntext", fs=7, above=4)
    # output flow routed above, back to the User
    topy = 82
    line(ax, (120, ys + 7.5), (120, topy))
    line(ax, (120, topy), (9, topy))
    ax.add_patch(FancyArrowPatch((9, topy), (9, ys + 8.2), arrowstyle="-|>", mutation_scale=12, color=BLACK, lw=1.3))
    ax.text(64, topy + 2.5, "NFC-normalized Unicode text (TXT / DOCX / searchable PDF)", ha="center", fontsize=8)
    # data stores (cylinders) below their process
    cylinder(ax, 64, 26, 20, 14, "D1", "Character + synthetic\nline datasets", fs=8)
    cylinder(ax, 92, 26, 20, 14, "D2", "Trained checkpoints\n(CRNN / TrOCR)", fs=8)
    cylinder(ax, 120, 26, 20, 14, "D3", "Recognized-text\ndatabase", fs=8)
    arrow(ax, (64, 33), (64, ys - 7.6), fs=7)
    ax.text(65.6, 46, "training\ndata", fontsize=7, ha="left")
    arrow(ax, (92, 33), (92, ys - 7.6), fs=7)
    ax.text(93.6, 46, "model\nweights", fontsize=7, ha="left")
    ax.add_patch(FancyArrowPatch((120, ys - 7.6), (120, 33), arrowstyle="-|>", mutation_scale=12, color=BLACK, lw=1.3))
    ax.text(121.6, 46, "store\ntext", fontsize=7, ha="left")
    caption(ax, 72, 6, "Figure 3-3: Data Flow Diagram — Level 1")
    save(fig, "dfd_level1.png")


# ------------------------------------------------------------------ 4. USE CASE
def use_case_diagram():
    fig, ax = canvas(120, 116)
    ax.add_patch(Rectangle((32, 10), 52, 96, ec=BLACK, fc="none", lw=1.5))
    ax.text(58, 101, "Devanagari OCR / Digitizer System", ha="center", fontsize=10, fontweight="bold")
    actor(ax, 13, 58, "User", s=1.15)
    actor(ax, 104, 58, "System\n(Backend)", s=1.15)
    ucs = [(58, 90, "Upload document (image / PDF)"),
           (58, 79, "View recognized Unicode text"),
           (58, 68, "Edit recognized text"),
           (58, 57, "Export TXT / DOCX / PDF"),
           (58, 46, "Preeti ↔ Unicode convert"),
           (58, 35, "Romanized typing aid"),
           (58, 22, "Select model / view history")]
    for x, y, t in ucs:
        ax.add_patch(Ellipse((x, y), 44, 8.5, ec=BLACK, fc=WHITE, lw=1.3))
        ax.text(x, y, t, ha="center", va="center", fontsize=8)
    for _, y, _ in ucs[:6]:
        line(ax, (18, 58), (36.5, y), lw=1.0)
    line(ax, (18, 58), (36.5, 22), lw=1.0)          # user -> history
    line(ax, (99, 58), (79.5, 22), lw=1.0)          # system -> history
    line(ax, (99, 58), (79.5, 57), lw=1.0)          # system -> export/recognition
    caption(ax, 58, 6, "Figure 3-4: Use Case Diagram")
    save(fig, "use_case_diagram.png")


# ------------------------------------------------------------------ 5. ER (Chen-style)
def er_diagram():
    fig, ax = canvas(130, 78)

    def entity(cx, cy, name, attrs):
        w, rh = 44, 5.6
        h = rh * (len(attrs) + 1)
        top = cy + h / 2
        ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, ec=BLACK, fc=WHITE, lw=1.5))
        ax.add_patch(Rectangle((cx - w / 2, top - rh), w, rh, ec=BLACK, fc=WHITE, lw=1.5))
        ax.text(cx, top - rh / 2, name, ha="center", va="center", fontsize=9, fontweight="bold")
        for i, a in enumerate(attrs):
            yy = top - rh * (i + 1) - rh / 2
            ax.text(cx - w / 2 + 3, yy, "• " + a, ha="left", va="center", fontsize=7.5,
                    fontstyle=("italic" if a.endswith("(FK)") else "normal"),
                    fontweight=("bold" if "(PK)" in a else "normal"))
        return w, h

    e1 = ["Document_ID (PK)", "Original_Filename", "File_Path", "Upload_Date"]
    e2 = ["Text_ID (PK)", "Model_Used", "Recognized_Text", "Confidence_Score",
          "Processing_Time", "Created_At", "Document_ID (FK)"]
    entity(28, 46, "DOCUMENT_IMAGE", e1)
    entity(102, 42, "RECOGNIZED_TEXT", e2)
    # diamond relationship with 1 : N cardinality
    dx, dy = 65, 46
    ax.add_patch(Polygon([(dx - 10, dy), (dx, dy + 6), (dx + 10, dy), (dx, dy - 6)],
                         closed=True, ec=BLACK, fc=WHITE, lw=1.4))
    ax.text(dx, dy, "Produces", ha="center", va="center", fontsize=8)
    line(ax, (50, 46), (55, 46))
    line(ax, (75, 46), (80, 42.5))
    ax.text(52.5, 48.3, "1", fontsize=9, fontweight="bold", ha="center")
    ax.text(78, 44.8, "N", fontsize=9, fontweight="bold", ha="center")
    caption(ax, 65, 8, "Figure 3-5: Entity Relationship Diagram")
    save(fig, "er_diagram.png")


# ------------------------------------------------------------------ 6. SEQUENCE
def sequence_diagram():
    fig, ax = canvas(156, 150)
    cols = {"User": 12, "Web\nInterface": 33, "Pre-\nprocessing": 55,
            "Line\nSegmentation": 78, "Text\nRecognition": 101,
            "Post-\nprocessing": 123, "Database": 143}
    top, bot = 132, 18
    for name, x in cols.items():
        box(ax, x, top + 5, 17, 8, name, fs=7.5)
        line(ax, (x, top), (x, bot), dashed=True)
    K = list(cols.keys())

    def msg(y, a, b, text, dashed=False, fs=7.5):
        x0, x1 = cols[K[a]], cols[K[b]]
        ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=11,
                                     color=BLACK, lw=1.2, linestyle=("dashed" if dashed else "solid")))
        ax.text((x0 + x1) / 2, y + 2.2, text, ha="center", fontsize=fs)

    def act(y, a, text):  # activation box straddling a lifeline, label inside
        x = cols[K[a]]
        ax.add_patch(Rectangle((x - 8, y - 4), 16, 8, ec=BLACK, fc=WHITE, lw=1.2))
        ax.text(x, y, text, ha="center", va="center", fontsize=6.4)

    y, step = 124, 9
    msg(y, 0, 1, "upload document (image / PDF)"); y -= step
    msg(y, 1, 2, "send image"); y -= step
    act(y, 2, "grayscale, denoise\nthreshold, deskew"); y -= step
    msg(y, 2, 3, "preprocessed image"); y -= step
    act(y, 3, "detect line boxes"); y -= step
    msg(y, 3, 4, "line crops"); y -= step
    act(y, 4, "recognize\n(CRNN / TrOCR)"); y -= step
    msg(y, 4, 5, "raw recognized text"); y -= step
    act(y, 5, "NFC normalize"); y -= step
    msg(y, 5, 6, "persist recognized text"); y -= step
    msg(y, 5, 1, "final text + line boxes", dashed=True); y -= step
    msg(y, 1, 0, "display / edit / export", dashed=True)
    caption(ax, 78, 10, "Figure 3-6: Sequence Diagram (Document Recognition)")
    save(fig, "sequence_diagram.png")


# ------------------------------------------------------------------ 7. CRNN ARCH
def crnn_architecture():
    fig, ax = canvas(230, 74, scale=13.0)
    cy = 36
    ax.text(115, 70, "Proposed CRNN-Based OCR Architecture",
            ha="center", va="top", fontsize=13, fontweight="bold")
    items = [
        {"kind": "plain", "w": 24, "h": 18, "title": "Input Image", "sub": "(64×64 Grayscale\nCharacter)"},
        {"kind": "detail", "w": 30, "h": 40, "title": "Image Preprocessing",
         "bullets": ["Grayscale Conversion", "Gaussian Blur", "Adaptive Thresholding",
                     "Skew Correction", "Normalization"]},
        {"kind": "detail", "w": 26, "h": 28, "title": "CNN Feature Extractor",
         "bullets": ["Convolution Layers", "ReLU", "Max Pooling"]},
        {"kind": "plain", "w": 20, "h": 13, "title": "Feature\nSequence"},
        {"kind": "plain", "w": 20, "h": 13, "title": "Bidirectional\nLSTM"},
        {"kind": "plain", "w": 22, "h": 13, "title": "Fully Connected\nLayer"},
        {"kind": "detail", "w": 22, "h": 20, "title": "CTC Decoder",
         "bullets": ["CTC Loss", "Greedy Decoding"]},
        {"kind": "plain", "w": 26, "h": 18, "title": "Predicted Unicode\nDevanagari Character", "tfs": 8},
    ]
    pipe(ax, cy, items, x0=6, gap=4)
    save(fig, "crnn_architecture.png")


# ------------------------------------------------------------------ 8. TrOCR ARCH
def trocr_architecture():
    fig, ax = canvas(244, 74, scale=13.0)
    cy = 36
    ax.text(122, 70, "Proposed TrOCR-Based OCR Architecture",
            ha="center", va="top", fontsize=13, fontweight="bold")
    items = [
        {"kind": "plain", "w": 26, "h": 18, "title": "Input Image", "sub": "(Character / Word /\nDocument Line)"},
        {"kind": "detail", "w": 28, "h": 26, "title": "Image Preprocessing",
         "bullets": ["Resize", "Normalization", "Background Correction"]},
        {"kind": "plain", "w": 20, "h": 13, "title": "Patch\nEmbedding"},
        {"kind": "plain", "w": 24, "h": 15, "title": "Vision Transformer", "sub": "(ViT Encoder)"},
        {"kind": "plain", "w": 24, "h": 13, "title": "Image Feature\nEmbeddings", "tfs": 8},
        {"kind": "detail", "w": 36, "h": 26, "title": "Transformer Decoder",
         "bullets": ["Self-Attention", "Cross-Attention", "Autoregressive Text Generation"], "bfs": 6.5},
        {"kind": "plain", "w": 24, "h": 15, "title": "Predicted Unicode\nNepali Text", "tfs": 8},
        {"kind": "detail", "w": 24, "h": 22, "title": "Output",
         "bullets": ["TXT", "DOCX", "Searchable PDF"]},
    ]
    pipe(ax, cy, items, x0=6, gap=4)
    save(fig, "trocr_architecture.png")


if __name__ == "__main__":
    context_diagram()
    dfd_level0()
    dfd_level1()
    use_case_diagram()
    er_diagram()
    sequence_diagram()
    crnn_architecture()
    trocr_architecture()
    print("All diagrams written to", OUT)
