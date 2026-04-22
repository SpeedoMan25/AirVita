# Pico Hardware Validation Suite (Iteration V2)

This documentation details the second iteration of the testing suite. This revision has been engineered for a standardized Pico breakout board utilizing shared power distribution rails and an expanded array of high-precision environmental sensors.

## Hardware Architecture Specifications

| Hardware Peripheral | Communication Protocol | Logic Pin Mapping | Physical Pin Allocation | Required Operating Voltage |
| :--- | :--- | :--- | :--- | :--- |
| **I2C LCD Display** | I2C (Address: 0x27) | SDA: GP0, SCL: GP1 | Pins 1, 2 | 5.0V |
| **NeoPixel Array (x16)** | Proprietary One-Wire | DIN: GP2 | Pin 4 | 5.0V |
| **GY-302 (Ambient Light)**| I2C (Address: 0x23) | SDA: GP0, SCL: GP1 | Pins 1, 2 | 3.3V |
| **BME688 (Environment)** | I2C (Address: 0x76/0x77)| SDA: GP0, SCL: GP1 | Pins 1, 2 | 3.3V |
| **PMS5003 (Particulates)**| UART1 | TX: GP4, RX: GP5 | Pins 6, 7 | 5.0V |
| **INMP441 (Microphone)** | I2S | SCK: GP16, WS: GP17, SD: GP18 | Pins 21, 22, 24 | 3.3V |
| **Active Buzzer** | Digital Logic | Signal: GP15 | Pin 20 | 3.3V |

---

## Execution Directives

> [!NOTE]
> All execution commands assume the Raspberry Pi Pico is enumerated on the host system as `COM4`. Adjust the port parameter as necessary for your specific environment.

### Phase 1-3: Core User Interface Validation
- **Display Subsystem:** `python -m mpremote connect COM4 run pico/test/v2/lcd_test.py`
- **Lighting Subsystem:** `python -m mpremote connect COM4 run pico/test/v2/neopixel_test.py`
- **UI Integration:** `python -m mpremote connect COM4 run pico/test/v2/integrated_test.py`

### Phase 4-5: Illumination and Automation Logic
- **Photometric Sensor:** `python -m mpremote connect COM4 run pico/test/v2/light_test_v2.py`
- **V2 Master Controller:** `python -m mpremote connect COM4 run pico/test/v2/master_v2.py`

### Phase 6: Digital Audio Acquisition
- **I2S Microphone:** `python -m mpremote connect COM4 run pico/test/v2/mic_test.py`

### Phase 7-8: Atmospheric and Environmental Telemetry
- **Air Quality Particulates:** `python -m mpremote connect COM4 run pico/test/v2/air_test_v2.py`
- **Comprehensive Environment:** `python -m mpremote connect COM4 run pico/test/v2/bme_test.py`
  *(Captures temperature, relative humidity, barometric pressure, and VOC gas resistance. Operates via a custom driver implementing non-volatile memory calibration compensation logic).*

### Phase 9: Alert Systems and Operational Simulations
- **Audible Alerts:** `python -m mpremote connect COM4 run pico/test/v2/buzzer_test.py`
- **System Simulation:** `python -m mpremote connect COM4 run pico/test/v2/bomb_sim.py`
  *(Executes a critical alert simulation sequence utilizing synchronized UI, LED array, and auditory responses).*

---

## Diagnostic and Troubleshooting Procedures

> [!WARNING]
> Proper wiring is critical. Deviations from the documented pinouts or voltages may result in component degradation or failure.

- **I2C Bus Enumeration Failures:** The BME688 module strictly requires the `CS` (Chip Select) pin tied to 3.3V and the `SDO` pin tied to GND to guarantee stable operation at I2C address 0x76.
- **PMS5003 UART Data Loss:** Verify that the UART transmission lines are correctly crossed (Pico RX is connected to Sensor TX, and vice versa).
- **Audio Signal Integrity:** The I2S protocol is highly susceptible to capacitance and loose connections. Ensure breadboard wiring is completely secure and wires are kept as short as feasible to prevent data corruption.
