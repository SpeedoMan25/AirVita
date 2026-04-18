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
        "abs_min": 15.0,   "abs_max": 32.0,
        "weight": 0.15,
    },
    "humidity_pct": {
        "ideal_low": 35.0, "ideal_high": 55.0,
        "abs_min": 10.0,   "abs_max": 90.0,
        "weight": 0.10,
    },
    "light_lux": {
        "ideal_low": 100.0, "ideal_high": 600.0,
        "abs_min": 0.0,     "abs_max": 2000.0,
        "weight": 0.10,
    },
    "noise_db": {
        "ideal_low": 20.0, "ideal_high": 50.0,
        "abs_min": 10.0,   "abs_max": 95.0,
        "weight": 0.20,
    },
    "pressure_hpa": {
        "ideal_low": 1000.0, "ideal_high": 1025.0,
        "abs_min": 950.0,    "abs_max": 1080.0,
        "weight": 0.05,
    },
    "pm25_ugm3": {
        "ideal_low": 0.0,  "ideal_high": 12.0,
        "abs_min": 0.0,    "abs_max": 150.0,
        "weight": 0.20,
    },
    "voc_ppb": {
        "ideal_low": 0.0,  "ideal_high": 250.0,
        "abs_min": 0.0,    "abs_max": 1500.0,
        "weight": 0.20,
    },
}


# Sleep-specific scoring configuration
# Focused on darkness, low noise, and cooler temperatures
SLEEP_SENSOR_CONFIG: Dict[str, dict] = {
    "temperature_c": {
        "ideal_low": 16.0, "ideal_high": 19.0,
        "abs_min": 10.0,   "abs_max": 28.0,
        "weight": 0.30,
    },
    "humidity_pct": {
        "ideal_low": 30.0, "ideal_high": 50.0,
        "abs_min": 10.0,   "abs_max": 80.0,
        "weight": 0.10,
    },
    "light_lux": {
        "ideal_low": 0.0,  "ideal_high": 5.0,
        "abs_min": 0.0,    "abs_max": 50.0,
        "weight": 0.30,
    },
    "noise_db": {
        "ideal_low": 20.0, "ideal_high": 35.0,
        "abs_min": 10.0,   "abs_max": 60.0,
        "weight": 0.20,
    },
    "pm25_ugm3": {
        "ideal_low": 0.0,  "ideal_high": 15.0,
        "abs_min": 0.0,    "abs_max": 50.0,
        "weight": 0.05,
    },
    "voc_ppb": {
        "ideal_low": 0.0,  "ideal_high": 300.0,
        "abs_min": 0.0,    "abs_max": 1000.0,
        "weight": 0.05,
    },
}


# Study-specific scoring configuration
# Focused on high light levels, low noise, and cool temperatures for alertness
STUDY_SENSOR_CONFIG: Dict[str, dict] = {
    "temperature_c": {
        "ideal_low": 19.0, "ideal_high": 22.0,
        "abs_min": 15.0,   "abs_max": 28.0,
        "weight": 0.15,
    },
    "humidity_pct": {
        "ideal_low": 35.0, "ideal_high": 50.0,
        "abs_min": 10.0,   "abs_max": 80.0,
        "weight": 0.05,
    },
    "light_lux": {
        "ideal_low": 300.0, "ideal_high": 700.0,
        "abs_min": 50.0,    "abs_max": 2000.0,
        "weight": 0.35,
    },
    "noise_db": {
        "ideal_low": 20.0, "ideal_high": 45.0,
        "abs_min": 10.0,   "abs_max": 75.0,
        "weight": 0.25,
    },
    "pm25_ugm3": {
        "ideal_low": 0.0,  "ideal_high": 12.0,
        "abs_min": 0.0,    "abs_max": 50.0,
        "weight": 0.10,
    },
    "voc_ppb": {
        "ideal_low": 0.0,  "ideal_high": 200.0,
        "abs_min": 0.0,    "abs_max": 1000.0,
        "weight": 0.10,
    },
}


# Work-specific scoring configuration
# Focused on moderate light levels and tolerance for typical office noise
WORK_SENSOR_CONFIG: Dict[str, dict] = {
    "temperature_c": {
        "ideal_low": 20.0, "ideal_high": 23.0,
        "abs_min": 15.0,   "abs_max": 30.0,
        "weight": 0.15,
    },
    "humidity_pct": {
        "ideal_low": 35.0, "ideal_high": 55.0,
        "abs_min": 10.0,   "abs_max": 85.0,
        "weight": 0.05,
    },
    "light_lux": {
        "ideal_low": 250.0, "ideal_high": 600.0,
        "abs_min": 100.0,   "abs_max": 1500.0,
        "weight": 0.25,
    },
    "noise_db": {
        "ideal_low": 20.0, "ideal_high": 55.0,
        "abs_min": 10.0,   "abs_max": 85.0,
        "weight": 0.25,
    },
    "pm25_ugm3": {
        "ideal_low": 0.0,  "ideal_high": 15.0,
        "abs_min": 0.0,    "abs_max": 60.0,
        "weight": 0.15,
    },
    "voc_ppb": {
        "ideal_low": 0.0,  "ideal_high": 300.0,
        "abs_min": 0.0,    "abs_max": 1200.0,
        "weight": 0.15,
    },
}


