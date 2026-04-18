import machine
import time
import neopixel
from lib.lcd1602 import LCD1602

# Pins matching photores_test.py and image
LDR_PIN = 28
NEO_PIN = 2
NUM_LEDS = 8
SDA_PIN = 0
SCL_PIN = 1

def scan_i2c():
    i2c = machine.I2C(0, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN))
    print("Scanning I2C bus (GP0/1)...")
    devices = i2c.scan()
    print(f"Devices found: {[hex(d) for d in devices]}")
    return i2c

def test_sensors():
    i2c = scan_i2c()
    ldr = machine.ADC(LDR_PIN)
    np = neopixel.NeoPixel(machine.Pin(NEO_PIN), NUM_LEDS)
    
    try:
        lcd = LCD1602(i2c)
        lcd.message("Smart Light Test", "Starting...")
        time.sleep(2)
        
        print("Running Smart Light Test (Ctrl+C to stop)...")
        while True:
            # 1. Get light percent
            raw = ldr.read_u16()
            light = (raw / 65535) * 100
            
            # 2. Logic matching photores_test.py
            if light < 25:
                mode = "NIGHT"
                color = (150, 150, 150) # Dim White
            elif light < 75:
                mode = "AMBIENT"
                color = (0, 0, 150)     # Blue
            else:
                mode = "BRIGHT"
                color = (0, 150, 0)     # Green
                
            # 3. Update LEDs
            for i in range(NUM_LEDS):
                np[i] = color
            np.write()
            
            # 4. Update LCD
            lcd.message(f"Light: {light:5.1f}%", f"MODE: {mode}")
            
            print(f"Light: {light:.1f}% | Mode: {mode}")
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nStopping test...")
        for i in range(NUM_LEDS): np[i] = (0,0,0)
        np.write()

if __name__ == "__main__":
    test_sensors()
