"""
Serial Reader — Reads JSON payloads from the Raspberry Pi Pico over USB.

Runs as a background asyncio task inside the FastAPI application.
When MOCK_SERIAL is enabled, it generates fake data locally so you
can develop the full stack without hardware connected.
"""

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from typing import Optional

from app.models import SensorReading, RoomStatus
from app.scoring import calculate_room_health_score

logger = logging.getLogger("airvita.serial")

# No longer using local _current_status, mapping directly to main monitors
DEVID = "Wired-Pico"


# get_current_status no longer needed as main.py handles registry


# ──────────────────────────────────────────────
# Mock data generator (mirrors the Pico's random walk)
# ──────────────────────────────────────────────
_mock_state = {
    "temperature_c": 22.0,
    "humidity_pct": 50.0,
    "light_lux": 400.0,
    "noise_db": 35.0,
    "pressure_hpa": 1013.0,
    "pm25_ugm3": 12.0,
}

_mock_bounds = {
    "temperature_c": (15.0, 35.0, 0.3),
    "humidity_pct": (20.0, 90.0, 1.0),
    "light_lux": (0.0, 1000.0, 15.0),
    "noise_db": (20.0, 90.0, 2.0),
    "pressure_hpa": (980.0, 1040.0, 0.5),
    "pm25_ugm3": (0.0, 150.0, 3.0),
}


def _generate_mock_reading() -> str:
    """Produce a JSON string that mimics Pico output."""
    for key, (lo, hi, step) in _mock_bounds.items():
        delta = (random.random() - 0.5) * 2 * step
        _mock_state[key] = max(lo, min(hi, round(_mock_state[key] + delta, 2)))

    payload = dict(_mock_state)
    
    # Simulation: Occasionally lose data on some sensors
    # Roughly every ~10s (5 intervals of 2s)
    if random.random() < 0.2:
        if "pm25_ugm3" in payload:
            del payload["pm25_ugm3"]

    payload["timestamp_ms"] = int(time.time() * 1000)
    payload["device_id"] = DEVID
    return json.dumps(payload)


# ──────────────────────────────────────────────
# Serial reading loop
# ──────────────────────────────────────────────

async def _process_line(line: str) -> None:
    """Parse a JSON line from serial and update shared state in main registry."""
    from app.main import update_status_from_dict
    try:
        data = json.loads(line)
        update_status_from_dict(data, device_id=DEVID)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Failed to parse serial data: {e} | raw: {line!r}")


async def run_serial_listener() -> None:
    """
    Main serial listener coroutine.

    Reads lines from the USB serial port (or generates mock data)
    and updates the in-memory application state.
    """
    use_mock = os.getenv("MOCK_SERIAL", "false").lower() in ("true", "1", "yes")
    port = os.getenv("SERIAL_PORT", "COM3")
    baud = int(os.getenv("SERIAL_BAUD", "115200"))

    if use_mock:
        logger.info("🧪 Running in MOCK mode — generating fake sensor data")
        while True:
            line = _generate_mock_reading()
            await _process_line(line)
            await asyncio.sleep(2)
    else:
        # Real serial reading with pyserial
        try:
            import serial  # pyserial
        except ImportError:
            logger.error("pyserial is not installed. Run: pip install pyserial")
            return

        logger.info(f"🔌 Connecting to serial port {port} @ {baud} baud")
        ser: Optional[serial.Serial] = None

        while True:
            try:
                if ser is None or not ser.is_open:
                    ser = serial.Serial(port, baud, timeout=1)
                    logger.info(f"✅ Serial port {port} opened")

                # Read from serial in a separate thread so we don't block the FastAPI event loop!
                raw = await asyncio.to_thread(ser.readline)
                
                if raw:
                    line = raw.decode("utf-8", errors="replace").strip()
                    if line:
                        await _process_line(line)
                else:
                    await asyncio.sleep(0.01)

            except serial.SerialException as e:
                logger.error(f"Serial error: {e}. Retrying in 3s...")
                if ser and ser.is_open:
                    ser.close()
                ser = None
                await asyncio.sleep(3)

            except Exception as e:
                logger.error(f"Unexpected error in serial reader: {e}")
                await asyncio.sleep(1)
