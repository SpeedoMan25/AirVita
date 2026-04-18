from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import json
import numpy as np
import os
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import pandas as pd
from app.models import RoomStatus, SensorReading, ScoreBreakdown
from app.gemini import generate_analysis
from app.scoring import (
    calculate_room_health_score,
    calculate_sleep_score_with_breakdown,
    calculate_study_score_with_breakdown,
    calculate_work_score_with_breakdown,
    calculate_fun_score_with_breakdown
)
from app.weather import weather_service

# Configuration
MODEL_DIR = Path(__file__).parent.parent / "model"
MODEL_PATH = MODEL_DIR / "mlp_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"

# Global variables for model, scaler, and state
model = None
scaler = None
latest_status = RoomStatus(
    reading=None,
    score=0,
    sleep_score=0,
    study_score=0,
    work_score=0,
    fun_score=0,
    last_updated=None,
    connected=False
)

# Simulation State
AUTO_CYCLE = False 
CURRENT_SCENARIO_INDEX = 0
ACTIVE_SCENARIO_ID = "ideal" 
CURRENT_SOURCE = "live" # 'live', 'simulation', or 'weather'
LAST_WEATHER_DATA = None
LAST_WEATHER_FETCH_TIME = 0

# Load Simulation Scenarios from JSON
SCENARIOS_FILE = Path(__file__).parent / "scenarios.json"
SIMULATION_SCENARIOS = []
try:
    if SCENARIOS_FILE.exists():
        with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
            SIMULATION_SCENARIOS = json.load(f)
        print(f"Loaded {len(SIMULATION_SCENARIOS)} simulation scenarios.")
    else:
        print(f"Warning: {SCENARIOS_FILE} not found.")
