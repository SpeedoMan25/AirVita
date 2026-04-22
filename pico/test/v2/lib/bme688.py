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
        time.sleep(0.1) # Datasheet says 2ms, we give 100ms
        
        # Check Chip ID
        chip_id = self.i2c.readfrom_mem(self.address, _BME680_REG_CHIPID, 1)[0]
        if chip_id != _BME680_CHIPID:
            raise RuntimeError(f"BME688 not found! (ID: 0x{chip_id:02x})")
            
        self._read_calibration()
        
        # Standard Settings
        self._pressure_oversample = 0b011 # 4x
        self._temp_oversample = 0b100     # 8x
        self._humidity_oversample = 0b010 # 2x
        self._filter = 0b010              # Coeff 3
        self._t_fine = None

    def _read_Calibration_reg(self, addr, length=1, signed=False):
        data = self.i2c.readfrom_mem(self.address, addr, length)
        if length == 1:
            val = data[0]
            if signed and val > 127: val -= 256
            return val
        elif length == 2:
            # Most calibration values are little-endian
            val = struct.unpack('<h' if signed else '<H', data)[0]
            return val
        return data

    def _read_calibration(self):
        # Temperature
        self._par_t1 = self._read_Calibration_reg(0xE9, 2, False)
        self._par_t2 = self._read_Calibration_reg(0x8A, 2, True)
        self._par_t3 = self._read_Calibration_reg(0x8C, 1, True)
        
        # Pressure
        self._par_p1 = self._read_Calibration_reg(0x8E, 2, False)
        self._par_p2 = self._read_Calibration_reg(0x90, 2, True)
        self._par_p3 = self._read_Calibration_reg(0x92, 1, True)
        self._par_p4 = self._read_Calibration_reg(0x94, 2, True)
        self._par_p5 = self._read_Calibration_reg(0x96, 2, True)
        self._par_p6 = self._read_Calibration_reg(0x99, 1, True)
        self._par_p7 = self._read_Calibration_reg(0x98, 1, True)
        self._par_p8 = self._read_Calibration_reg(0x9C, 2, True)
        self._par_p9 = self._read_Calibration_reg(0x9E, 2, True)
        self._par_p10 = self._read_Calibration_reg(0xA0, 1, True)
        
        # Humidity
        h1_lsb = self._read_Calibration_reg(0xE2, 1)
        h1_msb = self._read_Calibration_reg(0xE3, 1)
        self._par_h1 = (h1_msb << 4) | (h1_lsb & 0x0F)
        h2_msb = self._read_Calibration_reg(0xE1, 1)
        self._par_h2 = (h2_msb << 4) | (h1_lsb >> 4)
        self._par_h3 = self._read_Calibration_reg(0xE4, 1, True)
        self._par_h4 = self._read_Calibration_reg(0xE5, 1, True)
        self._par_h5 = self._read_Calibration_reg(0xE6, 1, True)
        self._par_h6 = self._read_Calibration_reg(0xE7, 1, False)
        self._par_h7 = self._read_Calibration_reg(0xE8, 1, True)
        
        # Gas / Heater
        self._par_g1 = self._read_Calibration_reg(0xED, 1, True)
        self._par_g2 = self._read_Calibration_reg(0xEB, 2, True)
        self._par_g3 = self._read_Calibration_reg(0xEE, 1, True)
        self._res_heat_range = (self._read_Calibration_reg(0x02, 1) & 0x30) >> 4
        self._res_heat_val = self._read_Calibration_reg(0x00, 1, True)

    def _calc_heater_res(self, target_temp, amb_temp):
        # BST-BME688-DS000-03 Integer Formula (3.6.5)
        var1 = (amb_temp * self._par_g3 / 10.0) * 256.0
        var2 = (self._par_g1 + 784.0) * (((((self._par_g2 + 154009.0) * target_temp * 5.0) / 100.0) + 3276800.0) / 10.0)
        var3 = var1 + (var2 / 2.0)
        var4 = (var3 / (self._res_heat_range + 4.0))
        var5 = (131.0 * self._res_heat_val) + 65536.0
        res_heat_x = ((var4 / var5) - 250.0) * 34.0
        return max(0, min(255, int((res_heat_x + 50.0) / 100.0)))

    def read_all(self):
        # 0. Ensure Heater is enabled
        self.i2c.writeto_mem(self.address, 0x70, b'\x00')
        time.sleep(0.01)
        
        # 1. Prepare Heater Step 0
        amb_temp = 25.0
        if self._t_fine:
            amb_temp = (self._t_fine * 5 + 128) >> 8
            amb_temp /= 100.0
            
        heater_code = self._calc_heater_res(320, amb_temp)
        
        self.i2c.writeto_mem(self.address, _BME680_BME680_RES_HEAT_0, bytearray([heater_code]))
        time.sleep(0.01)
        self.i2c.writeto_mem(self.address, _BME680_BME680_GAS_WAIT_0, b'\x59') # 100ms
        time.sleep(0.01)
        
        # 2. Configure Oversampling & Filter
        self.i2c.writeto_mem(self.address, _BME680_REG_CONFIG, bytearray([self._filter << 2]))
        time.sleep(0.01)
        self.i2c.writeto_mem(self.address, _BME680_REG_CTRL_HUM, bytearray([self._humidity_oversample]))
        time.sleep(0.01)
        ctrl_meas = (self._temp_oversample << 5) | (self._pressure_oversample << 2)
        self.i2c.writeto_mem(self.address, _BME680_REG_CTRL_MEAS, bytearray([ctrl_meas]))
        time.sleep(0.01)
        
        # run_gas=1 (bit 5), nb_conv=0 (bits 3:0) for step 0
        self.i2c.writeto_mem(self.address, _BME680_REG_CTRL_GAS, b'\x20')
        time.sleep(0.01)
        
        # 3. Trigger Forced Mode
        self.i2c.writeto_mem(self.address, _BME680_REG_CTRL_MEAS, bytearray([ctrl_meas | 0x01]))
        
        # 4. Wait for data
        start_wait = time.ticks_ms()
        while True:
            status = self.i2c.readfrom_mem(self.address, _BME680_REG_MEAS_STATUS, 1)[0]
            if status & 0x80: break
            if time.ticks_diff(time.ticks_ms(), start_wait) > 1000:
                return None
            time.sleep(0.01)
            
        # 5. Read Data Fields (0x1D to 0x2D -> 17 bytes)
        data = self.i2c.readfrom_mem(self.address, _BME680_REG_MEAS_STATUS, 17)
        
        adc_p = (data[2] << 12) | (data[3] << 4) | (data[4] >> 4)
        adc_t = (data[5] << 12) | (data[6] << 4) | (data[7] >> 4)
        adc_h = (data[8] << 8) | data[9]
        adc_g = (data[15] << 2) | (data[16] >> 6)
        gas_range = data[16] & 0x0F
        gas_stable = bool(data[16] & 0x10)
        gas_valid = bool(data[16] & 0x20)
        
        # 6. Compensate
        # Temperature
        v1 = (adc_t / 16384.0 - self._par_t1 / 1024.0) * self._par_t2
        v2 = ((adc_t / 131072.0 - self._par_t1 / 8192.0) ** 2) * (self._par_t3 * 16.0)
        self._t_fine = int(v1 + v2)
        calc_t = self._t_fine / 5120.0
        
        # Pressure
        v1_p = (self._t_fine / 2.0) - 64000.0
        v2_p = v1_p * v1_p * (self._par_p6 / 131072.0)
        v2_p = v2_p + (v1_p * self._par_p5 * 2.0)
        v2_p = (v2_p / 4.0) + (self._par_p4 * 65536.0)
        v1_p = (((self._par_p3 * v1_p * v1_p) / 16384.0) + (self._par_p2 * v1_p)) / 524288.0
        v1_p = (1.0 + (v1_p / 32768.0)) * self._par_p1
        calc_p = 1048576.0 - adc_p
        calc_p = ((calc_p - (v2_p / 4096.0)) * 6250.0) / v1_p
        v1_p = (self._par_p9 * calc_p * calc_p) / 2147483648.0
        v2_p = calc_p * (self._par_p8 / 32768.0)
        v3_p = ((calc_p / 256.0) ** 3) * (self._par_p10 / 131072.0)
        calc_p = calc_p + (v1_p + v2_p + v3_p + (self._par_p7 * 128.0)) / 16.0
        calc_p /= 100.0
        
        # Humidity
        v1_h = adc_h - (self._par_h1 * 16.0 + (self._par_h3 / 2.0) * calc_t)
        v2_h = v1_h * ((self._par_h2 / 262144.0) * (1.0 + (self._par_h4 / 16384.0) * calc_t + (self._par_h5 / 1048576.0) * (calc_t**2)))
        v3_h = self._par_h6 / 16384.0
        v4_h = self._par_h7 / 2097152.0
        calc_h = v2_h + (v3_h + v4_h * calc_t) * (v2_h ** 2)
        
        # Gas
        var1_g = 262144.0 / (2.0 ** gas_range)
        var2_g = adc_g - 512.0
        var2_g *= 3.0
        var2_g = 4096.0 + var2_g
        calc_gas = (1000000.0 * var1_g) / var2_g
        
        return {
            "temperature": calc_t,
            "humidity": calc_h,
            "pressure": calc_p,
            "gas_res": calc_gas,
            "gas_stable": gas_stable,
            "gas_valid": gas_valid
        }


        
        # 6. Compensate
        # Temperature
        v1 = (adc_t / 16384.0 - self._par_t1 / 1024.0) * self._par_t2
        v2 = ((adc_t / 131072.0 - self._par_t1 / 8192.0) ** 2) * (self._par_t3 * 16.0)
        self._t_fine = int(v1 + v2)
        calc_t = self._t_fine / 5120.0
        
        # Pressure
        v1_p = (self._t_fine / 2.0) - 64000.0
        v2_p = v1_p * v1_p * (self._par_p6 / 131072.0)
        v2_p = v2_p + (v1_p * self._par_p5 * 2.0)
        v2_p = (v2_p / 4.0) + (self._par_p4 * 65536.0)
        v1_p = (((self._par_p3 * v1_p * v1_p) / 16384.0) + (self._par_p2 * v1_p)) / 524288.0
        v1_p = (1.0 + (v1_p / 32768.0)) * self._par_p1
        calc_p = 1048576.0 - adc_p
        calc_p = ((calc_p - (v2_p / 4096.0)) * 6250.0) / v1_p
        v1_p = (self._par_p9 * calc_p * calc_p) / 2147483648.0
        v2_p = calc_p * (self._par_p8 / 32768.0)
        v3_p = ((calc_p / 256.0) ** 3) * (self._par_p10 / 131072.0)
        calc_p = calc_p + (v1_p + v2_p + v3_p + (self._par_p7 * 128.0)) / 16.0
        calc_p /= 100.0
        
        # Humidity
        v1_h = adc_h - (self._par_h1 * 16.0 + (self._par_h3 / 2.0) * calc_t)
        v2_h = v1_h * ((self._par_h2 / 262144.0) * (1.0 + (self._par_h4 / 16384.0) * calc_t + (self._par_h5 / 1048576.0) * (calc_t**2)))
        v3_h = self._par_h6 / 16384.0
        v4_h = self._par_h7 / 2097152.0
        calc_h = v2_h + (v3_h + v4_h * calc_t) * (v2_h ** 2)
        
        # Gas
        var1_g = 262144.0 / (2.0 ** gas_range) # More robust range calculation
        var2_g = adc_g - 512.0
        var2_g *= 3.0
        var2_g = 4096.0 + var2_g
        calc_gas = (1000000.0 * var1_g) / var2_g
        
        return {
            "temperature": calc_t,
            "humidity": calc_h,
            "pressure": calc_p,
            "gas_res": calc_gas,
            "gas_stable": gas_stable,
            "gas_valid": gas_valid
        }


    def init(self):
        pass

