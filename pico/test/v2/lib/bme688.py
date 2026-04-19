"""
MicroPython driver for BME680/BME688 - Based on robert-hh and Adafruit drivers
Supports Temperature, Humidity, Pressure, and Gas Resistance.
"""

import time
import math
from micropython import const
import struct

_BME680_CHIPID = const(0x61)
_BME680_REG_CHIPID = const(0xD0)
_BME680_BME680_COEFF_ADDR1 = const(0x89)
_BME680_BME680_COEFF_ADDR2 = const(0xE1)
_BME680_BME680_RES_HEAT_0 = const(0x5A)
_BME680_BME680_GAS_WAIT_0 = const(0x64)
_BME680_REG_SOFTRESET = const(0xE0)
_BME680_REG_CTRL_GAS = const(0x71)
_BME680_REG_CTRL_HUM = const(0x72)
_BME680_REG_CTRL_MEAS = const(0x74)
_BME680_REG_CONFIG = const(0x75)
_BME680_REG_MEAS_STATUS = const(0x1D)

_LOOKUP_TABLE_1 = (2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0,
                   2126008810.0, 2147483647.0, 2130303777.0, 2147483647.0, 2147483647.0,
                   2143188679.0, 2136746228.0, 2147483647.0, 2126008810.0, 2147483647.0,
                   2147483647.0)

_LOOKUP_TABLE_2 = (4096000000.0, 2048000000.0, 1024000000.0, 512000000.0, 255744255.0, 127110228.0,
                   64000000.0, 32258064.0, 16016016.0, 8000000.0, 4000000.0, 2000000.0, 1000000.0,
                   500000.0, 250000.0, 125000.0)

def _read24(arr):
    ret = 0.0
    for b in arr:
        ret *= 256.0
        ret += float(b & 0xFF)
    return ret

