from machine import I2C, Pin
from pico_i2c_lcd import I2cLcd
import time

# I2C Configuration (GP0/GP1)
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)

# Discover the address (we know it's 0x27 from the scan)
I2C_ADDR = 0x27

# Initialize LCD (2 lines, 16 columns)
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

def run_test():
    print("Starting LCD test...")
    
    # 1. Clear and show static text
    lcd.clear()
    lcd.putstr("Hello, Pico!")
    lcd.move_to(0, 1) # Move to second line
    lcd.putstr("I2C LCD 1602")
    time.sleep(3)
    
    # 2. Backlight test
    print("Testing backlight...")
    lcd.clear()
    lcd.putstr("Backlight Off")
    time.sleep(1)
    lcd.backlight_off()
    time.sleep(2)
    lcd.backlight_on()
    lcd.clear()
    lcd.putstr("Backlight On")
    time.sleep(2)
    
    # 3. Dynamic counter
    lcd.clear()
    lcd.putstr("Counter:")
    for i in range(11):
        lcd.move_to(9, 0)
        lcd.putstr(str(i))
        time.sleep(0.5)
    
    lcd.clear()
    lcd.putstr("Test Complete!")
    print("Test Complete!")

if __name__ == "__main__":
    try:
        run_test()
    except KeyboardInterrupt:
        lcd.clear()
        lcd.backlight_off()
