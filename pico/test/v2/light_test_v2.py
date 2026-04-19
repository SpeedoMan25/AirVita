import machine
import time
import sys

# Standard Path setup for the driver
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
        print("Error: Library not found in / or /lib/")

# 1. Configuration
I2C_ADDR_LCD = 0x27
I2C_ADDR_BH = 0x23
SDA_PIN = 0
SCL_PIN = 1

# 2. Initialization
i2c = machine.I2C(0, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=400000)

def run_test():
    print("--- V2 Digital Light Sensor Test (BH1750) ---")
    
    # Scan I2C
    devices = i2c.scan()
    print(f"I2C devices found: {[hex(d) for d in devices]}")
    
    if I2C_ADDR_LCD not in devices:
        print(f"Error: LCD ({hex(I2C_ADDR_LCD)}) not found! Check wiring.")
        return
    if I2C_ADDR_BH not in devices:
        print(f"Error: BH1750 ({hex(I2C_ADDR_BH)}) not found! Check wiring.")
        return

    lcd = None
    try:
        lcd = I2cLcd(i2c, I2C_ADDR_LCD, 2, 16)
        light_sensor = BH1750(i2c, I2C_ADDR_BH)
        
        print("Initializing BH1750...")
        light_sensor.init()
        
        lcd.clear()
        lcd.putstr("GY-302 Sensor")
        lcd.move_to(0, 1)
        lcd.putstr("Initializing...")
        time.sleep(1)
        
        print("Reading Light Levels (Lux)...")
        print("Press Ctrl+C to stop.")
        
        while True:
            lux = light_sensor.read()
            
            # 1. Update LCD (Throttled update)
            lcd.move_to(0, 0)
            lcd.putstr(f"Light: {lux:<7.1f} ")
            lcd.move_to(0, 1)
            lcd.putstr("Unit: LUX       ")
            
            # 2. Print to console
            print(f"LIGHT | LUX: {lux:7.1f}")
            
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nTest stopped.")
        if lcd: 
            lcd.clear()
            lcd.putstr("Test Stopped")
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    run_test()
