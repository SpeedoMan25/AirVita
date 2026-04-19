import machine, neopixel
import time

# Configuration
NUM_LEDS = 8
PIN_NUM = 0

# Connected to GP0
pin = machine.Pin(PIN_NUM, machine.Pin.OUT)
np = neopixel.NeoPixel(pin, NUM_LEDS)

def all_off():
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0)
    np.write()

def chase(color, delay=0.1):
    for i in range(NUM_LEDS):
        all_off()
        np[i] = color
        np.write()
        time.sleep(delay)

print(f"Starting Individual LED Chase on GP0...")
print("If Ctrl+C doesn't work, run: mpremote connect COM4 soft-reset")

try:
    while True:
        # Chase Red
        print("Chasing Red...")
        chase((255, 0, 0))
        
        # Chase Green
        print("Chasing Green...")
        chase((0, 255, 0))
        
        # Chase Blue
        print("Chasing Blue...")
        chase((0, 0, 255))
        
        # Rainbow Chase (simplified)
        print("Chasing Rainbow...")
        colors = [(255,0,0), (255,127,0), (255,255,0), (0,255,0), (0,0,255), (75,0,130), (148,0,211), (255,255,255)]
        for i in range(NUM_LEDS):
            np[i] = colors[i % len(colors)]
            np.write()
            time.sleep(0.1)
        time.sleep(1)
        all_off()

finally:
    all_off()
