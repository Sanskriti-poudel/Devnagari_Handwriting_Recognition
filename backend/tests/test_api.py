import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture()
def client():
    # TestClient must be used as a context manager for FastAPI's lifespan
    # (startup/shutdown) to actually run — otherwise create_tables() never
    # fires and every DB-backed route 500s with "no such table".
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/signup", json={"fullName": "Test User", "email": email, "password": "password123"})
    assert r.status_code == 200, r.text
    token = r.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}


def _sample_png_bytes():
    import numpy as np
    import cv2

    img = (np.ones((64, 64), dtype=np.uint8) * 255)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("operational", "degraded", "down")
    assert "models" in body


def test_models(client):
    r = client.get("/models")
    assert r.status_code == 200
    ids = [m["id"] for m in r.json()]
    assert "crnn" in ids
    assert "transformer" in ids


def test_signup_then_duplicate_rejected(client):
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    r1 = client.post("/signup", json={"fullName": "A", "email": email, "password": "password123"})
    assert r1.status_code == 200
    r2 = client.post("/signup", json={"fullName": "A", "email": email, "password": "password123"})
    assert r2.status_code == 400


def test_login_wrong_password(client):
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/signup", json={"fullName": "A", "email": email, "password": "password123"})
    r = client.post("/login", json={"email": email, "password": "wrong"})
    assert r.status_code == 401


def test_login_correct_password(client):
    email = f"login2_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/signup", json={"fullName": "A", "email": email, "password": "password123"})
    r = client.post("/login", json={"email": email, "password": "password123"})
    assert r.status_code == 200
    assert r.json()["user"]["email"] == email


def test_history_requires_auth(client):
    r = client.get("/history")
    assert r.status_code == 401


def test_document_ocr_persists_and_lists_in_history(client, auth_headers):
    r = client.post(
        "/api/document",
        headers=auth_headers,
        files={"image": ("sample.png", _sample_png_bytes(), "image/png")},
        data={"model": "crnn"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "text" in body and "avg_confidence" in body and "num_chars" in body

    hist = client.get("/history", headers=auth_headers, params={"page": 1, "pageSize": 10})
    assert hist.status_code == 200
    hist_body = hist.json()
    assert hist_body["total"] >= 1
    assert hist_body["items"][0]["fileName"] == "sample.png"


def test_document_ocr_rejects_bad_extension(client, auth_headers):
    r = client.post(
        "/api/document",
        headers=auth_headers,
        files={"image": ("bad.exe", b"data", "application/octet-stream")},
        data={"model": "crnn"},
    )
    assert r.status_code == 400


def test_history_delete(client, auth_headers):
    client.post(
        "/api/document",
        headers=auth_headers,
        files={"image": ("delete_me.png", _sample_png_bytes(), "image/png")},
        data={"model": "crnn"},
    )
    hist = client.get("/history", headers=auth_headers, params={"page": 1, "pageSize": 10}).json()
    item_id = hist["items"][0]["id"]

    r = client.delete(f"/history/{item_id}", headers=auth_headers)
    assert r.status_code == 200

    r2 = client.delete(f"/history/{item_id}", headers=auth_headers)
    assert r2.status_code == 404


def test_dashboard_stats_and_activity(client, auth_headers):
    client.post(
        "/api/document",
        headers=auth_headers,
        files={"image": ("stats.png", _sample_png_bytes(), "image/png")},
        data={"model": "crnn"},
    )
    stats = client.get("/dashboard/stats", headers=auth_headers)
    assert stats.status_code == 200
    assert stats.json()["totalDocuments"] >= 1

    activity = client.get("/dashboard/activity", headers=auth_headers)
    assert activity.status_code == 200
    assert isinstance(activity.json(), list)


def test_legacy_ocr_endpoint_still_works(client):
    r = client.post("/ocr", files={"file": ("sample.png", _sample_png_bytes(), "image/png")}, data={"model_name": "crnn"})
    assert r.status_code == 200
    body = r.json()
    assert "recognized_text" in body
    assert body["model_used"] == "crnn"


def test_history_not_found(client):
    r = client.get("/history/99999")
    assert r.status_code == 404
