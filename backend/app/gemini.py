"""
Gemini AI Analysis — AirVita

Sends current sensor readings to Gemini 2.0 Flash and returns a
research-backed health summary and list of flagged concerns.
"""

import json
import logging
import os
import time
from typing import Optional

logger = logging.getLogger("airvita.gemini")


# ──────────────────────────────────────────────
# Research context injected into every prompt
# ──────────────────────────────────────────────
_RESEARCH_CONTEXT = """
You are an indoor air quality and environmental health expert.
Analyze the following room sensor readings and provide a brief, friendly health summary
based on the scientific research standards listed below.

Reference standards:
- Temperature: ASHRAE Standard 55 — thermal comfort 20–24°C (68–75°F)
- Humidity: EPA — ideal 40–60% RH; below 30% causes dryness/static, above 60% promotes mold
- PM2.5: WHO 2021 guideline — annual mean < 5 µg/m³, 24-h mean < 15 µg/m³; > 35 µg/m³ is unhealthy

- Noise: WHO Environmental Noise Guidelines — < 35 dB for sleep, < 55 dB for daytime activity
- Light: IESNA — 300–500 lux for general office work; < 5 Lux for sleep
- Pressure: Normal atmospheric 1013 hPa; significant deviations affect comfort and weather

Respond ONLY with a valid JSON object in this exact format (no extra text, no markdown fences):
{
  "summary": "A 2-3 sentence friendly, encouraging summary of the current room environment and its suitability for both daytime activities and sleep.",
  "flags": ["Short concern #1", "Short concern #2"]
}

If everything is within ideal ranges, return an empty array for flags.
Keep flags concise (under 12 words each).
""".strip()


# ──────────────────────────────────────────────
# Analysis Cache Store
# ──────────────────────────────────────────────
_ANALYSIS_CACHE = {
    "data": None,
    "timestamp": None,
    "last_sensors": None, # dict of scores + key readings
    "last_room": None     # str room_type
}

from datetime import datetime, timedelta

def is_cache_valid(current_reading: dict, current_scores: dict, current_room_ctx: dict) -> bool:
    """
    Checks if we can reuse the cached analysis based on delta thresholds.
    Returns True if environment is stable enough to skip raw AI call.
    """
    if not _ANALYSIS_CACHE["data"] or not _ANALYSIS_CACHE["timestamp"]:
        return False
        
    # Max age of 4 minutes for cache hits during stability
    age = datetime.now() - _ANALYSIS_CACHE["timestamp"]
    if age > timedelta(minutes=4):
        return False

    # Check context identity
    current_room = current_room_ctx.get("room_type", "Unknown")
    if current_room != _ANALYSIS_CACHE["last_room"]:
        return False
        
    # Check sensor deltas
    last = _ANALYSIS_CACHE["last_sensors"]
    if not last: return False
    
    try:
        # Check health score shift (threshold: 3 points)
        score_shift = abs(current_scores.get("health", 0) - last.get("health", 0))
        if score_shift > 3: return False
        
        # Check specific sensor drifts (threshold: 2 units)
        for key, val in [("temperature_c", 2.0), ("humidity_pct", 5.0)]:
            delta = abs(current_reading.get(key, 0) - last.get(key, 0))
            if delta > val: return False
            
        return True
    except Exception:
        return False

def generate_analysis(reading: dict, scores: dict, room_ctx: dict) -> dict:
    """
    Call Gemini 2.0 Flash with current sensor readings.
    Includes Smart Caching to resolve 429 rate limits.
    """
    # ── Check Cache First ──
    if is_cache_valid(reading, scores, room_ctx):
        logger.info("Serving analysis from Smart Cache (Stable Environment)")
        return _ANALYSIS_CACHE["data"]

    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        logger.warning("GEMINI_API_KEY not set — skipping analysis")
        return _fallback("Gemini API key is not configured.")

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        objects_str = ", ".join(room_ctx.get('identified_objects', [])) if room_ctx.get('identified_objects') else "None detected"
        room_type = room_ctx.get('room_type', 'Unknown')
        
        sensor_lines = "\n".join([
            f"- AI Visual Room Classification: {room_type}",
            f"- AI Detected Objects: {objects_str}",
            f"- Temperature:  {reading.get('temperature_c', 'N/A')} °C",
            f"- Humidity:     {reading.get('humidity_pct', 'N/A')} %RH",
            f"- Light Level:  {reading.get('light_lux', 'N/A')} lux",
            f"- Noise Level:  {reading.get('noise_db', 'N/A')} dB",
            f"- Air Pressure: {reading.get('pressure_hpa', 'N/A')} hPa",
            f"- PM2.5:        {reading.get('pm25_ugm3', 'N/A')} µg/m³",

            f"- Room Health Score: {scores.get('health', 'N/A')}/99",
            f"- Sleep Conditions Score: {scores.get('sleep', 'N/A')}/99",
            f"- Work Conditions Score: {scores.get('work', 'N/A')}/99",
            f"- Fun/Social Conditions Score: {scores.get('fun', 'N/A')}/99",
        ])

        prompt = f"{_RESEARCH_CONTEXT}\n\nCurrent Context & Readings:\n{sensor_lines}"

        # ── Retry with Exponential Backoff ──
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=prompt,
                )
                raw = response.text.strip()

                # Strip markdown code fences
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                    raw = raw.strip()

                result = json.loads(raw)
                analysis_data = {
                    "summary": str(result.get("summary", "")),
                    "flags": [str(f) for f in result.get("flags", [])],
                }

                # ── Update Cache ──
                _ANALYSIS_CACHE["data"] = analysis_data
                _ANALYSIS_CACHE["timestamp"] = datetime.now()
                _ANALYSIS_CACHE["last_sensors"] = {**scores, **reading}
                _ANALYSIS_CACHE["last_room"] = room_type

                return analysis_data
            except Exception as e:
                last_exception = e
                err_str = str(e).upper()
                logger.error(f"Gemini attempt failing: {e}")
                
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "OVERLOADED" in err_str:
                    wait_time = (2 ** attempt) + 1
                    logger.warning(f"Gemini capacity hit (attempt {attempt+1}/{max_retries}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                if "404" in err_str or "NOT_FOUND" in err_str:
                    break
                break

        # Emergency Fallback: If quota reached but we have ANY old cache, show the old one 
        # instead of a "Quota reached" message to the user.
        err_str = str(last_exception)
        if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and _ANALYSIS_CACHE["data"]:
            logger.warning("Quota reached, serving stale cache as emergency fallback.")
            return _ANALYSIS_CACHE["data"]

        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            return _fallback("API quota reached. Please check your billing/usage tier or try again in a minute.")
        if "404" in err_str or "NOT_FOUND" in err_str:
            return _fallback(f"AI model not found ({last_exception}). Please verify your API key access.")
        
        logger.error(f"Final Gemini error: {last_exception}")
        return _fallback("AI analysis is temporarily unavailable (capacity exceeded).")

    except ImportError:
        logger.error("google-genai not installed. Run: pip install google-genai")
        return _fallback("AI analysis library not installed.")

    except json.JSONDecodeError as e:
        logger.error(f"Gemini returned invalid JSON: {e}")
        return _fallback("AI returned an unexpected response format.")

    except Exception as e:
        logger.error(f"Gemini initialization error: {e}")
        return _fallback("AI analysis is temporarily unavailable.")


def _fallback(reason: str) -> dict:
    """Return a safe default when Gemini is unavailable."""
    return {
        "summary": f"Analysis unavailable. {reason}",
        "flags": [],
    }
