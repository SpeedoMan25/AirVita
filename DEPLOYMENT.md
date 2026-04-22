# AirVita Deployment Guide

This document outlines the standard operating procedures for deploying the full AirVita stack using Docker Compose.

## Containerized Architecture

The deployment orchestrates two primary containers:
1. **Frontend**: The React/Vite Dashboard.
2. **Backend**: The FastAPI Python Server.

## Executing the Stack

We provide native startup scripts for both Unix-like and Windows environments. These scripts auto-detect your Local Area Network (LAN) IP address, export it as the `HOST_IP` environment variable, and trigger the Docker daemon.

### macOS & Linux
```bash
chmod +x start.sh
./start.sh
```

### Windows (PowerShell)
```powershell
.\start.ps1
```

> [!IMPORTANT]
> The startup scripts automatically attempt to open your default web browser to the secure `https://[HOST_IP]:5173` dashboard after a brief delay to allow container initialization.

## Hardware USB Constraints (Critical)

By default, the backend attempts to read telemetry from a physical Raspberry Pi Pico tethered via USB.

### Linux Hosts (Native Passthrough)
If deploying the Docker stack natively on a Linux host (e.g., a Raspberry Pi acting as a server):
1. Open `docker-compose.yml`.
2. Locate the backend service configuration.
3. Uncomment the `devices:` block to map the serial port:
   ```yaml
   devices:
     - "/dev/ttyACM0:/dev/ttyACM0"
   ```
4. Ensure the user running the docker daemon is part of the `dialout` or `tty` group:
   ```bash
   sudo usermod -a -G dialout $USER
   ```

### Windows / macOS Hosts (Docker Desktop)
Docker Desktop utilizes virtualization layers that **do not natively support USB serial passthrough**.

If developing on Windows/macOS, you must configure the backend to use the built-in mock telemetry generator:
1. Open `docker-compose.yml`.
2. Set the environment variable `MOCK_SERIAL=true`.
3. (Alternatively) Run the Python backend locally outside of Docker while pointing the Dockerized frontend to `localhost:8000`.


---

## 🔗 Related Documentation

- **[Project Overview](file:///c:/Projects/HackAugie/README.md)**: Main architecture and quick start.
- **[API Reference](file:///c:/Projects/HackAugie/API.md)**: Data schema for the telemetry endpoint.
- **[Deployment Guide](file:///c:/Projects/HackAugie/DEPLOYMENT.md)**: Docker and startup scripts.
