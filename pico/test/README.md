# Raspberry Pi Pico Hardware Testing Guide

This directory contains standalone and integrated tester scripts for the hardware modules connected to your Raspberry Pi Pico.

> [!IMPORTANT]
> **Main Testing File:** The [Integrated Smart Home System](file:///c:/Projects/HackAugie/pico/test/integrated_system/smart_light.py) is the primary script used to verify all hardware components simultaneously.

---

## Hardware Architecture

### Connection Summary

All components share a common ground (GND). Logic levels are 3.3V unless otherwise specified.

| Component | Component Pin | Pico Function | Pico Physical Pin | Wiring Notes |
| :--- | :--- | :--- | :--- | :--- |
| **All** | VCC / 5V | **VBUS** | **Pin 40** | Powers LCD, NeoPixels, and PIR |
| **All** | GND | **GND** | **Pin 38** | Common ground for all parts |
| **I2C LCD 1602** | SDA | **GP0** | **Pin 1** | Shared I2C0 data bus |
| **I2C LCD 1602** | SCL | **GP1** | **Pin 2** | Shared I2C0 clock bus |
| **WS2812 NeoPixel**| DIN | **GP2** | **Pin 4** | 5V signal recommended |
| **IR Sensor** | OUT | **GP16**| **Pin 21** | Logic 0 = Obstacle |
| **PIR Sensor** | OUT | **GP17**| **Pin 22** | Logic 1 = Motion |
| **DHT11 Sensor** | SIG | **GP3** | **Pin 5** | Seeed Studio Grove v1.2 |
| **Thermistor** | OUT / ADC | **GP26**| **Pin 31** | **Requires 10k Divider** to GND |
| **Photoresistor** | OUT / ADC | **GP28**| **Pin 34** | **Requires 10k Divider** to GND |
| **Sensors** | VCC (3.3V) | **3.3V(OUT)**| **Pin 36** | Powers LDR, Therm, and IR |

### Detailed Circuit Notes

*   **Voltage Dividers (Analog Sensors):**
    *   **Thermistor:** Connect one side of the thermistor to **3.3V (Pin 36)**. Connect the other side to **GP26 (Pin 31)**. Also connect a **10kΩ resistor** from **GP26** to **GND**.
    *   **Photoresistor (LDR):** Connect one side of the LDR to **3.3V (Pin 36)**. Connect the other side to **GP28 (Pin 34)**. Also connect a **10kΩ resistor** from **GP28** to **GND**.
*   **Power Management:**
    *   The **LCD** and **NeoPixel strip** are powered via **VBUS (5V)** for optimal brightness and performance.
    *   Ensure the **IR** and **PIR** sensors are stable before reading (PIR requires ~30s calibration time).
*   **I2C Contrast:** If the LCD screen is blank despite power, adjust the small blue potentiometer on the I2C backpack until text appears.

## Running the Tests

Ensure you have `mpremote` installed (`pip install mpremote`) and your Pico is connected.

### 0. The Master System (Main Test)
This combines the LDR, Thermistor, LCD, and NeoPixel strip into a single interactive system.
```bash
# 1. Upload the LCD Library
python -m mpremote connect COM4 cp pico/test/lcd/pico_i2c_lcd.py :pico_i2c_lcd.py

# 2. Run the Master System
python -m mpremote connect COM4 run pico/test/integrated_system/smart_light.py
```

### 1. Modular Tests
Use these to isolate issues with specific components.

| Module | Command |
| :--- | :--- |
| **Blink** | `python -m mpremote connect COM4 run pico/test/blink/blink.py` |
| **NeoPixel** | `python -m mpremote connect COM4 run pico/test/neopixel/neopixel_test.py` |
| **I2C Scanner** | `python -m mpremote connect COM4 run pico/test/lcd/i2c_scanner.py` |
| **IR Sensor** | `python -m mpremote connect COM4 run pico/test/ir_sensor/ir_test.py` |
| **Motion (PIR)** | `python -m mpremote connect COM4 run pico/test/motion_sensor/pir_test.py` |
| **Light (LDR)** | `python -m mpremote connect COM4 run pico/test/light_sensor/ldr_test.py` |
| **Temp (Therm)**| `python -m mpremote connect COM4 run pico/test/temp_sensor/thermistor_test.py` |

---

## Project Structure

- **`pico/main.py`**: The "Edge Code" designed to run automatically on boot. It formats sensor data into JSON strings for consumption by the backend system.
- **`pico/test/`**: Individual test scripts (this directory) used for hardware validation and debugging.
- **`pico/lib/`**: Reusable drivers (BME688, BH1750, etc.) used by the main edge code.

---

## Stopping a Script
If a script is looping and **Ctrl+C** fails, use the soft-reset command:
```bash
python -m mpremote connect COM4 soft-reset
```

## Troubleshooting
- **LCD blank?** Adjust the blue potentiometer on the back of the LCD backpack for contrast.
- **NeoPixels not lighting?** Double-check the 5V (VBUS) connection. They often won't trigger on 3.3V.
- **Permission Denied?** Close any other serial monitors (like Thonny) before running `mpremote`.