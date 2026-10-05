"""
RandomForest Model Training Pipeline for Parking Availability Prediction.
Loads historical parking data, splits train/test, fits pipeline, computes metrics, and persists artifacts.
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

from .config import (
    MODEL_PARAMS,
    MODEL_PATH,
    RAW_DATA_PATH,
    TARGET_COLUMN,
)
from .data_generator import generate_synthetic_dataset, save_dataset_to_csv
from .evaluate import (
    compute_regression_metrics,
    format_metrics_report,
    save_evaluation_metrics,
)
from .preprocess import build_full_pipeline


def load_or_generate_dataset(data_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Load dataset from CSV or generate synthetic dataset if not found."""
    path = Path(data_path or RAW_DATA_PATH)
    if not path.exists():
        print(f"Dataset not found at {path}. Generating synthetic historical data...")
        df = generate_synthetic_dataset(num_days=20, interval_minutes=30)
        save_dataset_to_csv(df, path)
        return df
    return pd.read_csv(path)


def train_model(
    data_path: Optional[Union[str, Path]] = None,
    model_output_path: Optional[Union[str, Path]] = None,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[object, Dict[str, float]]:
    """
    Train RandomForestRegressor model pipeline on historical parking dataset.
    Returns (trained_pipeline, metrics_dict).
    """
    df = load_or_generate_dataset(data_path)
    
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in dataset.")

    # Split Features and Target
    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    # 80/20 Train Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    print(f"Training dataset: {len(X_train)} samples | Testing dataset: {len(X_test)} samples")

    # Initialize Random Forest Regressor
    rf_model = RandomForestRegressor(
        n_estimators=MODEL_PARAMS["n_estimators"],
        max_depth=MODEL_PARAMS["max_depth"],
        min_samples_split=MODEL_PARAMS["min_samples_split"],
        min_samples_leaf=MODEL_PARAMS["min_samples_leaf"],
        random_state=MODEL_PARAMS["random_state"],
        n_jobs=MODEL_PARAMS["n_jobs"],
    )

    # Build end-to-end preprocessing + regressor pipeline
    pipeline = build_full_pipeline(rf_model)

    print("Fitting RandomForestRegressor pipeline...")
    pipeline.fit(X_train, y_train)

    # Evaluate on held-out test set
    y_pred = pipeline.predict(X_test)
    metrics = compute_regression_metrics(y_test, y_pred)

    print("\n" + format_metrics_report(metrics))

    # Persist model artifact
    save_path = Path(model_output_path or MODEL_PATH)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, save_path)
    print(f"Model artifact saved to: {save_path}")

    # Persist evaluation metrics
    save_evaluation_metrics(metrics)

    return pipeline, metrics


if __name__ == "__main__":
    train_model()
