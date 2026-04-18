from machine import Pin
import time

# Pin Configuration
# OUT connected to GP16 (Physical Pin 21)
IR_PIN = 16
sensor = Pin(IR_PIN, Pin.IN)

# Also use the onboard LED for visual feedback on the board
led = Pin(25, Pin.OUT)

print("--- IR Obstacle Avoidance Tester ---")
print(f"Monitoring GPIO {IR_PIN}...")
print("Logic: LOW (0) means obstacle detected, HIGH (1) means clear.")
print("Press Ctrl+C to stop.")
print("-" * 36)

last_state = -1

try:
    while True:
        # Read the current sensor state
        current_state = sensor.value()
        
        # Only print when the state changes to keep the console clean
        if current_state != last_state:
            if current_state == 0:
                print("[!] OBSTACLE DETECTED")
                led.value(1) # Turn on onboard LED
            else:
                print("[ ] Path Clear")
                led.value(0) # Turn off onboard LED
            last_state = current_state
            
        # Small delay to prevent CPU hogging
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nStopping IR Tester...")
    led.value(0)
