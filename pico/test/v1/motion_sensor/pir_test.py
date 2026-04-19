from machine import Pin
import time

# Pin Configuration
# OUT connected to GP17 (Physical Pin 22)
PIR_PIN = 17
sensor = Pin(PIR_PIN, Pin.IN)

# Also use the onboard LED for visual feedback on the board
led = Pin(25, Pin.OUT)

print("--- HC-SR501 PIR Motion Tester ---")
print(f"Monitoring GPIO {PIR_PIN}...")
print("Logic: HIGH (1) means motion detected, LOW (0) means clear.")
print("-" * 34)

# PIR sensors need a warm-up period to stabilize
print("Waiting for sensor to stabilize (approx 15s)...")
for i in range(15, 0, -1):
    print(f"{i}...", end=" ")
    time.sleep(1)
print("\nReady! monitoring for motion...")
print("Press Ctrl+C to stop.")
print("-" * 34)

last_state = -1

try:
    while True:
        # Read current state
        current_state = sensor.value()
        
        # Only print on change
        if current_state != last_state:
            timestamp = time.localtime()
            time_str = "{:02d}:{:02d}:{:02d}".format(timestamp[3], timestamp[4], timestamp[5])
            
            if current_state == 1:
                print(f"[{time_str}] [!] MOTION DETECTED")
                led.value(1) # Visual feedback on board
            else:
                print(f"[{time_str}] [ ] Stillness / No Motion")
                led.value(0)
            last_state = current_state
            
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopping PIR Tester...")
    led.value(0)
