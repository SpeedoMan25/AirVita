import time
import sys
import os

# Include lib/ in path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

def test_suite():
    print("=== AirVita Pi4B Diagnostic Suite ===")
    
    # 1. Test DHT11
    print("\n[1/3] Testing DHT11 on Grove D5...")
    try:
        from dht11_handler import DHT11Handler
        dht = DHT11Handler()
        success = False
        for i in range(5):
            temp, hum = dht.read()
            if temp is not None:
                print(f"  [✓] DHT11 Success: {temp}C, {hum}%")
                success = True
                break
            print(f"  [.] Attempt {i+1} failed, retrying...")
            time.sleep(2)
        if not success:
            print("  [!] DHT11 Failed to provide a reading.")
        dht.close()
    except Exception as e:
        print(f"  [!] DHT11 Error: {e}")

    # 2. Test BH1750
    print("\n[2/3] Testing BH1750 Light Sensor...")
    try:
        from bh1750 import BH1750
        light = BH1750()
        light.init()
        lux = light.read()
        print(f"  [✓] BH1750 Success: {lux} lux")
        light.close()
    except Exception as e:
        print(f"  [!] BH1750 Error: {e}")

    # 3. Test INMP441
    print("\n[3/3] Testing INMP441 Microphone...")
    try:
        from mic_handler import MicrophoneHandler
        mic = MicrophoneHandler()
        db = mic.get_noise_level()
        print(f"  [✓] INMP441 Success: {db} dB")
    except Exception as e:
        print(f"  [!] Microphone Error: {e}")

    print("\n=== Diagnostic Complete ===")

if __name__ == "__main__":
    test_suite()
