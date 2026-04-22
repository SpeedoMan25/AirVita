# AirVita Backend Service

The AirVita backend is a high-performance REST API built with FastAPI. It handles hardware telemetry ingestion, machine learning-based environmental scoring, computer vision room context analysis, and Generative AI insights.

## System Architecture

> [!NOTE]
> The backend operates via an asynchronous event loop to concurrently manage REST API requests, background data generation, and serial port hardware listening.

### Core Modules

- **FastAPI Application (`app/main.py`)**: The central entry point managing API routes, CORS policies, device registration, and global state management.
- **Serial Interface (`app/serial_reader.py`)**: An asynchronous background task utilizing PySerial to read JSON payloads directly from connected USB hardware. It also features a mock data generator for software-only development.
- **Scoring Engine (`app/scoring.py`)**: Computes the composite environmental health scores, including specialized sub-scores (Sleep, Work, Fun), based on raw sensor telemetry ranges.
- **Machine Learning Integrations**:
  - **MLP Regressor (`model/`)**: A Multi-Layer Perceptron trained on synthetic environmental data to predict base indoor air quality (IAQ) scores.
  - **Room Vision Classifier (`app/cv.py`)**: A computer vision module utilizing the Places365 dataset to analyze captured images, deduce the room type (e.g., bedroom, office), and identify environmental objects.
  - **Generative AI (`app/gemini.py`)**: Integrates with Google Gemini to provide actionable, human-readable insights based on both the sensor telemetry and the visual room context.

## Setup and Configuration

### Prerequisites
- Python 3.11 or newer

### Installation

Initialize your virtual environment and install the required dependencies:

```bash
cd backend
pip install -r requirements.txt
```

### Environment Variables

The backend relies on several environment variables to configure hardware interfaces and network broadcasting:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `MOCK_SERIAL` | `false` | Set to `true` to disable hardware polling and generate simulated sensor telemetry automatically. |
| `SERIAL_PORT` | `COM3` | The hardware serial port connected to the edge device (e.g., `COM3` for Windows, `/dev/ttyACM0` for Linux). |
| `SERIAL_BAUD` | `115200` | The baud rate for the serial connection. Must match the edge device configuration. |
| `HOST_IP` | (Auto-detected) | Overrides the local IP address broadcasted for mobile device pairing. |
| `TUNNEL_URL` | (None) | A secure tunnel URL (e.g., ngrok) to broadcast for external mobile access. |

### Execution Environments

> [!IMPORTANT]
> Always verify your serial port assignment before launching in physical hardware mode to prevent connection timeouts.

**1. Mock Development Mode**
If no physical hardware is connected, use mock mode:
```bash
MOCK_SERIAL=true uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**2. Physical Hardware Mode**
To read real data from a connected microcontroller:
```bash
# Example for Windows:
SERIAL_PORT=COM3 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Machine Learning Pipeline

The backend includes a dedicated model training and calibration pipeline to ensure the neural network aligns with established air quality standards.

### Training the MLP Model
The `train_model.py` script trains the Multi-Layer Perceptron using a combination of empirical CSV datasets and synthetically generated data.

```bash
python train_model.py
```
*Execution outputs the trained model (`mlp_model.pkl`) and scaler (`scaler.pkl`) to the `model/` directory.*

### Calibration Testing
The `calibrate.py` script validates the trained MLP model against predefined edge-case scenarios (`app/scenarios.json`) to ensure algorithmic deviations remain within a strict acceptable tolerance (typically < 2%) compared to manual scoring formulas.

```bash
python calibrate.py
```

## API Endpoint Reference

The backend exposes the following critical REST endpoints:

- `GET /api/current-status`: Retrieves real-time sensor data, calculated scores, and active pairing status for a given monitor.
- `GET /api/monitors`: Returns a summary list of all registered monitor instances.
- `POST /api/scan-room`: Accepts an image payload to classify the room environment using computer vision.
- `GET /api/analyze`: Triggers the LLM engine to generate contextual recommendations based on the current room status.
- `POST /api/sensor-data`: Allows external devices to push JSON telemetry over HTTP, facilitating Wi-Fi enabled microcontrollers.
- `POST /api/pairing/status`: Updates the pairing state for mobile device handshakes.
- `GET /api/scenarios`: Returns available simulation presets for UI demonstrations.


---

## 🔗 Related Documentation

- **[Project Overview](file:///c:/Projects/HackAugie/README.md)**: Main architecture and quick start.
- **[API Reference](file:///c:/Projects/HackAugie/API.md)**: Data schema for the telemetry endpoint.
- **[Deployment Guide](file:///c:/Projects/HackAugie/DEPLOYMENT.md)**: Docker and startup scripts.
