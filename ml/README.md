# 🔮 Machine Learning — Parking Availability Prediction (Day 05)

This module houses the end-to-end Machine Learning pipeline for the **Smart Parking Availability Platform**, predicting future parking space availability (~20 minutes ahead) from historical parking trends, temporal dynamics, facility capacities, and contextual events.

---

## 📁 Directory Structure

```
ml/
├── data/
│   └── historical_parking_data.csv    # Synthetic historical parking records (4,800 samples)
├── models/
│   ├── parking_availability_model.joblib # Serialized scikit-learn Pipeline artifact
│   └── model_metrics.json             # Regression evaluation metrics artifact
├── scripts/
│   └── train.py                       # CLI model training entry point
├── src/
│   ├── __init__.py
│   ├── config.py                      # Schema definitions, hyperparameters, paths
│   ├── data_generator.py              # Realistic synthetic data generation utility
│   ├── preprocess.py                  # Feature extraction, cyclical time & column transformer
│   ├── features.py                    # Temporal context, explainability factors & inputs
│   ├── train_model.py                 # RandomForestRegressor training pipeline
│   ├── evaluate.py                    # MAE, RMSE, R² metrics evaluation & formatting
│   ├── predict.py                     # Singleton-cached inference service & warnings
│   └── test_ml_pipeline.py            # Comprehensive ML test suite
└── requirements.txt                   # ML dependencies (scikit-learn, pandas, numpy, joblib)
```

---

## 📊 Dataset Schema & Synthetic Status

> **Important Note:** The training dataset currently consists of *synthetic historical parking data for development and model training*. Future releases can replace or augment this dataset with real IoT sensor telemetry or ticket logs from parking facilities.

### Columns
| Column | Type | Description |
|---|---|---|
| `Date` | String (`YYYY-MM-DD`) | Historical date of observation |
| `Day` | String | Monday through Sunday |
| `Time` | String (`HH:MM`) | Observation time |
| `Parking Lot` | String | Facility name (e.g. *Downtown Grand Plaza*) |
| `Total Slots` | Integer | Maximum capacity of the facility |
| `Occupied Slots` | Integer | Number of currently occupied spaces ($0 \le \text{Occupied} \le \text{Total}$) |
| `Available Slots` | Integer | Number of open spaces ($\text{Total} - \text{Occupied}$) |
| `Average Parking Duration` | Integer | Average duration in minutes (turnover rate) |
| `Nearby Event` | String (`Yes`/`No`) | Active sports/concert/commercial event flag |
| `Holiday` | String (`Yes`/`No`) | Weekend or calendar holiday indicator |
| `Future Available Slots` | Integer | Target variable: Available spaces in ~20 minutes |

---

## 🧠 ML Model & Pipeline Architecture

- **Regressor:** `RandomForestRegressor`
- **Hyperparameters:** `n_estimators=100`, `max_depth=15`, `min_samples_split=5`, `min_samples_leaf=2`, `random_state=42`
- **Feature Pipeline:**
  - `OneHotEncoder` for categorical features (`Parking Lot`, `Day`)
  - `StandardScaler` for numerical & engineered features:
    - Occupancy rate ($\frac{\text{Occupied}}{\text{Total}}$)
    - Minutes since midnight, hour, cyclical $\sin(\text{time})$ and $\cos(\text{time})$
    - Weekend flag, event flag, holiday flag, average duration
- **In-Memory Caching:** Trained model pipeline is cached as a singleton in memory, avoiding disk I/O on repeated API calls.

---

## 📈 Evaluation Metrics (Actual Results)

Evaluated on a held-out 20% test set (960 samples):

| Metric | Result | Interpretation |
|---|---|---|
| **Mean Absolute Error (MAE)** | **2.86 spaces** | Average prediction deviation under 3 spaces |
| **Root Mean Squared (RMSE)** | **3.88 spaces** | Low variance and stable bounding |
| **$R^2$ Score** | **0.9902** | 99.0% of variance explained |
| **Max Observed Error** | **26.33 spaces** | Worst-case outlier across large lots |

---

## 🛠️ Commands

### Train the ML Model
```bash
# Standalone ML script:
python ml/scripts/train.py

# Or via Django management command:
python manage.py train_parking_model
```

### Run Model Inference from CLI
```bash
# Predict availability for a specific facility:
python manage.py predict_parking_availability --parking-id 1

# Standalone interactive simulation test:
python manage.py predict_parking_availability --name "Parking A" --total-slots 100 --occupied-slots 92
```

### Run ML Unit Tests
```bash
python -m unittest ml.src.test_ml_pipeline
```
