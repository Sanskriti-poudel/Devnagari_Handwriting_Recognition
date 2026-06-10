# Project Plans — Devanagari Handwritten Document Recognition (OCR)

Task assignments for the three roles, broken into **step-by-step phases**. Read
[`.claude/skills.md`](../.claude/skills.md) first for the skills/tools each role needs.

## Files
- [`ml-developer-tasks.md`](./ml-developer-tasks.md) — data, models, evaluation, comparison.
- [`backend-developer-tasks.md`](./backend-developer-tasks.md) — inference API + storage.
- [`frontend-developer-tasks.md`](./frontend-developer-tasks.md) — React web app.

## Team → role mapping
| Member | Role |
|--------|------|
| Sanskriti Poudel | **ML** + Frontend |
| Chandan Dhakal | **ML** + Frontend |
| Savyata Poudel | **Backend** + Frontend |
| Bipin Jung Thapa | — (no assigned tasks) |

- **ML:** Sanskriti & Chandan (paired — heaviest workload, owns the comparative analysis).
- **Backend:** Savyata.
- **Frontend:** shared by all three active members (Sanskriti, Chandan, Savyata) after their primary deliverables are on track.

## Phases (aligned to the proposal's methodology, Ch. 3)
1. **Phase 0 — Setup & contracts (week 1):** repo structure, environments, and agree the
   two integration contracts (model artifact format + `/ocr` JSON schema) so all three
   roles can work in parallel against mocks.
2. **Phase 1 — Data & baseline:** ML builds preprocessing + CRNN baseline; backend/frontend
   build skeletons against a mock model.
3. **Phase 2 — Models & integration:** ML adds the Transformer pipeline; backend wires the
   real model; frontend connects to the real API.
4. **Phase 3 — Evaluation, polish, report:** comparative analysis (Accuracy/CER/WER),
   end-to-end testing, deployment, and the final report figures.

## The two contracts everyone must agree in Phase 0

**A. Model artifact (ML → Backend)**
```
artifacts/
  crnn/        model.pth (or .torchscript/.onnx), charset.json, preprocess.py, predict.py
  transformer/ model/ (HF dir or .pth), predict.py
predict.py exposes:  predict(image: np.ndarray) -> {"text": str, "confidence": float}
```

**B. API response (Backend → Frontend)** — `POST /ocr`
```json
{
  "text": "मेरो देश नेपाल",
  "confidence": 0.92,
  "model": "transformer",
  "regions": [{"bbox": [x, y, w, h], "text": "..."}],
  "processing_ms": 134
}
```
