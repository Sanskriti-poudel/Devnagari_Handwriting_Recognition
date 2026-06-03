import logging

logger = logging.getLogger(__name__)

# Holds loaded model objects keyed by name: {"crnn": <model>, "transformer": <model>}
# Populated at startup via FastAPI lifespan in main.py (Phase 2).
loaded_models: dict = {}


def load_all_models():
    """
    Load model artifacts from disk once at server startup.
    Fill in when the ML team delivers Contract A artifacts.
    """
    # Phase 2: uncomment and fill in with real model classes and paths
    # from config import CRNN_MODEL_PATH, TRANSFORMER_MODEL_PATH, DEVICE
    # import torch
    # try:
    #     from ml_package import CRNNModel
    #     model = CRNNModel(...)
    #     model.load_state_dict(torch.load(CRNN_MODEL_PATH, map_location=DEVICE))
    #     model.eval()
    #     loaded_models["crnn"] = model
    #     logger.info("CRNN model loaded")
    # except Exception as e:
    #     logger.warning(f"CRNN model not loaded: {e}")
    logger.info("Model loader called — no real artifacts yet (mock mode)")
