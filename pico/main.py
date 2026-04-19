"""
AirVita — Raspberry Pi Pico Edge Code (MicroPython)
Hardware Integrated Version (I2C, UART, I2S, ADC, NeoPixel)
"""

import json
import time
from machine import Pin, I2C, UART, ADC, I2S
import neopixel

# Import drivers from lib/
try:
    from lib.bme688 import BME688
    from lib.bh1750 import BH1750
    from lib.lcd1602 import LCD1602
except ImportError:
    print("Warning: Drivers not found in lib/. Ensure lib/ directory is uploaded.")

# Pins based on YOUR hardware setup image
PIN_SDA = 0
PIN_SCL = 1
PIN_LDR = 28
PIN_NEO = 2

# I2C Shared Bus (I2C0)
i2c = I2C(0, sda=Pin(PIN_SDA), scl=Pin(PIN_SCL), freq=400000)

# Global objects
lcd = None
status_leds = neopixel.NeoPixel(Pin(PIN_NEO), 8)
ldr_pin = ADC(Pin(PIN_LDR))

# ──────────────────────────────────────────────
# Visual Animations
# ──────────────────────────────────────────────

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
    """Display a rainbow wave on the 8 LEDs."""
    for i in range(8):
        status_leds[i] = wheel((i * 256 // 8 + offset) & 255)
    status_leds.write()

def dim_red():
    """Set all LEDs to a dim, steady red."""
    for i in range(8):
        status_leds[i] = (20, 0, 0)
    status_leds.write()

# ──────────────────────────────────────────────
# Setup and Main loop
# ──────────────────────────────────────────────

def setup():
    global lcd
    print("Initializing Focused Hardware (LCD + LDR + Neo)...")
    try:
        lcd = LCD1602(i2c)
        lcd.message("Focus Mode Active", "LDR + LCD + NEO")
    except Exception as e:
        print(f"LCD Init Error: {e}")

def loop():
    offset = 0
    lcd_counter = 0
    while True:
        try:
            # 1. Read Light Level (%)
            raw = ldr_pin.read_u16()
            light_pct = (raw / 65535) * 100
            is_bright = light_pct > 65 # Threshold approx matching your test
            
            # 2. Output to LEDs
            if is_bright:
                rainbow_wave(offset)
                offset = (offset + 10) % 256
                mode = "BRIGHT"
            else:
                dim_red()
                mode = "DIM"
            
            # 3. Output to LCD (Always update regardless of offset)
            if lcd_counter % 10 == 0:
                lcd.message(f"Light: {light_pct:5.1f}%", f"MODE: {mode}")
            
            lcd_counter = (lcd_counter + 1) % 100
            
            # 4. JSON for Backend
            payload = {
                "light_lux": light_pct,
                "mode": mode,
              """   "temperature_c": 0.0, # Placeholder
                "humidity_pct": 0.0,
                "pressure_hpa": 0.0,
                "pm25_ugm3": 0.0,
                "voc_ppb": 0.0, """
                "timestamp_ms": time.ticks_ms()
            }
            print(json.dumps(payload))
            
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            
        time.sleep(0.05 if is_bright else 0.1)

# Entry point
setup()
loop()

