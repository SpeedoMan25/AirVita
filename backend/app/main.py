from fastapi import FastAPI, HTTPException
from typing import Dict, List, Optional
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
monitors: Dict[str, RoomStatus] = {}

# Simulation State
AUTO_CYCLE = False 
CURRENT_SCENARIO_INDEX = 0
ACTIVE_SCENARIO_ID = "ideal" 
CURRENT_SOURCE = "live" # 'live', 'simulation', or 'weather'
LAST_WEATHER_DATA = None
LAST_WEATHER_FETCH_TIME = 0
CURRENT_PAIRING_STATUS = "ready" # ready, connected, completed

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
    device_id: str = Field(..., description="Unique ID of the transmitting device")
    humidity: float = 0.0
    pressure: float = 0.0
    light: float = 0.0
    temperature: float = 0.0
    sound_high: float = 0.0
    sound_mid: float = 0.0
    sound_low: float = 0.0
    sound_amp: float = 0.0
    vocs: float = Field(0.0, description="VOC level in ppb")
    particulates: float = Field(0.0, description="PM2.5 level in ug/m3")

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

from app.cv import classifier
import socket

def get_lan_ip():
    host_ip = os.getenv("HOST_IP")
    if host_ip and host_ip != "127.0.0.1":
        return host_ip
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, scaler
    print("Loading MLP base model...")
    try:
        if MODEL_PATH.exists() and SCALER_PATH.exists():
            model = joblib.load(MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
            print("MLP model and scaler loaded successfully.")
    except Exception as e:
        print(f"Error loading models: {e}")
    
    # Initialize Room Classifier (Places365)
    try:
        classifier.load_model()
    except Exception as e:
        print(f"Error loading CV model: {e}")
    
    # Start background task for data generation
    generator_task = asyncio.create_task(run_data_generator())
    
    # Print LAN-accessible URLs banner
    ip = get_lan_ip()
    frontend_url = f"https://{ip}:5173"
    backend_url = f"http://{ip}:8000"
    frontend_link = f"\033]8;;{frontend_url}\033\\{frontend_url}\033]8;;\033\\"
    backend_link = f"\033]8;;{backend_url}\033\\{backend_url}\033]8;;\033\\"
    
    print("\n" + "─" * 30, flush=True)
    print("🚀 AirVita Running\n", flush=True)
    print("📱 Frontend:", flush=True)
    print(f"{frontend_link}\n", flush=True)
    print("⚙️ Backend:", flush=True)
    print(f"{backend_link}", flush=True)
    print("─" * 30 + "\n", flush=True)
    
    yield
    generator_task.cancel()


async def run_data_generator():
    """
    Background job that generates data based on CURRENT_SOURCE.
    """
    global AUTO_CYCLE, CURRENT_SOURCE, LAST_WEATHER_DATA, LAST_WEATHER_FETCH_TIME
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
                update_status_from_dict(payload, device_id="simulation")
        
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
            update_status_from_dict(payload, device_id="weather")
        
        await asyncio.sleep(2)

def get_unique_room_name(room_type: str, current_device_id: str) -> str:
    """Calculates a unique name for a room, adding a number if duplicates exist."""
    # Find all other devices that have the same room_type
    similar_monitors = [
        m for m in monitors.values() 
        if m.room_context and m.room_context.room_type == room_type
        and m.device_id != current_device_id
    ]
    
    if not similar_monitors:
        return room_type
    
    return f"{room_type} {len(similar_monitors) + 1}"

def update_status_from_dict(payload_data: dict, device_id: str = "simulation"):
    """Utility to run prediction and update specific monitor status."""
    global monitors
    results = predict_score(payload_data)
    
    # Ensure monitor exists in registry
    if device_id not in monitors:
        monitors[device_id] = RoomStatus(
            device_id=device_id,
            display_name="Simulation" if device_id == "simulation" else "New Monitor",
            connected=True
        )

    if "error" not in results:
        reading = SensorReading(
            **results["reading"],
            device_id=device_id,
            timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000)
        )
        
        # Calculate base scores
        scores_reading = results["reading"]
        
        # Use outdoor-aware health score
        final_score = calculate_room_health_score(scores_reading, outdoor=LAST_WEATHER_DATA)

        # Calculate sub-activity scores
        sleep_res = calculate_sleep_score_with_breakdown(scores_reading)
        work_res = calculate_work_score_with_breakdown(scores_reading)
        fun_res = calculate_fun_score_with_breakdown(scores_reading)

        # Update specific monitor
        m = monitors[device_id]
        m.reading = reading
        m.score = final_score
        m.sleep_score = sleep_res["score"]
        m.work_score = work_res["score"]
        m.fun_score = fun_res["score"]
        m.activity_breakdowns = {
            "sleep": sleep_res["breakdown"],
            "work": work_res["breakdown"],
            "fun": fun_res["breakdown"],
        }
        m.breakdown = ScoreBreakdown(
            base_mlp_score=results["base_score"],
            voc_penalty=results["voc_penalty"],
            pm25_penalty=results["pm25_penalty"],
            final_score=results["final_score"]
        )
        m.last_updated = datetime.now(timezone.utc)
        m.connected = True
        
        # If simulation, force status (some sources use jitter)
        if device_id == "simulation":
            m.pairing_status = "completed"
    else:
        monitors[device_id].connected = False

