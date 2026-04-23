"""
AirVita — Raspberry Pi Pico Edge Code (MicroPython)
v2 Integrated Firmware: BME688 + BH1750 + I2S Mic + PMS5003 + LCD + NeoPixels
"""

import machine
import struct
import time
import math
import json
import neopixel
import sys

# Standard Path setup for the drivers in /lib
if "/lib" not in sys.path:
    sys.path.append("/lib")

try:
    from bme688 import BME688
    from bh1750 import BH1750
    from lcd1602 import LCD1602
except ImportError:
    print("Warning: Drivers missing in /lib. Ensure BME688, BH1750, and LCD1602 are uploaded.")

# --- 1. CONFIGURATION ---
# I2C (Bus 0) - Pins 0 (SDA), 1 (SCL)
SDA_PIN = 0
SCL_PIN = 1
I2C_ADDR_BME = 0x76
I2C_ADDR_BH = 0x23
I2C_ADDR_LCD = 0x27

# I2S (Mic) - Pins 16 (SCK), 17 (WS), 18 (SD)
SCK_PIN = 16
WS_PIN = 17
SD_PIN = 18

# UART (Air Quality - PMS5003) - Pins GP4 (TX), GP5 (RX)
UART_ID = 1
PMS_TX_PIN = 4
PMS_RX_PIN = 5

# Others
PIN_NEO = 2
PIN_LDR = 28 # Optional fallback analog sensor

# Audio Config
SAMPLE_RATE = 16000
BITS_PER_SAMPLE = 32
BUFFER_SIZE = 32768
SAMPLES_PER_READ = 256
GLITCH_THRESHOLD = 8000000 
ALPHA = 0.05 # Baseline smoothing

# --- 2. INITIALIZATION ---
i2c = machine.I2C(0, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=400000)
status_leds = neopixel.NeoPixel(machine.Pin(PIN_NEO), 8)
pms_uart = machine.UART(UART_ID, baudrate=9600, tx=machine.Pin(PMS_TX_PIN), rx=machine.Pin(PMS_RX_PIN))

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

read_buf = bytearray(SAMPLES_PER_READ * 8)

# --- 3. HELPERS ---

def wheel(pos):
    if pos < 85: return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

def rainbow_wave(offset):
    for i in range(8):
        status_leds[i] = wheel((i * 256 // 8 + offset) & 255)
    status_leds.write()

def dim_red():
    for i in range(8):
        status_leds[i] = (20, 0, 0)
    status_leds.write()

def parse_pms_data(data):
    if len(data) < 32: return None
    if data[0] != 0x42 or data[1] != 0x4D: return None
    
    check = sum(data[:30])
    calc_check = (data[30] << 8) | data[31]
    if check != calc_check:
        return None

    # Atmospheric environment readings (ug/m3)
    pm1_0 = (data[10] << 8) | data[11]
    pm2_5 = (data[12] << 8) | data[13]
    pm10  = (data[14] << 8) | data[15]
    
    # Particle counts per 0.1L of air
    pc_0_3 = (data[16] << 8) | data[17]
    pc_0_5 = (data[18] << 8) | data[19]
    pc_1_0 = (data[20] << 8) | data[21]
    
    return pm1_0, pm2_5, pm10, pc_0_3, pc_0_5, pc_1_0

def get_audio_metrics(baseline):
    bytes_read = mic.readinto(read_buf)
    if bytes_read == 0: return 0, 0, baseline
    
    count = bytes_read // 4
    raw = struct.unpack(f'<{count}i', read_buf[:bytes_read])
    
    clean = []
    for i in range(0, count, 2):
        s = raw[i] >> 8
        if abs(s) < GLITCH_THRESHOLD:
            clean.append(s)
            
    if not clean: return 0, 0, baseline
    
    current_avg = sum(clean) / len(clean)
    baseline = (ALPHA * current_avg) + ((1 - ALPHA) * baseline)
    sum_sq = sum((s - baseline)**2 for s in clean)
    rms = math.sqrt(sum_sq / len(clean))
    peak = max(abs(s - baseline) for s in clean)
    
    return rms, peak, baseline

# --- 4. MAIN LOOP ---

def setup():
    print("🚀 AirVita v2 Initializing...")
    devices = i2c.scan()
    print(f"I2C scan: {[hex(d) for d in devices]}")
    
    lcd, env, light = None, None, None
    
    if I2C_ADDR_LCD in devices:
        lcd = LCD1602(i2c)
        lcd.message("AirVita v2", "Initializing...")
    
    if I2C_ADDR_BME in devices:
        env = BME688(i2c, I2C_ADDR_BME)
        env.init()
        
    if I2C_ADDR_BH in devices:
        light = BH1750(i2c, I2C_ADDR_BH)
        light.init()

    # Stabilize Mic
    for _ in range(10):
        mic.readinto(read_buf)
        time.sleep(0.05)
        
    return lcd, env, light

def main():
    lcd, env, light = setup()
    baseline = 0
    pm1_0, pm2_5, pm10 = 0, 0, 0
    pc_0_3, pc_0_5, pc_1_0 = 0, 0, 0
    last_env_update = 0
    neo_offset = 0
    
    # Cached values for loop
    t, h, p, g, lux = 0, 0, 0, 0, 0
    
    while True:
        try:
            # 1. Update Audio (High Frequency)
            rms, peak, baseline = get_audio_metrics(baseline)
            noise_db = 20 * math.log10(rms) if rms > 0 else 0
            
            # 2. Update Environment (Slow Frequency)
            now = time.ticks_ms()
            if time.ticks_diff(now, last_env_update) > 1000:
                if env:
                    data = env.read_all()
                    if data:
                        t, h, p, g = data["temperature"], data["humidity"], data["pressure"], data["gas_res"]
                
                if light:
                    lux = light.read()
                
                if pms_uart.any() > 0:
                    buffer = pms_uart.read()
                    if buffer is not None:
                        for i in range(len(buffer) - 31, -1, -1):
                            if buffer[i] == 0x42 and buffer[i+1] == 0x4D:
                                packet = buffer[i:i+32]
                                parsed_pm = parse_pms_data(packet)
                                if parsed_pm is not None:
                                    pm1_0, pm2_5, pm10, pc_0_3, pc_0_5, pc_1_0 = parsed_pm
                                    break
                
                # Update LCD
                if lcd:
                    lcd.message(f"T:{t:2.0f} H:{h:2.0f} PM:{pm2_5:2.0f}", f"L:{lux:4.0f} N:{noise_db:2.0f}dB")
                
                last_env_update = now

            # 3. Update Visuals
            # Bright mode threshold
            if lux > 200:
                rainbow_wave(neo_offset)
                neo_offset = (neo_offset + 10) % 256
            else:
                dim_red()

            # 4. JSON Output (Bridge)
            payload = {
                "temperature": t,
                "humidity": h,
                "pressure": p,
                "light": lux,
                "sound_amp": noise_db,
                "pm1_0": pm1_0,
                "pm2_5": pm2_5,
                "pm10": pm10,
                "pc_0_3": pc_0_3,
                "pc_0_5": pc_0_5,
                "pc_1_0": pc_1_0,
                "particulates": pm2_5,
                "vocs": g / 1000.0 if g else 0,
                "timestamp_ms": time.ticks_ms()
            }
            print(json.dumps(payload))

        except Exception as e:
            print(json.dumps({"error": str(e)}))
            
        time.sleep(0.05)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopping...")
        mic.deinit()

