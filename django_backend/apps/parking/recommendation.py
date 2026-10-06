"""
Smart Parking Recommendation Engine — Day 06.

Evaluates and ranks candidate parking locations using a multi-factor weighted scoring model:
1. Current Availability (25%)
2. Predicted Availability via Day 05 ML Model (30%)
3. Distance from user / destination (20%)
4. Hourly Price (15%)
5. Walking Distance / Accessibility (10%)

All factor scores are normalized to a 0–100 scale where higher is always better.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Default weights (Sum = 1.0 / 100%)
DEFAULT_WEIGHT_CURRENT_AVAILABILITY = 0.25
DEFAULT_WEIGHT_PREDICTED_AVAILABILITY = 0.30
DEFAULT_WEIGHT_DISTANCE = 0.20
DEFAULT_WEIGHT_PRICE = 0.15
DEFAULT_WEIGHT_WALKING_DISTANCE = 0.10

# Default normalization limits & fallbacks
DEFAULT_MAX_DISTANCE_KM = 5.0
DEFAULT_MAX_WALKING_METERS = 2500.0
DEFAULT_MAX_PRICE_PER_HOUR = 500.0
WALKING_DISTANCE_FACTOR = 1.25  # Urban pedestrian routing factor (straight-line -> street network)


@dataclass
class RecommendationWeights:
    """Configurable weights for the parking recommendation engine."""
    current_availability: float = DEFAULT_WEIGHT_CURRENT_AVAILABILITY
    predicted_availability: float = DEFAULT_WEIGHT_PREDICTED_AVAILABILITY
    distance: float = DEFAULT_WEIGHT_DISTANCE
    price: float = DEFAULT_WEIGHT_PRICE
    walking_distance: float = DEFAULT_WEIGHT_WALKING_DISTANCE

    def validate(self) -> bool:
        total = (
            self.current_availability
            + self.predicted_availability
            + self.distance
            + self.price
            + self.walking_distance
        )
        return abs(total - 1.0) < 1e-4


@dataclass
class NormalizedScores:
    """Normalized individual factor scores on a 0-100 scale."""
    current_availability_score: float
    predicted_availability_score: float
    distance_score: float
    price_score: float
    walking_distance_score: float
    final_score: float


from .utils import haversine_distance, format_distance


class RecommendationScoringService:
    """
    Core scoring service for parking lot recommendations.
    Provides normalization routines and weighted aggregation.
    """

    def __init__(self, weights: Optional[RecommendationWeights] = None):
        self.weights = weights or RecommendationWeights()
        if not self.weights.validate():
            logger.warning(
                "Recommendation weights do not sum to 1.0. Using default normalized weights."
            )
            self.weights = RecommendationWeights()

    @staticmethod
    def calculate_distance_km(
        user_lat: float,
        user_lon: float,
        lot_lat: float,
        lot_lon: float
    ) -> float:
        """
        Calculate straight-line distance in kilometres using the existing Haversine utility.
        """
        return haversine_distance(user_lat, user_lon, lot_lat, lot_lon)

    @staticmethod
    def estimate_walking_distance_meters(distance_km: float) -> int:
        """
        Estimate pedestrian walking distance in meters from straight-line distance
        using a standard urban grid factor (1.25x).
        """
        straight_line_meters = distance_km * 1000.0
        return int(round(straight_line_meters * WALKING_DISTANCE_FACTOR))

    @staticmethod
    def normalize_distance_score(
        distance_km: float,
        max_distance_km: float = DEFAULT_MAX_DISTANCE_KM
    ) -> float:
        """
        Normalize distance score on a 0–100 scale (shorter distance = higher score).
        - 0 km -> 100.0
        - >= max_distance_km -> 0.0
        """
        if max_distance_km <= 0:
            return 100.0
        dist = max(0.0, float(distance_km))
        score = 100.0 * (1.0 - (dist / max_distance_km))
        return round(max(0.0, min(100.0, score)), 2)

    @staticmethod
    def normalize_walking_distance_score(
        walking_meters: float,
        max_walking_meters: float = DEFAULT_MAX_WALKING_METERS
    ) -> float:
        """
        Normalize walking distance score on a 0–100 scale (shorter walk = higher score).
        - 0 m -> 100.0
        - >= max_walking_meters -> 0.0
        """
        if max_walking_meters <= 0:
            return 100.0
        walk_m = max(0.0, float(walking_meters))
        score = 100.0 * (1.0 - (walk_m / max_walking_meters))
        return round(max(0.0, min(100.0, score)), 2)

