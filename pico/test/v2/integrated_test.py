import machine
import struct
import time
import math
import sys

# Standard Path setup for the drivers
if "/lib" not in sys.path:
    sys.path.append("/lib")

try:
    from bme688 import BME688
    from bh1750 import BH1750
except ImportError:
    print("Error: Sensor drivers (bme688 or bh1750) missing in /lib")

# --- 1. CONFIGURATION ---
# I2C (Bus 0) - Pins 0 (SDA), 1 (SCL)
SDA_PIN = 0
SCL_PIN = 1
I2C_ADDR_BME = 0x76
I2C_ADDR_BH = 0x23

# I2S (Mic) - Pins 16 (SCK), 17 (WS), 18 (SD)
SCK_PIN = 16
WS_PIN = 17
SD_PIN = 18

# UART (Air Quality - PMS5003) - Pins GP4 (TX), GP5 (RX)
UART_ID = 1
PMS_TX_PIN = 4
PMS_RX_PIN = 5

SAMPLE_RATE = 16000
BITS_PER_SAMPLE = 32
BUFFER_SIZE = 32768

# Calibration/Filtering
GLITCH_THRESHOLD = 8000000 
ALPHA = 0.05 # Baseline smoothing

# VU Meter Scaling (Decibel limits)
# A quiet room is around RMS 2000-4000 (roughly 66-72 dB on this scale)
# A loud sound/shouting will hit RMS 2M-4M (roughly 126-132 dB)
MIN_DB = 72   # The noise floor (0 bars)
MAX_DB = 135  # Max volume (50 bars)
BAR_WIDTH = 50

# --- 2. INITIALIZATION ---

# I2C
i2c = machine.I2C(0, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=100000)

# I2S Microphone
mic = machine.I2S(0, 
                  sck=machine.Pin(SCK_PIN), 
                  ws=machine.Pin(WS_PIN), 
                  sd=machine.Pin(SD_PIN),
                  mode=machine.I2S.RX, 
                  bits=BITS_PER_SAMPLE, 
                  format=machine.I2S.STEREO,
                  rate=SAMPLE_RATE, 
                  ibuf=BUFFER_SIZE)

SAMPLES_PER_READ = 256
read_buf = bytearray(SAMPLES_PER_READ * 8)

def parse_pms_data(data):
    """Parses 32-byte PMS5003 packet for PM 2.5 concentration."""
    if len(data) < 32: return None
    if data[0] != 0x42 or data[1] != 0x4D: return None
    # PM2.5 atmospheric is at bytes 12-13
    pm25 = (data[12] << 8) | data[13]
    return pm25

def get_clean_samples():
    """Reads I2S samples and filters hardware glitches."""
    bytes_read = mic.readinto(read_buf)
    if bytes_read == 0:
        return []
    
    count = bytes_read // 4
    raw = struct.unpack(f'<{count}i', read_buf[:bytes_read])
    
    clean = []
    # Left channel indexing [0, 2, 4...]
    for i in range(0, count, 2):
        s = raw[i] >> 8
        if abs(s) < GLITCH_THRESHOLD:
            clean.append(s)
            
    return clean

