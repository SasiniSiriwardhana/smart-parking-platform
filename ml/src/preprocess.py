"""
Data Preprocessing and Feature Engineering Pipeline for Parking Availability Prediction.
Ensures identical feature transformations during model training and real-time inference.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import DAYS_OF_WEEK, FEATURE_COLUMNS, TARGET_COLUMN


def parse_time_to_minutes(time_val: Union[str, int, float]) -> int:
    """Convert time representation (HH:MM or int minutes) into minutes since midnight."""
    if isinstance(time_val, (int, float)):
        return int(time_val) % 1440
    
    if isinstance(time_val, str):
        parts = time_val.strip().split(":")
        if len(parts) >= 2:
            try:
                hours = int(parts[0])
                mins = int(parts[1])
                return (hours * 60 + mins) % 1440
            except ValueError:
                pass
    return 720  # default midday


def parse_boolean_flag(flag_val: Any) -> int:
    """Parse boolean, string ('Yes'/'No', 'True'/'False'), or int flag to 0 or 1."""
    if isinstance(flag_val, bool):
        return 1 if flag_val else 0
    if isinstance(flag_val, (int, float)):
        return 1 if flag_val > 0 else 0
    if isinstance(flag_val, str):
        val = flag_val.strip().lower()
        if val in ["yes", "y", "true", "1", "t"]:
            return 1
    return 0


class ParkingFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Custom transformer extracting structured numerical and categorical features
    from raw parking DataFrame or dictionary inputs.
    """

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None):
        return self

    def transform(self, X: Union[pd.DataFrame, List[Dict], Dict]) -> pd.DataFrame:
        if isinstance(X, dict):
            df = pd.DataFrame([X])
        elif isinstance(X, list):
            df = pd.DataFrame(X)
        else:
            df = X.copy()

        # 1. Parse time into minutes, hour, and cyclical features
        time_minutes = df["Time"].apply(parse_time_to_minutes)
        df["time_minutes"] = time_minutes
        df["hour"] = time_minutes // 60
        df["sin_time"] = np.sin(2 * np.pi * time_minutes / 1440.0)
        df["cos_time"] = np.cos(2 * np.pi * time_minutes / 1440.0)

        # 2. Parse day into day index and weekend flag
        day_map = {day: idx for idx, day in enumerate(DAYS_OF_WEEK)}
        df["day_index"] = df["Day"].apply(lambda d: day_map.get(str(d).capitalize(), 0))
        df["is_weekend"] = df["day_index"].apply(lambda idx: 1 if idx >= 5 else 0)

        # 3. Parse boolean event and holiday flags
        df["has_event"] = df["Nearby Event"].apply(parse_boolean_flag)
        df["is_holiday"] = df["Holiday"].apply(parse_boolean_flag)

        # 4. Numerical validation and derived occupancy metrics
        df["Total Slots"] = pd.to_numeric(df["Total Slots"], errors="coerce").fillna(100).clip(lower=1)
        
        # Handle Occupied / Available
        if "Occupied Slots" in df.columns:
            df["Occupied Slots"] = pd.to_numeric(df["Occupied Slots"], errors="coerce").fillna(0)
        elif "Available Slots" in df.columns:
            df["Occupied Slots"] = df["Total Slots"] - pd.to_numeric(df["Available Slots"], errors="coerce").fillna(0)
        else:
            df["Occupied Slots"] = 0

        df["Occupied Slots"] = df["Occupied Slots"].clip(lower=0)
        df["Available Slots"] = (df["Total Slots"] - df["Occupied Slots"]).clip(lower=0)
        df["occupancy_rate"] = (df["Occupied Slots"] / df["Total Slots"]).clip(lower=0.0, upper=1.0)

        if "Average Parking Duration" in df.columns:
            df["avg_duration"] = pd.to_numeric(df["Average Parking Duration"], errors="coerce").fillna(60).clip(lower=5)
        else:
            df["avg_duration"] = 60.0

        return df


def build_preprocessor_pipeline() -> ColumnTransformer:
    """
    Construct a ColumnTransformer with OneHotEncoder for categorical features
    and StandardScaler for numerical features.
    """
    categorical_features = ["Parking Lot", "Day"]
    numerical_features = [
        "Total Slots",
        "Occupied Slots",
        "Available Slots",
        "occupancy_rate",
        "time_minutes",
        "hour",
        "sin_time",
        "cos_time",
        "day_index",
        "is_weekend",
        "has_event",
        "is_holiday",
        "avg_duration",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_features,
            ),
            (
                "num",
                StandardScaler(),
                numerical_features,
            ),
        ],
        remainder="drop",
    )
    return preprocessor


def build_full_pipeline(regressor_model: Any) -> Pipeline:
    """
    Construct complete end-to-end Pipeline:
    ParkingFeatureExtractor -> ColumnTransformer (OneHot + Scaler) -> RegressorModel
    """
    preprocessor = build_preprocessor_pipeline()
    pipeline = Pipeline(
        steps=[
            ("feature_extractor", ParkingFeatureExtractor()),
            ("preprocessor", preprocessor),
            ("regressor", regressor_model),
        ]
    )
    return pipeline