# Fun/Social-specific scoring configuration
# Focused on dimmer light, higher temperature tolerance, and high noise tolerance
FUN_SENSOR_CONFIG: Dict[str, dict] = {
    "temperature_c": {
        "ideal_low": 21.0, "ideal_high": 25.0,
        "abs_min": 15.0,   "abs_max": 32.0,
        "weight": 0.10,
    },
    "humidity_pct": {
        "ideal_low": 30.0, "ideal_high": 60.0,
        "abs_min": 10.0,   "abs_max": 90.0,
        "weight": 0.10,
    },
    "light_lux": {
        "ideal_low": 50.0,  "ideal_high": 250.0,
        "abs_min": 0.0,     "abs_max": 1000.0,
        "weight": 0.20,
    },
    "noise_db": {
        "ideal_low": 40.0, "ideal_high": 80.0,
        "abs_min": 20.0,   "abs_max": 100.0,
        "weight": 0.30,
    },
    "pm25_ugm3": {
        "ideal_low": 0.0,  "ideal_high": 25.0,
        "abs_min": 0.0,    "abs_max": 100.0,
        "weight": 0.15,
    },
    "voc_ppb": {
        "ideal_low": 0.0,  "ideal_high": 400.0,
        "abs_min": 0.0,    "abs_max": 1500.0,
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


def calculate_room_health_score(readings: dict, outdoor: dict = None) -> int:
    """
    Calculate the Room Health Score (1–99) from raw sensor readings.
    Optionally refines the score based on outdoor comparative conditions.
    """
    base_score = _calculate_weighted_score(readings, SENSOR_CONFIG)
    
    if outdoor:
        return apply_outdoor_refinements(base_score, readings, outdoor)
    return base_score


def apply_outdoor_refinements(indoor_score: int, indoor_readings: dict, outdoor_readings: dict) -> int:
    """
    Applies comparative adjustments to the room score based on outdoor conditions.
    Example: Rewarding effective air filtration when outdoor AQI is poor.
    """
    bonus = 0
    
    # 1. Protection Bonus (AQI)
    outdoor_pm = outdoor_readings.get("pm25_ugm3", 0)
    indoor_pm = indoor_readings.get("pm25_ugm3", 0)
    
    if outdoor_pm > 35 and indoor_pm < 15:
        # Significant delta, room is an effective shelter
        bonus += 5
    elif outdoor_pm > 25 and indoor_pm < 12:
        bonus += 3
        
    # 2. Thermal Stability Bonus
    outdoor_temp = outdoor_readings.get("temperature_c", 22)
    indoor_temp = indoor_readings.get("temperature_c", 22)
    if (outdoor_temp < 10 or outdoor_temp > 30) and (20 <= indoor_temp <= 24):
        bonus += 2

    return min(99, indoor_score + bonus)


def calculate_sleep_score_with_breakdown(readings: dict) -> Dict:
    """
    Calculate the Sleeping Conditions Score (1–99) with breakdown.
    """
    return calculate_weighted_score_with_breakdown(readings, SLEEP_SENSOR_CONFIG)


def calculate_study_score_with_breakdown(readings: dict) -> Dict:
    """
    Calculate the Study Conditions Score (1–99) with breakdown.
    """
    return calculate_weighted_score_with_breakdown(readings, STUDY_SENSOR_CONFIG)


def calculate_work_score_with_breakdown(readings: dict) -> Dict:
    """
    Calculate the Work Conditions Score (1–99) with breakdown.
    """
    return calculate_weighted_score_with_breakdown(readings, WORK_SENSOR_CONFIG)


def calculate_fun_score_with_breakdown(readings: dict) -> Dict:
    """
    Calculate the Fun/Social Conditions Score (1–99) with breakdown.
    """
    return calculate_weighted_score_with_breakdown(readings, FUN_SENSOR_CONFIG)


def calculate_weighted_score_with_breakdown(readings: dict, config: Dict[str, dict]) -> Dict:
    """
    Calculate a composite score and its mathematical breakdown.
    Returns: { "score": int, "breakdown": List[dict] }
    """
    weighted_sum = 0.0
    total_weight = 0.0
    contributors = []

    for sensor_key, cfg in config.items():
        value = readings.get(sensor_key)
        if value is None:
            continue

        ss = _sub_score(
            value,
            cfg["ideal_low"], cfg["ideal_high"],
            cfg["abs_min"], cfg["abs_max"],
        )
        contribution = ss * cfg["weight"]
        weighted_sum += contribution
        total_weight += cfg["weight"]
        
        contributors.append({
            "sensor": sensor_key,
            "value": value,
            "sub_score": ss,
            "weight": cfg["weight"],
            "points": contribution
        })

    if total_weight == 0:
        return {"score": 1, "breakdown": []}

    raw_score = weighted_sum / total_weight
    # Map from 0-100 internal scale to 1-99 output
    final = int(round(raw_score * 0.98 + 1))
    clamped = max(1, min(99, final))
    
    return {
        "score": clamped,
        "breakdown": contributors
    }


def _calculate_weighted_score(readings: dict, config: Dict[str, dict]) -> int:
    """Legacy utility for backward compatibility."""
    res = calculate_weighted_score_with_breakdown(readings, config)
    return res["score"]
