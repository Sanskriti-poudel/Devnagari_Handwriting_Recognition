"""
Mid-defense demo — Devanagari Handwritten Character Recognition.

A simple Streamlit UI over the REAL trained CRNN baseline (no mock): upload or
pick a character image, see what the model was fed and what it predicted, plus
the project's evaluation results.

Run from the repo root:
    streamlit run demo/app.py

Needs: the CRNN weights (kaggle_output/artifacts/best_model.pth) and the test
images under Datasets/ for the "random sample" button. CPU is fine (~5 ms/image).
"""
import os
import sys
import glob
import json
import random

import cv2
import numpy as np
import streamlit as st

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "models", "crnn"))

from Preprocessing.preprocess import preprocess_array
from data.devanagari_labels import class_to_glyph, class_to_translit

LOGS = os.path.join(PROJECT_ROOT, "logs")
TEST_DIR = os.path.join(PROJECT_ROOT, "Datasets", "test")

st.set_page_config(page_title="Devanagari OCR — Demo", page_icon="🖋️", layout="wide")


# --------------------------------------------------------------------------- #
# Model (cached across reruns)
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner="Loading CRNN model…")
def get_predict():
    from models.crnn.predict import predict  # caches the model internally too
    return predict


def recognize(bgr_or_gray):
    """ndarray -> (glyph, translit, class_name, confidence, preprocessed_64x64)."""
    predict = get_predict()
    proc = preprocess_array(bgr_or_gray)          # (64,64) float [0,1]
    res = predict(proc, device="cpu")             # pass preprocessed array
    cls = res["text"]
    glyph = class_to_glyph(cls) if cls else "—"
    translit = class_to_translit(cls) if cls else ""
    return glyph, translit, cls or "(blank)", res["confidence"], proc


def show_prediction(bgr, source_caption):
    glyph, translit, cls, conf, proc = recognize(bgr)
    c1, c2, c3 = st.columns([1, 1, 1.3])
    with c1:
        st.caption(source_caption)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB) if bgr.ndim == 3 else bgr
        st.image(rgb, width=200)
    with c2:
        st.caption("What the model sees (preprocessed 64×64)")
        st.image((proc * 255).astype(np.uint8), width=200, clamp=True)
    with c3:
        st.caption("Prediction")
        st.markdown(
            f"<div style='font-size:96px;line-height:1.1'>{glyph}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**{translit or '—'}**  ·  `{cls}`")
        st.progress(min(max(conf, 0.0), 1.0), text=f"confidence {conf*100:.1f}%")


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.title("🖋️ Devanagari Handwritten Character Recognition")
st.markdown("##### देवनागरी हस्तलेख पहिचान — mid-defense demo")

with st.sidebar:
    st.header("About")
    st.markdown(
        "- **Model:** CRNN (CNN → BiLSTM → CTC) baseline, trained on the DHCD "
        "(46 classes — 36 consonants + 10 digits).\n"
        "- **Test accuracy:** **98.67%**.\n"
        "- Inference runs on **CPU** (~5 ms/image).\n"
        "- **TrOCR** Transformer comparison: pipeline fixed; awaiting a GPU re-run."
    )
    st.caption("Same preprocessing as training (no train/serve skew).")

tab_try, tab_results = st.tabs(["▶️  Try it", "📊  Results"])


# --------------------------------------------------------------------------- #
# Tab: Try it
# --------------------------------------------------------------------------- #
with tab_try:
    st.subheader("Recognize a character")
    left, right = st.columns(2)

    with left:
        st.markdown("**Upload an image** (a single handwritten Devanagari character)")
        up = st.file_uploader("PNG / JPG", type=["png", "jpg", "jpeg", "bmp"],
                              label_visibility="collapsed")
        if up is not None:
            data = np.frombuffer(up.read(), np.uint8)
            bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if bgr is None:
                st.error("Could not read that image.")
            else:
                show_prediction(bgr, f"Uploaded: {up.name}")

    with right:
        st.markdown("**…or try a random sample** from the held-out test set")
        if st.button("🎲  Pick a random test image", use_container_width=True):
            paths = glob.glob(os.path.join(TEST_DIR, "*", "*.png"))
            if not paths:
                st.warning(f"No test images found under {TEST_DIR}.")
            else:
                p = random.choice(paths)
                bgr = cv2.imread(p)
                true_cls = os.path.basename(os.path.dirname(p))
                show_prediction(bgr, f"True label: {class_to_glyph(true_cls)} ({class_to_translit(true_cls)})")


# --------------------------------------------------------------------------- #
# Tab: Results
# --------------------------------------------------------------------------- #
with tab_results:
    st.subheader("Evaluation (held-out test split)")

    eval_path = os.path.join(LOGS, "crnn_eval.json")
    if os.path.exists(eval_path):
        ev = json.load(open(eval_path))
        m = st.columns(4)
        m[0].metric("Accuracy", f"{ev['accuracy']*100:.2f}%")
        m[1].metric("CER", f"{ev['cer']:.4f}")
        m[2].metric("WER", f"{ev['wer']:.4f}")
        m[3].metric("Params", f"{ev['param_count']/1e6:.1f}M")
        st.caption(f"{ev['test_samples']:,} test samples · "
                   f"{ev['avg_inference_latency_ms']:.1f} ms/image ({ev['device']})")
    else:
        st.info("Run `python models/crnn/evaluate.py` to generate logs/crnn_eval.json.")

    st.divider()
    st.subheader("CRNN vs TrOCR comparison")
    cmp_md = os.path.join(LOGS, "comparison.md")
    if os.path.exists(cmp_md):
        st.markdown(open(cmp_md, encoding="utf-8").read())
    imgs = [os.path.join(LOGS, f) for f in ("comparison_metrics.png", "comparison_size.png")]
    cols = st.columns(2)
    for col, img in zip(cols, imgs):
        if os.path.exists(img):
            col.image(img, use_container_width=True)

    st.divider()
    st.subheader("Where the CRNN errs (qualitative analysis)")
    heat = os.path.join(LOGS, "crnn_confusion_heatmap.png")
    if os.path.exists(heat):
        st.image(heat, use_container_width=True,
                 caption="Confusions cluster in look-alike consonants (e.g. घ↔ध, द↔ढ).")
    ea = os.path.join(LOGS, "crnn_error_analysis.md")
    if os.path.exists(ea):
        with st.expander("Full error-analysis report"):
            st.markdown(open(ea, encoding="utf-8").read())
