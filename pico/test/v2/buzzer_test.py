import machine
import time

# 1. Configuration
# We use GP15 (Pico Pin 20) for the buzzer
BUZZER_PIN = 15

# 2. Initialization
buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)

def run_test():
    print(f"--- V2 Buzzer Test (GP{BUZZER_PIN}) ---")
    print("Testing active buzzer patterns...")
    
    # Pattern 1: Short alert
    print("Pattern: Alert")
    for _ in range(3):
        buzzer.value(1)
        time.sleep(0.05)
        buzzer.value(0)
        time.sleep(0.05)
    
    time.sleep(0.5)
    
    # Pattern 2: Success chime
    print("Pattern: Success")
    buzzer.value(1)
    time.sleep(0.2)
    buzzer.value(0)
    
    time.sleep(0.5)
    
    # Pattern 3: Warning (Long beep)
    print("Pattern: Warning")
    buzzer.value(1)
    time.sleep(1.0)
    buzzer.value(0)
    
    print("Test complete.")

if __name__ == "__main__":
    run_test()
