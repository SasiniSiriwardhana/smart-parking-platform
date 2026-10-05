"""
Synthetic Historical Parking Data Generator.
Generates realistic historical parking occupancy records for training ML availability models.

NOTE: Synthetic historical parking data for development and model training.
"""

import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from .config import (
    DATASET_COLUMNS,
    DAYS_OF_WEEK,
    PREDICTION_HORIZON_MINUTES,
    RAW_DATA_PATH,
)

# Standard sample parking facilities
DEFAULT_LOTS = [
    {"name": "Downtown Grand Plaza", "total_slots": 100, "type": "commercial"},
    {"name": "Metro Central Hub", "total_slots": 120, "type": "transit"},
    {"name": "Harbor View Mall", "total_slots": 80, "type": "retail"},
    {"name": "Silicon Tech Park", "total_slots": 150, "type": "office"},
    {"name": "City Center Parking", "total_slots": 60, "type": "mixed"},
]


def calculate_base_occupancy_ratio(
    lot_type: str,
    day_name: str,
    hour: int,
    minute: int,
    is_holiday: bool,
    has_event: bool,
) -> float:
    """
    Calculate realistic occupancy ratio (0.0 to 1.0) based on time, day, lot type, and conditions.
    """
    time_float = hour + minute / 60.0
    is_weekend = day_name in ["Saturday", "Sunday"] or is_holiday

    if not is_weekend:
        # Weekday pattern
        if lot_type in ["office", "transit"]:
            # Peaks during morning rush (8:00 - 9:30) and stays high until 17:00
            if 7.0 <= time_float < 9.5:
                # Morning surge
                progress = (time_float - 7.0) / 2.5
                ratio = 0.25 + 0.65 * math.sin(progress * math.pi / 2)
            elif 9.5 <= time_float < 17.0:
                # Working hours high plateau
                ratio = 0.85 + 0.08 * math.sin((time_float - 9.5) * 0.4)
            elif 17.0 <= time_float < 19.5:
                # Evening departure
                progress = (time_float - 17.0) / 2.5
                ratio = 0.88 - 0.60 * math.sin(progress * math.pi / 2)
            else:
                # Night hours
                ratio = 0.15 + 0.08 * math.sin(time_float * 0.2)
        elif lot_type == "retail":
            # Shopping mall pattern: rises mid-day to evening
            if 10.0 <= time_float < 21.0:
                ratio = 0.40 + 0.45 * math.sin((time_float - 10.0) / 11.0 * math.pi)
            else:
                ratio = 0.10 + 0.05 * random.random()
        else:
            # Commercial / mixed
            if 8.0 <= time_float < 20.0:
                ratio = 0.50 + 0.38 * math.sin((time_float - 8.0) / 12.0 * math.pi)
            else:
                ratio = 0.20 + 0.05 * random.random()
    else:
        # Weekend / Holiday pattern
        if lot_type in ["retail", "commercial", "mixed"]:
            # Shopping and leisure peak in afternoon and evening (12:00 - 19:00)
            if 11.0 <= time_float < 21.0:
                ratio = 0.55 + 0.40 * math.sin((time_float - 11.0) / 10.0 * math.pi)
            else:
                ratio = 0.15 + 0.10 * random.random()
        else:
            # Office / commuter lots quiet on weekends
            ratio = 0.12 + 0.10 * math.sin(time_float * 0.2)

    # Apply event boost
    if has_event:
        ratio = min(0.98, ratio + random.uniform(0.20, 0.35))

    # Add small realistic noise (-0.04 to +0.04)
    noise = random.uniform(-0.04, 0.04)
    occupancy_ratio = max(0.02, min(0.98, ratio + noise))
    return occupancy_ratio


