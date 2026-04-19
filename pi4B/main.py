import os
import time
import json
import requests
import uuid
import sys

# Setup paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
try:
    from bh1750 import BH1750
    from mic_handler import MicrophoneHandler
except ImportError as e:
    print(f"❌ Driver Import Error: {e}")
    print("Ensure all files are in pi4B/lib/")

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").strip(' "\u201d\u201c')
DEVICE_ID = os.getenv("DEVICE_ID", hex(uuid.getnode()))
POLL_INTERVAL = 1.0 # Faster polling for live feeling

def main():
    print(f"📡 Device ID: {DEVICE_ID}")
    print(f"🔗 Target Backend: {BACKEND_URL}")
    print("\nAirVita Live Hardware Mode (GY-302 Light + INMP441 Audio)")
    print("-" * 50)

    # 1. Initialize Light Sensor (Pins 3, 5)
    light_sensor = None
    try:
        light_sensor = BH1750()
        light_sensor.init()
        # Verify it works immediately
        test_lx = light_sensor.read()
        print(f"✅ Light Sensor Active: {test_lx} Lux")
    except Exception as e:
        print(f"⚠️ Light Sensor (BH1750) not responding on I2C (Pins 3, 5).")
        print(f"   Check your wiring and ensure 'dtparam=i2c_arm=on' is in config.txt")

    # 2. Initialize Microphone (Pins 12, 35, 38)
    mic = None
    try:
        mic = MicrophoneHandler()
        # Test it
        test_db = mic.get_noise_level()
        print(f"✅ Audio Active: {test_db} dB")
    except Exception as e:
        print(f"⚠️ Microphone error (INMP441). Ensure I2S is enabled.")

    print("\nMonitoring Started. Data flow is LIVE.")

    try:
        while True:
            # Data Collection
            # We ONLY collect what we have. No more mock values.
            payload = {
                "device_id": DEVICE_ID,
                "timestamp_ms": int(time.time() * 1000)
            }

            if light_sensor:
                payload["light"] = light_sensor.read()
            
            if mic:
                payload["sound_amp"] = mic.get_noise_level()

            # Output
            l_val = payload.get("light", "N/A")
            n_val = payload.get("sound_amp", "N/A")
            print(f"📤 [LIVE] Light: {l_val} lx | Noise: {n_val} dB")

            # Upload to Backend
            try:
                requests.post(f"{BACKEND_URL}/api/sensor-data", json=payload, timeout=0.8)
            except:
                pass

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if light_sensor: light_sensor.close()

if __name__ == "__main__":
    main()
