# Machine Learning - Parking Availability Prediction

This directory will house the Machine Learning models and training pipelines for the **Smart Parking Availability Platform**.

## Scope & Timeline
- **Scheduled for:** Day 5 of development.
- **Objective:** Predict parking lot occupancy and spot availability using historical parking session data, time features (hour of day, day of week), weather, and local events.

## Planned Directory Structure (Day 5)
```
ml/
├── data/
│   ├── raw/                 # Historical occupancy records
│   └── processed/           # Feature-engineered training sets
├── models/
│   ├── trained_model.pkl    # Serialized ML model
│   └── scaler.pkl           # Feature scaler
├── notebooks/
│   └── exploration.ipynb    # Exploratory Data Analysis (EDA)
├── src/
│   ├── train.py             # Model training script
│   ├── predict.py           # Inference pipeline
│   └── evaluate.py          # Validation metrics (RMSE, MAE)
└── requirements.txt         # ML dependencies (scikit-learn, pandas, numpy, etc.)
```

> **Note:** For Day 1, no models or data files are implemented.
