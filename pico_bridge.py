import serial
import json
import requests
import time
import sys
import glob
import os
# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
BAUD_RATE = 115200
DEFAULT_BACKEND = "http://localhost:8000"
BACKEND_BASE = os.getenv("BACKEND_URL", DEFAULT_BACKEND).strip(' "\u201d\u201c').rstrip('/')
BACKEND_URL = f"{BACKEND_BASE}/api/sensor-data"
DEVICE_ID = "Wired-Pico"

def find_serial_port():
    """Find the first available USB modem port on macOS."""
    ports = glob.glob('/dev/cu.usbmodem*')
    if not ports:
        return None
    return ports[0]

def bridge_loop(port_name):
    print(f"🔌 Opening serial port: {port_name}...")
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=1)
        print(f"✅ Bridge Active: {port_name} -> {BACKEND_URL}")
        
        last_heartbeat = time.time()
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line:
                    print(f"📥 Received: {line}")
                    last_heartbeat = time.time()
                else:
                    continue
            else:
                if time.time() - last_heartbeat > 5:
                    print("⌛ Waiting for Pico... (No data received for 5s)")
                    last_heartbeat = time.time()
                time.sleep(0.1)
                continue
                
            try:
                # Parse Pico JSON
                if "{" in line and "}" in line:
                    data = json.loads(line)
                    
                    # Highlight individual particulate levels
                    p1 = data.get("pm1_0")
                    p2 = data.get("pm2_5")
                    p10 = data.get("pm10")
                    if p1 is not None and p2 is not None and p10 is not None:
                        print(f"🌬️  PM Levels — PM1.0: {p1} | PM2.5: {p2} | PM10: {p10} ug/m3")
                
                # Map to Backend Schema (Pico v2 uses short names)
                payload = {
                    "device_id": DEVICE_ID,
                    "light": data.get("light"),
                    "humidity": data.get("humidity"),
                    "pressure": data.get("pressure"),
                    "temperature": data.get("temperature"),
                    "sound_amp": data.get("sound_amp"),
                    "particulates": data.get("pm2_5", data.get("particulates", 0)),
                    "vocs": data.get("vocs"),
                    "timestamp_ms": int(time.time() * 1000)
                }
                
                # Send to Backend
                res = requests.post(BACKEND_URL, json=payload, timeout=2)
                if res.status_code == 200:
                    print(f"📤 Sent: {payload['light']:.1f}% Light | Status: OK")
                else:
                    print(f"⚠️ Backend error: {res.status_code}")
                    
            except json.JSONDecodeError:
                # Might be a debug print or partial line
                if "{" in line:
                    print(f"🤷 Received non-JSON: {line}")
            except requests.exceptions.ConnectionError:
                print(f"❌ Connection Refused: Cannot reach backend at {BACKEND_URL}")
                print("   Check: 1. Is the Docker backend running? (./start.sh)")
                print(f"   Check: 2. Is {BACKEND_URL} the correct address for your server?")
                time.sleep(2) # Throttle retries
            except Exception as e:
                print(f"❌ Bridge Error: {e}")

    except serial.SerialException as e:
        print(f"❌ Serial Error: {e}")
    except KeyboardInterrupt:
        print("\n👋 Stopping bridge...")
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    port = find_serial_port()
    if not port:
        print("❌ Error: No Pico found. Make sure it's plugged in via USB.")
        sys.exit(1)
    
    bridge_loop(port)
