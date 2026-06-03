import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_models():
    r = client.get("/models")
    assert r.status_code == 200
    names = [m["name"] for m in r.json()]
    assert "crnn" in names
    assert "transformer" in names


def test_ocr_mock(tmp_path):
    import numpy as np
    import cv2
    img = (np.ones((64, 64), dtype=np.uint8) * 255)
    p = tmp_path / "sample.png"
    cv2.imwrite(str(p), img)
    with open(p, "rb") as f:
        r = client.post("/ocr", files={"file": ("sample.png", f, "image/png")}, data={"model_name": "crnn"})
    assert r.status_code == 200
    body = r.json()
    assert "recognized_text" in body
    assert "confidence" in body
    assert body["model_used"] == "crnn"


def test_ocr_bad_extension():
    r = client.post("/ocr", files={"file": ("bad.exe", b"data", "application/octet-stream")}, data={"model_name": "crnn"})
    assert r.status_code == 400


def test_history_not_found():
    r = client.get("/history/99999")
    assert r.status_code == 404
