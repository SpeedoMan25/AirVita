import time
from smbus2 import SMBus

class LCD1602:
    """
    I2C LCD1602 Driver for Raspberry Pi 4B (Python 3).
    Based on the PCF8574 I2C adapter.
    """
    def __init__(self, bus_id=1, addr=0x27):
        self.bus = SMBus(bus_id)
        self.addr = addr
        self.backlight = 0x08
        self._write(0x33) # 8-bit mode
        self._write(0x32) # 4-bit mode
        self._write(0x28) # 2 lines, 5x7 matrix
        self._write(0x0C) # Display on, cursor off
        self._write(0x01) # Clear display
        time.sleep(0.005)

    def _write_nibble(self, n):
        # En=1, Rs=mode, Rw=0
        # Byte format: D7 D6 D5 D4 BL EN RW RS
        self.bus.write_byte(self.addr, n | self.backlight | 0x04)
        time.sleep(0.0001)
        self.bus.write_byte(self.addr, n | self.backlight)
        time.sleep(0.0001)

    def _write(self, cmd, mode=0):
        # mode=0 for command, mode=1 for data (RS pin)
        self._write_nibble(mode | (cmd & 0xF0))
        self._write_nibble(mode | ((cmd << 4) & 0xF0))

    def clear(self):
        self._write(0x01)
        time.sleep(0.005)

    def move_to(self, col, row):
        addr = col + (0x40 if row else 0x00)
        self._write(0x80 | addr)

    def putstr(self, s):
        for char in s:
            self._write(ord(char), 1)

    def putstr_fixed(self, s, row):
        """Write a string to a specific row, padded to 16 characters."""
        self.move_to(0, row)
        padded = (s[:16] + " " * 16)[:16]
        self.putstr(padded)

    def message(self, line1, line2=""):
        """Update both lines smoothly without clearing."""
        self.putstr_fixed(line1, 0)
        self.putstr_fixed(line2, 1)

    def close(self):
        self.bus.close()
