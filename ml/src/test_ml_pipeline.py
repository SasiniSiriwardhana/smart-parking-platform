"""
Unit Tests for Machine Learning Dataset, Preprocessing, Model Training, and Inference.
"""

import unittest
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from ml.src.config import DATASET_COLUMNS, PREDICTION_HORIZON_MINUTES
from ml.src.data_generator import (
    calculate_base_occupancy_ratio,
    generate_synthetic_dataset,
)
from ml.src.evaluate import compute_regression_metrics
from ml.src.features import (
    build_prediction_input,
    get_prediction_explainability_factors,
    get_temporal_context,
)
from ml.src.predict import (
    determine_confidence_and_range,
    determine_prediction_status,
    predict_availability,
)
from ml.src.preprocess import (
    ParkingFeatureExtractor,
    build_full_pipeline,
    parse_boolean_flag,
    parse_time_to_minutes,
)


class TestHistoricalDatasetAndGenerator(unittest.TestCase):
    """Test synthetic dataset generator and schema consistency."""

    def setUp(self):
        self.df = generate_synthetic_dataset(num_days=3, interval_minutes=60, seed=123)

    def test_dataset_required_columns(self):
        """Verify dataset contains all required schema columns."""
        for col in DATASET_COLUMNS:
            self.assertIn(col, self.df.columns, f"Missing required column: {col}")

    def test_dataset_no_empty_rows(self):
        """Ensure dataset contains valid records with no nulls."""
        self.assertGreater(len(self.df), 50)
        self.assertEqual(self.df.isnull().sum().sum(), 0)

    def test_occupancy_consistency(self):
        """Verify Available Slots = Total Slots - Occupied Slots and bounds [0, Total Slots]."""
        for _, row in self.df.iterrows():
            total = row["Total Slots"]
            occ = row["Occupied Slots"]
            avail = row["Available Slots"]
            future_avail = row["Future Available Slots"]

            self.assertEqual(avail, total - occ)
            self.assertTrue(0 <= occ <= total, f"Occupied {occ} out of bounds for total {total}")
            self.assertTrue(0 <= avail <= total, f"Available {avail} out of bounds for total {total}")
            self.assertTrue(0 <= future_avail <= total, f"Future available {future_avail} out of bounds")

    def test_occupancy_ratio_calculation(self):
        """Test base occupancy ratio respects bounds 0.0 to 1.0."""
        ratio = calculate_base_occupancy_ratio(
            lot_type="commercial",
            day_name="Monday",
            hour=8,
            minute=30,
            is_holiday=False,
            has_event=True,
        )
        self.assertTrue(0.0 <= ratio <= 1.0)


class TestFeaturePreprocessing(unittest.TestCase):
    """Test feature parsing and transformer pipeline."""

    def test_parse_time_to_minutes(self):
        self.assertEqual(parse_time_to_minutes("00:00"), 0)
        self.assertEqual(parse_time_to_minutes("08:30"), 510)
        self.assertEqual(parse_time_to_minutes("13:00"), 780)
        self.assertEqual(parse_time_to_minutes("23:59"), 1439)

    def test_parse_boolean_flag(self):
        self.assertEqual(parse_boolean_flag("Yes"), 1)
        self.assertEqual(parse_boolean_flag("No"), 0)
        self.assertEqual(parse_boolean_flag(True), 1)
        self.assertEqual(parse_boolean_flag(False), 0)

    def test_feature_extractor_transform(self):
        extractor = ParkingFeatureExtractor()
        raw_dict = {
            "Date": "2026-09-01",
            "Day": "Monday",
            "Time": "08:30",
            "Parking Lot": "Test Plaza",
            "Total Slots": 100,
            "Occupied Slots": 80,
            "Available Slots": 20,
            "Average Parking Duration": 45,
            "Nearby Event": "No",
            "Holiday": "No",
        }
        df_out = extractor.transform(raw_dict)
        self.assertIn("time_minutes", df_out.columns)
        self.assertIn("occupancy_rate", df_out.columns)
        self.assertEqual(df_out["occupancy_rate"].iloc[0], 0.80)


