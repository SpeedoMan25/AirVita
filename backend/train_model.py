import pandas as pd
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
from pathlib import Path

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

def train_model():
    print(f"Loading dataset from {DATASET_PATH}...")
    if not DATASET_PATH.exists():
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    # Load data
    df = pd.read_csv(DATASET_PATH)
    
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
