import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.scoring import calculate_room_health_score, calculate_sleep_score
import json

scenarios_path = Path("backend/app/scenarios.json")
with open(scenarios_path, "r") as f:
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
    print(f"Scenario: {s['name']} -> Health: {health}, Sleep: {sleep}")
