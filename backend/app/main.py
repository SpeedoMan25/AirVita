"""
RoomPulse — FastAPI Backend

Serves the latest sensor data and health score via a REST API.
Launches the serial reader as a background task on startup.

On startup, loads the pre-trained MLP model and scaler (.pkl) into
memory so the POST /api/sensor-data route can perform real-time
inference without re-loading on every request.

When ENABLE_MOCK_DATA is True a background task generates realistic,
drifting sensor readings every 2 seconds so the frontend can be
developed without physical hardware.
"""

import asyncio
import logging
import math
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.models import RoomStatus
from app.serial_reader import get_current_status, run_serial_listener
from app.gemini import generate_analysis

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-24s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger("roompulse")


# ──────────────────────────────────────────────
# ML Model artefacts (loaded once at startup)
# ──────────────────────────────────────────────
_MODEL_DIR = Path(__file__).resolve().parent.parent / "model"
_MODEL_PATH = _MODEL_DIR / "mlp_model.pkl"
_SCALER_PATH = _MODEL_DIR / "scaler.pkl"

_mlp_model = None
_mlp_scaler = None

# The 6 features in the order the model was trained on
_MODEL_FEATURES = [
    "Temperature",
    "Humidity",
    "Pressure",
    "Light",
    "Noise",
    "Particulates",
]

# ──────────────────────────────────────────────
# VOC Penalty Configuration
# ──────────────────────────────────────────────
VOC_SAFE_THRESHOLD = 300.0    # ppb — below this, no penalty
VOC_DANGER_CEILING = 2000.0   # ppb — at or above this, maximum penalty
VOC_MAX_PENALTY = 30.0        # max points deducted from base score

# ──────────────────────────────────────────────
# ★ MOCK DATA TOGGLE
# Set to True for frontend dev without hardware.
# Set to False once the real Pico is connected.
# ──────────────────────────────────────────────
ENABLE_MOCK_DATA: bool = True

# ──────────────────────────────────────────────
# Mock sensor state + physical bounds
# ──────────────────────────────────────────────
# Each entry: (initial_value, min_bound, max_bound, random_walk_step)
_MOCK_BOUNDS = {
    "Temperature":  (22.0,   10.0,  38.0,  0.25),
    "Humidity":     (50.0,    0.0, 100.0,  0.8),
    "Pressure":     (1013.0, 960.0, 1060.0, 0.4),
    "Light":        (400.0,   0.0, 1200.0, 12.0),
    "Noise":        (32.0,    0.0, 100.0,  1.5),
    "Particulates": (10.0,    0.0, 250.0,  2.0),
    "Extra_VOCs":   (120.0,   0.0, 2000.0, 15.0),
}

_mock_readings: dict = {
    k: v[0] for k, v in _MOCK_BOUNDS.items()
}

# Flag: True once a real POST /api/sensor-data has been received
_real_data_received: bool = False

# Holds the latest mock-derived RoomStatus for GET /api/current-status
_mock_status: Optional["RoomStatus"] = None


# ──────────────────────────────────────────────
# Pydantic model for the POST payload
# ──────────────────────────────────────────────
class SensorDataPayload(BaseModel):
    """JSON body expected by POST /api/sensor-data."""
    Temperature: float = Field(..., description="Temperature in Celsius")
    Humidity: float = Field(..., description="Relative humidity %")
    Pressure: float = Field(..., description="Atmospheric pressure in hPa")
    Light: float = Field(..., description="Light level in lux")
    Noise: float = Field(..., description="Noise level in dB")
    Particulates: float = Field(..., description="PM2.5 µg/m³")
    Extra_VOCs: float = Field(..., description="Volatile organic compounds in ppb (7th feature)")


# ──────────────────────────────────────────────
# VOC penalty utility
# ──────────────────────────────────────────────

def compute_voc_penalty(voc_ppb: float) -> float:
    """
    Evaluate the Extra_VOCs reading and return a penalty deduction.

    Rules:
        - Below VOC_SAFE_THRESHOLD (300 ppb): no penalty (0.0).
        - Above threshold: penalty scales linearly up to VOC_MAX_PENALTY
          as VOC approaches VOC_DANGER_CEILING (2000 ppb).
        - Clamped so penalty never exceeds VOC_MAX_PENALTY.

    Parameters
    ----------
    voc_ppb : float
        VOC reading in parts-per-billion.

    Returns
    -------
    float
        Non-negative deduction to subtract from the base score.
    """
    if voc_ppb <= VOC_SAFE_THRESHOLD:
        return 0.0

    excess = voc_ppb - VOC_SAFE_THRESHOLD
    span = VOC_DANGER_CEILING - VOC_SAFE_THRESHOLD  # 1700 ppb range
    ratio = min(excess / span, 1.0)                  # cap at 1.0
    return round(ratio * VOC_MAX_PENALTY, 2)


