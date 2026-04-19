"""
AirVita — Raspberry Pi 4B Edge Code (Python 3)
Simplified Version: DHT11 Only on Grove Port D5 (GPIO 5)
"""

import json
import time
import sys
import uuid
import requests
import socket
import os

# DHT11 Library (Most widely used standard)
try:
    import adafruit_dht
    import board
except ImportError:
    adafruit_dht = None
    print("Error: 'adafruit-circuitpython-dht' and 'board' libraries not found.")
    print("Install them with: pip3 install adafruit-circuitpython-dht")

# Hardware Config
# Seeed Studio Grove Base Hat D5 maps to GPIO 5
DHT_PIN = board.D5 if 'board' in locals() else 5

# Network Config
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEVICE_ID = os.getenv("DEVICE_ID", hex(uuid.getnode())) # MAC address based ID

print(f"📡 Device ID: {DEVICE_ID}")
print(f"🔗 Target Backend: {BACKEND_URL}")

def setup():
    print(f"Initializing AirVita (DHT11 Only) on GPIO {DHT_PIN}...")
    
    # 1. Network Connectivity Check
    try:
        print("🔍 Checking backend connectivity...")
        test_res = requests.get(f"{BACKEND_URL}/api/monitors", timeout=3)
        if test_res.status_code == 200:
            print("✅ Successfully connected to AirVita backend!")
        else:
            print(f"⚠️ Backend reached but returned status: {test_res.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach backend at {BACKEND_URL}.")
        print(f"   Error: {e}")
        print("   Make sure the IP is correct and Tailscale is connected on both units.")

    dht_sensor = None
    if adafruit_dht:
        try:
            dht_sensor = adafruit_dht.DHT11(DHT_PIN)
        except Exception as e:
            print(f"DHT11 Initialization Error: {e}")
    return dht_sensor

def loop(dht_sensor):
    print("Monitoring started. Outputting JSON to console...")
    while True:
        try:
            # Read Humidity & Temp
            temp_c = None
            hum_pct = None
            
            if dht_sensor:
                try:
                    # Note: DHT sensors require a few tries sometimes
                    temp_c = dht_sensor.temperature
                    hum_pct = dht_sensor.humidity
                except RuntimeError as e:
                    # Reading DHT can be finicky on Linux, just retry
                    print("⌛ Sensor reading failed, retrying...")
                    pass
            
            # If we have a successful read, output JSON and send to backend
            if temp_c is not None and hum_pct is not None:
                payload = {
                    "device_id": DEVICE_ID,
                    "temperature": float(temp_c),
                    "humidity": float(hum_pct),
                    "pressure": 1013.25, # Constants to satisfy backend model
                    "light": 400.0,
                    "timestamp_ms": int(time.time() * 1000)
                }
                
                # 1. Console Output
                print(f"📤 Sending: {json.dumps(payload)}")
                sys.stdout.flush()

                # 2. Network Upload
                try:
                    res = requests.post(f"{BACKEND_URL}/api/sensor-data", json=payload, timeout=2)
                    if res.status_code != 200:
                        print(f"⚠️ Backend returned error: {res.status_code}")
                except Exception as e:
                    print(f"❌ Network error: {e}")
            
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            
        # DHT11 requires at least 1-2 seconds between readings
        time.sleep(2.0)

if __name__ == "__main__":
    try:
        sensor = setup()
        loop(sensor)
    except KeyboardInterrupt:
        print("\nStopping...")
        if 'sensor' in locals() and sensor:
            sensor.exit()
