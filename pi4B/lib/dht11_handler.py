import time
import board
import adafruit_dht

class DHT11Handler:
    """
    Handler for DHT11 Temperature and Humidity sensor on Raspberry Pi 4B.
    Uses adafruit_dht library and handles common read errors.
    """
    def __init__(self, pin=board.D5):
        self.dht = adafruit_dht.DHT11(pin)
        self.last_temp = None
        self.last_hum = None

    def read(self):
        """
        Attempt to read temperature and humidity.
        DHT sensors are unreliable, so this handles retries and returns last known good values
        if a reading fails during a specific attempt.
        """
        try:
            temp = self.dht.temperature
            hum = self.dht.humidity
            
            if temp is not None and hum is not None:
                self.last_temp = temp
                self.last_hum = hum
                return temp, hum
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            # print(f"DHT11 Read Error: {error.args[0]}")
            pass
        except Exception as error:
            # self.dht.exit()
            # raise error
            print(f"DHT11 Fatal Error: {error}")
            
        return self.last_temp, self.last_hum

    def close(self):
        self.dht.exit()
