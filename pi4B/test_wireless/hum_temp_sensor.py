import Adafruit_DHT
import time

# Change to Adafruit_DHT.DHT11 if needed
SENSOR = Adafruit_DHT.DHT22
PIN = 4  # GPIO4

print("--- Temp & Humidity Sensor Tester ---")
print(f"Monitoring GPIO {PIN}...")
print("Press Ctrl+C to stop.")
print("-" * 40)

last_temp = None
last_humidity = None

try:
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(SENSOR, PIN)

        if humidity is not None and temperature is not None:
            if (
                last_temp is None or
                abs(temperature - last_temp) > 0.5 or
                abs(humidity - last_humidity) > 1
            ):
                print(f"[✓] Temp: {temperature:.1f}°C | Humidity: {humidity:.1f}%")
                last_temp = temperature
                last_humidity = humidity
        else:
            print("[!] Failed to retrieve data from sensor")

        time.sleep(2)

except KeyboardInterrupt:
    print("\nStopping Sensor Tester...")