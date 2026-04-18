from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import joblib
import numpy as np
import os
from pathlib import Path
from contextlib import asynccontextmanager

# Configuration
MODEL_DIR = Path(__file__).parent.parent / "model"
MODEL_PATH = MODEL_DIR / "mlp_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"

# Global variables for model, scaler, and state
model = None
scaler = None
latest_status = RoomStatus(reading=None, score=0, last_updated=None, connected=False)

# Hybrid Scoring Constants
COEFF_MLP_BASE = 1.0
COEFF_VOC = -0.02
COEFF_PARTICLES = -0.05
BIAS = 0.0

class SensorDataPayload(BaseModel):
    humidity: float
    pressure: float
    light: float
    temperature: float
    sound_high: float
    sound_mid: float
    sound_low: float
    sound_amp: float
    vocs: float = Field(..., description="VOC level in ppb")
    particulates: float = Field(..., description="PM2.5 level in ug/m3")

def calculate_final_iaq(base_score: float, vocs: float, particulates: float) -> int:
    score = (base_score * COEFF_MLP_BASE) + (vocs * COEFF_VOC) + (particulates * COEFF_PARTICLES) + BIAS
    return int(max(1, min(99, round(score))))

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, scaler
    print("Loading MLP base model...")
    try:
        if MODEL_PATH.exists() and SCALER_PATH.exists():
            model = joblib.load(MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
            print("MLP model and scaler loaded successfully.")
        else:
            print(f"Warning: Model files not found at {MODEL_PATH}.")
    except Exception as e:
        print(f"Error loading models: {e}")
    yield

app = FastAPI(title="RoomPulse Hybrid IAQ Backend", lifespan=lifespan)

@app.get("/")
async def root():
    return {"service": "RoomPulse API", "status": "running"}

@app.get("/api/current-status", response_model=RoomStatus)
async def current_status():
    return latest_status

@app.post("/api/sensor-data")
async def process_sensor_data(payload: SensorDataPayload):
    global latest_status
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="ML model is not loaded.")

    try:
        mlp_features = np.array([
            payload.humidity, payload.pressure, payload.light, payload.temperature,
            payload.sound_high, payload.sound_mid, payload.sound_low, payload.sound_amp
        ]).reshape(1, -1)

        scaled_input = scaler.transform(mlp_features)
        base_score = float(model.predict(scaled_input)[0])
        final_score = calculate_final_iaq(base_score, payload.vocs, payload.particulates)

        # Update global state for the dashboard
        from datetime import datetime, timezone
        from app.models import SensorReading
        
        latest_status = RoomStatus(
            reading=SensorReading(
                temperature_c=payload.temperature,
                humidity_pct=payload.humidity,
                light_lux=payload.light,
                noise_db=payload.sound_amp, # using amp as main noise display
                pressure_hpa=payload.pressure,
                pm25_ugm3=payload.particulates,
                voc_ppb=payload.vocs,
                timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000)
            ),
            score=final_score,
            last_updated=datetime.now(timezone.utc),
            connected=True
        )

        return {
            "status": "success",
            "base_mlp_score": round(base_score, 2),
            "final_iaq_score": final_score
        }
    except Exception as e:
        print(f"Prediction Error: {e}")
        raise HTTPException(status_code=500, detail="Error during score computation.")

@app.get("/health")
async def health():
    return {"status": "ready", "model_active": model is not None}
