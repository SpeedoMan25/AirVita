import machine
import time
import sys

# Standard Path setup for the driver
if "/lib" not in sys.path:
    sys.path.append("/lib")

try:
    from bh1750 import BH1750
except ImportError:
    try:
        from lib.bh1750 import BH1750
    except ImportError:
        print("Error: Library not found in / or /lib/")

# 1. Configuration
I2C_ADDR_BH = 0x23
SDA_PIN = 0
SCL_PIN = 1

# 2. Initialization (Use Hardware I2C 0 on GP0/GP1)
# User specifically confirmed SDA=GP0, SCL=GP1 and only GY-302 connected.
i2c = machine.I2C(0, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=400000)

def run_test():
    print("--- V2 Digital Light Sensor Test (GY-302/BH1750) ---")
    print(f"Setup: Hardware I2C 0 | SDA=GP{SDA_PIN}, SCL=GP{SCL_PIN} | 5V Power")
    
    # Scan I2C
    try:
        devices = i2c.scan()
        print(f"I2C devices found: {[hex(d) for d in devices]}")
    except Exception as e:
        print(f"I2C Scan Failed: {e}")
        return
    
    if I2C_ADDR_BH not in devices:
        print(f"Error: BH1750 ({hex(I2C_ADDR_BH)}) not found! Check wiring.")
        return

    # Optional LCD initialization
    lcd = None
    try:
        from pico_i2c_lcd import I2cLcd
        I2C_ADDR_LCD = 0x27
        if I2C_ADDR_LCD in devices:
            lcd = I2cLcd(i2c, I2C_ADDR_LCD, 2, 16)
            lcd.clear()
            lcd.putstr("GY-302 Active")
            print("LCD detected and initialized.")
        else:
            # print("LCD (0x27) not found, skipping LCD output.")
            pass
    except Exception:
        pass

    try:
        light_sensor = BH1750(i2c, I2C_ADDR_BH)
        
        print("Initializing BH1750...")
        # Wake up / Power on
        try: i2c.writeto(I2C_ADDR_BH, b'\x01')
        except: pass 
        time.sleep(0.2)
        light_sensor.init()
        
        if lcd:
            lcd.move_to(0, 1)
            lcd.putstr("Reading Lux...")
        
        print("Reading Light Levels (Lux)...")
        print("Press Ctrl+C to stop.")
        
        while True:
            lux = light_sensor.read()
            
            # Print to console
            print(f"LIGHT | LUX: {lux:7.1f}")
            
            # Update LCD if available
            if lcd:
                lcd.move_to(0, 0)
                lcd.putstr(f"Light: {lux:<7.1f}")
                lcd.move_to(0, 1)
                lcd.putstr("Unit: LUX       ")
            
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
