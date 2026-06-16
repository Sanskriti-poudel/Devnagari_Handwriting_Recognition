"""
Lightweight web app for the Devanagari OCR demo (HTML/CSS/JS frontend, Flask backend).

Serves one attractive page and a small JSON API backed by the REAL trained CRNN
(no mock). Self-contained: no npm, no separate backend, no branch merge.

Run from the repo root:
    python webapp/server.py
Then open http://localhost:8000

Endpoints:
    GET  /              -> the web page
    POST /api/predict   -> multipart "image" -> {glyph, translit, class, confidence, time_ms, processed}
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

app = Flask(__name__, template_folder="templates", static_folder="static")

# import the real CRNN predictor (loads + caches the model on first call)
from models.crnn.predict import predict as crnn_predict


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
    return render_template("index.html")


@app.route("/api/predict", methods=["POST"])
def api_predict():
    file = request.files.get("image")
    if file is None:
        return jsonify({"error": "No image uploaded."}), 400
    data = np.frombuffer(file.read(), np.uint8)
    bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if bgr is None:
        return jsonify({"error": "Could not read that image."}), 400
    return jsonify(_recognize(bgr))


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
