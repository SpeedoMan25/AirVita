import serial
import time

class PMS5003:
    """
    PMS5003 Laser Particle Sensor Driver for Raspberry Pi 4B (Python 3).
    Uses UART connection (Default: /dev/ttyS0 or /dev/ttyAMA0).
    """
    def __init__(self, port='/dev/serial0', baudrate=9600):
        self.serial = serial.Serial(port, baudrate=baudrate, timeout=1.0)
        
    def read(self):
        """
        Reads a full 32-byte frame from the sensor.
        Returns a dictionary with PM1.0, PM2.5, and PM10 values.
        """
        try:
            # Sync with start bytes 0x42 0x4D
            while True:
                if self.serial.read(1) == b'\x42':
                    if self.serial.read(1) == b'\x4D':
                        break
            
            # Read the remaining 30 bytes
            data = self.serial.read(30)
            if len(data) < 30:
                return None
            
            # Frame: [Length(2)][PM1.0(2)][PM2.5(2)][PM10(2)] ... [Checksum(2)]
            # We use indices offset by -2 because we already read the start bytes
            pm1_0 = (data[2] << 8) | data[3]
            pm2_5 = (data[4] << 8) | data[5]
            pm10  = (data[6] << 8) | data[7]
            
            # Verification (Optional: Checksum calculation)
            # For simplicity in this hackathon, we return the parsed data
            return {
                "pm1_0": pm1_0,
                "pm2_5": pm2_5,
                "pm10": pm10
            }
        except Exception as e:
            # print(f"PMS5003 Error: {e}")
            return None

    def close(self):
        self.serial.close()
