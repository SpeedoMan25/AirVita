"""
AirVita — Raspberry Pi 4B Edge Code (Python 3)
Simplified Version: DHT11 Only on Grove Port D5 (GPIO 5)
"""

import json
import time
import sys

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

def setup():
    print(f"Initializing AirVita (DHT11 Only) on GPIO {DHT_PIN}...")
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
                    pass
            
            # If we have a successful read, output JSON
            if temp_c is not None and hum_pct is not None:
                payload = {
                    "temperature_c": temp_c,
                    "humidity_pct": hum_pct,
                    "timestamp_ms": int(time.time() * 1000)
                }
                print(json.dumps(payload))
                sys.stdout.flush()
            
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