def run_integrated():
    print("\n" + "="*60)
    print("--- INTEGRATED TEST: BME688 + MIC (Console Log) ---")
    print("="*60)
    
    # I2C Device Detection
    devices = i2c.scan()
    bme_addr = 0x76 if 0x76 in devices else 0x77 if 0x77 in devices else None
    bh_detected = 0x23 in devices
    
    env_sensor = None
    if bme_addr:
        print(f"BME688 detected at {hex(bme_addr)}")
        env_sensor = BME688(i2c, bme_addr)
        env_sensor.init()
    else:
        print("WARNING: BME688 sensor not found.")

    light_sensor = None
    if bh_detected:
        print(f"BH1750 detected at {hex(0x23)}")
        light_sensor = BH1750(i2c, 0x23)
        light_sensor.init()
    else:
        print("WARNING: BH1750 sensor not found.")

    # UART for PMS5003
    pms_uart = machine.UART(UART_ID, baudrate=9600, tx=machine.Pin(PMS_TX_PIN), rx=machine.Pin(PMS_RX_PIN))
    pm25 = 0
    
    baseline = 0
    last_env_update = 0
    env_data_str = "Initializing..."
    
    print("\nStabilizing Microphone (0.5s)...")
    start_stab = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_stab) < 500:
        mic.readinto(read_buf) # Discard startup samples
        
    print("\033[2J\033[H", end="") # Clear screen and home cursor
    
    # Store sensor data in variables for the dashboard
    t, h, p, g, lux, status, g_str = 0, 0, 0, 0, 0, "--", "--"
    
    try:
        while True:
            # --- PHASE A: AUDIO (High Frequency) ---
            samples = get_clean_samples()
            rms = 0
            if samples:
                # Update Baseline for DC Offset removal
                current_avg = sum(samples) / len(samples)
                if baseline == 0:
                    baseline = current_avg
                else:
                    baseline = (ALPHA * current_avg) + ((1 - ALPHA) * baseline)
                
                # Calculate RMS
                sum_sq = sum((s - baseline)**2 for s in samples)
                rms = math.sqrt(sum_sq / len(samples))
                
                # Peak detection
                peak = max(abs(s - baseline) for s in samples)
            else:
                peak = 0
            
            # --- PHASE B: ENVIRONMENT (1Hz Update) ---
            now = time.ticks_ms()
            env_updated_now = False
            if env_sensor and time.ticks_diff(now, last_env_update) > 1000:
                data = env_sensor.read_all()
                lux = light_sensor.read() if light_sensor else 0
                
                # Check for Air Quality (PMS5003) - Non-blocking
                if pms_uart.any() >= 32:
                    raw_pms = pms_uart.read(32)
                    parsed_pm = parse_pms_data(raw_pms)
                    if parsed_pm is not None:
                        pm25 = parsed_pm

                if data:
                    t = data["temperature"]
                    h = data["humidity"]
                    p = data["pressure"]
                    g = data["gas_res"]
                    is_stab = data.get("gas_stable", False)
                    
                    status = "OK" if is_stab else "--"
                    g_str = f"{g/1000000:.2f}M" if g > 1000000 else f"{g/1000:.1f}k"
                last_env_update = now
            
            # --- PHASE C: DASHBOARD RENDERING ---
            # Create volume bar using Decibels (dB)
            if rms > 0:
                db = 20 * math.log10(rms)
            else:
                db = 0
            normalized_db = (db - MIN_DB) / (MAX_DB - MIN_DB)
            normalized_db = max(0.0, min(1.0, normalized_db))
            
            bar_len = int(normalized_db * BAR_WIDTH)
            bar = "#" * bar_len + "-" * (BAR_WIDTH - bar_len)
            glitch_indicator = " [!]" if len(samples) < (SAMPLES_PER_READ * 0.5) else "    "

            # Move cursor to home and redraw the dashboard
            print("\033[H", end="") # Move to 0,0
            print("============================================================")
            print("                PICO V2 SENSOR DASHBOARD                    ")
            print("============================================================")
            
            # [AUDIO BLOCK]
            print(f"[AUDIO]  [{bar}]")
            print(f"         RMS: {int(rms):7d} | Peak: {int(peak):7d}{glitch_indicator}")
            print("-" * 60)
            
            # [ATMOSPHERE & LIGHT BLOCK]
            # Categorize PM2.5 roughly
            aqi_label = "EXCELLENT" if pm25 <= 12 else "GOOD" if pm25 <= 35 else "POOR"
            print(f"[AIR]    PM2.5: {pm25:3d} ug/m3 (Status: {aqi_label:9s})")
            print(f"[LIGHT]  Lux:   {lux:7.1f} lx")
            print("-" * 60)
            
            # [ENVIRONMENT BLOCK]
            print(f"[ENV]    Temp: {t:4.1f} C    | Hum:  {h:4.1f} %")
            print(f"[ENV]    Pres: {p:6.1f} hPa | Gas:  {g_str:7s} ({status})")
            print("============================================================")
            print("Press Ctrl+C to stop.                           ")

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\n\nStopping integrated test...")
    finally:
        mic.deinit()
        print("I2S Microphone deinitialized.")

if __name__ == "__main__":
    run_integrated()