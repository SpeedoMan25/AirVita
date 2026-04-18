"""
Gemini AI Analysis — RoomPulse

Sends current sensor readings to Gemini 2.0 Flash and returns a
research-backed health summary and list of flagged concerns.
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger("roompulse.gemini")


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
- VOCs: EPA — total VOC concern starts ~500 ppb; > 1000 ppb indicates poor ventilation
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


def generate_analysis(reading: dict, score: int, sleep_score: int) -> dict:
    """
    Call Gemini 2.0 Flash with current sensor readings and return
    a dict with keys: summary (str), flags (list[str]).

    Falls back to a safe default on any error.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set — skipping analysis")
        return _fallback("Gemini API key is not configured.")

    try:
        from google import genai  # lazily imported so missing dep doesn't crash app startup

        client = genai.Client(api_key=api_key)

        sensor_lines = "\n".join([
            f"- Temperature:  {reading.get('temperature_c', 'N/A')} °C",
            f"- Humidity:     {reading.get('humidity_pct', 'N/A')} %RH",
            f"- Light Level:  {reading.get('light_lux', 'N/A')} lux",
            f"- Noise Level:  {reading.get('noise_db', 'N/A')} dB",
            f"- Air Pressure: {reading.get('pressure_hpa', 'N/A')} hPa",
            f"- PM2.5:        {reading.get('pm25_ugm3', 'N/A')} µg/m³",
            f"- VOCs:         {reading.get('voc_ppb', 'N/A')} ppb",
            f"- Room Health Score: {score}/99",
            f"- Sleep Conditions Score: {sleep_score}/99",
        ])

        prompt = f"{_RESEARCH_CONTEXT}\n\nCurrent Readings:\n{sensor_lines}"

        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
        )

        raw = response.text.strip()

        # Strip markdown code fences if the model adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        result = json.loads(raw)

        return {
            "summary": str(result.get("summary", "")),
            "flags": [str(f) for f in result.get("flags", [])],
        }

    except ImportError:
        logger.error("google-genai not installed. Run: pip install google-genai")
        return _fallback("AI analysis library not installed.")

    except json.JSONDecodeError as e:
        logger.error(f"Gemini returned invalid JSON: {e}")
        return _fallback("AI returned an unexpected response format.")

    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            logger.warning("Gemini quota exceeded")
            return _fallback("API quota reached — please try again shortly.")
        logger.error(f"Gemini error: {e}")
        return _fallback("AI analysis is temporarily unavailable.")


def _fallback(reason: str) -> dict:
    """Return a safe default when Gemini is unavailable."""
    return {
        "summary": f"Analysis unavailable. {reason}",
        "flags": [],
    }
