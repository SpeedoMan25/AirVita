import machine
import time
import sys

# Standard Path setup for the driver
if "/lib" not in sys.path:
    sys.path.append("/lib")

try:
    from pico_i2c_lcd import I2cLcd
    from bme688 import BME688
except ImportError:
    try:
        from lib.pico_i2c_lcd import I2cLcd
        from lib.bme688 import BME688
    except ImportError:
        print("Error: Library not found in / or /lib/")

# 1. Configuration
I2C_ADDR_LCD = 0x27
I2C_ADDR_BME = None   # Will be detected automatically
SDA_PIN = 0
SCL_PIN = 1

# 2. Initialization (Lowered to 100kHz for stability)
i2c = machine.I2C(0, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=100000)

def run_test():
    global I2C_ADDR_BME # Allow updating the global
    print("--- V2 Environmental Sensor Test (BME688) ---")
    
    # Scan I2C (Multiple retries)
    devices = []
    print("Scanning I2C bus...")
    for i in range(5):
        devices = i2c.scan()
        # Look for BME688 at either address 0x76 or 0x77
        if 0x76 in devices:
            I2C_ADDR_BME = 0x76
            break
        if 0x77 in devices:
            I2C_ADDR_BME = 0x77
            break
        print(f"  Attempt {i+1}: Found {[hex(d) for d in devices]}")
        time.sleep(0.5)
    
    print(f"Final devices found: {[hex(d) for d in devices]}")
    
    lcd = None
    if I2C_ADDR_LCD in devices:
        lcd = I2cLcd(i2c, I2C_ADDR_LCD, 2, 16)
        lcd.clear()
        lcd.putstr("BME688 Init...")
    else:
        print("Warning: LCD not detected in scan.")

    if I2C_ADDR_BME is None:
        print(f"Error: BME688 (0x76 or 0x77) not found! Final scan: {[hex(d) for d in devices]}")
        if lcd:
            lcd.clear()
            lcd.putstr("BME688 Missing")
        return

    try:
        sensor = BME688(i2c, I2C_ADDR_BME)
        sensor.init()
        
        if lcd:
            lcd.clear()
            lcd.putstr("BME688 Active")
            time.sleep(1)
        
        print("Reading Data (Temperature, Humidity, Gas)...")
        print("Press Ctrl+C to stop.")
        
        while True:
            data = sensor.read_all()
            
            if data:
                temp = data["temperature"]
                hum = data["humidity"]
                pres = data["pressure"]
                gas = data["gas_res"]
                
                # 1. Update LCD
                if lcd:
                    lcd.move_to(0, 0)
                    lcd.putstr(f"{temp:.1f}C {hum:.1f}%RH ")
                    lcd.move_to(0, 1)
                    lcd.putstr(f"{pres:.0f}hPa G:{gas//1000}k ")
                
                # 2. Print to console
                print(f"ENV | T: {temp:.1f}C | H: {hum:.1f}% | P: {pres:.1f}hPa | GAS: {gas} Ohm")
            
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nTest stopped.")
        if lcd: 
            lcd.clear()
            lcd.putstr("BME Test Stopped")
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    run_test()
