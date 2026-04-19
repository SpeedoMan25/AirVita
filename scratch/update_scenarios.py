import sys
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path.cwd() / "backend"))

from app.scoring import calculate_room_health_score, calculate_sleep_score

scenarios_path = Path("backend/app/scenarios.json")
with open(scenarios_path, "r", encoding="utf-8") as f:
    scenarios = json.load(f)

for s in scenarios:
    inputs = s["inputs"]
    reading = {
        "temperature_c": inputs["temperature"],
        "humidity_pct": inputs["humidity"],
        "light_lux": inputs["light"],
        "noise_db": inputs["noise"],
        "pressure_hpa": inputs["pressure"],
        "pm25_ugm3": inputs["particulates"],
        "voc_ppb": inputs["vocs"]
    }
    health = calculate_room_health_score(reading)
    sleep = calculate_sleep_score(reading)
    s["expected"] = { "health": health, "sleep": sleep }

with open(scenarios_path, "w", encoding="utf-8") as f:
    json.dump(scenarios, f, indent=2)

print("Updated scenarios.json with ground truth scores.")
