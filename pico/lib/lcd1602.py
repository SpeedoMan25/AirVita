import time

class LCD1602:
    def __init__(self, i2c, addr=0x27):
        self.i2c = i2c
        self.addr = addr
        self.backlight = 0x08
        self._write(0x33)
        self._write(0x32)
        self._write(0x28)
        self._write(0x0C)
        self._write(0x01)
        time.sleep(0.005)

    def _write_nibble(self, n):
        self.i2c.writeto(self.addr, bytes([n | self.backlight | 0x04]))
        self.i2c.writeto(self.addr, bytes([n | self.backlight]))

    def _write(self, cmd, mode=0):
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
        # Pad string to 16 chars to overwrite old data
        padded = (s[:16] + " " * 16)[:16]
        self.putstr(padded)

    def message(self, line1, line2=""):
        """Update both lines smoothly without clearing."""
        self.putstr_fixed(line1, 0)
        self.putstr_fixed(line2, 1)
