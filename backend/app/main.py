"""
RoomPulse — FastAPI Backend

Serves the latest sensor data and health score via a REST API.
Launches the serial reader as a background task on startup.

On startup, loads the pre-trained MLP model and scaler (.pkl) into
memory so the POST /api/sensor-data route can perform real-time
inference without re-loading on every request.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
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
# Lifespan (startup / shutdown)
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the serial listener and load ML artefacts at startup."""
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
    task = asyncio.create_task(run_serial_listener())
    yield
    task.cancel()
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

    The response includes:
    - `reading`: raw sensor values (null if no data yet)
    - `score`: composite health score 1–99 (0 = no data)
    - `last_updated`: UTC timestamp of last successful reading
    - `connected`: whether the serial port is active
    """
    return get_current_status()


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
