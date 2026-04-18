"""
RoomPulse — MLP Model Training Script

Trains a Multi-Layer Perceptron (MLPRegressor) on 6 room-environment
features from dataset.csv to predict the Indoor Air Quality (IAQ) score.

Exports:
  - model/mlp_model.pkl    → trained MLPRegressor
  - model/scaler.pkl       → fitted StandardScaler (for inference-time normalisation)

Usage:
    python train_model.py                        # default: dataset.csv
    python train_model.py --csv path/to/data.csv # custom CSV path

Feature columns (X):
    Temperature, Humidity, Pressure, Light, Noise, Particulates

Target column (y):
    IAQ  (continuous score)
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
FEATURE_COLS = [
    "Temperature",
    "Humidity",
    "Pressure",
    "Light",
    "Noise",
    "Particulates",
]
TARGET_COL = "IAQ"

MODEL_DIR = Path(__file__).resolve().parent / "model"
MODEL_PATH = MODEL_DIR / "mlp_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger("roompulse.train")


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def load_and_validate(csv_path: str) -> pd.DataFrame:
    """Load the CSV and validate that all required columns exist."""
    if not os.path.isfile(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from {csv_path}")

    required = FEATURE_COLS + [TARGET_COL]
    missing = [c for c in required if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        logger.error(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    return df


def preprocess(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Handle missing values and return clean X, y.

    Strategy:
      - Drop rows where the target (IAQ) is missing — we can't train on unknown labels.
      - Fill remaining NaN feature values with the column median (robust to outliers).
    """
    before = len(df)
    df = df.dropna(subset=[TARGET_COL])
    dropped = before - len(df)
    if dropped:
        logger.warning(f"Dropped {dropped} rows with missing target '{TARGET_COL}'")

    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].copy()

    # Fill any remaining missing feature values with column median
    na_counts = X.isna().sum()
    if na_counts.any():
        logger.info(f"Filling NaN features with median:\n{na_counts[na_counts > 0]}")
        X = X.fillna(X.median())

    return X, y


# ──────────────────────────────────────────────
# Training
# ──────────────────────────────────────────────

def train(X: pd.DataFrame, y: pd.Series) -> tuple[MLPRegressor, StandardScaler]:
    """Scale features, train the MLP, and report performance metrics."""

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,
    )
    logger.info(f"Train set: {len(X_train)} rows  |  Test set: {len(X_test)} rows")

    # ── Feature scaling ──────────────────────
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ── MLP Regressor ────────────────────────
    mlp = MLPRegressor(
        hidden_layer_sizes=(128, 64, 32),
        activation="relu",
        solver="adam",
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=20,
        random_state=42,
        verbose=False,
    )

    logger.info("Training MLPRegressor (128-64-32, ReLU, Adam, early stopping) ...")
    mlp.fit(X_train_scaled, y_train)
    logger.info(f"Training converged in {mlp.n_iter_} iterations")

    # ── Evaluation ───────────────────────────
    y_pred = mlp.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    logger.info("── Test Set Metrics ──────────────────")
    logger.info(f"  MAE  = {mae:.4f}")
    logger.info(f"  RMSE = {rmse:.4f}")
    logger.info(f"  R²   = {r2:.4f}")

    return mlp, scaler


# ──────────────────────────────────────────────
# Export
# ──────────────────────────────────────────────

def export(model: MLPRegressor, scaler: StandardScaler) -> None:
    """Serialise the trained model and scaler to disk."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, MODEL_PATH)
    logger.info(f"✅ Model saved  → {MODEL_PATH}")

    joblib.dump(scaler, SCALER_PATH)
    logger.info(f"✅ Scaler saved → {SCALER_PATH}")


# ──────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train MLP model on room-environment IAQ data.",
    )
    parser.add_argument(
        "--csv",
        default=str(Path(__file__).resolve().parent / "dataset.csv"),
        help="Path to the training CSV (default: backend/dataset.csv)",
    )
    args = parser.parse_args()

    df = load_and_validate(args.csv)
    X, y = preprocess(df)
    model, scaler = train(X, y)
    export(model, scaler)

    logger.info("🎉 Training complete. Model artefacts are ready for the backend.")


if __name__ == "__main__":
    main()
