import sys
import os
import time

# Setup paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

def diagnostic():
    print("🔬 AirVita Pi 4B Diagnostic (Real Sensors Only)")
    print("-" * 50)

    # 1. GY-302 Light Sensor
    print("\n🔍 Checking Light Sensor (GY-302) on Pins 3 & 5...")
    try:
        from bh1750 import BH1750
        light = BH1750()
        light.init()
        lx = light.read()
        if lx > 0 or lx == 0:
            print(f"   ✅ SUCCESS: Current Light: {lx} Lux")
        else:
            print("   ⚠️ SENSOR DETECTED BUT RETURNED NO DATA.")
        light.close()
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        print("   💡 Troubleshooting:")
        print("      1. Swap Pin 3 and Pin 5 (SDA/SCL often get flipped).")
        print("      2. Ensure Pin 1 (3.3V) and Pin 6 (GND) are secure.")

    # 2. INMP441 Microphone
    print("\n🔍 Checking Microphone (INMP441) on Pins 12, 35, 38...")
    try:
        from mic_handler import MicrophoneHandler
        mic = MicrophoneHandler()
        db = mic.get_noise_level()
        if db > 0:
            print(f"   ✅ SUCCESS: Current Noise Level: {db} dB")
        else:
            print("   ⚠️ MICROPHONE INITIALIZED BUT SILENT (Check L/R Pin 20).")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        print("   💡 Troubleshooting:")
        print("      1. Ensure you rebooted after editing /boot/firmware/config.txt.")
        print("      2. Run 'arecord -l' to check if card appears in OS.")

    print("\n" + "-" * 50)
    print("Diagnostic Complete.")

if __name__ == "__main__":
    diagnostic()
