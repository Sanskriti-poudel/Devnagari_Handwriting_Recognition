# Deployment Environment Variables

## Backend (Render)

These environment variables are required for the FastAPI backend deployed on Render.

| Key | Value | Notes |
|---|---|---|
| `DEVICE` | `cpu` | CPU inference |
| `CRNN_MODEL_PATH` | (empty) | Leave empty for mock mode. On local/Railway deployment, use: `C:/Users/Sanskriti Poudel/OneDrive/Desktop/Devnagari recognition/Devnagari_Handwriting_Recognition/kaggle_output/artifacts/best_model.pth` |
| `TRANSFORMER_MODEL_PATH` | (empty) | Leave empty for mock mode. On local/Railway deployment, use: `C:/Users/Sanskriti Poudel/OneDrive/Desktop/Devnagari recognition/Devnagari_Handwriting_Recognition/models/trocr/checkpoints_words` |
| `DATABASE_URL` | `sqlite:///./ocr_results.db` | SQLite database |
| `MAX_FILE_SIZE_MB` | `20` | Max upload file size in MB |
| `UPLOAD_DIR` | `./uploads` | Directory for uploaded files |
| `JWT_SECRET` | `dev-only-insecure-secret-change-me` | Change this to a random string in production |
| `JWT_EXPIRES_MINUTES` | `10080` | Token expiration (7 days) |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:5174,http://localhost:3000,https://devnagari-ocr.vercel.app` | Allowed CORS origins for the frontend |

## Frontend (Vercel)

The frontend uses a `.env` file for local development:

| Key | Value |
|---|---|
| `VITE_API_URL` | `http://localhost:8000` |
| `VITE_USE_MOCK_API` | `false` |

### vercel.json Rewrite Configuration

The Vercel frontend rewrites `/api/*` requests to the backend:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://devnagari-ocr-backend.onrender.com/api/:path*" }
  ]
}
```

## Live URLs

- **Frontend:** https://devnagari-ocr.vercel.app
- **Backend:** https://devnagari-ocr-backend.onrender.com

## Notes

- Since model files use local Windows absolute paths, the deployed backend runs in **mock mode** (no real OCR inference). Only the upload/upload flow is functional.
- For full OCR support on Render, upload model weights to cloud storage and update `CRNN_MODEL_PATH` and `TRANSFORMER_MODEL_PATH` to point to those files.