class BME688:
    def __init__(self, i2c, address=0x77):
        self.i2c = i2c
        self.address = address
        
        # Soft Reset
        self.i2c.writeto_mem(self.address, _BME680_REG_SOFTRESET, b'\xB6')
        time.sleep(0.01)
        
        # Check Chip ID
        chip_id = self.i2c.readfrom_mem(self.address, _BME680_REG_CHIPID, 1)[0]
        if chip_id != _BME680_CHIPID:
            raise RuntimeError(f"BME688 not found! (ID: 0x{chip_id:02x})")
            
        self._read_calibration()
        
        # Initial config
        self.i2c.writeto_mem(self.address, _BME680_BME680_RES_HEAT_0, b'\x73')
        self.i2c.writeto_mem(self.address, _BME680_BME680_GAS_WAIT_0, b'\x65')
        
        self._pressure_oversample = 0b011
        self._temp_oversample = 0b100
        self._humidity_oversample = 0b010
        self._filter = 0b010
        self._t_fine = None

    def _read_calibration(self):
        coeff = list(self.i2c.readfrom_mem(self.address, _BME680_BME680_COEFF_ADDR1, 25))
        coeff += list(self.i2c.readfrom_mem(self.address, _BME680_BME680_COEFF_ADDR2, 16))
        
        params = list(struct.unpack('<hbBHhbBhhbbHhhBBBHbbbBbHhbb', bytes(coeff[1:39])))
        params = [float(i) for i in params]
        
        self._temp_cal = [params[x] for x in [23, 0, 1]]
        self._pres_cal = [params[x] for x in [3, 4, 5, 7, 8, 10, 9, 12, 13, 14]]
        self._hum_cal = [params[x] for x in [17, 16, 18, 19, 20, 21, 22]]
        self._gas_cal = [params[x] for x in [25, 24, 26]]
        
        self._hum_cal[1] = self._hum_cal[1] * 16.0 + (self._hum_cal[0] % 16.0)
        self._hum_cal[0] = self._hum_cal[0] / 16.0
        
        # SW error calculation
        self._sw_err = (self.i2c.readfrom_mem(self.address, 0x04, 1)[0] & 0xF0) / 16.0

    def read_all(self):
        # Trigger measurement (Forced Mode)
        self.i2c.writeto_mem(self.address, _BME680_REG_CONFIG, bytearray([self._filter << 2]))
        self.i2c.writeto_mem(self.address, _BME680_REG_CTRL_MEAS, bytearray([(self._temp_oversample << 5) | (self._pressure_oversample << 2)]))
        self.i2c.writeto_mem(self.address, _BME680_REG_CTRL_HUM, bytearray([self._humidity_oversample]))
        self.i2c.writeto_mem(self.address, _BME680_REG_CTRL_GAS, b'\x10')
        
        # Set to forced mode
        ctrl = self.i2c.readfrom_mem(self.address, _BME680_REG_CTRL_MEAS, 1)[0]
        self.i2c.writeto_mem(self.address, _BME680_REG_CTRL_MEAS, bytearray([(ctrl & 0xFC) | 0x01]))
        
        # Wait for data
        while not (self.i2c.readfrom_mem(self.address, _BME680_REG_MEAS_STATUS, 1)[0] & 0x80):
            time.sleep(0.01)
            
        # Read data registers
        data = self.i2c.readfrom_mem(self.address, _BME680_REG_MEAS_STATUS, 15)
        
        adc_p = _read24(data[2:5]) / 16.0
        adc_t = _read24(data[5:8]) / 16.0
        adc_h = struct.unpack('>H', bytes(data[8:10]))[0]
        adc_g = int(struct.unpack('>H', bytes(data[13:15]))[0] / 64)
        gas_range = data[14] & 0x0F
        
        # Compensate Temperature
        var1 = (adc_t / 8.0) - (self._temp_cal[0] * 2.0)
        var2 = (var1 * self._temp_cal[1]) / 2048.0
        var3 = ((var1 / 2.0) * (var1 / 2.0)) / 4096.0
        var3 = (var3 * self._temp_cal[2] * 16.0) / 16384.0
        self._t_fine = int(var2 + var3)
        calc_t = ((self._t_fine * 5.0 + 128.0) / 256.0) / 100.0
        
        # Compensate Humidity
        t_scaled = ((self._t_fine * 5.0) + 128.0) / 256.0
        v1_h = (adc_h - (self._hum_cal[0] * 16.0)) - ((t_scaled * self._hum_cal[2]) / 200.0)
        v2_h = (self._hum_cal[1] * (((t_scaled * self._hum_cal[3]) / 100.0) + (((t_scaled * ((t_scaled * self._hum_cal[4]) / 100.0)) / 64.0) / 100.0) + 16384.0)) / 1024.0
        v3_h = v1_h * v2_h
        v4_h = (self._hum_cal[5] * 128.0 + ((t_scaled * self._hum_cal[6]) / 100.0)) / 16.0
        v5_h = ((v3_h / 16384.0) * (v3_h / 16384.0)) / 1024.0
        v6_h = (v4_h * v5_h) / 2.0
        calc_h = (((v3_h + v6_h) / 1024.0) * 1000.0) / 4096.0 / 1000.0
        
        # Compensate Gas
        vg1 = ((1340.0 + (5.0 * self._sw_err)) * (_LOOKUP_TABLE_1[gas_range])) / 65536.0
        vg2 = ((adc_g * 32768.0) - 16777216.0) + vg1
        vg3 = (_LOOKUP_TABLE_2[gas_range] * vg1) / 512.0
        calc_gas = int((vg3 + (vg2 / 2.0)) / vg2)
        
        # Compensate Pressure
        var1_p = (self._t_fine / 2.0) - 64000.0
        var2_p = ((var1_p / 4.0) * (var1_p / 4.0)) / 2048.0
        var2_p = (var2_p * self._pres_cal[5]) / 4.0
        var2_p = var2_p + (var1_p * self._pres_cal[4] * 2.0)
        var2_p = (var2_p / 4.0) + (self._pres_cal[3] * 65536.0)
        var1_p = (((((var1_p / 4.0) * (var1_p / 4.0)) / 8192.0) * (self._pres_cal[2] * 32.0) / 8.0) + ((self._pres_cal[1] * var1_p) / 2.0))
        var1_p = var1_p / 262144.0
        var1_p = ((32768.0 + var1_p) * self._pres_cal[0]) / 32768.0
        calc_p = 1048576.0 - adc_p
        calc_p = (calc_p - (var2_p / 4096.0)) * 3125.0
        calc_p = (calc_p / var1_p) * 2.0
        var1_p = (self._pres_cal[8] * (((calc_p / 8.0) * (calc_p / 8.0)) / 8192.0)) / 4096.0
        var2_p = ((calc_p / 4.0) * self._pres_cal[7]) / 8192.0
        var3_p = (((calc_p / 256.0) ** 3.0) * self._pres_cal[9]) / 131072.0
        calc_p += ((var1_p + var2_p + var3_p + (self._pres_cal[6] * 128.0)) / 16.0)
        calc_p /= 100.0  # hPa
        
        return {
            "temperature": calc_t,
            "humidity": calc_h,
            "pressure": calc_p,
            "gas_res": calc_gas
        }

    def init(self):
        pass # Compatibility with test script
