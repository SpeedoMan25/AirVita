# AirVita Computer Vision Scanner

The `scanner` module is a standalone Flask application that utilizes deep learning computer vision models to deduce the environmental context of a room (e.g., Bedroom, Classroom, Cafe). This visual context is passed to the backend's Generative AI engine to contextualize the sensor telemetry.

## System Architecture

> [!NOTE]
> The scanner runs completely independently of the primary backend on port `5001`. It relies on PyTorch and the `torchvision` models library.

### Core Technologies
- **Model**: ResNet18 trained on the MIT CSAIL Places365 dataset.
- **Backend**: Flask application running locally with `ssl_context='adhoc'` to ensure the browser permits webcam access.
- **Temporal Hysteresis**: The application maintains a sliding window queue of the last 25 inferences. It requires a 60% agreement threshold to change the active room label, preventing UI flickering caused by motion blur or sudden lighting changes.

## Setup & Execution

### Prerequisites
Ensure you have installed the required PyTorch and Flask dependencies:

```bash
cd scanner
pip install -r requirements.txt
```

### Running the Scanner

Start the Flask server. On the first launch, it will automatically download the ~45MB `resnet18_places365.pth.tar` weights from the MIT CSAIL repository.

```bash
python app.py
```

### Accessing the Web Interface
Navigate to `https://localhost:5001` in your browser.

> [!WARNING]
> Because the server generates ad-hoc SSL certificates, your browser will likely display a security warning. You must bypass this warning (e.g., clicking "Advanced" -> "Proceed") to allow the application to access your webcam.

## Integration

The scanner provides a `/upload` endpoint that accepts base64 encoded images via HTTP POST. Upon analyzing the image, it returns the stabilized room classification and prediction confidence, mapping the raw Places365 categories (e.g., `coffee_shop`, `dorm_room`) into simplified AirVita categories (e.g., `Cafe`, `Dorm Room`).


---

## 🔗 Related Documentation

- **[Project Overview](file:///c:/Projects/HackAugie/README.md)**: Main architecture and quick start.
- **[API Reference](file:///c:/Projects/HackAugie/API.md)**: Data schema for the telemetry endpoint.
- **[Deployment Guide](file:///c:/Projects/HackAugie/DEPLOYMENT.md)**: Docker and startup scripts.
