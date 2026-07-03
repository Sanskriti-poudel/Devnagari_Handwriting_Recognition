import os
from dotenv import load_dotenv

load_dotenv()

DEVICE = os.getenv("DEVICE", "cpu")
CRNN_MODEL_PATH = os.getenv(
    "CRNN_MODEL_PATH",
    "../kaggle_output/artifacts/best_model.pth",
)
TRANSFORMER_MODEL_PATH = os.getenv(
    "TRANSFORMER_MODEL_PATH",
    "../models/trocr/checkpoints_words",
)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ocr_results.db")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tiff", "pdf"}
