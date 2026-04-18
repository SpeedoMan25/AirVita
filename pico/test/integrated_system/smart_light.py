import machine, neopixel, time, math
from pico_i2c_lcd import I2cLcd

# 1. Configuration
LDR_PIN = 28
THERM_PIN = 26
NEO_PIN = 2
NUM_LEDS = 8
LCD_ADDR = 0x27

# Thermistor Constants
B_COEFFICIENT = 3950
SERIES_RESISTOR = 10000 
TERM_RESISTANCE = 10000 
TEMP_NOMINAL = 25

# 2. Initialization
ldr = machine.ADC(LDR_PIN)
therm = machine.ADC(THERM_PIN)
i2c = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
lcd = I2cLcd(i2c, LCD_ADDR, 2, 16)
np = neopixel.NeoPixel(machine.Pin(NEO_PIN), NUM_LEDS)

def set_neopixels(color):
    for i in range(NUM_LEDS):
        np[i] = color
    np.write()

def get_light_percent():
    raw = ldr.read_u16()
    return (raw / 65535) * 100

def get_temperature():
    reading = therm.read_u16()
    if reading == 0 or reading >= 65535: return None
    resistance = SERIES_RESISTOR / (65535 / reading - 1)
    steinhart = resistance / TERM_RESISTANCE
    steinhart = math.log(steinhart)
    steinhart /= B_COEFFICIENT
    steinhart += 1.0 / (TEMP_NOMINAL + 273.15)
    return (1.0 / steinhart) - 273.15

def map_light_color(percent):
    # Transition from Amber (Low) to Bright White (High)
    brightness = int((percent / 100) * 180) + 20
    if percent < 30:
        return (brightness, brightness // 3, 0) # Amber/Orange
    return (brightness, brightness, brightness) # White

def map_temp_color(temp_f):
    # Vibrant Gradient: Blue (Cold) -> Green (Comfort) -> Red (Hot)
    # Range 65F to 85F
    if temp_f <= 65: return (0, 0, 180)  # Solid Blue
    if temp_f >= 85: return (180, 0, 0)  # Solid Red
    
    if temp_f < 75: # Blue to Green
        ratio = (temp_f - 65) / 10
        return (0, int(ratio * 150), int((1 - ratio) * 150))
    else: # Green to Red
        ratio = (temp_f - 75) / 10
        return (int(ratio * 150), int((1 - ratio) * 150), 0)

# 3. History Management
light_history = [(0,0,0)] * 4
temp_history = [(0,0,0)] * 4

print("--- Integrated Smart Home System (v3 High-Speed) ---")
print("Press Ctrl+C to stop.")

try:
    lcd.clear()
    lcd.putstr("System Booting...")
    time.sleep(1)
    
    # Pre-fill history to avoid empty start
    initial_light = map_light_color(get_light_percent())
    t_c = get_temperature()
    initial_temp = map_temp_color((t_c * 9/5) + 32) if t_c else (0,0,0)
    light_history = [initial_light] * 4
    temp_history = [initial_temp] * 4
    
    while True:
        # Get new readings
        light = get_light_percent()
        temp_c = get_temperature()
        temp_f = (temp_c * 9/5) + 32 if temp_c else 0
        
        # 1. Update History Lists
        light_history.insert(0, map_light_color(light))
        light_history.pop()
        
        temp_history.insert(0, map_temp_color(temp_f))
        temp_history.pop()
        
        # 2. Update NeoPixels
        for i in range(4):
            np[i] = light_history[i]
            np[i+4] = temp_history[i]
        np.write()
        
        # 3. Update LCD (Only every 5th cycle to prevent flickering)
        if time.ticks_ms() % 500 < 100:
            lcd.move_to(0, 0)
            lcd.putstr(f"Light: {light:4.1f}%   ")
            lcd.move_to(0, 1)
            lcd.putstr(f"Temp: {temp_f:4.1f}F    ")
            
        time.sleep(0.1) # 10x Faster!

except KeyboardInterrupt:
    print("\nShutting down...")
    lcd.clear()
    lcd.backlight_off()
    for i in range(NUM_LEDS): 
        np[i] = (0,0,0)
    np.write()