class TestModelTrainingAndInference(unittest.TestCase):
    """Test model fitting, evaluation metrics, and prediction bounds."""

    def setUp(self):
        self.df = generate_synthetic_dataset(num_days=2, interval_minutes=60, seed=42)
        X = self.df.drop(columns=["Future Available Slots"])
        y = self.df["Future Available Slots"]

        rf = RandomForestRegressor(n_estimators=10, max_depth=5, random_state=42)
        self.pipeline = build_full_pipeline(rf)
        self.pipeline.fit(X, y)

    def test_pipeline_prediction(self):
        """Test pipeline returns numeric prediction within valid bounds."""
        test_input = pd.DataFrame([{
            "Date": "2026-09-01",
            "Day": "Monday",
            "Time": "09:00",
            "Parking Lot": "Downtown Grand Plaza",
            "Total Slots": 100,
            "Occupied Slots": 90,
            "Available Slots": 10,
            "Average Parking Duration": 60,
            "Nearby Event": "No",
            "Holiday": "No",
        }])
        pred = self.pipeline.predict(test_input)
        self.assertEqual(len(pred), 1)
        self.assertTrue(0.0 <= pred[0] <= 100.0)

    def test_regression_metrics(self):
        """Test evaluation metrics computation."""
        y_true = np.array([10.0, 20.0, 30.0, 40.0])
        y_pred = np.array([11.0, 19.0, 31.0, 39.0])
        metrics = compute_regression_metrics(y_true, y_pred)
        self.assertIn("mae", metrics)
        self.assertIn("rmse", metrics)
        self.assertIn("r2_score", metrics)
        self.assertAlmostEqual(metrics["mae"], 1.0)

    def test_confidence_and_range_derivation(self):
        """Test prediction range bounding and confidence scoring."""
        # High confidence for low RMSE / capacity
        rng, conf = determine_confidence_and_range(raw_prediction=15.2, total_slots=100, rmse=3.5)
        self.assertEqual(conf, "High")
        self.assertTrue(0 <= rng["min"] <= 15 <= rng["max"] <= 100)

    def test_status_warning_levels(self):
        """Test status code and warning messages for different availability thresholds."""
        # Full / <= 10%
        code, level, msg = determine_prediction_status(predicted_available=5, total_slots=100)
        self.assertEqual(code, "likely_full_soon")
        self.assertEqual(level, "red")

        # Limited / <= 25%
        code, level, msg = determine_prediction_status(predicted_available=20, total_slots=100)
        self.assertEqual(code, "limited_availability")
        self.assertEqual(level, "yellow")

        # Ample / > 25%
        code, level, msg = determine_prediction_status(predicted_available=60, total_slots=100)
        self.assertEqual(code, "ample_availability")
        self.assertEqual(level, "green")

    def test_predict_availability_service(self):
        """Test end-to-end predict_availability function."""
        res = predict_availability(
            parking_lot_name="Downtown Grand Plaza",
            total_slots=100,
            current_occupied=92,
            current_available=8,
        )
        self.assertEqual(res["parking_name"], "Downtown Grand Plaza")
        self.assertEqual(res["total_slots"], 100)
        self.assertEqual(res["current_available"], 8)
        self.assertEqual(res["prediction_minutes"], PREDICTION_HORIZON_MINUTES)
        self.assertTrue(0 <= res["predicted_available"] <= 100)
        self.assertTrue(0 <= res["predicted_range"]["min"] <= res["predicted_range"]["max"] <= 100)
        self.assertIn(res["confidence"], ["High", "Medium", "Low"])
        self.assertGreater(len(res["factors"]), 0)


if __name__ == "__main__":
    unittest.main()