app = FastAPI(title="AirVita Hybrid IAQ Backend", lifespan=lifespan)

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
    return {"service": "AirVita API", "status": "running"}

@app.get("/api/current-status", response_model=RoomStatus)
async def current_status(device_id: Optional[str] = None):
    global monitors
    # Default to first live device, or simulation if nothing else exists
    if not device_id:
        live_ids = [k for k in monitors.keys() if k not in ["simulation", "weather"]]
        device_id = live_ids[0] if live_ids else "simulation"
    
    if device_id not in monitors:
        # Create a blank entry if it doesn't exist (e.g. simulation hasn't run yet)
        if device_id == "simulation":
            update_status_from_dict({}, device_id="simulation")
        else:
            raise HTTPException(status_code=404, detail=f"Monitor {device_id} not found")
            
    return monitors[device_id]

@app.api_route("/api/monitors", methods=["GET", "HEAD"])
async def get_monitors():
    """Returns a list of all active monitors."""
    return [
        {
            "id": m.device_id,
            "name": m.display_name,
            "connected": m.connected,
            "room_type": m.room_context.room_type if m.room_context else None
        }
        for m in monitors.values()
    ]

class PairingStatusUpdate(BaseModel):
    device_id: str
    status: str

@app.post("/api/pairing/status")
async def update_pairing_status(update: PairingStatusUpdate):
    if update.device_id not in monitors:
         raise HTTPException(status_code=404, detail="Monitor not found")
    
    if update.status not in ["ready", "connected", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    monitors[update.device_id].pairing_status = update.status
    print(f"🔄 Pairing Status [ {update.device_id} ]: {update.status}")
    return {"status": "success", "pairing_status": update.status}

class PairingReset(BaseModel):
    device_id: str

@app.post("/api/pairing/reset")
async def reset_pairing(reset: PairingReset):
    if reset.device_id not in monitors:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    monitors[reset.device_id].pairing_status = "ready"
    monitors[reset.device_id].room_context = None
    print(f"🧹 Pairing/Context Reset [ {reset.device_id} ]")
    return {"status": "success"}

import socket

@app.get("/api/connection-info")
async def connection_info():
    """Returns the LAN IP or Tunnel URL for mobile pairing."""
    tunnel_url = os.getenv("TUNNEL_URL")
    if tunnel_url:
        return {"ip": tunnel_url, "url": tunnel_url}
    
    ip = get_lan_ip()
    return {"ip": ip, "url": f"https://{ip}:5173"}

@app.get("/api/analyze")
async def analyze_room(device_id: str):
    """
    Triggers a Gemini AI analysis for a specific room environment.
    """
    if device_id not in monitors:
        raise HTTPException(status_code=404, detail="Monitor not found")
        
    m = monitors[device_id]
    
    if not m.reading:
        return {"summary": "Waiting for sensor data...", "flags": []}
        
    if not m.room_context:
        return {
            "summary": "LOCKED: Please use the Room Scanner to capture environmental context before accessing Neural AI insights.",
            "flags": ["Missing Visual Context"]
        }
    
    # Format the reading for Gemini
    reading_dict = m.reading.model_dump()
    scores = {
        "health": m.score,
        "sleep": m.sleep_score,
        "work": m.work_score,
        "fun": m.fun_score
    }
    room_ctx = m.room_context.model_dump()
    analysis = generate_analysis(reading_dict, scores, room_ctx)
    return analysis

@app.post("/api/sensor-data")
async def process_sensor_data(payload: SensorDataPayload):
    try:
        update_status_from_dict(payload.model_dump(), device_id=payload.device_id)
        return {
            "status": "success",
            "final_iaq_score": monitors[payload.device_id].score
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

@app.post("/api/scan-room")
async def scan_room(payload: dict):
    if "image" not in payload:
        raise HTTPException(status_code=400, detail="Image required")
    
    device_id = payload.get("device_id")
    if not device_id or device_id not in monitors:
         raise HTTPException(status_code=400, detail="Valid device_id required")

    result = classifier.predict(payload["image"])
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    if result.get("confidence", 0) > 0.60 or payload.get("force_lock"):
        from app.models import RoomContext
        room_type = result.get("room", "Unknown")
        
        # Update Room Context
        m = monitors[device_id]
        m.room_context = RoomContext(
            room_type=room_type,
            identified_objects=result.get("objects", [])
        )
        
        # Dynamically trigger renaming with deduplication logic
        m.display_name = get_unique_room_name(room_type, device_id)
        print(f"🏷️ Device Renamed [ {device_id} ] -> {m.display_name}")
        
    return result
