# Raspberry Pi Pico Edge Firmware

This directory contains the production MicroPython firmware engineered for the Raspberry Pi Pico. This code runs autonomously on boot, aggregates environmental telemetry from a suite of hardware sensors, and streams serialized JSON payloads over the USB serial interface.

## Hardware Support (V2 Integrated System)

The `main.py` firmware expects the following components to be wired to the designated GPIO pins:

| Component | Protocol | Pin Mapping |
| :--- | :--- | :--- |
| **BME688 (Environment)** | I2C (Address 0x76) | SDA: GP0, SCL: GP1 |
| **BH1750 (Ambient Light)** | I2C (Address 0x23) | SDA: GP0, SCL: GP1 |
| **LCD 1602 Display** | I2C (Address 0x27) | SDA: GP0, SCL: GP1 |
| **PMS5003 (Particulates)** | UART 1 (9600 Baud) | TX: GP4, RX: GP5 |
| **INMP441 (I2S Mic)** | I2S 0 | SCK: 16, WS: 17, SD: 18 |
| **NeoPixel Strip (8x)** | One-Wire | DIN: GP2 |

## Installation & Deployment

> [!IMPORTANT]
> The Pico must be flashed with the official **MicroPython** firmware before proceeding.

1. **Install Dependencies:** You must copy the hardware drivers into the `/lib` directory on the Pico's internal storage.
   Ensure the following files are present on the Pico:
   - `/lib/bme688.py`
   - `/lib/bh1750.py`
   - `/lib/lcd1602.py`
2. **Deploy Main Loop:** Copy `main.py` from this directory to the root directory of the Pico. If named exactly `main.py`, MicroPython will execute it automatically whenever power is applied.

## Serialized Telemetry Schema

The firmware continuously polls the sensors and transmits a JSON string over the standard USB serial output.

**Sample Payload:**
```json
{
  "temperature": 22.5,
  "humidity": 45.0,
  "pressure": 1013.2,
  "light": 420.0,
  "sound_amp": 35.2,
  "pm1_0": 5,
  "pm2_5": 8,
  "pm10": 12,
  "particulates": 8,
  "vocs": 2.5,
  "timestamp_ms": 1698765432100
}
```

> [!NOTE]
> The audio metric (`sound_amp`) is calculated internally using Root Mean Square (RMS) on the high-frequency I2S buffer, converting the raw digital waveform into an estimated Decibel (dB) relative value.


---

## 🔗 Related Documentation

- **[Project Overview](file:///c:/Projects/HackAugie/README.md)**: Main architecture and quick start.
- **[API Reference](file:///c:/Projects/HackAugie/API.md)**: Data schema for the telemetry endpoint.
- **[Deployment Guide](file:///c:/Projects/HackAugie/DEPLOYMENT.md)**: Docker and startup scripts.
