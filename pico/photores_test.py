import machine, neopixel, time
from pico_i2c_lcd import I2cLcd

# 1. Configuration
LDR_PIN = 28
NEO_PIN = 2
NUM_LEDS = 8
LCD_ADDR = 0x27

# 2. Initialization
# ADC for Photoresistor
ldr = machine.ADC(LDR_PIN)

# I2C for LCD (GP0/GP1)
i2c = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
lcd = I2cLcd(i2c, LCD_ADDR, 2, 16)

# NeoPixels on GP2
np = neopixel.NeoPixel(machine.Pin(NEO_PIN), NUM_LEDS)

def set_neopixels(color):
    for i in range(NUM_LEDS):
        np[i] = color
    np.write()

def get_light_percent():
    raw = ldr.read_u16()
    return (raw / 65535) * 100

print("--- Integrated Smart Light System ---")
print("Press Ctrl+C to stop.")

try:
    lcd.clear()
    lcd.putstr("Smart Home Sys")
    time.sleep(2)
    
    while True:
        # Get light level
        light = get_light_percent()
        
        # Display on LCD
        lcd.move_to(0, 0)
        lcd.putstr(f"Light: {light:5.1f}%  ") # Padding to clear artifacts
        
        lcd.move_to(0, 1)
        if light < 25:
            lcd.putstr("MODE: NIGHT     ")
            set_neopixels((150, 150, 150)) # Dim White
        elif light < 75:
            lcd.putstr("MODE: AMBIENT   ")
            set_neopixels((0, 0, 150))     # Blue
        else:
            lcd.putstr("MODE: BRIGHT    ")
            set_neopixels((0, 150, 0))     # Green
            
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nShutting down...")
    lcd.clear()
    lcd.backlight_off()
    set_neopixels((0, 0, 0))




