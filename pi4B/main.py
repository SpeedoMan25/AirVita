import os
import time
import json
import requests
import uuid
import sys

# Import custom drivers from lib/
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
try:
    from bme688 import BME688
    from bh1750 import BH1750
    from pms5003 import PMS5003
    from mic_handler import MicrophoneHandler
except ImportError as e:
    print(f"❌ Driver Import Error: {e}")
    print("Ensure all files are in pi4B/lib/")

# --- Configuration ---
# Allow setting backend via environment variable
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").strip(' "\u201d\u201c')
DEVICE_ID = os.getenv("DEVICE_ID", hex(uuid.getnode())) # MAC address based ID
POLL_INTERVAL = 2  # Seconds

def main():
    print(f"📡 Device ID: {DEVICE_ID}")
    print(f"🔗 Target Backend: {BACKEND_URL}")
    print("Initializing AirVita Sensor Suite...")

    # Initialize Drivers
    # BME688 (Environment)
    try:
        bme = BME688()
        print("✅ BME688 Initialized (I2C 0x76)")
    except Exception as e:
        bme = None
        print(f"⚠️ BME688 not found: {e}")

    # BH1750 (Light)
    try:
        light_sensor = BH1750()
        light_sensor.init()
        print("✅ BH1750 Initialized (I2C 0x23)")
    except Exception as e:
        light_sensor = None
        print(f"⚠️ BH1750 not found: {e}")

    # PMS5003 (Particulates)
    try:
        pms = PMS5003()
        print("✅ PMS5003 Initialized (Serial)")
    except Exception as e:
        pms = None
        print(f"⚠️ PMS5003 not found: {e}")

    # Microphone (Noise)
    try:
        mic = MicrophoneHandler()
        print("✅ Microphone Initialized (ALSA)")
    except Exception as e:
        mic = None
        print(f"⚠️ Microphone not found: {e}")

    # Check Connectivity
    try:
        print("🔍 Checking backend connectivity...")
        requests.get(f"{BACKEND_URL}/api/monitors", timeout=3)
        print("✅ Successfully connected to AirVita backend!")
    except Exception as e:
        print(f"❌ Cannot reach backend at {BACKEND_URL}.\n   Error: {e}")
        print("\n💡 Hint: Check your BACKEND_URL and ensure the server is running.")

    print("Monitoring started. Press Ctrl+C to stop.")

    try:
        while True:
            # 1. Read BME688 (Environment)
            env_data = bme.read_all() if bme else {}
            if env_data is None: env_data = {}
            
            # 2. Read Light
            lux = light_sensor.read() if light_sensor else 400.0
            
            # 3. Read Particulates
            pm_data = pms.read() if pms else {"pm2_5": 5}
            if pm_data is None: pm_data = {"pm2_5": 5}
            
            # 4. Read Noise
            noise_db = mic.get_noise_level() if mic else 35.0

            # 5. Build Payload
            payload = {
                "device_id": DEVICE_ID,
                "temperature": env_data.get("temperature", 22.0),
                "humidity": env_data.get("humidity", 40.0),
                "pressure": env_data.get("pressure", 1013.25),
                "vocs": env_data.get("gas_res", 50000),
                "light": lux,
                "sound_amp": noise_db,
                "particulates": pm_data.get("pm2_5", 5.0),
                "timestamp_ms": int(time.time() * 1000)
            }

            # 6. Output to console
            print(f"📤 Sending: {json.dumps(payload)}")
            sys.stdout.flush()

            # 7. POST to Backend
            try:
                res = requests.post(f"{BACKEND_URL}/api/sensor-data", json=payload, timeout=2)
                if res.status_code != 200:
                    print(f"⚠️ Backend returned error: {res.status_code}")
            except Exception as e:
                print(f"❌ Network error: {e}")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if bme: bme.close()
        if light_sensor: light_sensor.close()
        if pms: pms.close()

if __name__ == "__main__":
    main()
