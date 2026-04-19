"""
AirVita — Raspberry Pi 4B Edge Code (Python 3)
Hardware Integrated Version (I2C, UART, NeoPixel)
"""

import json
import time
import sys
import os

# Drivers
try:
    from lib.bme688 import BME688
    from lib.bh1750 import BH1750
    from lib.lcd1602 import LCD1602
except ImportError:
    # Handle if running from different directory
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from lib.bme688 import BME688
    from lib.bh1750 import BH1750
    from lib.lcd1602 import LCD1602

# NeoPixel Library (rpi_ws281x)
try:
    from rpi_ws281x import PixelStrip, Color
except ImportError:
    print("Warning: rpi_ws281x not installed. NeoPixels will be mocked.")
    PixelStrip = None

# Hardware Config
LED_COUNT = 8
LED_PIN = 18          # GPIO 18 (PWM0)
LED_FREQ_HZ = 800000 
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0

# Shared Bus
I2C_BUS = 1

# Global Objects
lcd = None
bh = None
bme = None
strip = None

def wheel(pos):
    """Generate rainbow colors across 0-255."""
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

def rainbow_wave(offset):
    if strip:
        for i in range(LED_COUNT):
            r, g, b = wheel((i * 256 // LED_COUNT + offset) & 255)
            strip.setPixelColor(i, Color(r, g, b))
        strip.show()

def dim_red():
    if strip:
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(20, 0, 0))
        strip.show()

def setup():
    global lcd, bh, bme, strip
    print("Initializing AirVita Hardware (Pi 4B Implementation)...")
    
    # 1. I2C Initialization
    try:
        lcd = LCD1602(I2C_BUS)
        lcd.message("AirVita Pi4B", "Initializing...")
        
        bh = BH1750(I2C_BUS)
        bh.init()
        
        bme = BME688(I2C_BUS)
        bme.init()
        
        lcd.message("Sensors Ready", "Starting Loop...")
    except Exception as e:
        print(f"I2C Init Error: {e}")

    # 2. NeoPixel Initialization
    if PixelStrip:
        try:
            strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
            strip.begin()
        except Exception as e:
            print(f"NeoPixel Init Error (Needs sudo?): {e}")

def loop():
    offset = 0
    lcd_counter = 0
    while True:
        try:
            # 1. Read Light Level (Lux from BH1750)
            lux = bh.read() if bh else 0.0
            # Normalize lux to % for compatibility with Pico backend expectation (0-1000 lux typical room)
            light_pct = min((lux / 1000.0) * 100, 100)
            is_bright = light_pct > 65
            
            # 2. Read Environmental Data
            data = bme.read_all() if bme else {}
            
            # 3. Output to LEDs
            if is_bright:
                rainbow_wave(offset)
                offset = (offset + 10) % 256
                mode = "BRIGHT"
            else:
                dim_red()
                mode = "DIM"
            
            # 4. Update LCD
            if lcd_counter % 10 == 0:
                if lcd:
                    lcd.message(f"Light: {light_pct:5.1f}%", f"MODE: {mode}")
            
            lcd_counter = (lcd_counter + 1) % 100
            
            # 5. JSON for Backend (Matching Pico Schema)
            payload = {
                "light_lux": lux,
                "light_pct": light_pct,
                "mode": mode,
                "temperature_c": data.get("temperature", 0.0),
                "humidity_pct": data.get("humidity", 0.0),
                "pressure_hpa": data.get("pressure", 0.0),
                "voc_ppb": data.get("gas_res", 0.0),
                "timestamp_ms": int(time.time() * 1000)
            }
            print(json.dumps(payload))
            sys.stdout.flush() # Ensure it gets picked up by listener
            
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            
        time.sleep(0.05 if is_bright else 0.1)

if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        print("\nStopping...")
        if strip:
            for i in range(LED_COUNT):
                strip.setPixelColor(i, Color(0,0,0))
            strip.show()
        if lcd: lcd.close()
        if bh: bh.close()
        if bme: bme.close()
