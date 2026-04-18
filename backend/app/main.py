from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import numpy as np
import os
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from app.models import RoomStatus, SensorReading
from app.gemini import generate_analysis

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

def predict_score(data: dict) -> dict:
    """
    Unified scoring function for both POST API and Background Serial Reader.
    Calculates MLP base score + Hybrid IAQ final score.
    """
    if model is None or scaler is None:
        return {"error": "Model not loaded"}

    # Extract MLP features (order matters!)
    # Scenarios: (humidity, pressure, light, temperature, sound_high, sound_mid, sound_low, sound_amp)
    mlp_feature_keys = [
        "humidity_pct", "pressure_hpa", "light_lux", "temperature_c",
        "noise_high", "noise_mid", "noise_low", "noise_db"
    ]
    
    # Map input keys to our internal MLP feature list
    # The Pico sends 'temperature_c' etc. The API payload sends 'temperature'. 
    # We normalize to the Pico names for internal scoring.
    features_raw = [
        data.get("humidity_pct", data.get("humidity", 0)),
        data.get("pressure_hpa", data.get("pressure", 0)),
        data.get("light_lux", data.get("light", 0)),
        data.get("temperature_c", data.get("temperature", 0)),
        data.get("noise_high", data.get("sound_high", 0)),
        data.get("noise_mid", data.get("sound_mid", 0)),
        data.get("noise_low", data.get("sound_low", 0)),
        data.get("noise_db", data.get("sound_amp", 0))
    ]

    features = np.array(features_raw).reshape(1, -1)
    scaled = scaler.transform(features)
    base_score = float(model.predict(scaled)[0])
    
    vocs = data.get("voc_ppb", data.get("vocs", 0))
    pm25 = data.get("pm25_ugm3", data.get("particulates", 0))
    
    final_score = calculate_final_iaq(base_score, vocs, pm25)
    
    return {
        "base_score": base_score,
        "final_score": final_score,
        "reading": {
            "temperature_c": features_raw[3],
            "humidity_pct": features_raw[0],
            "light_lux": features_raw[2],
            "noise_db": features_raw[7],
            "pressure_hpa": features_raw[1],
            "pm25_ugm3": pm25,
            "voc_ppb": vocs,
        }
    }

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
    
    # Start background task for data generation
    generator_task = asyncio.create_task(run_data_generator())
    
    yield
    
    # Cleanup
    generator_task.cancel()

async def run_data_generator():
    """
    Background job that either reads serial or generates mock scenarios.
    Updates the global 'latest_status'.
    """
    global latest_status
    use_mock = os.getenv("MOCK_SERIAL", "false").lower() in ("true", "1", "yes")
    
    if use_mock:
        print("🧪 Simulation Mode: Cycling through health scenarios...")
        # Scenarios from simulate_scenarios.py
        scenarios = [
            {"name": "Ideal Spring Day", "data": [45.0, 1013.0, 500.0, 22.0, 10.0, 15.0, 20.0, 15.0], "vocs": 50.0, "particulates": 5.0},
            {"name": "California Wildfire (Smoke)", "data": [15.0, 1005.0, 200.0, 35.0, 10.0, 15.0, 20.0, 15.0], "vocs": 800.0, "particulates": 250.0},
            {"name": "Loud Classroom / Party", "data": [55.0, 1010.0, 800.0, 26.0, 80.0, 90.0, 70.0, 85.0], "vocs": 400.0, "particulates": 20.0},
            {"name": "Stuffy Basement", "data": [85.0, 1015.0, 50.0, 18.0, 5.0, 5.0, 5.0, 5.0], "vocs": 1200.0, "particulates": 10.0}
        ]
        
        while True:
            for s in scenarios:
                # Prepare data for predict_score
                # MLP expects: [humidity, pressure, light, temperature, sound_high, sound_mid, sound_low, sound_amp]
                payload = {
                    "humidity": s["data"][0],
                    "pressure": s["data"][1],
                    "light": s["data"][2],
                    "temperature": s["data"][3],
                    "sound_high": s["data"][4],
                    "sound_mid": s["data"][5],
                    "sound_low": s["data"][6],
                    "sound_amp": s["data"][7],
                    "vocs": s["vocs"],
                    "particulates": s["particulates"]
                }
                
                results = predict_score(payload)
                if "error" not in results:
                    latest_status = RoomStatus(
                        reading=SensorReading(
                            **results["reading"],
                            timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000)
                        ),
                        score=results["final_score"],
                        last_updated=datetime.now(timezone.utc),
                        connected=True
                    )
                    print(f"Simulated Scene: {s['name']} | Score: {results['final_score']}")
                
                await asyncio.sleep(5) # Give the user time to see the scene change
    else:
        # Real Serial Logic (Simplified to keep main.py clean)
        # In a real app, this would use the serial_reader.py logic
        print("🔌 Production Mode: Waiting for serial data...")
        pass

app = FastAPI(title="RoomPulse Hybrid IAQ Backend", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"service": "RoomPulse API", "status": "running"}

@app.get("/api/current-status", response_model=RoomStatus)
async def current_status():
    return latest_status

@app.get("/api/analyze")
async def analyze_room():
    """
    Triggers a Gemini AI analysis of the current room environment.
    """
    if not latest_status.reading:
        return {"summary": "Waiting for sensor data...", "flags": []}
    
    # Format the reading for Gemini
    reading_dict = latest_status.reading.model_dump()
    analysis = generate_analysis(reading_dict, latest_status.score)
    return analysis

@app.post("/api/sensor-data")
async def process_sensor_data(payload: SensorDataPayload):
    global latest_status
    
    try:
        results = predict_score(payload.model_dump())
        if "error" in results:
            raise HTTPException(status_code=503, detail=results["error"])

        # Update global state
        latest_status = RoomStatus(
            reading=SensorReading(
                **results["reading"],
                timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000)
            ),
            score=results["final_score"],
            last_updated=datetime.now(timezone.utc),
            connected=True
        )

        return {
            "status": "success",
            "base_mlp_score": round(results["base_score"], 2),
            "final_iaq_score": results["final_score"]
        }
    except Exception as e:
        print(f"Prediction Error: {e}")
        raise HTTPException(status_code=500, detail="Error during score computation.")

@app.get("/health")
async def health():
    return {"status": "ready", "model_active": model is not None}
