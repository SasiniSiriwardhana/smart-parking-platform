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
