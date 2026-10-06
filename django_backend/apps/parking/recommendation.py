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

    @staticmethod
    def normalize_price_score(
        price_per_hour: float,
        max_price: float = DEFAULT_MAX_PRICE_PER_HOUR
    ) -> float:
        """
        Normalize hourly price score on a 0–100 scale (lower price = higher score).
        - Rs. 0.0 -> 100.0
        - >= max_price -> 0.0
        """
        if max_price <= 0:
            return 100.0
        price = max(0.0, float(price_per_hour))
        score = 100.0 * (1.0 - (price / max_price))
        return round(max(0.0, min(100.0, score)), 2)

    @staticmethod
    def normalize_availability_score(
        available_slots: int,
        total_slots: int
    ) -> float:
        """
        Normalize current availability score on a 0–100 scale (more spaces = higher score).
        - 100% available -> 100.0
        - 0 spaces available -> 0.0
        """
        if total_slots <= 0:
            return 0.0
        avail = max(0, min(total_slots, int(available_slots)))
        score = (avail / float(total_slots)) * 100.0
        return round(max(0.0, min(100.0, score)), 2)

    @staticmethod
    def normalize_predicted_availability_score(
        predicted_available: int,
        total_slots: int
    ) -> float:
        """
        Normalize predicted availability score on a 0–100 scale (more predicted spaces = higher score).
        - 100% capacity predicted available -> 100.0
        - 0 spaces predicted available -> 0.0
        """
        if total_slots <= 0:
            return 0.0
        pred_avail = max(0, min(total_slots, int(predicted_available)))
        score = (pred_avail / float(total_slots)) * 100.0
        return round(max(0.0, min(100.0, score)), 2)

    @staticmethod
    def get_ml_prediction(
        parking_lot_name: str,
        total_slots: int,
        current_occupied: int,
        current_available: int,
        target_datetime=None,
        avg_duration: float = 60.0,
        has_event: bool = False,
        is_holiday: bool = False,
    ) -> Dict[str, Any]:
        """
        Invoke the existing Day 05 ML availability prediction service.
        Reuses the trained RandomForest model without duplicate pipelines.
        """
        try:
            from ml.src.predict import predict_availability
            return predict_availability(
                parking_lot_name=parking_lot_name,
                total_slots=total_slots,
                current_occupied=current_occupied,
                current_available=current_available,
                target_datetime=target_datetime,
                average_parking_duration=avg_duration,
                nearby_event=has_event,
                holiday=is_holiday,
            )
        except Exception as e:
            logger.warning(
                f"ML Prediction fallback for {parking_lot_name}: {e}"
            )
            # Fallback estimation based on current state
            return {
                "parking_name": parking_lot_name,
                "total_slots": total_slots,
                "current_available": current_available,
                "current_occupied": current_occupied,
                "predicted_available": current_available,
                "predicted_occupied": current_occupied,
                "predicted_range": {
                    "min": max(0, current_available - 2),
                    "max": min(total_slots, current_available + 2)
                },
                "confidence": "Medium",
                "status": "normal",
                "warning_level": "green" if current_available > 0.25 * total_slots else "yellow",
                "warning_message": "Availability based on current telemetry.",
                "factors": [],
            }

    def evaluate_candidate(

        self,
        lot,
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        dest_lat: Optional[float] = None,
        dest_lon: Optional[float] = None,
        max_distance_km: float = DEFAULT_MAX_DISTANCE_KM,
        max_price: float = DEFAULT_MAX_PRICE_PER_HOUR,
        max_walking_meters: float = DEFAULT_MAX_WALKING_METERS,
        avg_duration: float = 60.0,
        has_event: bool = False,
        is_holiday: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluate a single ParkingLot candidate across all 5 weighted factors.
        Returns a rich structured recommendation dictionary.
        """
        # Ensure slots exist if needed
        if hasattr(lot, 'slots') and not lot.slots.exists():
            lot.generate_default_slots()

        total_slots = int(lot.total_slots if lot.total_slots > 0 else (lot.slots.count() or 1))
        
        # Real-time availability
        if hasattr(lot, 'slots') and lot.slots.exists():
            occupied_slots = lot.slots.filter(status='OCCUPIED').count()
            available_slots = max(0, total_slots - occupied_slots)
        else:
            available_slots = int(lot.available_slots)
            occupied_slots = max(0, total_slots - available_slots)

        # Distance computation (destination takes precedence if provided, otherwise user location)
        ref_lat = dest_lat if dest_lat is not None else user_lat
        ref_lon = dest_lon if dest_lon is not None else user_lon

        if ref_lat is not None and ref_lon is not None:
            distance_km = self.calculate_distance_km(
                float(ref_lat), float(ref_lon),
                float(lot.latitude), float(lot.longitude)
            )
            distance_meters = int(round(distance_km * 1000))
            walking_meters = self.estimate_walking_distance_meters(distance_km)
            distance_text = format_distance(distance_km)
        else:
            distance_km = 0.5  # Neutral default for testing when no coords passed
            distance_meters = 500
            walking_meters = self.estimate_walking_distance_meters(distance_km)
            distance_text = "500 m"

        # Pricing
        price_per_hour = float(lot.price_per_hour)

        # ML Prediction (Day 05 model)
        prediction_result = self.get_ml_prediction(
            parking_lot_name=lot.name,
            total_slots=total_slots,
            current_occupied=occupied_slots,
            current_available=available_slots,
            avg_duration=avg_duration,
            has_event=has_event,
            is_holiday=is_holiday,
        )
        predicted_available = int(prediction_result.get("predicted_available", available_slots))
        predicted_range = prediction_result.get("predicted_range", {
            "min": max(0, predicted_available - 2),
            "max": min(total_slots, predicted_available + 2)
        })
        prediction_confidence = prediction_result.get("confidence", "Medium")
        prediction_status = prediction_result.get("status", "normal")
        warning_level = prediction_result.get("warning_level", "green")
        warning_message = prediction_result.get("warning_message", "")

        # Normalize 5 factors (0–100)
        score_avail = self.normalize_availability_score(available_slots, total_slots)
        score_pred = self.normalize_predicted_availability_score(predicted_available, total_slots)
        score_dist = self.normalize_distance_score(distance_km, max_distance_km)
        score_price = self.normalize_price_score(price_per_hour, max_price)
        score_walk = self.normalize_walking_distance_score(walking_meters, max_walking_meters)

        # Compute weighted final score (0–100)
        w = self.weights
        final_score = round(
            (score_avail * w.current_availability)
            + (score_pred * w.predicted_availability)
            + (score_dist * w.distance)
            + (score_price * w.price)
            + (score_walk * w.walking_distance),
            1
        )
        # Ensure score stays bounded [0.0, 100.0]
        final_score = max(0.0, min(100.0, final_score))

        # Generate explainability reasons based on actual scoring data
        reasons = self.generate_explainability_reasons(
            score_avail=score_avail,
            score_pred=score_pred,
            score_dist=score_dist,
            score_price=score_price,
            score_walk=score_walk,
            available_slots=available_slots,
            total_slots=total_slots,
            predicted_range=predicted_range,
            price_per_hour=price_per_hour,
            distance_meters=distance_meters,
            walking_meters=walking_meters,
        )

        return {
            "id": lot.pk,
            "name": lot.name,
            "address": lot.address,
            "latitude": float(lot.latitude),
            "longitude": float(lot.longitude),
            "score": final_score,
            "price_per_hour": price_per_hour,
            "total_slots": total_slots,
            "available_slots": available_slots,
            "occupied_slots": occupied_slots,
            "distance_km": round(distance_km, 3),
            "distance_meters": distance_meters,
            "distance_text": distance_text,
            "walking_distance_meters": walking_meters,
            "predicted_available": predicted_available,
            "predicted_min": predicted_range.get("min", predicted_available),
            "predicted_max": predicted_range.get("max", predicted_available),
            "predicted_range": predicted_range,
            "prediction_confidence": prediction_confidence,
            "prediction_status": prediction_status,
            "warning_level": warning_level,
            "warning_message": warning_message,
            "is_open_now": getattr(lot, 'is_open_now', True),
            "opening_time": str(lot.opening_time) if getattr(lot, 'opening_time', None) else "00:00",
            "closing_time": str(lot.closing_time) if getattr(lot, 'closing_time', None) else "23:59",
            "reasons": reasons,
            "factor_scores": {
                "current_availability": score_avail,
                "predicted_availability": score_pred,
                "distance": score_dist,
                "price": score_price,
                "walking_distance": score_walk,
            },
            "weights": {
                "current_availability": w.current_availability,
                "predicted_availability": w.predicted_availability,
                "distance": w.distance,
                "price": w.price,
                "walking_distance": w.walking_distance,
            }
        }

    @staticmethod
    def generate_explainability_reasons(
        score_avail: float,
        score_pred: float,
        score_dist: float,
        score_price: float,
        score_walk: float,
        available_slots: int,
        total_slots: int,
        predicted_range: Dict[str, int],
        price_per_hour: float,
        distance_meters: int,
        walking_meters: int,
    ) -> List[str]:
        """
        Produce clear, human-understandable explanation reasons ("Why this parking?")
        backed strictly by actual computed factors.
        """
        reasons = []

        if score_avail >= 50.0:
            reasons.append(f"High current availability ({available_slots}/{total_slots} spots open)")
        elif available_slots > 0:
            reasons.append(f"Currently open with {available_slots} available spots")

        if score_pred >= 50.0:
            pred_min = predicted_range.get("min", 0)
            pred_max = predicted_range.get("max", available_slots)
            reasons.append(f"Strong predicted availability ({pred_min}–{pred_max} spaces expected)")

        if score_price >= 60.0:
            reasons.append(f"Economical rate at Rs. {price_per_hour:.0f}/hour")
        elif score_price >= 40.0:
            reasons.append(f"Fair pricing at Rs. {price_per_hour:.0f}/hour")

        if score_dist >= 60.0:
            reasons.append(f"Close proximity ({distance_meters} m away)")

        if score_walk >= 60.0:
            reasons.append(f"Short walking distance (~{walking_meters} m)")

        # Fallback if no specific threshold was crossed
        if not reasons:
            reasons.append("Balanced combination of distance, pricing, and availability")

        return reasons

    def rank_parking_lots(
        self,
        parking_lots,
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        dest_lat: Optional[float] = None,
        dest_lon: Optional[float] = None,
        max_distance_km: float = DEFAULT_MAX_DISTANCE_KM,
        max_price: Optional[float] = None,
        min_slots: Optional[int] = None,
        avg_duration: float = 60.0,
        has_event: bool = False,
        is_holiday: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluate and rank all candidate parking lots.
        Returns top recommendation and ranked list.
        """
        candidate_lots = list(parking_lots)
        if not candidate_lots:
            return {
                "recommended_parking": None,
                "recommendations": [],
                "weights_used": {
                    "current_availability": self.weights.current_availability,
                    "predicted_availability": self.weights.predicted_availability,
                    "distance": self.weights.distance,
                    "price": self.weights.price,
                    "walking_distance": self.weights.walking_distance,
                },
                "total_evaluated": 0,
            }

        # Dynamically calibrate max reference price from pool if not specified
        if max_price is not None:
            ref_max_price = max(10.0, float(max_price))
        else:
            observed_max = max((float(lot.price_per_hour) for lot in candidate_lots), default=DEFAULT_MAX_PRICE_PER_HOUR)
            ref_max_price = max(DEFAULT_MAX_PRICE_PER_HOUR, observed_max)

        scored_candidates = []
        for lot in candidate_lots:
            # Apply optional min_slots filter
            if min_slots is not None and lot.available_slots < int(min_slots):
                continue

            # Apply optional max_price filter
            if max_price is not None and float(lot.price_per_hour) > float(max_price):
                continue

            evaluated = self.evaluate_candidate(

                lot=lot,
                user_lat=user_lat,
                user_lon=user_lon,
                dest_lat=dest_lat,
                dest_lon=dest_lon,
                max_distance_km=max_distance_km,
                max_price=ref_max_price,
                avg_duration=avg_duration,
                has_event=has_event,
                is_holiday=is_holiday,
            )

            # Apply hard distance filter if requested
            if max_distance_km and evaluated["distance_km"] > max_distance_km:
                continue

            scored_candidates.append(evaluated)

        # Sort descending by final score, secondary key: available slots descending, tertiary: distance ascending
        scored_candidates.sort(
            key=lambda item: (
                item["score"],
                item["available_slots"],
                -item["distance_meters"]
            ),
            reverse=True
        )

        recommended = scored_candidates[0] if scored_candidates else None

        return {
            "recommended_parking": recommended,
            "recommendations": scored_candidates,
            "weights_used": {
                "current_availability": self.weights.current_availability,
                "predicted_availability": self.weights.predicted_availability,
                "distance": self.weights.distance,
                "price": self.weights.price,
                "walking_distance": self.weights.walking_distance,
            },
            "total_evaluated": len(scored_candidates),
        }


def get_parking_recommendations(
    parking_lots,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    dest_lat: Optional[float] = None,
    dest_lon: Optional[float] = None,
    max_distance_km: float = DEFAULT_MAX_DISTANCE_KM,
    max_price: Optional[float] = None,
    min_slots: Optional[int] = None,
    avg_duration: float = 60.0,
    has_event: bool = False,
    is_holiday: bool = False,
    weights: Optional[RecommendationWeights] = None,
) -> Dict[str, Any]:
    """
    Convenience function for scoring and ranking parking lots.
    """
    service = RecommendationScoringService(weights=weights)
    return service.rank_parking_lots(
        parking_lots=parking_lots,
        user_lat=user_lat,
        user_lon=user_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
        max_distance_km=max_distance_km,
        max_price=max_price,
        min_slots=min_slots,
        avg_duration=avg_duration,
        has_event=has_event,
        is_holiday=is_holiday,
    )





