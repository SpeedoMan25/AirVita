import os
import sys
import subprocess

def check_i2c():
    print("\n--- I2C Bus Scan (Bus 1) ---")
    try:
        # Try to run i2cdetect -y 1
        output = subprocess.check_output(["i2cdetect", "-y", "1"], stderr=subprocess.STDOUT).decode()
        print(output)
        if "23" in output:
            print("✅ Found BH1750 at address 0x23")
        elif "5c" in output:
            print("✅ Found BH1750 at address 0x5c")
        else:
            print("❌ BH1750 (0x23 or 0x5c) NOT FOUND on I2C bus.")
            print("   Check: 1. Is I2C enabled in raspi-config?")
            print("          2. Are Pin 1 (3.3V), 6 (GND), 3 (SDA), 5 (SCL) connected?")
    except FileNotFoundError:
        print("⚠️ 'i2cdetect' command not found. Install with: sudo apt install i2c-tools")
    except Exception as e:
        print(f"❌ I2C Scan Failed: {e}")

def check_audio():
    print("\n--- Audio Input Device Scan ---")
    try:
        output = subprocess.check_output(["arecord", "-l"], stderr=subprocess.STDOUT).decode()
        print(output)
        if "I2S" in output or "snd_rpi" in output or "Generic" in output:
            print("✅ I2S Microphone device detected in ALSA.")
        else:
            print("❌ I2S Microphone NOT FOUND.")
            print("   Check: 1. Did you add 'dtparam=i2s=on' to /boot/config.txt?")
            print("          2. Did you add 'dtoverlay=googlevoicehat-soundcard' to /boot/config.txt?")
            print("          3. Did you REBOOT after changes?")
    except FileNotFoundError:
        print("⚠️ 'arecord' command not found. Install with: sudo apt install alsa-utils")
    except Exception as e:
        print(f"❌ Audio Scan Failed: {e}")

if __name__ == "__main__":
    print("=== AirVita Pi 4B Diagnostic Tool ===")
    check_i2c()
    check_audio()
    print("\n=====================================")
