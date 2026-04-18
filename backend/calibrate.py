import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from app.scoring import calculate_room_health_score, calculate_sleep_score

# Paths
ROOT_DIR = Path(__file__).parent
SCENARIOS_PATH = ROOT_DIR / "app" / "scenarios.json"
MODEL_PATH = ROOT_DIR / "model" / "mlp_model.pkl"
SCALER_PATH = ROOT_DIR / "model" / "scaler.pkl"

def run_calibration():
    print("\n" + "="*80)
    print(" ROOMPULSE SCORE CALIBRATION SYSTEM")
    print("="*80)

    # 1. Load Scenarios
    if not SCENARIOS_PATH.exists():
        print(f"Error: Scenarios file not found at {SCENARIOS_PATH}")
        return
    
    with open(SCENARIOS_PATH, 'r', encoding='utf-8') as f:
        all_scenarios = json.load(f)
    
    # Filter for scenarios that have expectations
    scenarios = [s for s in all_scenarios if "expected" in s]

    if not scenarios:
        print("No scenarios with 'expected' scores found in scenarios.json.")
        return

    # 2. Load MLP Model (for comparison)
    model = None
    scaler = None
    if MODEL_PATH.exists() and SCALER_PATH.exists():
        try:
            model = joblib.load(MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
            print("Successfully loaded MLP Model for comparison.")
        except Exception as e:
            print(f"Warning: Could not load MLP model: {e}")
    else:
        print("Warning: MLP Model not found. Comparing only against manual formulas.")

    print(f"\nEvaluating {len(scenarios)} scenarios...")
    print("-" * 115)
    header = f"{'Scenario Name':<25} | {'Metric':<10} | {'Expected':<10} | {'Manual':<10} | {'ML Model':<10} | {'Delta (%)':<10}"
    print(header)
    print("-" * 115)

    total_error_manual = 0
    total_error_ml = 0
    ml_count = 0

    for s in scenarios:
        name = s['name']
        inputs = s['inputs']
        expected = s['expected']

        # Prepare dict for manual scoring (names must match SENSOR_CONFIG)
        reading_dict = {
            "temperature_c": inputs['temperature'],
            "humidity_pct": inputs['humidity'],
            "light_lux": inputs['light'],
            "noise_db": inputs['noise'],
            "pressure_hpa": inputs['pressure'],
            "pm25_ugm3": inputs['particulates'],
            "voc_ppb": inputs['vocs']
        }

        # --- Health Score ---
        manual_health = calculate_room_health_score(reading_dict)
        ml_health = "N/A"
        
        if model and scaler:
            # Features order matching train_model.py
            feature_names = ["humidity", "pressure", "light", "temperature", "sound_high", "sound_mid", "sound_low", "sound_amp"]
            # Map inputs to features (estimating high/mid/low sounds for now as we don't have them in calibration JSON)
            features_raw = [inputs['humidity'], inputs['pressure'], inputs['light'], inputs['temperature'], 10.0, 10.0, 10.0, inputs['noise']]
            df = pd.DataFrame([features_raw], columns=feature_names)
            scaled = scaler.transform(df)
            ml_health_base = float(model.predict(scaled)[0])
            
            # Apply IAQ penalties (Matching main.py)
            COEFF_VOC = -0.02
            COEFF_PARTICLES = -0.05
            ml_health = int(max(1, min(99, round(ml_health_base + (inputs['vocs'] * COEFF_VOC) + (inputs['particulates'] * COEFF_PARTICLES)))))
            
            error_ml = abs(ml_health - expected['health'])
            total_error_ml += error_ml
            ml_count += 1
            ml_str = f"{ml_health:>10}"
            delta_ml = f"{ (error_ml / 99 * 100):>9.1f}%"
        else:
            ml_str = f"{'N/A':>10}"
            delta_ml = f"{'N/A':>10}"

        error_manual = abs(manual_health - expected['health'])
        total_error_manual += error_manual
        delta_manual = (error_manual / 99 * 100)
        
        print(f"{name[:25]:<25} | {'Health':<10} | {expected['health']:>10} | {manual_health:>10} | {ml_str} | {delta_manual:>9.1f}%")

        # --- Sleep Score ---
        manual_sleep = calculate_sleep_score(reading_dict)
        error_sleep = abs(manual_sleep - expected['sleep'])
        delta_sleep = (error_sleep / 99 * 100)
        
        print(f"{'':<25} | {'Sleep':<10} | {expected['sleep']:>10} | {manual_sleep:>10} | {'-':>10} | {delta_sleep:>9.1f}%")
        print("-" * 115)

    print("\nSUMMARY")
    print(f"Average Delta (Manual Health): { (total_error_manual / len(scenarios) / 99 * 100):.2f}%")
    if ml_count > 0:
        print(f"Average Delta (ML Model Health): { (total_error_ml / ml_count / 99 * 100):.2f}%")
    print("="*80)

if __name__ == "__main__":
    run_calibration()
