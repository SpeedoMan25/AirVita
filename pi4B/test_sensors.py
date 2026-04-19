import sys
import os
import time

# Setup paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

def diagnostic():
    print("🔬 AirVita Pi 4B Diagnostic Tool")
    print("-" * 40)

    # 1. GY-302 Light Sensor
    print("\n🔍 Checking Light Sensor (GY-302)...")
    try:
        from bh1750 import BH1750
        light = BH1750()
        light.init()
        lx = light.read()
        print(f"   ✅ Detected! Current Light: {lx} Lux")
        light.close()
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        print("   💡 Tip: Check Pins 3 & 5 (SDA/SCL) and ensure 'i2c' is enabled in raspi-config.")

    # 2. INMP441 Microphone
    print("\n🔍 Checking Microphone (INMP441)...")
    try:
        from mic_handler import MicrophoneHandler
        mic = MicrophoneHandler()
        db = mic.get_noise_level()
        print(f"   ✅ Initialized! Current Noise: {db} dB")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        print("   💡 Tip: Check Pins 12, 35, 38 and ensure I2S is enabled in /boot/firmware/config.txt.")

    print("\n" + "-" * 40)
    print("Diagnostic Complete.")

if __name__ == "__main__":
    diagnostic()
