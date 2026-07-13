import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from main import app

client = TestClient(app).__enter__()


def _devanagari_font(size=36):
    for p in (r"C:\Windows\Fonts\Nirmala.ttf", r"C:\Windows\Fonts\mangal.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _text_image_bytes(text):
    img = Image.new("L", (500, 80), color=255)
    draw = ImageDraw.Draw(img)
    draw.text((10, 15), text, fill=0, font=_devanagari_font())
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _blank_image_bytes():
    img = Image.new("L", (200, 80), color=255)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_document_single_image():
    data = _text_image_bytes("नेपाल सरकार")
    r = client.post("/document", files={"file": ("doc.png", data, "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["doc_id"]
    assert body["engine"] in ("word-trocr", "crnn-chars")
    assert body["num_pages"] == 1
    assert "text" in body
    assert len(body["pages"]) == 1


def test_document_multipage_pdf():
    import fitz  # PyMuPDF

    page1 = _text_image_bytes("पहिलो पाना")
    page2 = _text_image_bytes("दोस्रो पाना")
    doc = fitz.open()
    for png_bytes in (page1, page2):
        img_doc = fitz.open(stream=png_bytes, filetype="png")
        pdf_bytes = img_doc.convert_to_pdf()
        img_pdf = fitz.open("pdf", pdf_bytes)
        doc.insert_pdf(img_pdf)
    pdf_bytes = doc.tobytes()
    doc.close()

    r = client.post("/document", files={"file": ("doc.pdf", pdf_bytes, "application/pdf")})
    assert r.status_code == 200
    body = r.json()
    assert body["num_pages"] == 2
    assert len(body["pages"]) == 2


def test_document_no_text_detected():
    data = _blank_image_bytes()
    r = client.post("/document", files={"file": ("blank.png", data, "image/png")})
    assert r.status_code == 400


def test_document_bad_upload():
    r = client.post("/document", files={"file": ("bad.png", b"not an image", "image/png")})
    assert r.status_code == 400


def test_export_txt():
    r = client.post("/export", json={"format": "txt", "text": "नमस्ते"})
    assert r.status_code == 200
    assert r.content.decode("utf-8") == "नमस्ते"


def test_export_docx():
    r = client.post("/export", json={"format": "docx", "text": "नमस्ते"})
    assert r.status_code == 200
    assert len(r.content) > 0


def test_export_pdf_missing_doc_id():
    r = client.post("/export", json={"format": "pdf", "text": "नमस्ते"})
    assert r.status_code == 410


def test_export_pdf_with_doc_id():
    data = _text_image_bytes("नेपाल सरकार")
    doc_r = client.post("/document", files={"file": ("doc.png", data, "image/png")})
    doc_id = doc_r.json()["doc_id"]

    r = client.post("/export", json={"format": "pdf", "text": "नेपाल सरकार", "doc_id": doc_id})
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


def test_export_unknown_format():
    r = client.post("/export", json={"format": "xml", "text": "x"})
    assert r.status_code == 400
