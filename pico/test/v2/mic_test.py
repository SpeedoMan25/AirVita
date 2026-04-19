import machine
from machine import I2S, Pin
import time
import math
import struct
import sys

# Standard Path setup for the LCD driver
if "/lib" not in sys.path:
    sys.path.append("/lib")

try:
    from pico_i2c_lcd import I2cLcd
except ImportError:
    try:
        from lib.pico_i2c_lcd import I2cLcd
    except ImportError:
        I2cLcd = None

# 1. Configuration
SCK_PIN = 16
WS_PIN = 17
SD_PIN = 18
I2C_SDA = 0
I2C_SCL = 1
LCD_ADDR = 0x27

# 2. I2S Initialization (Bus 0)
audio_in = I2S(
    0, 
    sck=Pin(SCK_PIN), 
    ws=Pin(WS_PIN), 
    sd=Pin(SD_PIN),
    mode=I2S.RX, 
    bits=32,          # 24-bit data padded to 32 bits
    format=I2S.MONO, 
    rate=16000, 
    ibuf=2048
)

# 3. LCD Initialization (Optional)
lcd = None
try:
    i2c = machine.I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL))
    if LCD_ADDR in i2c.scan():
        lcd = I2cLcd(i2c, LCD_ADDR, 2, 16)
except Exception:
    pass

def calculate_volume(buffer):
    """Calculates a basic volume level (RMS) from raw 32-bit I2S data."""
    count = len(buffer) // 4
    if count == 0: return 0
    
    # Unpack as signed integers (l or i for 32-bit signed)
    # The microphone returns 24bit data shifted into a 32bit int
    samples = struct.unpack(str(count) + 'i', buffer)
    
    sum_sq = 0
    for s in samples:
        # Normalize the 32-bit signed value to a small float to avoid overflow
        val = s / 1048576.0 # Normalize relative to ~20 bits of data
        sum_sq += val * val
        
    rms = math.sqrt(sum_sq / count)
    return rms

def run_test():
    print("--- V2 I2S Microphone Test (INMP441) ---")
    print(f"I2S SCK:GP{SCK_PIN}, WS:GP{WS_PIN}, SD:GP{PD_PIN if 'PD_PIN' in locals() else SD_PIN}")
    print("Clap or speak to see volume levels!")
    print("Press Ctrl+C to stop.")
    
    # Buffer for audio data
    buffer = bytearray(1024)
    
    try:
        if lcd:
            lcd.clear()
            lcd.putstr("V2 Mic Test")
            lcd.move_to(0, 1)
            lcd.putstr("Listening...")
            
        while True:
            # Read from I2S
            num_bytes = audio_in.readinto(buffer)
            
            if num_bytes > 0:
                # Calculate relative volume
                vol = calculate_volume(buffer[:num_bytes])
                
                # Create a simple console bar graph
                bar_len = min(int(vol * 2), 50)
                bar = "#" * bar_len
                print(f"VOL: {vol:7.1f} | {bar}")
                
                # Update LCD if detected
                if lcd:
                    lcd.move_to(0, 1)
                    lcd.putstr(f"Volume: {vol:7.1f}  ")
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        audio_in.deinit()
        if lcd: 
            lcd.clear()
            lcd.putstr("Test Stopped")

if __name__ == "__main__":
    run_test()
