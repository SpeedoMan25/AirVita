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
import pandas as pd
from app.models import RoomStatus, SensorReading, ScoreBreakdown
from app.gemini import generate_analysis

# Configuration
MODEL_DIR = Path(__file__).parent.parent / "model"
MODEL_PATH = MODEL_DIR / "mlp_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"

# Global variables for model, scaler, and state
model = None
scaler = None
latest_status = RoomStatus(reading=None, score=0, last_updated=None, connected=False)

# Simulation State
AUTO_CYCLE = True
MANUAL_SCENARIO_EXPIRY = 0 # timestamp when auto-cycle should resume

SIMULATION_SCENARIOS = [
    {"id": "ideal", "name": "Ideal Spring Day", "data": [45.0, 1013.0, 500.0, 22.0, 10.0, 15.0, 20.0, 15.0], "vocs": 50.0, "particulates": 5.0},
    {"id": "wildfire", "name": "California Wildfire (Smoke)", "data": [15.0, 1005.0, 200.0, 35.0, 10.0, 15.0, 20.0, 15.0], "vocs": 800.0, "particulates": 250.0},
    {"id": "party", "name": "Loud Classroom / Party", "data": [55.0, 1010.0, 800.0, 26.0, 80.0, 90.0, 70.0, 85.0], "vocs": 400.0, "particulates": 20.0},
    {"id": "basement", "name": "Stuffy Basement", "data": [85.0, 1015.0, 50.0, 18.0, 5.0, 5.0, 5.0, 5.0], "vocs": 1200.0, "particulates": 10.0}
]

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
    Calculates MLP base score + Hybrid IAQ final score breakdown.
    """
    if model is None or scaler is None:
        return {"error": "Model not loaded"}

    # Extract MLP features (ORDER AND NAMES MUST MATCH train_model.py)
    feature_names = [
        "humidity", "pressure", "light", "temperature",
        "sound_high", "sound_mid", "sound_low", "sound_amp"
    ]
    
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

    # Use a DataFrame to satisfy scikit-learn's feature name check
    df = pd.DataFrame([features_raw], columns=feature_names)
    scaled = scaler.transform(df)
    base_score = float(model.predict(scaled)[0])
    
    vocs = data.get("voc_ppb", data.get("vocs", 0))
    pm25 = data.get("pm25_ugm3", data.get("particulates", 0))
    
    # Calculate penalty components
    voc_penalty = vocs * COEFF_VOC
    pm25_penalty = pm25 * COEFF_PARTICLES
    
    final_score = calculate_final_iaq(base_score, vocs, pm25)
    
    return {
        "base_score": base_score,
        "voc_penalty": voc_penalty,
        "pm25_penalty": pm25_penalty,
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
    global latest_status, AUTO_CYCLE, MANUAL_SCENARIO_EXPIRY
    use_mock = os.getenv("MOCK_SERIAL", "false").lower() in ("true", "1", "yes")
    
    if use_mock:
        print("🧪 Simulation Mode: Started.")
        current_idx = 0
        
        while True:
            # Check if manual override is active
            if not AUTO_CYCLE and datetime.now(timezone.utc).timestamp() < MANUAL_SCENARIO_EXPIRY:
                await asyncio.sleep(1)
                continue
            
            # If we reached here, either AUTO_CYCLE is True or override expired
            if not AUTO_CYCLE:
                print("♻️ Manual override expired. Resuming auto-cycle...")
                AUTO_CYCLE = True

            s = SIMULATION_SCENARIOS[current_idx % len(SIMULATION_SCENARIOS)]
            current_idx += 1
            
            # Prepare data
            payload = {
                "humidity": s["data"][0], "pressure": s["data"][1], "light": s["data"][2], "temperature": s["data"][3],
                "sound_high": s["data"][4], "sound_mid": s["data"][5], "sound_low": s["data"][6], "sound_amp": s["data"][7],
                "vocs": s["vocs"], "particulates": s["particulates"]
            }
            
            update_status_from_dict(payload)
            print(f"Simulated Scene: {s['name']} | Score: {latest_status.score}")
            await asyncio.sleep(8) # Cycle every 8 seconds in auto mode
    else:
        print("🔌 Production Mode: Waiting for serial data...")
        pass

def update_status_from_dict(payload_data: dict):
    """Utility to run prediction and update latest_status."""
    global latest_status
    results = predict_score(payload_data)
    if "error" not in results:
        latest_status = RoomStatus(
            reading=SensorReading(
                **results["reading"],
                timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000)
            ),
            score=results["final_score"],
            breakdown=ScoreBreakdown(
                base_mlp_score=results["base_score"],
                voc_penalty=results["voc_penalty"],
                pm25_penalty=results["pm25_penalty"],
                final_score=results["final_score"]
            ),
            last_updated=datetime.now(timezone.utc),
            connected=True
        )
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
    try:
        update_status_from_dict(payload.model_dump())
        return {
            "status": "success",
            "base_mlp_score": round(latest_status.breakdown.base_mlp_score, 2),
            "final_iaq_score": latest_status.score
        }
    except Exception as e:
        print(f"Prediction Error: {e}")
        raise HTTPException(status_code=500, detail="Error during score computation.")

@app.get("/api/scenarios")
async def get_scenarios():
    """Returns available simulation presets."""
    return [
        {"id": s["id"], "name": s["name"]} 
        for s in SIMULATION_SCENARIOS
    ]

class ScenarioSelect(BaseModel):
    id: str

@app.post("/api/scenarios/select")
async def select_scenario(selection: ScenarioSelect):
    """Manually triggers a specific scenario and pauses auto-cycling."""
    global AUTO_CYCLE, MANUAL_SCENARIO_EXPIRY
    
    scenario = next((s for s in SIMULATION_SCENARIOS if s["id"] == selection.id), None)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Prepare data
    payload = {
        "humidity": scenario["data"][0], "pressure": scenario["data"][1], "light": scenario["data"][2], "temperature": scenario["data"][3],
        "sound_high": scenario["data"][4], "sound_mid": scenario["data"][5], "sound_low": scenario["data"][6], "sound_amp": scenario["data"][7],
        "vocs": scenario["vocs"], "particulates": scenario["particulates"]
    }
    
    update_status_from_dict(payload)
    
    # Pause auto-cycle for 60 seconds
    AUTO_CYCLE = False
    MANUAL_SCENARIO_EXPIRY = datetime.now(timezone.utc).timestamp() + 60
    
    return {"status": "success", "scenario": scenario["name"], "resumes_in": 60}

@app.get("/health")
async def health():
    return {"status": "ready", "model_active": model is not None}
