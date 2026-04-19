import time
import sys

def test_dht11():
    print("--- DHT11 Grove D5 Diagnostic ---")
    try:
        import adafruit_dht
        import board
    except ImportError:
        print("Error: Required libraries not found.")
        print("Run: pip3 install adafruit-circuitpython-dht")
        return

    # D5 port on Seeed Grove Hat maps to GPIO 5
    DHT_PIN = board.D5
    dht = adafruit_dht.DHT11(DHT_PIN)
    
    print(f"Testing DHT11 on GPIO {DHT_PIN}...")
    print("Waiting for stable reading (usually 2-4 seconds)...")
    
    success = False
    for i in range(5):
        try:
            temp = dht.temperature
            hum = dht.humidity
            if temp is not None:
                print(f"[✓] Success! Temp: {temp}C | Hum: {hum}%")
                success = True
                break
        except RuntimeError:
            print(f"Attempt {i+1}: Reading failed (normal for DHT), retrying...")
            time.sleep(2)
            
    if not success:
        print("[!] Failed to get a reading after 5 attempts.")
        print("Check that the sensor is plugged firmly into port D5.")

    dht.exit()

if __name__ == "__main__":
    test_dht11()
