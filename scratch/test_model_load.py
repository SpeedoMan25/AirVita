import joblib
from pathlib import Path

MODEL_DIR = Path("backend/model")
MODEL_PATH = MODEL_DIR / "mlp_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"

try:
    print(f"Loading model from {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully")
    print(f"Loading scaler from {SCALER_PATH}")
    scaler = joblib.load(SCALER_PATH)
    print("Scaler loaded successfully")
except Exception as e:
    print(f"Error: {e}")
