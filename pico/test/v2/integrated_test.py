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
    """Parses 32-byte PMS5003 packet for PM values and particle counts."""
    if len(data) < 32: return None
    if data[0] != 0x42 or data[1] != 0x4D: return None
    
    # Checksum verification
    check = sum(data[:30])
    calc_check = (data[30] << 8) | data[31]
    if check != calc_check:
        return None

    return {
        "pm10_std":  (data[4] << 8) | data[5],
        "pm25_std":  (data[6] << 8) | data[7],
        "pm100_std": (data[8] << 8) | data[9],
        "pm10_atm":  (data[10] << 8) | data[11],
        "pm25_atm":  (data[12] << 8) | data[13],
        "pm100_atm": (data[14] << 8) | data[15],
        "pc_03um":   (data[16] << 8) | data[17],
        "pc_05um":   (data[18] << 8) | data[19],
        "pc_10um":   (data[20] << 8) | data[21],
        "pc_25um":   (data[22] << 8) | data[23],
        "pc_50um":   (data[24] << 8) | data[25],
        "pc_100um":  (data[26] << 8) | data[27],
    }

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
    pms_data = {}
    pms_packets_read = 0
    
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
            if env_sensor and time.ticks_diff(now, last_env_update) > 1000:
                data = env_sensor.read_all()
                lux = light_sensor.read() if light_sensor else 0
                
                if pms_uart.any() > 0:
                    buffer = pms_uart.read()
                    for i in range(len(buffer) - 31, -1, -1):
                        if buffer[i] == 0x42 and buffer[i+1] == 0x4D:
                            packet = buffer[i:i+32]
                            parsed = parse_pms_data(packet)
                            if parsed:
                                pms_data = parsed
                                pms_packets_read += 1
                                break
                if data:
                    t = data["temperature"]
                    h = data["humidity"]
                    p = data["pressure"]
                    g = data["gas_res"]
                    is_stab = data.get("gas_stable", False)
                    is_valid = data.get("gas_valid", False)
                    
                    if not is_valid:
                        status = "INVALID"
                    elif not is_stab:
                        status = "HEATING"
                    else:
                        status = "STABLE"
                        
                    g_str = f"{g/1000000:.2f}M" if g > 1000000 else f"{g/1000:.1f}k"
                last_env_update = now
            
            # --- PHASE C: DASHBOARD RENDERING ---
            try:
                if rms > 0:
                    db = 20 * math.log10(rms)
                else:
                    db = 0
                normalized_db = (db - MIN_DB) / (MAX_DB - MIN_DB)
                normalized_db = max(0.0, min(1.0, normalized_db))
                
                bar_len = int(normalized_db * BAR_WIDTH)
                bar = "#" * bar_len + "-" * (BAR_WIDTH - bar_len) 
                glitch_indicator = " [!]" if len(samples) < (SAMPLES_PER_READ * 0.5) else "    "

                print("\033[H", end="") 
                print("\033[1;36m============================================================\033[0m")
                print("\033[1;37m                AIRVITA PICO V2 DASHBOARD                   \033[0m")
                print("\033[1;36m============================================================\033[0m")
                
                # [AUDIO BLOCK]
                print(f"\033[1;33m[AUDIO]\033[0m  [{bar}]")
                print(f"         RMS: {int(rms):7d} | Peak: {int(peak):7d}{glitch_indicator}")
                print("-" * 60)
                
                # [AIR QUALITY BLOCK]
                pm25_a = pms_data.get("pm25_atm", 0)
                pm10_a = pms_data.get("pm10_atm", 0)
                pm100_a = pms_data.get("pm100_atm", 0)
                
                aqi_color = "\033[1;32m" if pm25_a <= 12 else "\033[1;33m" if pm25_a <= 35 else "\033[1;31m"
                aqi_label = "EXCELLENT" if pm25_a <= 12 else "GOOD" if pm25_a <= 35 else "POOR"
                
                print(f"\033[1;34m[AIR]\033[0m    Mass (ug/m3): {pm10_a:3d} / {pm25_a:3d} / {pm100_a:3d} (AQI: {aqi_color}{aqi_label}\033[0m)")
                
                p03 = pms_data.get("pc_03um", 0)
                p05 = pms_data.get("pc_05um", 0)
                p10 = pms_data.get("pc_10um", 0)
                print(f"\033[1;34m[PART.]\033[0m  >0.3u: {p03:5d} | >0.5u: {p05:5d} | >1.0u: {p10:5d}")
                print(f"\033[1;35m[LIGHT]\033[0m  Lux:   {lux:7.1f} lx")
                print("-" * 60)
                
                # [ENVIRONMENT BLOCK]
                gas_color = "\033[1;32m" if status == "STABLE" else "\033[1;33m"
                print(f"\033[1;32m[ENV]\033[0m    Temp: {t:4.1f} C    | Hum:  {h:4.1f} %")
                print(f"\033[1;32m[ENV]\033[0m    Pres: {p:6.1f} hPa | Gas:  {g_str:7s} ({gas_color}{status}\033[0m)")
                print("\033[1;36m============================================================\033[0m")
                print("Press Ctrl+C to stop.                           ")
            except Exception as e:
                print(f"Error in Dashboard: {e}")

            time.sleep(0.1) # Increased delay for serial stability


    except KeyboardInterrupt:
        print("\n\nStopping integrated test...")
    finally:
        mic.deinit()
        print("I2S Microphone deinitialized.")

if __name__ == "__main__":
    run_integrated()