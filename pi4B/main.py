import os
import time
import math
import json
import requests
import uuid
import sys

# Setup paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

DHT11Handler = None
BH1750 = None
MicrophoneHandler = None

try:
    from dht11_handler import DHT11Handler
except ImportError as e:
    print(f"⚠️ DHT11 driver not available: {e}")

try:
    from bh1750 import BH1750
except ImportError as e:
    print(f"⚠️ BH1750 driver not available: {e}")

try:
    from mic_handler import MicrophoneHandler
except ImportError as e:
    print(f"⚠️ Mic driver not available: {e}")

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").strip(' "\u201d\u201c')
DEVICE_ID = os.getenv("DEVICE_ID", hex(uuid.getnode()))
POLL_INTERVAL = 2  # Seconds

# VU Meter Scaling
MIN_DB = 30   # Noise floor (0 bars)
MAX_DB = 90   # Max volume (50 bars)
BAR_WIDTH = 50

def main():
    print(f"📡 Device ID: {DEVICE_ID}")
    print(f"🔗 Target Backend: {BACKEND_URL}")
    print("Initializing AirVita Sensor Suite (Pi4B)...")


    # Initialize Drivers
    # DHT11 (Temp/Hum)
    dht = None
    if DHT11Handler:
        try:
            dht = DHT11Handler()
            print("✅ DHT11 Initialized (Pin 11 / D17)")
        except Exception as e:
            print(f"⚠️ DHT11 not found or failed to init: {e}")
    else:
        print("⚠️ DHT11 driver not loaded (missing dependency)")

    # BH1750 (Light)
    light_sensor = None
    if BH1750:
        try:
            light_sensor = BH1750()
            light_sensor.init()
            print("✅ BH1750 Initialized (I2C 0x23)")
        except Exception as e:
            print(f"⚠️ BH1750 not found: {e}")
    else:
        print("⚠️ BH1750 driver not loaded (missing dependency)")

    # Microphone (Noise)
    mic = None
    if MicrophoneHandler:
        try:
            mic = MicrophoneHandler()
            print("✅ Microphone Initialized (I2S/ALSA)")
        except Exception as e:
            print(f"⚠️ Microphone not found: {e}")
    else:
        print("⚠️ Mic driver not loaded (missing dependency)")

    # Check Connectivity
    backend_ok = False
    try:
        print("🔍 Checking backend connectivity...")
        requests.get(f"{BACKEND_URL}/api/monitors", timeout=3)
        print("✅ Successfully connected to AirVita backend!")
        backend_ok = True
    except Exception as e:
        print(f"❌ Cannot reach backend at {BACKEND_URL}.\n   Error: {e}")

    time.sleep(1)
    print("\033[2J\033[H", end="")  # Clear screen

    post_ok = backend_ok
    cycle_count = 0

    try:
        while True:
            cycle_count += 1

            # 1. Read DHT11 (Environment)
            temp, hum = dht.read() if dht else (None, None)
            
            # 2. Read Light
            lux = light_sensor.read() if light_sensor else 0.0
            
            # 3. Read Noise
            noise_db = mic.get_noise_level() if mic else 0.0

            # 4. Build VU meter bar
            if noise_db > 0:
                normalized = (noise_db - MIN_DB) / (MAX_DB - MIN_DB)
                normalized = max(0.0, min(1.0, normalized))
            else:
                normalized = 0.0
            bar_len = int(normalized * BAR_WIDTH)
            bar = "#" * bar_len + "-" * (BAR_WIDTH - bar_len)

            # 5. Build Payload
            send_temp = temp if temp is not None else 0.0
            send_hum = hum if hum is not None else 0.0
            payload = {
                "device_id": DEVICE_ID,
                "temperature": send_temp,
                "humidity": send_hum,
                "light": lux,
                "sound_amp": noise_db,
                "timestamp_ms": int(time.time() * 1000)
            }

            # 6. POST to Backend
            try:
                res = requests.post(f"{BACKEND_URL}/api/sensor-data", json=payload, timeout=2)
                post_ok = res.status_code == 200
            except Exception:
                post_ok = False

            # 7. Dashboard Rendering
            dht_status = "✅" if (temp is not None) else "❌"
            light_status = "✅" if light_sensor else "❌"
            mic_status = "✅" if mic else "❌"
            net_status = "✅ CONNECTED" if post_ok else "❌ OFFLINE"

            print("\033[H", end="")  # Move cursor to top-left
            print("============================================================")
            print("              PI 4B SENSOR DASHBOARD                        ")
            print(f"              Device: {DEVICE_ID}")
            print("============================================================")
            
            # [AUDIO BLOCK]
            print(f"[AUDIO]  [{bar}]")
            print(f"         dB: {noise_db:6.1f}                     Sensor: {mic_status}")
            print("-" * 60)

            # [LIGHT BLOCK]
            print(f"[LIGHT]  Lux: {lux:8.1f} lx                  Sensor: {light_status}")
            print("-" * 60)
            
            # [ENVIRONMENT BLOCK]
            t_str = f"{temp:.1f}" if temp is not None else " --"
            h_str = f"{hum:.1f}" if hum is not None else " --"
            print(f"[ENV]    Temp: {t_str:>5s} C  | Hum: {h_str:>5s} %    Sensor: {dht_status}")
            print("-" * 60)

            # [NETWORK BLOCK]
            print(f"[NET]    Backend: {net_status}  | Cycle: {cycle_count}")
            print("============================================================")
            print("Press Ctrl+C to stop.                           ")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping AirVita Suite...")
    finally:
        if dht: dht.close()
        if light_sensor: light_sensor.close()
        print("✨ Cleanup complete.")

if __name__ == "__main__":
    main()
