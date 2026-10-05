"""
ML Configuration and Dataset Schema Definitions for Smart Parking Availability Prediction.
"""

from pathlib import Path

# Base Paths
ML_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ML_DIR / "data"
MODELS_DIR = ML_DIR / "models"

# Default File Paths
RAW_DATA_PATH = DATA_DIR / "historical_parking_data.csv"
MODEL_PATH = MODELS_DIR / "parking_availability_model.joblib"
METRICS_PATH = MODELS_DIR / "model_metrics.json"

# Dataset Schema Definition
DATASET_COLUMNS = [
    "Date",
    "Day",
    "Time",
    "Parking Lot",
    "Total Slots",
    "Occupied Slots",
    "Available Slots",
    "Average Parking Duration",
    "Nearby Event",
    "Holiday",
    "Future Available Slots",
]

# Categorical and Numerical Feature Lists
FEATURE_COLUMNS = [
    "Parking Lot",
    "Day",
    "Time",
    "Total Slots",
    "Occupied Slots",
    "Available Slots",
    "Average Parking Duration",
    "Nearby Event",
    "Holiday",
]

TARGET_COLUMN = "Future Available Slots"

# Days of week mapping
DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# Prediction Horizon (in minutes)
PREDICTION_HORIZON_MINUTES = 20

# Model Hyperparameters
MODEL_PARAMS = {
    "n_estimators": 100,
    "max_depth": 15,
    "min_samples_split": 5,
    "min_samples_leaf": 2,
    "random_state": 42,
    "n_jobs": -1,
}
