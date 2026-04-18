from machine import I2C, Pin
import time

# Using I2C0 on GP0/GP1
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)

print("Scanning I2C bus...")
devices = i2c.scan()

if len(devices) == 0:
    print("No I2C devices found! Check your wiring and ensure VCC is on Pin 40.")
else:
    print(f"I2C devices found: {len(devices)}")
    for device in devices:
        print(f"Decimal address: {device} | Hex address: {hex(device)}")
