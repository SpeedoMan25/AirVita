"""
AirVita — Raspberry Pi 4B Edge Code (Python 3)
Final Hardware Version: I2C Sensors, UART Particles, I2S Mic, DHT11
"""

import json
import time
import sys
import os

# Drivers
try:
    from lib.bme688 import BME688
    from lib.bh1750 import BH1750
    from lib.lcd1602 import LCD1602
    from lib.pms5003 import PMS5003
    from lib.mic_handler import MicrophoneHandler
except ImportError:
    # Handle if running from different directory
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from lib.bme688 import BME688
    from lib.bh1750 import BH1750
    from lib.lcd1602 import LCD1602
    from lib.pms5003 import PMS5003
    from lib.mic_handler import MicrophoneHandler

# DHT11 Library
try:
    import adafruit_dht
    import board
except ImportError:
    adafruit_dht = None
    print("Warning: 'adafruit-circuitpython-dht' not installed. DHT11 will be mocked.")

# Hardware Config
I2C_BUS = 1
UART_PORT = '/dev/serial0'
DHT_PIN = board.D5 if 'board' in locals() else 5

# Global Objects
lcd = None
bh = None
bme = None
pms = None
mic = None
dht_sensor = None

def setup():
    global lcd, bh, bme, pms, mic, dht_sensor
    print("Initializing AirVita Final Suite (Pi 4B)...")
    
    # 1. I2C Initialization
    try:
        lcd = LCD1602(I2C_BUS)
        lcd.message("AirVita Pi 4B", "Loading Sensors...")
        
        bh = BH1750(I2C_BUS)
        bh.init()
        
        bme = BME688(I2C_BUS)
        bme.init()
    except Exception as e:
        print(f"I2C Init Error: {e}")

    # 2. UART Initialization (PMS5003)
    try:
        pms = PMS5003(UART_PORT)
    except Exception as e:
        print(f"UART Init Error (PMS5003): {e}")

    # 3. I2S/Audio Initialization
    try:
        mic = MicrophoneHandler()
    except Exception as e:
        print(f"Mic Handler Error: {e}")

    # 4. DHT11 Initialization
    if adafruit_dht:
        try:
            dht_sensor = adafruit_dht.DHT11(DHT_PIN)
        except Exception as e:
            print(f"DHT11 Init Error: {e}")
            
    if lcd: lcd.message("Setup Complete", "Monitoring...")

def loop():
    lcd_counter = 0
    while True:
        try:
            # 1. Read Light Level (BH1750)
            lux = bh.read() if bh else 0.0
            
            # 2. Read Humidity & Temp (DHT11)
            temp_c = 0.0
            hum_pct = 0.0
            if dht_sensor:
                try:
                    temp_c = dht_sensor.temperature
                    hum_pct = dht_sensor.humidity
                except RuntimeError as e:
                    # DHT sensors are finicky, often fail a read
                    pass
            
            # 3. Read Gas/Pressure (BME688)
            env = bme.read_all() if bme else {}
            # Fallback for temp/hum if DHT11 fails
            if temp_c is None or temp_c == 0.0: temp_c = env.get("temperature", 0.0)
            if hum_pct is None or hum_pct == 0.0: hum_pct = env.get("humidity", 0.0)
            
            # 4. Read Particles (PMS5003)
            particles = pms.read() if pms else {"pm1_0": 0, "pm2_5": 0, "pm10": 0}
            
            # 5. Read Noise Level (Mic)
            noise_db = mic.get_noise_level() if mic else 0.0
            
            # 6. Update LCD (Rotating View)
            if lcd_counter % 20 == 0:
                if lcd:
                    lcd.message(f"T:{temp_c:.1f}C H:{hum_pct:.1f}%", f"PM2.5: {particles.get('pm2_5', 0)}")
            elif lcd_counter % 20 == 10:
                if lcd:
                    lcd.message(f"Lux: {lux:.0f}", f"Noise: {noise_db:.1f}dB")
            
            lcd_counter = (lcd_counter + 1) % 100
            
            # 7. JSON for Backend (Full Sensor Payload)
            payload = {
                "temperature_c": temp_c,
                "humidity_pct": hum_pct,
                "pressure_hpa": env.get("pressure", 0.0),
                "voc_ppb": env.get("gas_res", 0.0),
                "light_lux": lux,
                "light_pct": min((lux / 1000.0) * 100, 100),
                "pm1_0": particles.get("pm1_0", 0),
                "pm2_5": particles.get("pm2_5", 0),
                "pm10": particles.get("pm10", 0),
                "noise_db": noise_db,
                "timestamp_ms": int(time.time() * 1000)
            }
            print(json.dumps(payload))
            sys.stdout.flush()
            
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            
        time.sleep(2.0) # DHT11 requires at least 1-2s between reads

if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        print("\nStopping...")
        if dht_sensor: dht_sensor.exit()
        if lcd: lcd.close()
        if bh: bh.close()
        if bme: bme.close()
        if pms: pms.close()
