# Raspberry Pi 4B Wireless Node

This directory contains the edge firmware designed to run on a full Linux environment (specifically a Raspberry Pi 4B). Unlike the Pico (which relies on a USB serial tether to the backend), this node acts as an autonomous IoT device that transmits telemetry securely over the local network via HTTP POST requests.

## Architecture

> [!NOTE]
> The Pi 4B node utilizes standard Python 3 (not MicroPython) and interfaces with hardware using standard Linux GPIO libraries (e.g., `RPi.GPIO`, `smbus2`, `pyaudio`).

### Sensor Support
- **DHT11**: Temperature and Humidity via digital GPIO.
- **BH1750**: Ambient Light via the I2C bus.
- **Microphone**: Acoustic noise levels captured via ALSA (Advanced Linux Sound Architecture).

## Setup & Configuration

### Environment Variables
The application utilizes environment variables to target the centralized AirVita Backend:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `BACKEND_URL` | `http://localhost:8000` | The network endpoint of the AirVita FastAPI server. |
| `DEVICE_ID` | (Auto-generated MAC) | The unique identifier for this specific IoT node. |

### Execution
Run the main loop to begin scanning and transmitting data. The application features a built-in terminal UI rendering a live dashboard (including a dynamic VU meter for the audio feed).

```bash
python main.py
```

### Diagnostic Tools
Execute `diagnose_pi.py` to run an isolated hardware check. This validates I2C bus enumeration and ALSA audio device capture without attempting to establish network connectivity.


---

## 🔗 Related Documentation

- **[Project Overview](file:///c:/Projects/HackAugie/README.md)**: Main architecture and quick start.
- **[API Reference](file:///c:/Projects/HackAugie/API.md)**: Data schema for the telemetry endpoint.
- **[Deployment Guide](file:///c:/Projects/HackAugie/DEPLOYMENT.md)**: Docker and startup scripts.