except Exception as e:
    print(f"Error loading scenarios.json: {e}")

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
    Background job that generates data based on CURRENT_SOURCE.
    """
    global latest_status, AUTO_CYCLE, CURRENT_SOURCE, LAST_WEATHER_DATA, LAST_WEATHER_FETCH_TIME
    import random
    
    print("🛰️ Data Generator Task Started.")
    last_cycle_time = 0
    
    while True:
        now = datetime.now(timezone.utc).timestamp()
        
        # Periodically refresh weather data (every 5 minutes)
        if now - LAST_WEATHER_FETCH_TIME > 300:
            try:
                LAST_WEATHER_DATA = await weather_service.fetch_weather()
                LAST_WEATHER_FETCH_TIME = now
                print(f"🌍 Weather Updated: {LAST_WEATHER_DATA.get('location', 'Unknown')}")
            except Exception as e:
                print(f"Weather update error: {e}")

        if CURRENT_SOURCE == "simulation":
            # ... existing simulation logic ...
            if AUTO_CYCLE and (now - last_cycle_time > 8):
                global CURRENT_SCENARIO_INDEX, ACTIVE_SCENARIO_ID
                CURRENT_SCENARIO_INDEX = (CURRENT_SCENARIO_INDEX + 1) % len(SIMULATION_SCENARIOS)
                ACTIVE_SCENARIO_ID = SIMULATION_SCENARIOS[CURRENT_SCENARIO_INDEX]["id"]
                last_cycle_time = now
                print(f"♻️ Auto-cycle: Switched to {ACTIVE_SCENARIO_ID}")

            s = next((scen for scen in SIMULATION_SCENARIOS if scen["id"] == ACTIVE_SCENARIO_ID), None)
            if s:
                def jitter(val):
                    return val * random.uniform(0.985, 1.015)

                payload = {
                    "humidity": jitter(s["inputs"]["humidity"]), 
                    "pressure": jitter(s["inputs"]["pressure"]), 
                    "light": jitter(s["inputs"]["light"]), 
                    "temperature": jitter(s["inputs"]["temperature"]),
                    "sound_amp": jitter(s["inputs"]["noise"]),
                    "vocs": jitter(s["inputs"]["vocs"]), 
                    "particulates": jitter(s["inputs"]["particulates"])
                }
                update_status_from_dict(payload)
        
        elif CURRENT_SOURCE == "weather" and LAST_WEATHER_DATA:
            # Map weather data to sensor payload
            payload = {
                "temperature": LAST_WEATHER_DATA.get("temperature_c", 20),
                "humidity": LAST_WEATHER_DATA.get("humidity_pct", 50),
                "pressure": LAST_WEATHER_DATA.get("pressure_hpa", 1013),
                "light": 500 if 6 < datetime.now().hour < 18 else 10, # Mock light based on time
                "sound_amp": 35.0, # Baseline noise
                "vocs": LAST_WEATHER_DATA.get("voc_ppb", 0),
                "particulates": LAST_WEATHER_DATA.get("pm25_ugm3", 5)
            }
            update_status_from_dict(payload)
        
        await asyncio.sleep(2)

def update_status_from_dict(payload_data: dict):
    """Utility to run prediction and update latest_status."""
    global latest_status
    results = predict_score(payload_data)
    if "error" not in results:
        reading = SensorReading(
            **results["reading"],
            timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000)
        )
        
        # Calculate base scores
        scores_reading = results["reading"]
        
        # Use outdoor-aware health score
        final_score = calculate_room_health_score(scores_reading, outdoor=LAST_WEATHER_DATA)

        # Calculate sub-activity scores with math internal
        sleep_res = calculate_sleep_score_with_breakdown(scores_reading)
        study_res = calculate_study_score_with_breakdown(scores_reading)
        work_res = calculate_work_score_with_breakdown(scores_reading)
        fun_res = calculate_fun_score_with_breakdown(scores_reading)

        latest_status = RoomStatus(
            reading=reading,
            score=final_score,
            sleep_score=sleep_res["score"],
            study_score=study_res["score"],
            work_score=work_res["score"],
            fun_score=fun_res["score"],
            activity_breakdowns={
                "sleep": sleep_res["breakdown"],
                "study": study_res["breakdown"],
                "work": work_res["breakdown"],
                "fun": fun_res["breakdown"],
            },
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
    scores = {
        "health": latest_status.score,
        "sleep": latest_status.sleep_score,
        "study": latest_status.study_score,
        "work": latest_status.work_score,
        "fun": latest_status.fun_score
    }
    analysis = generate_analysis(reading_dict, scores)
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
        {"id": s["id"], "name": s["name"], "icon": s.get("icon", "🔹")} 
        for s in SIMULATION_SCENARIOS
    ]

class ScenarioSelect(BaseModel):
    id: str

@app.post("/api/scenarios/select")
async def select_scenario(selection: ScenarioSelect):
    """Manually triggers a specific scenario and stops auto-cycling."""
    global AUTO_CYCLE, ACTIVE_SCENARIO_ID, CURRENT_SOURCE
    
    if selection.id == "live":
        CURRENT_SOURCE = "live"
        print("🔌 Source Switched: LIVE (Hardware)")
        return {"status": "success", "source": "live"}

    if selection.id == "weather":
        CURRENT_SOURCE = "weather"
        print("🌍 Source Switched: WEATHER (Local Outdoor)")
        return {"status": "success", "source": "weather"}

    scenario = next((s for s in SIMULATION_SCENARIOS if s["id"] == selection.id), None)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    CURRENT_SOURCE = "simulation"
    ACTIVE_SCENARIO_ID = selection.id
    AUTO_CYCLE = False # Lock to this scenario
    
    # Immediate update
    payload = {
        "humidity": scenario["inputs"]["humidity"], "pressure": scenario["inputs"]["pressure"], "light": scenario["inputs"]["light"], "temperature": scenario["inputs"]["temperature"],
        "sound_high": 10.0, "sound_mid": 10.0, "sound_low": 10.0, "sound_amp": scenario["inputs"]["noise"],
        "vocs": scenario["inputs"]["vocs"], "particulates": scenario["inputs"]["particulates"]
    }
    update_status_from_dict(payload)
    
    return {"status": "success", "scenario": scenario["name"]}

@app.get("/health")
async def health():
    return {"status": "ready", "model_active": model is not None}
