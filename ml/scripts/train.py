#!/usr/bin/env python
"""
Command-line runner for ML Model Training and Evaluation.
Usage:
    python ml/scripts/train.py
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.train_model import train_model


def main():
    print("=" * 60)
    print("Smart Parking ML Model Training Pipeline")
    print("=" * 60)
    pipeline, metrics = train_model()
    print("Model training and serialization completed successfully.")


if __name__ == "__main__":
    main()
