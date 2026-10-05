"""
Feature Engineering Utilities and Context Extractors.
Provides contextual helpers for temporal, holiday, event, and parking features.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from .config import DAYS_OF_WEEK, PREDICTION_HORIZON_MINUTES


def get_temporal_context(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Extract temporal features for a given datetime (defaults to now).
    """
    dt = dt or datetime.now()
    day_idx = dt.weekday()
    day_name = DAYS_OF_WEEK[day_idx]
    time_str = dt.strftime("%H:%M")
    date_str = dt.strftime("%Y-%m-%d")
    minutes_since_midnight = dt.hour * 60 + dt.minute

    return {
        "datetime": dt,
        "date_str": date_str,
        "day_name": day_name,
        "time_str": time_str,
        "minutes_since_midnight": minutes_since_midnight,
        "is_weekend": 1 if day_idx >= 5 else 0,
    }


def build_prediction_input(
    parking_lot_name: str,
    total_slots: int,
    current_occupied: int,
    current_available: Optional[int] = None,
    target_dt: Optional[datetime] = None,
    avg_duration: float = 60.0,
    nearby_event: bool = False,
    holiday: bool = False,
) -> Dict[str, Any]:
    """
    Construct a validated feature dictionary for ML model inference.
    """
    if target_dt is None:
        target_dt = datetime.now() + timedelta(minutes=PREDICTION_HORIZON_MINUTES)

    temp_ctx = get_temporal_context(target_dt)

    if current_available is None:
        current_available = max(0, total_slots - current_occupied)
    else:
        current_occupied = max(0, total_slots - current_available)

    return {
        "Date": temp_ctx["date_str"],
        "Day": temp_ctx["day_name"],
        "Time": temp_ctx["time_str"],
        "Parking Lot": parking_lot_name,
        "Total Slots": total_slots,
        "Occupied Slots": current_occupied,
        "Available Slots": current_available,
        "Average Parking Duration": avg_duration,
        "Nearby Event": "Yes" if nearby_event else "No",
        "Holiday": "Yes" if holiday else "No",
    }


def get_prediction_explainability_factors(
    day_name: str,
    time_str: str,
    occupancy_rate: float,
    nearby_event: bool,
    holiday: bool,
    avg_duration: float,
) -> List[str]:
    """
    Generate readable explainability factor bullets explaining model behavior.
    """
    factors = []
    
    # Occupancy factor
    if occupancy_rate >= 0.85:
        factors.append("Very high current occupancy (near capacity)")
    elif occupancy_rate >= 0.60:
        factors.append("Moderate to high parking lot utilization")
    else:
        factors.append("Low current occupancy with ample open spots")

    # Time and Day factor
    factors.append(f"{day_name} traffic pattern at {time_str}")

    # Event factor
    if nearby_event:
        factors.append("Nearby event active (+ increased demand)")

    # Holiday factor
    if holiday:
        factors.append("Holiday schedule in effect")

    # Duration factor
    factors.append(f"Average turnover rate (~{int(avg_duration)} min duration)")

    return factors
