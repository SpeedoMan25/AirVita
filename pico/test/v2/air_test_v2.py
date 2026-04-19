import machine
import time
import sys

# Standard Path setup for the LCD driver
if "/lib" not in sys.path:
    sys.path.append("/lib")

try:
    from pico_i2c_lcd import I2cLcd
except ImportError:
    try:
        from lib.pico_i2c_lcd import I2cLcd
    except ImportError:
        I2cLcd = None

# 1. Configuration
UART_ID = 1
TX_PIN = 4
RX_PIN = 5
I2C_SDA = 0
I2C_SCL = 1
LCD_ADDR = 0x27

# 2. UART Initialization (9600 baud for PMS5003)
uart = machine.UART(UART_ID, baudrate=9600, tx=machine.Pin(TX_PIN), rx=machine.Pin(RX_PIN))

# 3. LCD Initialization (Optional)
lcd = None
try:
    i2c = machine.I2C(0, sda=machine.Pin(I2C_SDA), scl=machine.Pin(I2C_SCL))
    if LCD_ADDR in i2c.scan():
        lcd = I2cLcd(i2c, LCD_ADDR, 2, 16)
except Exception:
    pass

def parse_pms_data(data):
    """
    Parses 32-byte PMS5003 packet.
    Standard PM values are at bytes 10-15 (1-indexed in datasheet).
    Indices below are 0-indexed for the buffer.
    """
    if len(data) < 32: return None
    
    # PM values are 16-bit big-endian
    # pmX_standard = Data from sensor "under standard particle"
    # pmX_atmospheric = Data from sensor "under atmospheric environment"
    
    # Atmospheric environment values are generally preferred for indoor use
    pm1_0 = (data[10] << 8) | data[11]
    pm2_5 = (data[12] << 8) | data[13]
    pm10 = (data[14] << 8) | data[15]
    
    return {"pm10": pm1_0, "pm25": pm2_5, "pm100": pm10}

def get_quality_label(pm25):
    """Categorizes PM2.5 levels into human-readable status."""
    if pm25 <= 12: return "EXCELLENT", "Clean Air"
    if pm25 <= 35: return "GOOD", "Moderate"
    if pm25 <= 55: return "FAIR", "Slightly Dusty"
    if pm25 <= 150: return "POOR", "Unhealthy"
    return "DANGER", "Hazardous"

def run_test():
    print("--- V2 Human-Friendly Air Quality ---")
    print("Waiting for sensor...")
    
    try:
        if lcd:
            lcd.clear()
            lcd.putstr("V2 Air Quality")
            lcd.move_to(0, 1)
            lcd.putstr("Warming up...")

        while True:
            # PMS5003 sends 32-byte packets
            if uart.any() >= 32:
                # Look for the start of the packet header [0x42, 0x4D]
                header = uart.read(1)
                if header == b'\x42':
                    second_byte = uart.read(1)
                    if second_byte == b'\x4D':
                        # Valid header found, read the remaining 30 bytes
                        data = uart.read(30)
                        if len(data) == 30:
                            # Reconstruct full packet for parsing
                            full_packet = b'\x42\x4D' + data
                            res = parse_pms_data(full_packet)
                            
                            if res:
                                pm25 = res["pm25"]
                                # Get friendly labels
                                status, desc = get_quality_label(pm25)
                                
                                # High sensitivity counts
                                smoke_count = (full_packet[16] << 8) | full_packet[17]   # 0.3um
                                fine_dust = (full_packet[18] << 8) | full_packet[19]    # 0.5um
                                coarse_dust = (full_packet[24] << 8) | full_packet[25]  # 5.0um
                                
                                # Clear Human-Friendly Console Output
                                print("\n" + "="*30)
                                print(f"STATUS:  {status} ({desc})")
                                print(f"MASS:    {pm25} ug/m3 (Microscopic Weight)")
                                print("-" * 30)
                                print(f"SMOKE/VIRUS: {smoke_count} units")
                                print(f"FINE DUST:   {fine_dust} units")
                                print(f"POLLEN/MOLD: {coarse_dust} units")
                                print("="*30)
                                
                                # Human-Friendly LCD Output
                                if lcd:
                                    lcd.move_to(0, 0)
                                    lcd.putstr(f"AIR: {status:<10}")
                                    lcd.move_to(0, 1)
                                    lcd.putstr(f"PM2.5: {pm25:<3} {desc[:6]} ")
                
            time.sleep(0.1) # Small delay to prevent CPU saturation
            
    except KeyboardInterrupt:
        print("\nTest stopped. Clearing LCD...")
        if lcd:
            lcd.clear()
            lcd.putstr("V2 System")
            lcd.move_to(0, 1)
            lcd.putstr("Sensor Offline")
    except Exception as e:
        print(f"System Error: {e}")

if __name__ == "__main__":
    run_test()