def clamp_score(score: float, lo: int = 1, hi: int = 99) -> int:
    """Clamp a floating-point score into the integer range [lo, hi]."""
    return max(lo, min(hi, int(round(score))))


# ──────────────────────────────────────────────
# Mock data helpers
# ──────────────────────────────────────────────

def _score_from_mock() -> int:
    """
    Run the current _mock_readings through the hybrid scoring pipeline:
      MLP prediction on 6 base features  →  VOC penalty  →  clamped 1-99.

    Falls back to the legacy weighted-average scorer if the MLP model
    hasn't been trained yet.
    """
    from app.scoring import calculate_room_health_score  # avoid circular at top-level

    if _mlp_model is not None and _mlp_scaler is not None:
        feature_values = [
            _mock_readings["Temperature"],
            _mock_readings["Humidity"],
            _mock_readings["Pressure"],
            _mock_readings["Light"],
            _mock_readings["Noise"],
            _mock_readings["Particulates"],
        ]
        features_array = np.array(feature_values, dtype=np.float64).reshape(1, -1)
        scaled = _mlp_scaler.transform(features_array)
        base_score = float(_mlp_model.predict(scaled)[0])
        penalty = compute_voc_penalty(_mock_readings["Extra_VOCs"])
        return clamp_score(base_score - penalty)

    # Fallback: map mock keys → legacy model field names
    legacy_map = {
        "temperature_c": _mock_readings["Temperature"],
        "humidity_pct":  _mock_readings["Humidity"],
        "pressure_hpa": _mock_readings["Pressure"],
        "light_lux":    _mock_readings["Light"],
        "noise_db":     _mock_readings["Noise"],
        "pm25_ugm3":    _mock_readings["Particulates"],
        "voc_ppb":      _mock_readings["Extra_VOCs"],
    }
    return calculate_room_health_score(legacy_map)


async def _run_mock_sensor_loop() -> None:
    """
    Background coroutine that mutates _mock_readings every 2 seconds
    using a random walk with a subtle sine-wave bias for realism.
    """
    global _mock_status
    from app.models import SensorReading  # local import to avoid circular

    logger.info("🧪 Mock sensor loop started — generating data every 2s")
    tick = 0

    while True:
        for key, (_, lo, hi, step) in _MOCK_BOUNDS.items():
            # Random walk component
            delta = (random.random() - 0.5) * 2.0 * step
            # Sine-wave bias: slow ~60s period, small amplitude
            bias = math.sin(tick * 0.1 + hash(key) % 7) * step * 0.3
            new_val = _mock_readings[key] + delta + bias
            _mock_readings[key] = round(max(lo, min(hi, new_val)), 2)

        # Build a RoomStatus from the mock readings
        score = _score_from_mock()
        _mock_status = RoomStatus(
            reading=SensorReading(
                temperature_c=_mock_readings["Temperature"],
                humidity_pct=_mock_readings["Humidity"],
                light_lux=_mock_readings["Light"],
                noise_db=_mock_readings["Noise"],
                pressure_hpa=_mock_readings["Pressure"],
                pm25_ugm3=_mock_readings["Particulates"],
                voc_ppb=_mock_readings["Extra_VOCs"],
                timestamp_ms=int(time.time() * 1000),
            ),
            score=score,
            last_updated=datetime.now(timezone.utc),
            connected=False,  # no real hardware
        )

        logger.debug(
            f"Mock tick {tick}: score={score}  temp={_mock_readings['Temperature']}°C  "
            f"VOC={_mock_readings['Extra_VOCs']} ppb"
        )
        tick += 1
        await asyncio.sleep(2)


# ──────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the serial listener, mock loop, and load ML artefacts."""
    global _mlp_model, _mlp_scaler

    logger.info("🚀 RoomPulse backend starting up")

    # Load ML model + scaler ──────────────────
    if _MODEL_PATH.exists() and _SCALER_PATH.exists():
        try:
            _mlp_model = joblib.load(_MODEL_PATH)
            _mlp_scaler = joblib.load(_SCALER_PATH)
            logger.info(f"✅ MLP model loaded from {_MODEL_PATH}")
            logger.info(f"✅ Scaler  loaded from {_SCALER_PATH}")
        except Exception as e:
            logger.error(f"Failed to load ML artefacts: {e}")
            _mlp_model = None
            _mlp_scaler = None
    else:
        logger.warning(
            "⚠️  ML model files not found — run train_model.py first. "
            "POST /api/sensor-data will return 503."
        )

    # Start serial listener ───────────────────
    serial_task = asyncio.create_task(run_serial_listener())

    # Start mock sensor loop (if enabled) ─────
    mock_task = None
    if ENABLE_MOCK_DATA:
        mock_task = asyncio.create_task(_run_mock_sensor_loop())
    else:
        logger.info("Mock data disabled — waiting for real hardware")

    yield

    serial_task.cancel()
    if mock_task is not None:
        mock_task.cancel()
    logger.info("🛑 RoomPulse backend shutting down")


# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────
app = FastAPI(
    title="RoomPulse API",
    description="IoT Room Environment Monitoring — sensor data & health scoring",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server and Docker frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev default
        "http://localhost:3000",   # Alt port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://frontend:3000",    # Docker service name
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# API Routes
# ──────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "RoomPulse API", "status": "running"}


@app.get("/api/current-status", response_model=RoomStatus)
async def current_status():
    """
    Return the latest sensor reading and computed Room Health Score.

    If real hardware data has been POSTed, return that.
    Otherwise, if ENABLE_MOCK_DATA is True, return the simulated
    data from the background mock loop.

    The response includes:
    - `reading`: raw sensor values (null if no data yet)
    - `score`: composite health score 1–99 (0 = no data)
    - `last_updated`: UTC timestamp of last successful reading
    - `connected`: whether the serial port is active
    """
    real = get_current_status()

    # If we have real data from the Pico, always prefer it
    if real.reading is not None:
        return real

    # Fall back to simulated data when mock is enabled
    if ENABLE_MOCK_DATA and _mock_status is not None:
        return _mock_status

    return real


@app.get("/api/analyze")
async def analyze():
    """
    Run Gemini AI analysis on the latest sensor reading.

    Called on-demand (e.g., when the user clicks "Refresh Analysis").
    Returns a friendly summary and list of flagged concerns.
    """
    status = get_current_status()
    if status.reading is None:
        return {"summary": "No sensor data available yet.", "flags": []}

    reading_dict = status.reading.model_dump()
    result = generate_analysis(reading_dict, status.score)
    return result


# ──────────────────────────────────────────────
# NEW: Neural-network-powered sensor scoring
# ──────────────────────────────────────────────

@app.post("/api/sensor-data")
async def sensor_data(payload: SensorDataPayload):
    """
    Accept sensor readings (7 features), compute Room Score via the
    trained MLP (on 6 base features) + a VOC penalty from the 7th.

    **Hybrid Computation Layer**

    1. Extract the 6 base features, scale them, and run through the MLP
       to obtain the *Base_Room_Score*.
    2. Evaluate `Extra_VOCs` using the penalty function.
    3. Final score = clamp(Base_Room_Score − penalty, 1, 99).

    Returns
    -------
    JSON with base_score, voc_penalty, final_score, and features echo.
    """
    global _real_data_received
    _real_data_received = True  # real hardware is online

    if _mlp_model is None or _mlp_scaler is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "ML model is not loaded. Run `python train_model.py` to "
                "generate the model artefacts before using this endpoint."
            ),
        )

    # ── 1. Build the feature vector in training order ──
    feature_values = [
        payload.Temperature,
        payload.Humidity,
        payload.Pressure,
        payload.Light,
        payload.Noise,
        payload.Particulates,
    ]

    # Guard against NaN / None reaching the model
    if any(v is None or (isinstance(v, float) and np.isnan(v)) for v in feature_values):
        raise HTTPException(
            status_code=422,
            detail="One or more base feature values are missing or NaN.",
        )

    features_array = np.array(feature_values, dtype=np.float64).reshape(1, -1)

    # ── 2. Scale features and predict ──
    try:
        scaled = _mlp_scaler.transform(features_array)
        base_score = float(_mlp_model.predict(scaled)[0])
    except Exception as e:
        logger.error(f"Model inference failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Model inference error — check server logs.",
        )

    # ── 3. VOC penalty ──
    voc_penalty = compute_voc_penalty(payload.Extra_VOCs)

    # ── 4. Final score (clamped 1–99) ──
    final_score = clamp_score(base_score - voc_penalty)

    logger.info(
        f"Sensor POST → base={base_score:.2f}  penalty={voc_penalty:.2f}  "
        f"final={final_score}  VOC={payload.Extra_VOCs} ppb"
    )

    return {
        "base_score": round(base_score, 2),
        "voc_penalty": voc_penalty,
        "final_score": final_score,
        "features": {
            "Temperature": payload.Temperature,
            "Humidity": payload.Humidity,
            "Pressure": payload.Pressure,
            "Light": payload.Light,
            "Noise": payload.Noise,
            "Particulates": payload.Particulates,
            "Extra_VOCs": payload.Extra_VOCs,
        },
    }
