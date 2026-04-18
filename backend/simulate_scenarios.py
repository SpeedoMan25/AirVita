import joblib
import numpy as np
from pathlib import Path

# Paths
MODEL_DIR = Path(__file__).parent / "model"
MODEL_PATH = MODEL_DIR / "mlp_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"

# Scoring Constants (Matching main.py)
COEFF_MLP_BASE = 1.0
COEFF_VOC = -0.02
COEFF_PARTICLES = -0.05
BIAS = 0.0

def calculate_final_iaq(base_score: float, vocs: float, particulates: float) -> int:
    score = (base_score * COEFF_MLP_BASE) + (vocs * COEFF_VOC) + (particulates * COEFF_PARTICLES) + BIAS
    return int(max(1, min(99, round(score))))

def simulate():
    print("--- RoomPulse Scenario Simulation ---")
    
    if not MODEL_PATH.exists():
        print("Error: Model not found. Please run train_model.py first.")
        return

    # Load artifacts
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    # Scenarios (humidity, pressure, light, temperature, sound_high, sound_mid, sound_low, sound_amp, vocs, particulates)
    scenarios = [
        {
            "name": "Ideal Spring Day",
            "data": [45.0, 1013.0, 500.0, 22.0, 10.0, 15.0, 20.0, 15.0],
            "vocs": 50.0,
            "particulates": 5.0
        },
        {
            "name": "California Wildfire (Smoke)",
            "data": [15.0, 1005.0, 200.0, 35.0, 10.0, 15.0, 20.0, 15.0],
            "vocs": 800.0,
            "particulates": 250.0
        },
        {
            "name": "Loud Classroom / Party",
            "data": [55.0, 1010.0, 800.0, 26.0, 80.0, 90.0, 70.0, 85.0],
            "vocs": 400.0,
            "particulates": 20.0
        },
        {
            "name": "Stuffy Basement (High Humid/VOC)",
            "data": [85.0, 1015.0, 50.0, 18.0, 5.0, 5.0, 5.0, 5.0],
            "vocs": 1200.0,
            "particulates": 10.0
        }
    ]

    print(f"{'Scenario':<30} | {'Base MLP':<10} | {'VOC/PM':<10} | {'Final IAQ':<10}")
    print("-" * 75)

    for s in scenarios:
        # 1. MLP Base Prediction
        features = np.array(s["data"]).reshape(1, -1)
        scaled = scaler.transform(features)
        base_score = float(model.predict(scaled)[0])

        # 2. Hybrid Scoring
        final_score = calculate_final_iaq(base_score, s["vocs"], s["particulates"])

        contaminants = f"{int(s['vocs'])}/{int(s['particulates'])}"
        print(f"{s['name']:<30} | {base_score:>10.2f} | {contaminants:>10} | {final_score:>10}")

if __name__ == "__main__":
    simulate()
