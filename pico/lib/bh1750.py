import time

class BH1750:
    """
    BH1750 Digital Light Sensor Driver for MicroPython.
    Default I2C address is 0x23 (ADDR grounded).
    """
    def __init__(self, i2c, address=0x23):
        self.i2c = i2c
        self.address = address
        self.mode = 0x10  # Continuously H-Resolution Mode
        
    def init(self):
        try:
            # 0x01 = Power On, 0x07 = Reset, 0x10 = Continuous H-Res
            self.i2c.writeto(self.address, bytes([0x01])) 
            time.sleep(0.05)
            self.i2c.writeto(self.address, bytes([0x07])) # Soft Reset
            time.sleep(0.05)
            self.i2c.writeto(self.address, bytes([self.mode]))
        except Exception as e:
            print(f"BH1750 Init Failed: {e}")

    def read(self):
        try:
            data = self.i2c.readfrom(self.address, 2)
            lux = (data[0] << 8 | data[1]) / 1.2
            return round(lux, 2)
        except Exception:
            return 0.0
