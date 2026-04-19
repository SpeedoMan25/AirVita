import machine
import time
import sys

# Add lib to path if it's not there (for MicroPython)
if "/lib" not in sys.path:
    sys.path.append("/lib")

try:
    from pico_i2c_lcd import I2cLcd
except ImportError:
    from lib.pico_i2c_lcd import I2cLcd

# 1. Configuration
I2C_ADDR = 0x27
SDA_PIN = 0
SCL_PIN = 1

# 2. Initialization
i2c = machine.I2C(0, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=400000)
lcd = None

def run_test():
    global lcd
    print("--- V2 LCD Hardware Test ---")
    
    # Scan for I2C devices to verify wiring
    devices = i2c.scan()
    if not devices:
        print("Error: No I2C devices found! Check your VCC/GND and SDA/SCL wiring.")
        return
    else:
        print(f"I2C devices found: {[hex(d) for d in devices]}")
        if I2C_ADDR not in devices:
            print(f"Warning: LCD address {hex(I2C_ADDR)} not found. Check your soldering/address.")

    try:
        lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
        lcd.clear()
        lcd.putstr("V2 System: READY")
        lcd.move_to(0, 1)
        lcd.putstr("LCD Test OK!")
        print("LCD Test Successful: Check your screen!")
        
        # Blink backlight to confirm control
        for _ in range(3):
            time.sleep(0.5)
            lcd.backlight_off()
            time.sleep(0.5)
            lcd.backlight_on()
            
    except Exception as e:
        print(f"Error initializing LCD: {e}")

if __name__ == "__main__":
    run_test()