def generate_synthetic_dataset(
    num_days: int = 30,
    interval_minutes: int = 30,
    lots: Optional[List[Dict]] = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic historical parking data records.
    Each row captures current occupancy and the future available slots after PREDICTION_HORIZON_MINUTES.
    """
    random.seed(seed)
    lots = lots or DEFAULT_LOTS
    records = []

    start_date = datetime(2026, 8, 1, 6, 0)
    total_intervals_per_day = (24 * 60) // interval_minutes

    for lot in lots:
        total_slots = lot["total_slots"]
        lot_name = lot["name"]
        lot_type = lot["type"]

        # Base parking duration for the lot type (in minutes)
        base_duration = {
            "office": 240,
            "transit": 300,
            "retail": 90,
            "commercial": 120,
            "mixed": 75,
        }.get(lot_type, 60)

        for day_offset in range(num_days):
            current_day_date = start_date + timedelta(days=day_offset)
            day_name = DAYS_OF_WEEK[current_day_date.weekday()]
            
            # Realistic probability of events and holidays
            is_holiday = 1 if (current_day_date.weekday() == 6 and day_offset % 7 == 0) or day_offset in [15, 25] else 0
            has_event = 1 if random.random() < 0.15 else 0

            for interval_idx in range(total_intervals_per_day):
                dt = current_day_date + timedelta(minutes=interval_idx * interval_minutes)
                hour = dt.hour
                minute = dt.minute

                time_str = f"{hour:02d}:{minute:02d}"
                date_str = dt.strftime("%Y-%m-%d")

                # Average parking duration fluctuates slightly
                duration_noise = random.randint(-15, 15)
                avg_duration = max(20, base_duration + duration_noise)

                # Calculate current occupancy ratio
                occ_ratio = calculate_base_occupancy_ratio(
                    lot_type=lot_type,
                    day_name=day_name,
                    hour=hour,
                    minute=minute,
                    is_holiday=bool(is_holiday),
                    has_event=bool(has_event),
                )

                occupied_slots = int(round(occ_ratio * total_slots))
                occupied_slots = max(0, min(total_slots, occupied_slots))
                available_slots = total_slots - occupied_slots

                # Calculate future occupancy (+PREDICTION_HORIZON_MINUTES)
                future_dt = dt + timedelta(minutes=PREDICTION_HORIZON_MINUTES)
                future_occ_ratio = calculate_base_occupancy_ratio(
                    lot_type=lot_type,
                    day_name=DAYS_OF_WEEK[future_dt.weekday()],
                    hour=future_dt.hour,
                    minute=future_dt.minute,
                    is_holiday=bool(is_holiday),
                    has_event=bool(has_event),
                )

                # Future slots influenced by current trajectory and rate of change
                delta_ratio = future_occ_ratio - occ_ratio
                future_occ = int(round((occ_ratio + delta_ratio) * total_slots))
                future_occ = max(0, min(total_slots, future_occ))
                future_available = total_slots - future_occ

                records.append({
                    "Date": date_str,
                    "Day": day_name,
                    "Time": time_str,
                    "Parking Lot": lot_name,
                    "Total Slots": total_slots,
                    "Occupied Slots": occupied_slots,
                    "Available Slots": available_slots,
                    "Average Parking Duration": avg_duration,
                    "Nearby Event": "Yes" if has_event else "No",
                    "Holiday": "Yes" if is_holiday else "No",
                    "Future Available Slots": future_available,
                })

    df = pd.DataFrame(records, columns=DATASET_COLUMNS)
    return df


def save_dataset_to_csv(df: pd.DataFrame, file_path: Optional[str] = None) -> str:
    """Save generated dataset to CSV."""
    target_path = file_path or RAW_DATA_PATH
    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target_path, index=False)
    return str(target_path)


if __name__ == "__main__":
    print("Generating synthetic historical parking dataset...")
    data = generate_synthetic_dataset(num_days=20, interval_minutes=30)
    saved_path = save_dataset_to_csv(data)
    print(f"Generated {len(data)} records saved to {saved_path}")
    print(data.head())
