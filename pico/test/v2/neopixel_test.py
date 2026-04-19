import machine
import neopixel
import time

# 1. Configuration
NEO_PIN = 2
NUM_LEDS = 8

# 2. Initialization
np = neopixel.NeoPixel(machine.Pin(NEO_PIN), NUM_LEDS)

def clear_leds():
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0)
    np.write()

def chase(color, delay=0.1):
    for i in range(NUM_LEDS):
        # We don't clear all, just set the one
        # to create a "trailing" or "chase" effect
        # If we wanted only one at a time we'd clear all:
        # for j in range(NUM_LEDS): np[j] = (0,0,0)
        np[i] = color
        np.write()
        time.sleep(delay)
        np[i] = (0, 0, 0) # Turn off after delay

def fade_in(color, steps=10, delay=0.05):
    for s in range(steps):
        ratio = (s + 1) / steps
        r = int(color[0] * ratio)
        g = int(color[1] * ratio)
        b = int(color[2] * ratio)
        for i in range(NUM_LEDS):
            np[i] = (r, g, b)
        np.write()
        time.sleep(delay)

def run_test():
    print("--- V2 NeoPixel Hardware Test ---")
    print(f"Testing {NUM_LEDS} LEDs on GP{NEO_PIN}...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            # Color Pulse
            for color in [(100, 0, 0), (0, 100, 0), (0, 0, 100)]:
                fade_in(color)
                time.sleep(0.2)
                clear_leds()
                time.sleep(0.2)
                
            # Chase
            for _ in range(3):
                chase((100, 100, 100)) # White chase
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nTest stopped. Clearing LEDs...")
        clear_leds()

if __name__ == "__main__":
    run_test()
