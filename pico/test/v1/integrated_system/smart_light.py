import machine, neopixel, time, math, dht
from pico_i2c_lcd import I2cLcd

# 1. Configuration
LDR_PIN = 28
THERM_PIN = 26
NEO_PIN = 2
DHT_PIN = 3
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
dht_sensor = dht.DHT11(machine.Pin(DHT_PIN))

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

def map_humidity_color(humidity):
    # Yellow (Dry) -> Green (Comfort) -> Blue (Humid)
    if humidity <= 30: return (180, 100, 0) # Dry Orange/Yellow
    if humidity >= 60: return (0, 0, 180)   # Humid Blue
    
    if humidity < 45: # Dry to Comfort (Yellow to Green)
        ratio = (humidity - 30) / 15
        return (int((1 - ratio) * 180), 150, 0)
    else: # Comfort to Humid (Green to Blue)
        ratio = (humidity - 45) / 15
        return (0, int((1 - ratio) * 150), int(ratio * 150))

# 3. History Management
light_history = [(0,0,0)] * 8
hum_history = [(0,0,0)] * 8
therm_history = [(0,0,0)] * 8
dht_history = [(0,0,0)] * 8

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
    
    light_history = [initial_light] * 8
    hum_history = [(0, 150, 0)] * 8 # Green for comfort
    therm_history = [initial_temp] * 8
    dht_history = [initial_temp] * 8
    
    last_dht_read = 0
    last_mode_switch = 0
    last_console_log = 0
    last_lcd_update = 0
    display_mode = 0 # 0:LIGHT, 1:HUMIDITY, 2:THERM, 3:DHT11
    
    dht_temp_f = 0
    dht_humidity = 0
    
    while True:
        curr_time = time.ticks_ms()
        
        # 0. Throttled DHT11 Read (Every 3 seconds)
        if time.ticks_diff(curr_time, last_dht_read) > 3000:
            try:
                dht_sensor.measure()
                dht_temp_c = dht_sensor.temperature()
                dht_temp_f = (dht_temp_c * 9/5) + 32
                dht_humidity = dht_sensor.humidity()
                last_dht_read = curr_time
            except Exception as e:
                print(f"DHT11 Error: {e}")
        
        # 1. Get current readings
        light = get_light_percent()
        therm_c = get_temperature()
        therm_f = (therm_c * 9/5) + 32 if therm_c else 0
        
        # Update History Lists
        light_history.insert(0, map_light_color(light))
        light_history.pop()
        
        hum_history.insert(0, map_humidity_color(dht_humidity))
        hum_history.pop()
        
        therm_history.insert(0, map_temp_color(therm_f))
        therm_history.pop()
        
        dht_history.insert(0, map_temp_color(dht_temp_f))
        dht_history.pop()
        
        # 2. Handle Display Cycling (Every 3 seconds)
        if time.ticks_diff(curr_time, last_mode_switch) > 3000:
            display_mode = (display_mode + 1) % 4
            last_mode_switch = curr_time
            lcd.clear() # Clear screen for new mode
        
        # 3. Console Logging (Every 1 second)
        if time.ticks_diff(curr_time, last_console_log) > 1000:
            print(f"DATA | Light: {light:4.1f}% | Humidity: {dht_humidity}% | Thermistor: {therm_f:4.1f}F | DHT11: {dht_temp_f:4.1f}F")
            last_console_log = curr_time

        # 4. Update LCD (Throttled to every 200ms)
        if time.ticks_diff(curr_time, last_lcd_update) > 200:
            current_color = (0,0,0)
            lcd.backlight_on() # Ensure backlight stays on
            
            if display_mode == 0: # LIGHT MODE
                current_color = map_light_color(light)
                lcd.move_to(0, 0)
                lcd.putstr("-- LIGHT LEVEL --")
                lcd.move_to(0, 1)
                lcd.putstr(f"     {light:4.1f} %")
                
            elif display_mode == 1: # HUMIDITY MODE
                current_color = map_humidity_color(dht_humidity)
                lcd.move_to(0, 0)
                lcd.putstr("-- HUMIDITY --")
                lcd.move_to(0, 1)
                lcd.putstr(f"     {dht_humidity:2.0f} %")
                
            elif display_mode == 2: # THERMISTOR MODE
                current_color = map_temp_color(therm_f)
                lcd.move_to(0, 0)
                lcd.putstr("-- THERMISTOR --")
                lcd.move_to(0, 1)
                lcd.putstr(f"    {therm_f:4.1f} F")

            elif display_mode == 3: # DHT11 MODE
                current_color = map_temp_color(dht_temp_f)
                lcd.move_to(0, 0)
                lcd.putstr("-- DHT11 TEMP --")
                lcd.move_to(0, 1)
                lcd.putstr(f"    {dht_temp_f:4.1f} F")
            
            last_lcd_update = curr_time

        # 5. Apply NeoPixel Color to ALL 8 LEDs (History Mode)
        if display_mode == 0:
            for i in range(8): np[i] = light_history[i]
        elif display_mode == 1:
            for i in range(8): np[i] = hum_history[i]
        elif display_mode == 2:
            for i in range(8): np[i] = therm_history[i]
        elif display_mode == 3:
            for i in range(8): np[i] = dht_history[i]
        np.write()
            
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nShutting down...")
    lcd.clear()
    lcd.backlight_off()
    for i in range(NUM_LEDS): 
        np[i] = (0,0,0)
    np.write()
