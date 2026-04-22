import machine
import time
import sys

# Standard Path setup for the driver
if "/lib" not in sys.path:
    sys.path.append("/lib")

try:
    from bme688 import BME688
except ImportError:
    try:
        from lib.bme688 import BME688
    except ImportError:
        print("Error: BME688 driver not found in / or /lib/")

# 1. Configuration
I2C_ADDR_BME = None   # Will be scan-detected
SDA_PIN = 0
SCL_PIN = 1

# 2. Initialization
i2c = machine.I2C(0, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=100000)

def run_test():
    global I2C_ADDR_BME
    print("\n" + "="*45)
    print("--- V2 Environmental Sensor Test (Console) ---")
    print("="*45)
    
    # Identify BME688
    devices = i2c.scan()
    if 0x76 in devices:
        I2C_ADDR_BME = 0x76
    elif 0x77 in devices:
        I2C_ADDR_BME = 0x77
    
    if I2C_ADDR_BME is None:
        print("CRITICAL: BME688 not found at 0x76 or 0x77.")
        print(f"I2C Scan found: {[hex(d) for d in devices]}")
        return

    print(f"BME688 identified at {hex(I2C_ADDR_BME)}")

    try:
        sensor = BME688(i2c, I2C_ADDR_BME)
        sensor.init()
        
        print("\nStarting Measurement Loop. Press Ctrl+C to stop.")
        
        start_time = time.ticks_ms()
        
        while True:
            data = sensor.read_all()
            
            if data:
                t = data["temperature"]
                h = data["humidity"]
                p = data["pressure"]
                g = data["gas_res"]
                is_stable = data.get("gas_stable", False)
                is_valid = data.get("gas_valid", False)
                
                # Format Gas for better readability
                if g > 1000000:
                    g_str = f"{g/1000000:.2f} M-Ohm"
                else:
                    g_str = f"{g/1000:.1f} k-Ohm"
                
                status_tag = "[OK]" if (is_stable and is_valid) else "[HEATING]" if is_valid else "[INVALID]"
                elapsed = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0
                    
                print(f"DATA | T: {t:5.2f}C | H: {h:5.1f}% | P: {p:7.2f}hPa | GAS: {status_tag} {g_str} ({elapsed:.1f}s)")
            else:
                print("DATA | Timeout or Error reading BME688")
            
            time.sleep(1)


    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")

if __name__ == "__main__":
    run_test()