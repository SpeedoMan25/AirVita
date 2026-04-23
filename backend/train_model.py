import pandas as pd
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
from pathlib import Path
from app.scoring import calculate_room_health_score, SENSOR_CONFIG
import random

# Configuration
DATASET_PATH = Path(__file__).parent.parent / "data" / "rpi_23_reg_with_IAQ.csv"
MODEL_DIR = Path(__file__).parent / "model"
MODEL_PATH = MODEL_DIR / "mlp_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"

# Features and Target (Exact column names from CSV)
FEATURES = [
    "humidity", 
    "pressure", 
    "light", 
    "temperature", 
    "sound_high", 
    "sound_mid", 
    "sound_low", 
    "sound_amp"
]
TARGET = "IAQ_score"

def generate_synthetic_data(num_samples=5000):
    """
    Generates synthetic sensor data labeled with the manual scoring logic.
    This ensures the model is calibrated to our 'Ideal' definitions.
    """
    print(f"Generating {num_samples} synthetic samples for calibration...")
    data = []
    
    # We only generate features the MLP actually uses
    # Note: VOC and PM2.5 are handled as penalties outside the MLP
    mlp_sensor_keys = ["humidity_pct", "pressure_hpa", "light_lux", "temperature_c", "noise_db"]
    
    for _ in range(num_samples):
        # random samples across typical/extreme ranges
        sample = {
            "humidity": random.uniform(10, 95),
            "pressure": random.uniform(960, 1060),
            "light": random.uniform(0, 1500),
            "temperature": random.uniform(10, 35),
            "sound_high": 10.0,
            "sound_mid": 10.0,
            "sound_low": 10.0,
            "sound_amp": random.uniform(20, 90)
        }
        
        # Calculate ground truth score for these 5 features ONLY
        # We use calculate_room_health_score but since VOC/PM2.5 are missing,
        # it will correctly calculate weighted score based on the remaining 0.6 weight.
        reading_for_scoring = {
            "humidity_pct": sample["humidity"],
            "pressure_hpa": sample["pressure"],
            "light_lux": sample["light"],
            "temperature_c": sample["temperature"],
            "noise_db": sample["sound_amp"]
        }
        
        score = calculate_room_health_score(reading_for_scoring)
        
        sample[TARGET] = score
        data.append(sample)
        
    return pd.DataFrame(data)

def train_model():
    # Load data
    csv_data = pd.DataFrame()
    if DATASET_PATH.exists():
        csv_data = pd.read_csv(DATASET_PATH)
        print(f"Loaded {len(csv_data)} rows from CSV.")
        # Filter CSV data to 1-99 range (remove the >200 outliers)
        csv_data = csv_data[(csv_data[TARGET] >= 1) & (csv_data[TARGET] <= 99)]
        print(f"Retained {len(csv_data)} rows from CSV after filtering outliers.")
    else:
        print(f"Warning: Dataset not found at {DATASET_PATH}. Proceeding with synthetic calibration data only.")

    
    # Generate Synthetic Data
    synthetic_data = generate_synthetic_data(30000)
    
    # Combine
    if not csv_data.empty:
        # Take a smaller sample of CSV data to avoid overwhelming the synthetic ground truth
        csv_sample = csv_data.sample(n=min(len(csv_data), 10000), random_state=42)
        df = pd.concat([csv_sample, synthetic_data], ignore_index=True)
    else:
        df = synthetic_data
        
    # Preprocessing
    print("Pre-processing data...")
    # Drop rows with missing target or features
    df = df.dropna(subset=[TARGET] + FEATURES)
    
    X = df[FEATURES]
    y = df[TARGET]

    print(f"Dataset size: {len(df)} rows")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train MLP
    print("Training MLPRegressor (Relu, 100-50 hidden layers)...")
    mlp = MLPRegressor(
        hidden_layer_sizes=(100, 50), 
        max_iter=1000, 
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1
    )
    mlp.fit(X_train_scaled, y_train)

    # Evaluate
    predictions = mlp.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    print(f"Model Training Complete.")
    print(f"MAE: {mae:.4f}")
    print(f"R²: {r2:.4f}")

    # Export
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(mlp, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"Model and scaler successfully exported to {MODEL_DIR}/")

if __name__ == "__main__":
    train_model()
