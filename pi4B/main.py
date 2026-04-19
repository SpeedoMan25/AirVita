import os
import time
import json
import requests
import uuid
import sys

# Import custom drivers from lib/
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
try:
    from dht11_handler import DHT11Handler
    from bh1750 import BH1750
    from mic_handler import MicrophoneHandler
except ImportError as e:
    print(f"❌ Driver Import Error: {e}")
    print("Ensure all files are in pi4B/lib/")

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").strip(' "\u201d\u201c')
DEVICE_ID = os.getenv("DEVICE_ID", hex(uuid.getnode())) # MAC address based ID
POLL_INTERVAL = 2  # Seconds

def main():
    print(f"📡 Device ID: {DEVICE_ID}")
    print(f"🔗 Target Backend: {BACKEND_URL}")
    print("Initializing AirVita Simplified Sensor Suite (Pi4B)...")

    # Initialize Drivers
    # DHT11 (Temp/Hum)
    try:
        dht = DHT11Handler()
        print("✅ DHT11 Initialized (Grove D5)")
    except Exception as e:
        dht = None
        print(f"⚠️ DHT11 not found or failed to init: {e}")

    # BH1750 (Light)
    try:
        light_sensor = BH1750()
        light_sensor.init()
        print("✅ BH1750 Initialized (I2C 0x23)")
    except Exception as e:
        light_sensor = None
        print(f"⚠️ BH1750 not found: {e}")

    # Microphone (Noise)
    try:
        mic = MicrophoneHandler()
        print("✅ Microphone Initialized (I2S/ALSA)")
    except Exception as e:
        mic = None
        print(f"⚠️ Microphone not found: {e}")

    # Check Connectivity
    try:
        print("🔍 Checking backend connectivity...")
        # Check if backend is reachable
        requests.get(f"{BACKEND_URL}/api/monitors", timeout=3)
        print("✅ Successfully connected to AirVita backend!")
    except Exception as e:
        print(f"❌ Cannot reach backend at {BACKEND_URL}.\n   Error: {e}")

    print("\n🚀 Monitoring started. Press Ctrl+C to stop.\n")

    try:
        while True:
            # 1. Read DHT11 (Environment)
            temp, hum = dht.read() if dht else (None, None)
            
            # 2. Read Light
            lux = light_sensor.read() if light_sensor else 0.0
            
            # 3. Read Noise
            noise_db = mic.get_noise_level() if mic else 35.0

            # 4. Build Payload
            payload = {
                "device_id": DEVICE_ID,
                "temperature": temp if temp is not None else 22.0,
                "humidity": hum if hum is not None else 40.0,
                "light": lux,
                "sound_db": noise_db,
                "timestamp_ms": int(time.time() * 1000)
            }

            # 5. Output to logger/console
            print(f"📊 [TEMP: {payload['temperature']}°C | HUM: {payload['humidity']}% | LUX: {payload['light']} | SOUND: {payload['sound_db']}dB]")
            
            # 6. POST to Backend
            try:
                res = requests.post(f"{BACKEND_URL}/api/sensor-data", json=payload, timeout=2)
                if res.status_code != 200:
                    print(f"⚠️ Backend error: {res.status_code}")
            except Exception as e:
                print(f"❌ Network error: {e}")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n🛑 Stopping AirVita Suite...")
    finally:
        if dht: dht.close()
        if light_sensor: light_sensor.close()
        # MicrophoneHandler usually handles own cleanup if using sounddevice
        print("✨ Cleanup complete.")

if __name__ == "__main__":
    main()
