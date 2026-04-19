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
POLL_INTERVAL = 2

def main():
    print(f"📡 Device ID: {DEVICE_ID}")
    print(f"🔗 Target Backend: {BACKEND_URL}")
    print("\nStarting AirVita (Light + Audio Configuration)...")

    # 1. Initialize Light Sensor (Pins 3, 5)
    try:
        light_sensor = BH1750()
        light_sensor.init()
        print("✅ Light Sensor (GY-302) Detected.")
    except Exception as e:
        light_sensor = None
        print(f"⚠️ Light Sensor not found [Pins 3, 5]: {e}")

    # 2. Initialize Microphone (Pins 12, 35, 38)
    try:
        mic = MicrophoneHandler()
        print("✅ Microphone (INMP441) Initialized.")
    except Exception as e:
        mic = None
        print(f"⚠️ Microphone error [Pins 12, 35, 38]: {e}")

    # 3. Connectivity Check
    try:
        print("🔍 Checking AirVita Backend...")
        requests.get(f"{BACKEND_URL}/api/monitors", timeout=3)
        print("✅ Backend Reachable.")
    except:
        print("❌ Backend Unreachable. Data will be logged to console only.")

    print("\nMonitoring Active. Press Ctrl+C to exit.")

    try:
        while True:
            # Data Collection
            lux = light_sensor.read() if light_sensor else 0.0
            noise_db = mic.get_noise_level() if mic else 0.0

            # Payload (Mocking env data to satisfy backend requirements)
            payload = {
                "device_id": DEVICE_ID,
                "temperature": 22.0,  # No environmental sensor connected
                "humidity": 40.0,
                "pressure": 1013.25,
                "light": lux,
                "sound_amp": noise_db,
                "timestamp_ms": int(time.time() * 1000)
            }

            print(f"📤 Data: Light: {lux}lx | Noise: {noise_db}dB")

            # Upload
            try:
                requests.post(f"{BACKEND_URL}/api/sensor-data", json=payload, timeout=2)
            except:
                pass

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if light_sensor: light_sensor.close()

if __name__ == "__main__":
    main()
