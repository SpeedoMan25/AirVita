# API Data Schema Reference

The AirVita backend exposes a RESTful API designed to accept telemetry from any compatible edge device (e.g., Raspberry Pi 4B, ESP32) using standard HTTP POST requests. 

This decoupling ensures you are not restricted strictly to the USB-tethered Raspberry Pi Pico.

## Endpoint: Ingest Sensor Telemetry

### `POST /api/sensor-data`

Transmits real-time environmental telemetry to the processing pipeline. The backend will automatically register new `device_id`s upon receiving their first payload.

**Headers:**
- `Content-Type: application/json`

**Payload Schema:**

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `device_id` | `string` | **Yes** | A unique identifier for the transmitting edge device (e.g., MAC Address). |
| `temperature` | `float` | No | Ambient temperature in Celsius. Default: `0.0`. |
| `humidity` | `float` | No | Relative humidity percentage (0-100). Default: `0.0`. |
| `pressure` | `float` | No | Barometric pressure in hPa. Default: `0.0`. |
| `light` | `float` | No | Ambient illumination in Lux. Default: `0.0`. |
| `sound_amp` | `float` | No | Calculated acoustic noise level in Decibels (dB). Default: `0.0`. |
| `particulates` | `float` | No | PM2.5 density in µg/m³. Default: `0.0`. |
| `voc_ppb` | `float` | No | Volatile Organic Compounds in parts-per-billion. Default: `0.0`. |

**Example Request:**
```json
{
  "device_id": "pi4b-living-room",
  "temperature": 21.5,
  "humidity": 42.0,
  "pressure": 1011.0,
  "light": 350.5,
  "sound_amp": 40.0,
  "particulates": 5.0
}
```

**Example Response:**
```json
{
  "status": "success",
  "final_iaq_score": 92
}
```

> [!NOTE]
> The backend uses advanced validation models. If optional fields are omitted, the system assumes `0.0` or utilizes the last known state depending on internal buffering logic.


---

## 🔗 Related Documentation

- **[Project Overview](file:///c:/Projects/HackAugie/README.md)**: Main architecture and quick start.
- **[API Reference](file:///c:/Projects/HackAugie/API.md)**: Data schema for the telemetry endpoint.
- **[Deployment Guide](file:///c:/Projects/HackAugie/DEPLOYMENT.md)**: Docker and startup scripts.
