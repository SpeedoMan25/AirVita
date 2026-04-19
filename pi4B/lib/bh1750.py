import time
from smbus2 import SMBus

class BH1750:
    """
    BH1750 Digital Light Sensor Driver for Raspberry Pi 4B (Python 3).
    Default I2C address is 0x23 (ADDR grounded).
    """
    def __init__(self, bus_id=1, address=0x23):
        self.bus = SMBus(bus_id)
        self.address = address
        self.mode = 0x10  # Continuously H-Resolution Mode
        
    def init(self):
        try:
            self.bus.write_byte(self.address, 0x01) # Power On
            time.sleep(0.1)
            self.bus.write_byte(self.address, self.mode)
        except Exception as e:
            print(f"BH1750 Init Failed: {e}")

    def read(self):
        try:
            # Trigger a new measurement
            self.bus.write_byte(self.address, self.mode)
            time.sleep(0.18)  # BH1750 needs ~180ms for H-res measurement
            # Read 2 bytes of data
            data = self.bus.read_i2c_block_data(self.address, self.mode, 2)
            lux = (data[0] << 8 | data[1]) / 1.2
            return round(lux, 2)
        except Exception as e:
            print(f"BH1750 Read Failed: {e}")
            return 0.0

    def close(self):
        self.bus.close()
