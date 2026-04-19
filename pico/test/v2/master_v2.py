import machine
import neopixel
import time
import sys

# Standard Path setup for drivers
if "/lib" not in sys.path:
    sys.path.append("/lib")

try:
    from pico_i2c_lcd import I2cLcd
    from bh1750 import BH1750
except ImportError:
    try:
        from lib.pico_i2c_lcd import I2cLcd
        from lib.bh1750 import BH1750
    except ImportError:
        print("Error: Drivers (pico_i2c_lcd or bh1750) not found in / or /lib/")

# 1. Configuration
I2C_ADDR_LCD = 0x27
I2C_ADDR_BH = 0x23
SDA_PIN = 0
SCL_PIN = 1
NEO_PIN = 2
NUM_LEDS = 8

# 2. Hardware Initialization
i2c = machine.I2C(0, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=400000)
np = neopixel.NeoPixel(machine.Pin(NEO_PIN), NUM_LEDS)
lcd = I2cLcd(i2c, I2C_ADDR_LCD, 2, 16)
light_sensor = BH1750(i2c, I2C_ADDR_BH)

def set_leds(r, g, b, brightness=1.0):
    """Sets all 8 LEDs to a specific color and brightness."""
    color = (int(r * brightness), int(g * brightness), int(b * brightness))
    for i in range(NUM_LEDS):
        np[i] = color
    np.write()

def run_system():
    print("--- V2 Smart Light Master System ---")
    print("Self-Diagnostic Starting...")
    
    # Verify I2C Bus Response
    devices = i2c.scan()
    print(f"I2C scan results: {[hex(d) for d in devices]}")
    
    if I2C_ADDR_BH not in devices:
        print("Warning: BH1750 missing. Check wiring.")
    else:
        light_sensor.init()

    print("System active. Press Ctrl+C to stop.")
    
    last_lcd_update = 0
    last_log = 0
    
    try:
        lcd.backlight_on()
        while True:
            curr_time = time.ticks_ms()
            
            # 1. Read Light Sensor (with error handling for I2C timeouts)
            try:
                lux = light_sensor.read()
            except Exception as e:
                # If sensor fails, we'll log it but keep the system running
                print(f"Sensor Error: {e}")
                lux = -1
                
            # 2. Determine System Mode based on Light Level
            if lux > 500:
                mode_str = "DAYLIGHT"
                r, g, b = (0, 0, 0) # Off during day
            elif lux > 100:
                mode_str = "INDOOR"
                r, g, b = (60, 60, 100) # Soft cool white/blue
            elif lux > 0:
                mode_str = "NIGHTLIGHT"
                r, g, b = (100, 35, 0) # Warm amber night light
            else:
                mode_str = "SENSOR ERROR"
                r, g, b = (20, 0, 0) # Dim red warning
                
            # 3. Apply LED Color
            set_leds(r, g, b)
            
            # 4. Update LCD (Throttled to every 250ms for I2C stability)
            if time.ticks_diff(curr_time, last_lcd_update) > 250:
                lcd.move_to(0, 0)
                # Left-aligned lux with clearing spaces
                lcd.putstr(f"LIGHT: {lux:<7.1f} ")
                lcd.move_to(0, 1)
                # Mode status
                lcd.putstr(f"MODE: {mode_str:<10}")
                last_lcd_update = curr_time
                
            # 5. Console Log (Throttled to every 2 seconds)
            if time.ticks_diff(curr_time, last_log) > 2000:
                print(f"DATA | LUX: {lux:7.1f} | MODE: {mode_str}")
                last_log = curr_time
                
            time.sleep(0.05) # Loop frequency stability
            
    except KeyboardInterrupt:
        print("\nShutdown signal received. Clearing hardware...")
        set_leds(0, 0, 0)
        lcd.clear()
        lcd.putstr("V2 System Offline")
        time.sleep(1)
        lcd.backlight_off()
    except Exception as e:
        print(f"Critical System Failure: {e}")

if __name__ == "__main__":
    run_system()
