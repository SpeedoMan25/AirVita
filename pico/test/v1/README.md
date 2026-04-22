# Raspberry Pi Pico Hardware Testing Suite (Iteration V1)

This repository section contains isolated and integrated validation scripts designed for the hardware peripherals connected to the Raspberry Pi Pico.

> [!IMPORTANT]
> **System Validation**
> The [Integrated Smart Home System](file:///c:/Projects/HackAugie/pico/test/v1/integrated_system/smart_light.py) serves as the primary integration test. Execute this script to verify the simultaneous operation of all hardware components.

---

## Hardware Architecture and Pin Configuration

### Peripheral Mapping

All components share a common ground reference (GND). Logic levels are strictly 3.3V unless explicitly noted otherwise.

| Component | Component Pin | Pico Function | Pico Physical Pin | Integration Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Common Rail** | VCC / 5V | **VBUS** | **Pin 40** | Supplies 5V to LCD, NeoPixels, and PIR module. |
| **Common Rail** | GND | **GND** | **Pin 38** | System-wide common ground. |
| **I2C LCD 1602** | SDA | **GP0** | **Pin 1** | Shared I2C0 data line. |
| **I2C LCD 1602** | SCL | **GP1** | **Pin 2** | Shared I2C0 clock line. |
| **WS2812 NeoPixel** | DIN | **GP2** | **Pin 4** | 5V logic signal recommended for stability. |
| **IR Sensor** | OUT | **GP16** | **Pin 21** | Active Low (Logic 0 indicates obstacle detection). |
| **PIR Sensor** | OUT | **GP17** | **Pin 22** | Active High (Logic 1 indicates motion detection). |
| **DHT11 Sensor** | SIG | **GP3** | **Pin 5** | Seeed Studio Grove v1.2 interface. |
| **Thermistor** | OUT / ADC | **GP26** | **Pin 31** | **Requires 10kΩ voltage divider** pulled to GND. |
| **Photoresistor** | OUT / ADC | **GP28** | **Pin 34** | **Requires 10kΩ voltage divider** pulled to GND. |
| **Sensor Power** | VCC (3.3V) | **3.3V(OUT)** | **Pin 36** | Supplies 3.3V to LDR, Thermistor, and IR module. |

### Circuit Implementation Details

*   **Analog Sensor Voltage Dividers:**
    *   **Thermistor:** Interface the thermistor between **3.3V (Pin 36)** and the ADC input **GP26 (Pin 31)**. Install a **10kΩ pull-down resistor** from **GP26** to **GND**.
    *   **Photoresistor (LDR):** Interface the LDR between **3.3V (Pin 36)** and the ADC input **GP28 (Pin 34)**. Install a **10kΩ pull-down resistor** from **GP28** to **GND**.
*   **Power Distribution:**
    *   The **LCD module** and **NeoPixel array** must be powered via the **VBUS (5V)** pin to ensure adequate luminance and prevent undervoltage resets.
    *   The **PIR sensor** requires an initial calibration period of approximately 30 seconds upon power-up before yielding stable readings.
*   **I2C LCD Contrast Calibration:** If the display remains unreadable upon initialization, adjust the onboard potentiometer located on the I2C backpack interface.

## Execution Procedures

Ensure the `mpremote` utility is installed in your Python environment (`pip install mpremote`) and that the Raspberry Pi Pico is successfully enumerated on the host system.

### 0. Master System Integration Test
This protocol executes a comprehensive test combining the LDR, Thermistor, LCD, and NeoPixel peripherals into a unified event loop.

```bash
# Step 1: Provision the LCD Library Firmware
python -m mpremote connect COM4 cp pico/test/v1/lcd/pico_i2c_lcd.py :pico_i2c_lcd.py

# Step 2: Execute the Integration Module
python -m mpremote connect COM4 run pico/test/v1/integrated_system/smart_light.py
```

### 1. Isolated Modular Testing
Utilize the following commands to isolate and debug individual hardware subsystems.

| Hardware Subsystem | Execution Command |
| :--- | :--- |
| **Blink Diagnostic** | `python -m mpremote connect COM4 run pico/test/v1/blink/blink.py` |
| **NeoPixel Array** | `python -m mpremote connect COM4 run pico/test/v1/neopixel/neopixel_test.py` |
| **I2C Bus Scanner** | `python -m mpremote connect COM4 run pico/test/v1/lcd/i2c_scanner.py` |
| **IR Proximity** | `python -m mpremote connect COM4 run pico/test/v1/ir_sensor/ir_test.py` |
| **Motion (PIR)** | `python -m mpremote connect COM4 run pico/test/v1/motion_sensor/pir_test.py` |
| **Light Level (LDR)** | `python -m mpremote connect COM4 run pico/test/v1/light_sensor/ldr_test.py` |
| **Temperature** | `python -m mpremote connect COM4 run pico/test/v1/temp_sensor/thermistor_test.py` |

---

## Firmware Repository Structure

- **`pico/main.py`**: The production edge firmware designed for autonomous execution on boot. It aggregates sensor telemetry and serializes it into JSON format for host consumption.
- **`pico/test/v1/`**: The directory containing all V1 hardware validation and diagnostic scripts.
- **`pico/lib/`**: The repository for shared hardware drivers (e.g., BME688, BH1750) utilized by the production firmware.

---

## Interrupt Handling and Recovery
In the event that an infinite loop prevents standard **Ctrl+C** interruption, issue a software reset via `mpremote`:
```bash
python -m mpremote connect COM4 soft-reset
```

## System Troubleshooting
- **Unresponsive LCD:** Adjust the contrast potentiometer on the I2C backpack. Verify 5V power supply.
- **NeoPixel Failure:** Confirm the VBUS (5V) connection. 3.3V logic levels may fail to trigger the NeoPixel data line reliably depending on the specific diode batch.
- **Serial Port Access Denied:** Ensure all external serial monitors (such as Thonny IDE or Putty) are terminated prior to executing `mpremote` commands.