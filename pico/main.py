"""
RoomPulse — Raspberry Pi Pico Edge Code (MicroPython)

This script runs on a Raspberry Pi Pico (standard, no Wi-Fi).
It reads from wired sensors and prints JSON payloads over USB serial
at a configurable interval.

When real sensors are not connected, it generates realistic mock data
with smooth random walk so you can test the full data pipeline immediately.

Sensors Supported:
  - Temperature (°C)       — e.g., DHT22 / BME280
  - Humidity (%RH)         — e.g., DHT22 / BME280
  - Light Level (lux)      — e.g., BH1750 / LDR + ADC
  - Noise Level (dB)       — e.g., MAX4466 analog mic + ADC
  - Air Pressure (hPa)     — e.g., BMP280 / BME280
  - Particles (µg/m³)      — e.g., PMS5003 (PM2.5)
  - VOCs (ppb)             — e.g., SGP30 / CCS811
"""

import json
import time

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
READING_INTERVAL_S = 2  # seconds between readings
USE_MOCK = True          # Set to False when real sensor drivers are wired up

# ──────────────────────────────────────────────
# Mock Data Generator (random walk with bounds)
# ──────────────────────────────────────────────

# Simple pseudo-random number generator for MicroPython
# (works even without the `random` module on some Pico builds)
_seed = int(time.ticks_ms())

def _pseudo_random():
    """Returns a float between 0.0 and 1.0 using an LCG."""
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7FFFFFFF
    return (_seed >> 16) / 32767.0

def _clamp(value, lo, hi):
    """Clamp a value between lo and hi."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value

# Current mock values (starting points)
_mock_state = {
    "temperature_c":   22.0,
    "humidity_pct":    50.0,
    "light_lux":       400.0,
    "noise_db":        35.0,
    "pressure_hpa":    1013.0,
    "pm25_ugm3":       12.0,
    "voc_ppb":         150.0,
}

# Bounds and max step sizes for random-walk
_mock_config = {
    "temperature_c":   {"min": 15.0,  "max": 35.0,  "step": 0.3},
    "humidity_pct":    {"min": 20.0,  "max": 90.0,  "step": 1.0},
    "light_lux":       {"min": 0.0,   "max": 1000.0,"step": 15.0},
    "noise_db":        {"min": 20.0,  "max": 90.0,  "step": 2.0},
    "pressure_hpa":    {"min": 980.0, "max": 1040.0,"step": 0.5},
    "pm25_ugm3":       {"min": 0.0,   "max": 150.0, "step": 3.0},
    "voc_ppb":         {"min": 0.0,   "max": 1500.0,"step": 20.0},
}


def _read_mock_sensors():
    """
    Advances the random-walk mock state and returns a sensor dict.
    Values drift naturally, making the dashboard feel alive.
    """
    for key, cfg in _mock_config.items():
        delta = ((_pseudo_random() - 0.5) * 2.0) * cfg["step"]
        _mock_state[key] = _clamp(
            round(_mock_state[key] + delta, 2),
            cfg["min"],
            cfg["max"],
        )
    return dict(_mock_state)


# ──────────────────────────────────────────────
# Real Sensor Reading (stubs – fill in per your wiring)
# ──────────────────────────────────────────────

def _read_real_sensors():
    """
    Replace the body of this function with actual sensor driver calls.
    Each driver should already be initialized in setup().
    """
    # Example (pseudo-code):
    # temp, hum = dht_sensor.read()
    # lux = light_sensor.read()
    # ...
    return {
        "temperature_c":   0.0,
        "humidity_pct":    0.0,
        "light_lux":       0.0,
        "noise_db":        0.0,
        "pressure_hpa":    0.0,
        "pm25_ugm3":       0.0,
        "voc_ppb":         0.0,
    }


# ──────────────────────────────────────────────
# Main Loop
# ──────────────────────────────────────────────

def setup():
    """
    Initialize sensor drivers here when USE_MOCK is False.
    For example: i2c = I2C(0, sda=Pin(0), scl=Pin(1))
    """
    pass


def loop():
    """Continuously read sensors and print JSON over USB serial."""
    read_fn = _read_mock_sensors if USE_MOCK else _read_real_sensors

    while True:
        payload = read_fn()
        payload["timestamp_ms"] = time.ticks_ms()
        print(json.dumps(payload))
        time.sleep(READING_INTERVAL_S)


# Entry point
setup()
loop()
