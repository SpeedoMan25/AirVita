import machine
import neopixel
import time
import sys

# Standard Path setup
if "/lib" not in sys.path:
    sys.path.append("/lib")

try:
    from pico_i2c_lcd import I2cLcd
except ImportError:
    try:
        from lib.pico_i2c_lcd import I2cLcd
    except ImportError:
        print("LCD Driver missing")

# 1. Configuration
PIXEL_PIN = 2
NUM_PIXELS = 16
BUZZER_PIN = 15
LCD_ADDR = 0x27

# 2. Initialization
pixels = neopixel.NeoPixel(machine.Pin(PIXEL_PIN), NUM_PIXELS)
buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)
i2c = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)

try:
    lcd = I2cLcd(i2c, LCD_ADDR, 2, 16)
except:
    lcd = None

def explosion():
    print("BOOM!")
    if lcd:
        lcd.clear()
        lcd.putstr("    !!!BOOM!!!")
        lcd.move_to(0, 1)
        lcd.putstr(" SYSTEM OFFLINE")
    
    # Visual-only Chaos Strobe
    for _ in range(20):
        pixels.fill((255, 255, 255)) # White flash
        pixels.write()
        time.sleep(0.04)
        
        pixels.fill((255, 0, 0)) # Red flash
        pixels.write()
        time.sleep(0.04)
        
    pixels.fill((0, 0, 0))
    pixels.write()
    buzzer.value(0)

def run_sim():
    print("Armed. Starting 30-second simulation...")
    
    count = 30
    while count > 0:
        # 1. Color Logic
        if count > 20:
            color = (0, 150, 0) # Green
        elif count > 10:
            color = (150, 150, 0) # Yellow
        else:
            color = (200, 0, 0) # Red
            
        # 2. LCD Update
        if lcd:
            lcd.clear()
            lcd.putstr("DANGER: ARMED")
            lcd.move_to(0, 1)
            lcd.putstr(f"DETONATE IN: {count}s")
        
        # 3. Beep and Light
        pixels.fill(color)
        pixels.write()
        buzzer.value(1)
        time.sleep(0.12) # Slightly longer beep for "volume"
        
        pixels.fill((0, 0, 0))
        pixels.write()
        buzzer.value(0)
        
        # Variable delay (gets faster)
        if count > 5:
            time.sleep(0.9)
        elif count > 2:
            time.sleep(0.4)
            # Extra beep for half-seconds
            buzzer.value(1)
            time.sleep(0.05)
            buzzer.value(0)
            time.sleep(0.35)
        else:
            time.sleep(0.2)
            buzzer.value(1)
            time.sleep(0.05)
            buzzer.value(0)
            time.sleep(0.15)
            
        count -= 1
        
    explosion()

if __name__ == "__main__":
    try:
        run_sim()
    except KeyboardInterrupt:
        buzzer.value(0)
        pixels.fill((0, 0, 0))
        pixels.write()
        print("\nDisarmed.")
