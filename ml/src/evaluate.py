"""
Model Evaluation and Metrics Utilities.
Computes MAE, RMSE, R² and saves evaluation summary artifacts.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Union
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .config import METRICS_PATH


def compute_regression_metrics(
    y_true: Union[np.ndarray, list],
    y_pred: Union[np.ndarray, list],
) -> Dict[str, float]:
    """
    Compute regression evaluation metrics: MAE, RMSE, R2, and Max Error.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))
    max_err = float(np.max(np.abs(y_true - y_pred)))

    metrics = {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "r2_score": round(r2, 4),
        "max_error": round(max_err, 3),
    }
    return metrics


def save_evaluation_metrics(
    metrics: Dict[str, float],
    output_path: Optional[Union[str, Path]] = None,
) -> Path:
    """Save metrics to JSON artifact."""
    target_path = Path(output_path or METRICS_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)
    return target_path


def format_metrics_report(metrics: Dict[str, float]) -> str:
    """Return a formatted string report of model performance metrics."""
    return (
        f"=== Model Evaluation Metrics ===\n"
        f"  • Mean Absolute Error (MAE) : {metrics['mae']:.2f} spaces\n"
        f"  • Root Mean Squared (RMSE)  : {metrics['rmse']:.2f} spaces\n"
        f"  • R² Score (Variance Exp.)  : {metrics['r2_score']:.4f}\n"
        f"  • Max Observed Error        : {metrics['max_error']:.2f} spaces\n"
        f"================================"
    )
