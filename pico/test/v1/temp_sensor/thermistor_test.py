from machine import ADC
import math
import time

# Pin Configuration: GP26 (ADC0) on Physical Pin 31
THERM_PIN = 26
adc = ADC(THERM_PIN)

# Constants for 10k NTC Thermistor
B_COEFFICIENT = 3950
SERIES_RESISTOR = 10000 # 10k fixed resistor
TERM_RESISTANCE = 10000 # resistance at 25 degrees C
TEMP_NOMINAL = 25

print("--- Thermistor Temperature Tester ---")
print(f"Reading Analog values on GP{THERM_PIN}...")
print("Press Ctrl+C to stop.")
print("-" * 34)

def get_temperature():
    # Read ADC value (0-65535)
    reading = adc.read_u16()
    
    if reading == 0 or reading >= 65535:
        return None
        
    # Calculate resistance of the thermistor
    # Wiring: 3.3V -> 10k Resistor -> GP26 -> Thermistor -> GND
    # Formula: R_therm = R_fixed / (65535/reading - 1)
    resistance = SERIES_RESISTOR / (65535 / reading - 1)
    
    # Steinhart-Hart equation (simplified Beta formula)
    steinhart = resistance / TERM_RESISTANCE      # (R/Ro)
    steinhart = math.log(steinhart)               # ln(R/Ro)
    steinhart /= B_COEFFICIENT                    # 1/B * ln(R/Ro)
    steinhart += 1.0 / (TEMP_NOMINAL + 273.15)    # + (1/To)
    steinhart = 1.0 / steinhart                    # Invert
    steinhart -= 273.15                           # Convert to Celsius
    
    return steinhart

try:
    while True:
        temp_c = get_temperature()
        if temp_c is not None:
            temp_f = (temp_c * 9/5) + 32
            print(f"Raw ADC: {adc.read_u16():5} | Temp: {temp_c:.1f} °C | {temp_f:.1f} °F")
        else:
            print("Error reading sensor (check wiring)")
            
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping Thermistor Tester...")
