# 🌡️ AirVita — IoT Room Environment Monitor

A full-stack IoT room environment monitoring system that reads sensor data from a Raspberry Pi Pico, processes it through a FastAPI backend, and displays a real-time dashboard via a React frontend.

## Architecture

```
┌──────────────┐    USB/Serial    ┌──────────────────┐    HTTP/REST    ┌──────────────────┐
│  Pico (Edge) │ ──────────────► │  FastAPI Backend  │ ◄────────────► │  React Frontend  │
│  MicroPython │   JSON payload  │  Serial Listener  │   /api/...     │  Vite Dashboard  │
│  Sensors     │                 │  Health Scoring   │                │  Live Score UI   │
└──────────────┘                 └──────────────────┘                └──────────────────┘
```

## Directory Structure

```
HackAugie/
├── pico/               # MicroPython code for the Raspberry Pi Pico
│   └── main.py         # Sensor reading & serial output (mock mode included)
├── backend/            # FastAPI server + serial listener
│   ├── app/
│   │   ├── main.py     # FastAPI application entry point
│   │   ├── serial_reader.py   # PySerial USB listener
│   │   ├── scoring.py  # Room Health Score algorithm (1–99)
│   │   └── models.py   # Pydantic data models
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/           # React + Vite dashboard
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── components/
│   │   │   ├── ScoreGauge.jsx
│   │   │   ├── ScoreGauge.css
│   │   │   ├── SensorCard.jsx
│   │   │   └── SensorCard.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)

### 1. Run the Backend

```bash
cd backend
pip install -r requirements.txt

# Without a Pico connected (uses mock data):
MOCK_SERIAL=true uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With a Pico connected:
SERIAL_PORT=COM3 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

### 3. Run with Docker Compose

```bash
docker-compose up --build
```

> **Windows USB Passthrough:** Docker Desktop on Windows does not natively support USB passthrough.
> Use `MOCK_SERIAL=true` in `docker-compose.yml`, or run the backend natively with `SERIAL_PORT=COM3`.
>
> **Linux USB Passthrough:** Uncomment the `devices` section in `docker-compose.yml` to map `/dev/ttyACM0`.

### 4. Flash the Pico

Copy `pico/main.py` to your Raspberry Pi Pico running MicroPython. It will immediately begin streaming JSON sensor data over USB serial.

## Room Health Score

The score ranges from **1** (hazardous) to **99** (ideal) and is computed as a weighted average of individual sensor sub-scores:

| Sensor         | Weight | Ideal Range           |
|----------------|--------|-----------------------|
| Temperature    | 20%    | 20–24 °C              |
| Humidity       | 15%    | 40–60 %RH             |
| Light Level    | 10%    | 300–500 lux           |
| Noise Level    | 15%    | 0–40 dB               |
| Air Pressure   | 10%    | 1000–1025 hPa         |
| Particles      | 15%    | 0–35 µg/m³ (PM2.5)    |
| VOCs           | 15%    | 0–300 ppb             |

## License

MIT