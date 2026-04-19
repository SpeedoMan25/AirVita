import os
import sys
import time
import json

# Setup paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

def test_sensors():
    print("🚀 AirVita Pi 4B Full Sensor Suite Diagnostic")
    print("-" * 50)

    # 1. BME688
    print("\n🔍 Testing BME688 (I2C 0x76)...")
    try:
        from bme688 import BME688
        bme = BME688()
        data = bme.read_all()
        if data:
            print(f"   ✅ Temp: {data['temperature']}°C")
            print(f"   ✅ Hum:  {data['humidity']}%")
            print(f"   ✅ Pres: {data['pressure']} hPa")
            print(f"   ✅ Gas:  {data['gas_res']} Ohms")
        else:
            print("   ❌ Read failed.")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 2. BH1750
    print("\n🔍 Testing BH1750 (I2C 0x23)...")
    try:
        from bh1750 import BH1750
        light = BH1750()
        light.init()
        lux = light.read()
        print(f"   ✅ Light: {lux} Lux")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 3. PMS5003
    print("\n🔍 Testing PMS5003 (Serial)...")
    try:
        from pms5003 import PMS5003
        pm_sensor = PMS5003()
        pm_data = pm_sensor.read()
        if pm_data:
            print(f"   ✅ PM1.0: {pm_data['pm1_0']} ug/m3")
            print(f"   ✅ PM2.5: {pm_data['pm2_5']} ug/m3")
            print(f"   ✅ PM10:  {pm_data['pm10']} ug/m3")
        else:
            print("   ❌ Read failed (Check serial permissions).")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 4. Microphone
    print("\n🔍 Testing Microphone (ALSA)...")
    try:
        from mic_handler import MicrophoneHandler
        mic = MicrophoneHandler()
        db = mic.get_noise_level()
        print(f"   ✅ Noise: {db} dB")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "-" * 50)
    print("Diagnostic Complete.")

if __name__ == "__main__":
    test_sensors()
