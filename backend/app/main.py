"""
RoomPulse — FastAPI Backend

Serves the latest sensor data and health score via a REST API.
Launches the serial reader as a background task on startup.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
# Lifespan (startup / shutdown)
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the serial listener in the background when the app starts."""
    logger.info("🚀 RoomPulse backend starting up")
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
    version="1.0.0",
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
