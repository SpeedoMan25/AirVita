import machine
import utime

# Standard Pico onboard LED is on GP25
led = machine.Pin(25, machine.Pin.OUT)

print("Starting blink script... Press Ctrl+C in REPL to stop.")

while True:
    led.toggle()
    utime.sleep(0.5)
