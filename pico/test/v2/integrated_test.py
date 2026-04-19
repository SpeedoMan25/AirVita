import machine
import neopixel
import time
import sys
import struct

# Standard Path setup for the drivers
if "/lib" not in sys.path:
    sys.path.append("/lib")

try:
    from pico_i2c_lcd import I2cLcd
    from bh1750 import BH1750
    from bme688 import BME688
except ImportError:
    print("Error: Required libraries (lcd, bh1750, bme688) missing in /lib")

# --- 1. CONFIGURATION ---
# I2C (Bus 0) - Pins 1/2
I2C_ADDR_LCD = 0x27
I2C_ADDR_LIGHT = 0x23
I2C_ADDR_BME = 0x76 # Or 0x77
SDA_PIN = 0
SCL_PIN = 1

# UART (Bus 1) - Pins 6/7
UART_TX = 4
UART_RX = 5

# I2S (Mic) - Pins 21/22/24
I2S_SCK = 16
I2S_WS = 17
I2S_SD = 18

# GPIOs
NEO_PIN = 2
NUM_LEDS = 16
BUZZER_PIN = 15

# --- 2. INITIALIZATION ---
# I2C
i2c = machine.I2C(0, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=100000)
# UART for PMS5003
uart = machine.UART(1, baudrate=9600, tx=machine.Pin(UART_TX), rx=machine.Pin(UART_RX))
# I2S for Microphone
mic = machine.I2S(0, sck=machine.Pin(I2S_SCK), ws=machine.Pin(I2S_WS), sd=machine.Pin(I2S_SD),
                  mode=machine.I2S.RX, bits=32, format=machine.I2S.MONO,
                  rate=44100, ibuf=1024)

# Peripherals
np = neopixel.NeoPixel(machine.Pin(NEO_PIN), NUM_LEDS)
buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)

# Driver Instances (Handle discovery)
lcd = None
light_sensor = None
env_sensor = None

def init_drivers():
    global lcd, light_sensor, env_sensor, I2C_ADDR_BME
    devices = i2c.scan()
    print(f"I2C Scan: {[hex(d) for d in devices]}")
    
    if I2C_ADDR_LCD in devices: lcd = I2cLcd(i2c, I2C_ADDR_LCD, 2, 16)
    if I2C_ADDR_LIGHT in devices: light_sensor = BH1750(i2c)
    
    if 0x76 in devices: I2C_ADDR_BME = 0x76
    elif 0x77 in devices: I2C_ADDR_BME = 0x77
    
    if I2C_ADDR_BME in devices:
        env_sensor = BME688(i2c, I2C_ADDR_BME)
        env_sensor.init()

# --- 3. SENSOR HELPERS ---

def get_air_quality():
    """Non-blocking read from PMS5003 UART"""
    if uart.any() >= 32:
        data = uart.read(32)
        if data and data[0] == 0x42 and data[1] == 0x4d:
            pm25 = struct.unpack('>H', data[6:8])[0]
            return pm25
    return None

def get_audio_volume():
    """Calculate RMS volume from I2S stream"""
    read_buf = bytearray(512)
    bytes_read = mic.readinto(read_buf)
    if bytes_read > 0:
        samples = struct.unpack(f'<{bytes_read//4}i', read_buf[:bytes_read])
        sum_sq = sum((s >> 16)**2 for s in samples) # Use high 16 bits
        return (sum_sq / (len(samples)))**0.5
    return 0

# --- 4. MAIN LOOP ---

def run_integrated():
    print("--- V2 Full Integrated System ---")
    init_drivers()
    
    current_pm25 = 0
    current_lux = 0
    current_temp = 0
    current_hum = 0
    display_page = 0
    last_page_flip = time.ticks_ms()
    
    try:
        while True:
            # A. Update Sensors
            # 1. Light
            if light_sensor:
                try: current_lux = light_sensor.luminance(BH1750.ONCE_HIRES_1)
                except: pass
            
            # 2. Environment
            if env_sensor:
                env_data = env_sensor.read_all()
                current_temp = env_data['temperature']
                current_hum = env_data['humidity']
            
            # 3. Air Quality
            aq = get_air_quality()
            if aq is not None: current_pm25 = aq
            
            # 4. Audio level (Directly controls LED brightness)
            vol = get_audio_volume()
            brightness = min(1.0, vol / 5000.0) # Scaling factor
            
            # 5. Gas Alert
            if env_sensor and env_data['gas_res'] < 50000:
                buzzer.value(1)
                time.sleep(0.01) # Very brief tick
                buzzer.value(0)
            
            # B. React with NeoPixels
            # Color based on PM2.5 (Air Quality)
            if current_pm25 < 35: color = (0, 255, 0) # Green
            elif current_pm25 < 75: color = (255, 255, 0) # Yellow
            else: color = (255, 0, 0) # Red
            
            # Apply brightness to the color
            final_color = tuple(int(c * brightness) for c in color)
            np.fill(final_color)
            np.write()
            
            # C. Update LCD (Page Rotation)
            if time.ticks_diff(time.ticks_ms(), last_page_flip) > 3000:
                display_page = (display_page + 1) % 3
                last_page_flip = time.ticks_ms()
                if lcd: lcd.clear()

            if lcd:
                lcd.move_to(0, 0)
                if display_page == 0:
                    lcd.putstr(f"Temp: {current_temp:.1f}C")
                    lcd.move_to(0, 1)
                    lcd.putstr(f"Hum:  {current_hum:.1f}%")
                elif display_page == 1:
                    lcd.putstr(f"PM2.5: {current_pm25} ug/m3")
                    lcd.move_to(0, 1)
                    status = "GOOD" if current_pm25 < 35 else "POOR"
                    lcd.putstr(f"Air: {status}")
                elif display_page == 2:
                    lcd.putstr(f"Light: {current_lux:.0f} Lux")
                    lcd.move_to(0, 1)
                    lcd.putstr(f"Noise: {int(vol)}")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")
        if lcd: lcd.clear()
        np.fill((0,0,0))
        np.write()

if __name__ == "__main__":
    run_integrated()
