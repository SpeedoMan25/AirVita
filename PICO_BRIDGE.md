# Pico Serial-to-HTTP Bridge (`pico_bridge.py`)

This utility script acts as a middleware bridge connecting a physical Raspberry Pi Pico to a containerized or remote AirVita backend.

## Purpose

> [!IMPORTANT]
> Docker Desktop on macOS and Windows does not support native USB device passthrough.

If you are running the AirVita backend inside a Docker container on macOS or Windows, the backend cannot read directly from the `/dev/ttyACM0` or `COM3` USB ports. 

`pico_bridge.py` solves this by running natively on your host machine. It reads the raw JSON telemetry emitted by the Pico over serial and securely forwards it to the Dockerized backend via HTTP POST requests to the `/api/sensor-data` endpoint.

## Execution

Ensure you have the `pyserial` and `requests` libraries installed on your host machine.

```bash
# macOS / Linux / Windows
python pico_bridge.py
```

### Configuration

The bridge script will automatically attempt to locate the Pico on macOS (`/dev/cu.usbmodem*`). For Windows, you may need to explicitly define your COM port.

By default, the script targets the backend at `http://localhost:8000`. If your backend is hosted remotely, you can override this via an environment variable:

```bash
export BACKEND_URL="http://192.168.1.100:8000"
python pico_bridge.py
```

## Features

- **Automatic Reconnection**: If the backend Docker container restarts or the Pico is temporarily unplugged, the script will gracefully retry the connection.
- **Data Formatting**: The bridge automatically maps the Pico's abbreviated JSON keys (e.g., parsing the PM arrays) into the full schema expected by the REST API.
- **Heartbeat Monitoring**: Provides terminal feedback if the Pico stops transmitting data for more than 5 seconds.


---

## 🔗 Related Documentation

- **[Project Overview](file:///c:/Projects/HackAugie/README.md)**: Main architecture and quick start.
- **[API Reference](file:///c:/Projects/HackAugie/API.md)**: Data schema for the telemetry endpoint.
- **[Deployment Guide](file:///c:/Projects/HackAugie/DEPLOYMENT.md)**: Docker and startup scripts.
