# Devanagari OCR Quick Start Guide

**For demonstrations, handoffs, and quick reference**

---

## 🚀 5-Minute Demo Setup

```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Run the live demo server
KMP_DUPLICATE_LIB_OK=TRUE python webapp/server.py

# Open browser to: http://localhost:8000
```

**Demo Features:**
- 🎲 **Random sample testing** - Click "Random sample" for live recognition
- 📄 **Document processing** - Upload PDF/images for full document OCR
- 🔧 **Nepali tools** - Preeti↔Unicode converter, romanized typing
- 📥 **Export options** - Searchable PDF, DOCX, TXT downloads

---

## 📊 Key Numbers (One-Pager)

| Metric | CRNN | TrOCR |
|--------|------|-------|
| **Test Accuracy** | **98.67%** | Pending GPU run |
| **CER** | 0.0003 | Pending |
| **WER** | 0.0018 | Pending |
| **Parameters** | ~6.7M | ~124M (base) |
| **Inference Time** | ~5ms (CPU) | ~50ms (CPU) |
| **Training Time** | ~2h (T4 GPU) | ~4h (T4 GPU) |

**Dataset:** 92,000 images, 46 classes (36 consonants + 10 digits)

---

## 🏗️ Project Architecture (30-Second Overview)

```
Input → Preprocessing → Model → Recognition → Export
  ↓          ↓            ↓         ↓          ↓
Image  →  Grayscale   → CRNN/  → Devanagari  → TXT/
PDF      → Noise        TrOCR     Unicode      DOCX/
         → Threshold                            PDF
         → Deskew
         → Normalize
```

**Two Model Approaches:**
- **CRNN:** Traditional CNN → BiLSTM → CTC (baseline)
- **TrOCR:** Modern Transformer encoder-decoder (comparison)

---

## 📁 Key Files & Locations

**ML Components:**
- `data/preprocess.py` - Shared preprocessing pipeline
- `models/crnn/predict.py` - CRNN inference
- `models/trocr/predict.py` - TrOCR inference  
- `notebooks/kaggle_train_trocr.ipynb` - TrOCR training

**Backend:**
- `backend/main.py` - FastAPI application
- `backend/services/ocr.py` - OCR service logic
- `backend/ml_models/` - Model loading utilities

**Frontend:**
- `webapp/server.py` - Live demo server
- `frontend/src/App.jsx` - React application

**Documentation:**
- `docs/PROJECT_OVERVIEW.md` - Complete project description
- `docs/PROJECT_GUIDE.md` - Architecture & troubleshooting
- `docs/FINALIZATION_STATUS.md` - Current project status
- `docs/KAGGLE_TROCR_QUICKTEST_DEBUG_LOG.md` - Recent debugging

---

## 🎯 What Works Right Now ✅

**Immediately Available:**
1. **Character recognition** - 98.67% accuracy, live demo ready
2. **Document processing** - Multi-page PDF with searchable export
3. **Web interface** - Full offline demo with multiple tools
4. **Backend API** - Real model integration with database
5. **Training pipeline** - Complete and debugged

**Pending GPU Run:**
- TrOCR final training (2-4 hours on Kaggle T4)
- Word-level OCR enhancement (awaiting quota reset)

---

## 🔧 Common Commands

```bash
# Run tests
pytest backend/tests/

# Start backend API
cd backend && uvicorn main:app --reload

# Start React frontend  
cd frontend && npm run dev

# Database management
sqlite3 backend/ocr_database.db ".tables"

# GPU training (Kaggle)
kaggle kernels push -p notebooks/
```

---

## 🐛 Troubleshooting Quick Reference

**Issue:** "OSError: preprocessor_config.json"
**Solution:** Transformers version mismatch - pin to `transformers==5.13.1`

**Issue:** "CUDA error: no kernel image is available"
**Solution:** GPU compatibility - code falls back to CPU automatically

**Issue:** "Unicode rendering issues"
**Solution:** Ensure Noto Sans Devanagari font is loaded (included in webapp)

**Issue:** "Model loading failures"
**Solution:** Check `ml_models/` directory and verify checkpoint paths

**Full troubleshooting guide:** `docs/PROJECT_GUIDE.md` §5

---

## 📈 Demo Script (For Presentations)

1. **Introduction (1 min):**
   - Problem: Nepali documents can't be searched/edited
   - Solution: Deep learning OCR with Unicode output

2. **Character Demo (2 min):**
   - Click "🎲 Random sample" 3-4 times
   - Show confidence scores and ✓/✗ results
   - Explain: "98.67% accuracy on 46 character classes"

3. **Document Demo (2 min):**
   - Upload a sample PDF/image
   - Show editable Unicode output
   - Export as searchable PDF (Ctrl+F demo)

4. **Nepali Tools (1 min):**
   - Demonstrate Preeti↔Unicode converter
   - Show romanized typing feature

5. **Q&A:** Reference architecture and next steps

---

## 🎓 For Thesis/Report

**Key Results to Include:**
- CRNN: 98.67% accuracy, detailed confusion analysis
- Complete preprocessing pipeline with augmentation
- End-to-end system architecture and design
- Real-world application with live demo

**Next Steps for Complete Analysis:**
- TrOCR GPU training run (final comparison metrics)
- Word-level OCR enhancement (document processing)
- Performance optimization and deployment

---

## 📞 Team & Roles

| Member | Responsibility | Contact |
|--------|---------------|---------|
| **Sanskriti Poudel** | ML Lead, CRNN training | - |
| **Chandan Dhakal** | TrOCR, EDA, GPU debugging | - |
| **Savyata Poudel** | Backend API, Integration | - |
| **Bipin Jung Thapa** | Testing, Documentation | - |

---

## 🔐 Security & Deployment Notes

**Deployment Requirements:**
- Poppler for PDF processing (`apt-get install poppler-utils`)
- CUDA-capable GPU for optimal performance (CPU fallback available)
- Minimum 4GB RAM for document processing
- Python 3.8+ environment

**Production Considerations:**
- Database scaling for high-volume usage
- Caching for repeated document processing
- API rate limiting and authentication
- Log rotation and monitoring

---

## 📚 Further Reading

1. **Technical Deep Dive:** `docs/PROJECT_OVERVIEW.md`
2. **Architecture Details:** `docs/PROJECT_GUIDE.md`  
3. **Implementation Status:** `docs/REMAINING_WORK.md`
4. **Debugging History:** `docs/KAGGLE_TROCR_QUICKTEST_DEBUG_LOG.md`

---

**Last Updated:** 2026-07-16
**Project Status:** ✅ Production-ready for character recognition
**Next Milestone:** Complete TrOCR GPU training for final comparison

---

*This quick reference accompanies the comprehensive documentation in the docs/ directory*