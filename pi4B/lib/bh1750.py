import time
from smbus2 import SMBus

class BH1750:
    """
    BH1750 Digital Light Sensor Driver for Raspberry Pi 4B (Python 3).
    Common addresses: 0x23 (ADDR grounded) or 0x5C (ADDR high).
    """
    def __init__(self, bus_id=1, address=0x23):
        self.bus = SMBus(bus_id)
        self.address = address
        self.mode = 0x10  # Continuously H-Resolution Mode
        self.initialized = False
        
    def init(self):
        # Try primary address
        try:
            self.bus.write_byte(self.address, 0x01) # Power On
            time.sleep(0.1)
            self.bus.write_byte(self.address, self.mode)
            self.initialized = True
            return True
        except Exception as e_primary:
            # Try alternate address if primary fails
            alt_address = 0x5C if self.address == 0x23 else 0x23
            try:
                self.bus.write_byte(alt_address, 0x01)
                time.sleep(0.1)
                self.bus.write_byte(alt_address, self.mode)
                self.address = alt_address
                self.initialized = True
                print(f"BH1750 found at alternate address: {hex(self.address)}")
                return True
            except Exception as e_alt:
                print(f"BH1750 Init Failed on all addresses.\nPrimary Error: {e_primary}\nAlternate Error: {e_alt}")
                print("HINT: Ensure I2C is enabled in sudo raspi-config and wiring to GPIO 2/3 is correct.")
                self.initialized = False
                return False

    def read(self):
        if not self.initialized:
            if not self.init():
                return 0.0
        try:
            # Trigger/Check measurement
            # Read 2 bytes of data
            data = self.bus.read_i2c_block_data(self.address, self.mode, 2)
            lux = (data[0] << 8 | data[1]) / 1.2
            return round(lux, 2)
        except Exception as e:
            # print(f"BH1750 Read Failed: {e}")
            self.initialized = False # Force re-init on next read
            return 0.0

    def close(self):
        try:
            self.bus.close()
        except:
            pass
