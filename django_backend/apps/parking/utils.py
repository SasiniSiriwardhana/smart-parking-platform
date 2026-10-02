"""
Haversine distance utility — reusable for both backend API and frontend JS.

Used by the Day 03 parking finder to calculate the distance between:
  - A user's destination / current location
  - Parking lot coordinates

Does NOT rely on any external geocoding library.
"""
import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance (km) between two geographic points
    using the Haversine formula.

    Args:
        lat1, lon1: Latitude / longitude of point A (decimal degrees)
        lat2, lon2: Latitude / longitude of point B (decimal degrees)

    Returns:
        Distance in kilometres (float).
    """
    R = 6371.0  # Earth's mean radius in km

    lat1_r = math.radians(float(lat1))
    lon1_r = math.radians(float(lon1))
    lat2_r = math.radians(float(lat2))
    lon2_r = math.radians(float(lon2))

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def format_distance(km: float) -> str:
    """
    Return a human-readable distance string.

    < 1 km  → "850 m"
    >= 1 km → "1.3 km"
    """
    if km < 1.0:
        meters = int(km * 1000)
        return f"{meters} m"
    return f"{km:.1f} km"
