# AirVita Machine Learning Engine

This directory contains the core machine learning assets, training scripts, and scalers used by the backend to derive human-readable Indoor Air Quality (IAQ) and Health scores from raw telemetry.

## Methodology

The environmental scoring system employs a **hybrid architecture**, utilizing both a trained neural network for complex non-linear sensor relationships and deterministic algorithmic penalties for hazardous elements.

### 1. Multi-Layer Perceptron (MLP Regressor)
The base environmental score is predicted by an MLP Regressor utilizing the `scikit-learn` framework. The model evaluates a 5-dimensional feature matrix:
- Temperature
- Relative Humidity
- Ambient Light
- Barometric Pressure
- Acoustic Noise (dB)

**Network Architecture:**
- **Hidden Layers:** (100, 50) using the ReLU activation function.
- **Optimization:** Trained using empirical datasets combined with a synthetic calibration set.

### 2. Synthetic Calibration
Because true "ideal" environments are highly subjective, `train_model.py` generates 30,000 synthetic data samples. These samples are algorithmically labeled according to strict architectural standards (e.g., classifying 22°C and 45% Humidity as peak 99 score). Training the MLP against these synthetic constraints forces the neural network to align tightly with our designed thresholds while gracefully handling edge-case interpolations.

### 3. Deterministic IAQ Penalties
Particulate Matter (PM2.5) and Volatile Organic Compounds (VOCs) represent immediate, linear health hazards. Rather than passing these through the MLP, the backend applies them as strict post-prediction penalties:
- **Particulates (PM2.5):** Coefficient `-0.05` applied directly against the base score.
- **VOCs:** Coefficient `-0.02` applied directly against the base score.

## Generating the Model

To retrain the model and overwrite the `.pkl` binary files:

```bash
# Ensure you are running this from the backend directory
python train_model.py
```

> [!WARNING]
> Do not manually modify the `.pkl` files. Ensure you always invoke `train_model.py` to regenerate the `scaler.pkl` simultaneously; mismatched scalers and models will produce drastically skewed predictions.


---

## 🔗 Related Documentation

- **[Project Overview](file:///c:/Projects/HackAugie/README.md)**: Main architecture and quick start.
- **[API Reference](file:///c:/Projects/HackAugie/API.md)**: Data schema for the telemetry endpoint.
- **[Deployment Guide](file:///c:/Projects/HackAugie/DEPLOYMENT.md)**: Docker and startup scripts.
