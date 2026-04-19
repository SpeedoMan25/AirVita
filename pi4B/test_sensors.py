import time
import sys
import os
from smbus2 import SMBus

# Add lib to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from lib.bh1750 import BH1750
from lib.lcd1602 import LCD1602
from lib.pms5003 import PMS5003
from lib.mic_handler import MicrophoneHandler

# Config
I2C_BUS = 1
UART_PORT = '/dev/serial0'
DHT_PIN = 5 # GPIO 5

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
    lcd = None
    
    # 1. LCD Test
    print("\n[1/5] Testing LCD1602...")
    try:
        lcd = LCD1602(I2C_BUS)
        lcd.message("Pi 4B Suite", "Diagnostic Mode")
        print("Done. Check LCD screen.")
        time.sleep(1)
    except Exception as e:
        print(f"LCD Test Failed: {e}")

    # 2. BH1750 Test (Light)
    print("\n[2/5] Testing BH1750 (Light Sensor)...")
    try:
        bh = BH1750(I2C_BUS)
        bh.init()
        lux = bh.read()
        print(f"Ambient Light: {lux} lux")
        if lcd: lcd.message("Light Sensor", f"{lux} lux")
        time.sleep(1)
    except Exception as e:
        print(f"BH1750 Test Failed: {e}")

    # 3. DHT11 Test (Temp/Hum)
    print("\n[3/5] Testing DHT11 (GPIO 5)...")
    try:
        import adafruit_dht
        import board
        dht = adafruit_dht.DHT11(board.D5)
        print("Reading DHT11...")
        time.sleep(2)
        temp = dht.temperature
        hum = dht.humidity
        print(f"Temp: {temp}C | Humidity: {hum}%")
        if lcd: lcd.message(f"T:{temp}C H:{hum}%", "DHT11 Check")
        dht.exit()
    except Exception as e:
        print(f"DHT11 Test Failed: {e}")
        print("Note: Ensure 'adafruit-circuitpython-dht' is installed.")

    # 4. PMS5003 Test (Particles)
    print("\n[4/5] Testing PMS5003 (Particles)...")
    try:
        pms = PMS5003(UART_PORT)
        print("Wait for 2s for PMS5003 data...")
        time.sleep(2)
        p_data = pms.read()
        if p_data:
            print(f"PM2.5: {p_data['pm2_5']} ug/m3")
            if lcd: lcd.message("PMS5003", f"PM2.5: {p_data['pm2_5']}")
        else:
            print("No data received from PMS5003. Check UART config.")
        pms.close()
    except Exception as e:
        print(f"PMS5003 Test Failed: {e}")

    # 5. Microphone Test (Noise)
    print("\n[5/5] Testing INMP441 (Noise Level)...")
    try:
        mic = MicrophoneHandler()
        db = mic.get_noise_level()
        print(f"Estimated Noise: {db} dB")
        if lcd: lcd.message("Mic Test", f"{db} dB")
    except Exception as e:
        print(f"Mic Test Failed: {e}")

    if lcd:
        lcd.message("Test Complete", "Ready for Alpha")
        time.sleep(2)
        lcd.close()

if __name__ == "__main__":
    test_sensors()
    print("\nAll diagnostic steps finished.")
