from machine import ADC, Pin
import time

# Pin Configuration
# ADC Input on GP28 (Physical Pin 34)
LDR_PIN = 28
ldr = ADC(LDR_PIN)

# Also use the onboard LED for visual feedback
led = Pin(25, Pin.OUT)

print("--- Photoresistor (LDR) Tester ---")
print(f"Reading Analog values on GP{LDR_PIN}...")
print("Press Ctrl+C to stop.")
print("-" * 34)

try:
    while True:
        # Read the raw 16-bit value (0-65535)
        raw_value = ldr.read_u16()
        
        # Calculate percentage (assuming 0 is dark and 65535 is bright)
        # Note: Depending on your resistor, it might stay between 300 - 64000
        percent = (raw_value / 65535) * 100
        
        # Calculate voltage (Pico ADC is 3.3V max)
        voltage = (raw_value / 65535) * 3.3
        
        # Terminal Output
        print(f"Raw: {raw_value:5} | Voltage: {voltage:.2f}V | Light: {percent:5.1f}%")
        
        # Simple threshold for the onboard LED
        if percent < 20:
            led.value(1) # Turn on light when it's dark
        else:
            led.value(0)
            
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nStopping LDR Tester...")
    led.value(0)
