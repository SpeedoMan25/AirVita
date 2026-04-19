import time
import sys
import os
from smbus2 import SMBus

# Add lib to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from lib.bh1750 import BH1750
from lib.lcd1602 import LCD1602

# Bus config
I2C_BUS = 1

def scan_i2c():
    bus = SMBus(I2C_BUS)
    print(f"Scanning I2C bus {I2C_BUS}...")
    devices = []
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            devices.append(hex(addr))
        except:
            pass
    print(f"Devices found: {devices}")
    bus.close()
    return devices

def test_sensors():
    devices = scan_i2c()
    
    # 1. LCD Test
    print("\n[1/3] Testing LCD1602...")
    try:
        lcd = LCD1602(I2C_BUS)
        lcd.message("Pi 4B Test", "In Progress...")
        print("Done. Check LCD screen.")
        time.sleep(2)
    except Exception as e:
        print(f"LCD Test Failed: {e}")

    # 2. BH1750 Test
    print("\n[2/3] Testing BH1750 (Light Sensor)...")
    try:
        bh = BH1750(I2C_BUS)
        bh.init()
        for _ in range(5):
            lux = bh.read()
            print(f"Ambient Light: {lux} lux")
            if lcd:
                lcd.message("Light Sensor", f"{lux} lux")
            time.sleep(1)
    except Exception as e:
        print(f"BH1750 Test Failed: {e}")

    # 3. NeoPixel Note
    print("\n[3/3] NeoPixel Note...")
    print("NeoPixels on Pi 4B require sudo and rpi_ws281x.")
    print("Run 'sudo python3 main.py' to test NeoPixels.")

    if 'lcd' in locals():
        lcd.message("Test Complete", "Ready for Alpha")
        time.sleep(2)
        lcd.close()

if __name__ == "__main__":
    test_sensors()
    print("\nAll diagnostic steps finished.")
