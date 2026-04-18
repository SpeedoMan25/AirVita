"""
Room Health Score Algorithm

Calculates a composite score from 1 (hazardous) to 99 (ideal)
based on weighted sub-scores for each sensor reading.

Each sub-score is computed as:
  - 100 if the value is within the ideal range
  - Linearly decreasing toward 0 as it deviates from the ideal range
  - Clamped to [0, 100]

The final score is a weighted sum, clamped to [1, 99].
"""

from typing import Dict

# ──────────────────────────────────────────────
# Sensor scoring configuration
# ──────────────────────────────────────────────
# Each entry: (ideal_low, ideal_high, absolute_min, absolute_max, weight)
# - ideal_low..ideal_high: value range that scores 100
# - absolute_min..absolute_max: value range outside which score = 0
# - weight: contribution to final composite score

SENSOR_CONFIG: Dict[str, dict] = {
    "temperature_c": {
        "ideal_low": 20.0, "ideal_high": 24.0,
        "abs_min": 10.0,   "abs_max": 38.0,
        "weight": 0.20,
    },
    "humidity_pct": {
        "ideal_low": 40.0, "ideal_high": 60.0,
        "abs_min": 10.0,   "abs_max": 95.0,
        "weight": 0.15,
    },
    "light_lux": {
        "ideal_low": 300.0, "ideal_high": 500.0,
        "abs_min": 0.0,     "abs_max": 1200.0,
        "weight": 0.10,
    },
    "noise_db": {
        # Lower is better — ideal is 20-40 dB
        "ideal_low": 20.0, "ideal_high": 40.0,
        "abs_min": 0.0,    "abs_max": 100.0,
        "weight": 0.15,
    },
    "pressure_hpa": {
        "ideal_low": 1000.0, "ideal_high": 1025.0,
        "abs_min": 960.0,    "abs_max": 1060.0,
        "weight": 0.10,
    },
    "pm25_ugm3": {
        # Lower is better — ideal is 0-35 µg/m³
        "ideal_low": 0.0,  "ideal_high": 35.0,
        "abs_min": 0.0,    "abs_max": 250.0,
        "weight": 0.15,
    },
    "voc_ppb": {
        # Lower is better — ideal is 0-300 ppb
        "ideal_low": 0.0,  "ideal_high": 300.0,
        "abs_min": 0.0,    "abs_max": 2000.0,
        "weight": 0.15,
    },
}


def _sub_score(value: float, ideal_low: float, ideal_high: float,
               abs_min: float, abs_max: float) -> float:
    """
    Compute a sub-score from 0 to 100 for a single sensor.

    Returns 100 if value is within [ideal_low, ideal_high].
    Linearly decays toward 0 outside the ideal range, reaching 0
    at abs_min (below ideal) or abs_max (above ideal).
    """
    if ideal_low <= value <= ideal_high:
        return 100.0

    if value < ideal_low:
        span = ideal_low - abs_min
        if span <= 0:
            return 0.0
        return max(0.0, 100.0 * (value - abs_min) / span)
    else:  # value > ideal_high
        span = abs_max - ideal_high
        if span <= 0:
            return 0.0
        return max(0.0, 100.0 * (abs_max - value) / span)


def calculate_room_health_score(readings: dict) -> int:
    """
    Calculate the Room Health Score (1–99) from raw sensor readings.

    Parameters
    ----------
    readings : dict
        Keys matching SENSOR_CONFIG (e.g. "temperature_c", "humidity_pct", ...).

    Returns
    -------
    int
        Composite score clamped to [1, 99].
    """
    weighted_sum = 0.0
    total_weight = 0.0

    for sensor_key, cfg in SENSOR_CONFIG.items():
        value = readings.get(sensor_key)
        if value is None:
            continue

        ss = _sub_score(
            value,
            cfg["ideal_low"], cfg["ideal_high"],
            cfg["abs_min"], cfg["abs_max"],
        )
        weighted_sum += ss * cfg["weight"]
        total_weight += cfg["weight"]

    if total_weight == 0:
        return 1  # No data → worst score

    raw_score = weighted_sum / total_weight
    # Map from 0-100 internal scale to 1-99 output
    final = int(round(raw_score * 0.98 + 1))
    return max(1, min(99, final))
