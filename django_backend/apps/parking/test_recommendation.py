"""
Day 06 Unit and Integration Tests — Smart Parking Recommendation Engine.
"""
from datetime import time
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import UserProfile, UserRole
from apps.parking.models import ParkingLot, ParkingSlot, SlotStatus
from apps.parking.recommendation import (
    RecommendationScoringService,
    RecommendationWeights,
    get_parking_recommendations,
)


class RecommendationScoringUnitTests(TestCase):
    """
    Test recommendation factor normalizations, weights, and ranking formulas independently.
    """

    def setUp(self):
        self.service = RecommendationScoringService()

    def test_default_weights_sum_to_one(self):
        """Default weights must sum to exactly 1.0 (100%)."""
        w = self.service.weights
        total = (
            w.current_availability
            + w.predicted_availability
            + w.distance
            + w.price
            + w.walking_distance
        )
        self.assertAlmostEqual(total, 1.0, places=4)
        self.assertEqual(w.current_availability, 0.25)
        self.assertEqual(w.predicted_availability, 0.30)
        self.assertEqual(w.distance, 0.20)
        self.assertEqual(w.price, 0.15)
        self.assertEqual(w.walking_distance, 0.10)

    def test_custom_weights_validation(self):
        """Custom valid weights are accepted; invalid weights fallback to defaults."""
        custom = RecommendationWeights(0.2, 0.2, 0.2, 0.2, 0.2)
        service = RecommendationScoringService(weights=custom)
        self.assertTrue(service.weights.validate())

        invalid = RecommendationWeights(0.5, 0.5, 0.5, 0.5, 0.5)
        self.assertFalse(invalid.validate())
        service_invalid = RecommendationScoringService(weights=invalid)
        self.assertTrue(service_invalid.weights.validate())  # falls back to valid default

    def test_availability_normalization(self):
        """More available spaces = higher score (0–100 scale)."""
        # 100% capacity free -> 100
        self.assertEqual(RecommendationScoringService.normalize_availability_score(50, 50), 100.0)
        # 50% capacity free -> 50
        self.assertEqual(RecommendationScoringService.normalize_availability_score(25, 50), 50.0)
        # 0 capacity free -> 0
        self.assertEqual(RecommendationScoringService.normalize_availability_score(0, 50), 0.0)
        # 0 total slots -> 0
        self.assertEqual(RecommendationScoringService.normalize_availability_score(0, 0), 0.0)

    def test_predicted_availability_normalization(self):
        """More predicted available spaces = higher score (0–100 scale)."""
        self.assertEqual(RecommendationScoringService.normalize_predicted_availability_score(40, 50), 80.0)
        self.assertEqual(RecommendationScoringService.normalize_predicted_availability_score(0, 50), 0.0)
        self.assertEqual(RecommendationScoringService.normalize_predicted_availability_score(0, 0), 0.0)

    def test_distance_normalization(self):
        """Shorter distance = higher score (0–100 scale)."""
        # 0 km distance -> 100 score
        self.assertEqual(RecommendationScoringService.normalize_distance_score(0.0, max_distance_km=5.0), 100.0)
        # 2.5 km with 5 km max -> 50 score
        self.assertEqual(RecommendationScoringService.normalize_distance_score(2.5, max_distance_km=5.0), 50.0)
        # 5 km with 5 km max -> 0 score
        self.assertEqual(RecommendationScoringService.normalize_distance_score(5.0, max_distance_km=5.0), 0.0)
        # Beyond max distance -> 0 score (clamped)
        self.assertEqual(RecommendationScoringService.normalize_distance_score(8.0, max_distance_km=5.0), 0.0)

    def test_price_normalization(self):
        """Lower price = higher score (0–100 scale)."""
        # Free parking (Rs. 0) -> 100 score
        self.assertEqual(RecommendationScoringService.normalize_price_score(0.0, max_price=500.0), 100.0)
        # Rs. 250 with Rs. 500 max -> 50 score
        self.assertEqual(RecommendationScoringService.normalize_price_score(250.0, max_price=500.0), 50.0)
        # Rs. 500 with Rs. 500 max -> 0 score
        self.assertEqual(RecommendationScoringService.normalize_price_score(500.0, max_price=500.0), 0.0)
        # Higher than max -> 0 score (clamped)
        self.assertEqual(RecommendationScoringService.normalize_price_score(600.0, max_price=500.0), 0.0)

    def test_walking_distance_normalization(self):
        """Shorter walking distance = higher score (0–100 scale)."""
        self.assertEqual(RecommendationScoringService.normalize_walking_distance_score(0.0, max_walking_meters=2000.0), 100.0)
        self.assertEqual(RecommendationScoringService.normalize_walking_distance_score(1000.0, max_walking_meters=2000.0), 50.0)
        self.assertEqual(RecommendationScoringService.normalize_walking_distance_score(2000.0, max_walking_meters=2000.0), 0.0)
        self.assertEqual(RecommendationScoringService.normalize_walking_distance_score(3000.0, max_walking_meters=2000.0), 0.0)

    def test_empty_parking_lot_pool_handling(self):
        """Empty parking lot candidate list must return structured empty response without exceptions."""
        result = self.service.rank_parking_lots([])
        self.assertIsNone(result["recommended_parking"])
        self.assertEqual(result["recommendations"], [])
        self.assertEqual(result["total_evaluated"], 0)


class RecommendationIntegrationTests(TestCase):
    """
    Test end-to-end parking ranking comparing candidate locations with actual database models.
    """

    def setUp(self):
        self.client = APIClient()
        self.provider = User.objects.create_user(
            username='provider_rec',
            email='provider_rec@test.com',
            password='Password123!'
        )
        UserProfile.objects.create(
            user=self.provider,
            role=UserRole.PARKING_PROVIDER,
            phone_number='0771122334'
        )

        # Parking A: Distance 200m, Price Rs. 200, Available 2/50
        self.lot_a = ParkingLot.objects.create(
            owner=self.provider,
            name="Parking A",
            address="200 Colombo Road",
            latitude=Decimal("6.9275"),
            longitude=Decimal("79.8615"),
            total_slots=50,
            available_slots=2,
            price_per_hour=Decimal("200.00"),
            opening_time=time(6, 0),
            closing_time=time(23, 0),
        )

        # Parking B: Distance 450m, Price Rs. 100, Available 25/30
        self.lot_b = ParkingLot.objects.create(
            owner=self.provider,
            name="Parking B",
            address="450 Galle Road",
            latitude=Decimal("6.9300"),
            longitude=Decimal("79.8630"),
            total_slots=30,
            available_slots=25,
            price_per_hour=Decimal("100.00"),
            opening_time=time(6, 0),
            closing_time=time(23, 0),
        )

        # Parking C: Distance 700m, Price Rs. 150, Available 12/40
        self.lot_c = ParkingLot.objects.create(
            owner=self.provider,
            name="Parking C",
            address="700 Union Place",
            latitude=Decimal("6.9330"),
            longitude=Decimal("79.8650"),
            total_slots=40,
            available_slots=12,
            price_per_hour=Decimal("150.00"),
            opening_time=time(6, 0),
            closing_time=time(23, 0),
        )

    def test_parking_b_is_recommended_over_parking_a(self):
        """
        Parking B should rank higher than Parking A due to superior availability (25/30 vs 2/50)
        and lower hourly rate (Rs. 100 vs Rs. 200) despite slightly larger distance.
        """
        user_lat = 6.9270
        user_lon = 79.8610

        result = get_parking_recommendations(
            parking_lots=ParkingLot.objects.all(),
            user_lat=user_lat,
            user_lon=user_lon,
        )

        recommended = result["recommended_parking"]
        self.assertIsNotNone(recommended)
        self.assertEqual(recommended["id"], self.lot_b.id)
        self.assertEqual(recommended["name"], "Parking B")
        self.assertGreater(recommended["score"], 0)

        # Verify ranking order
        rankings = result["recommendations"]
        self.assertGreaterEqual(len(rankings), 3)
        self.assertEqual(rankings[0]["id"], self.lot_b.id)

    def test_recommendation_api_endpoint(self):
        """GET /api/parking/recommendations/ returns 200 OK with formatted JSON payload."""
        url = reverse('parking:api_recommendations')
        response = self.client.get(url, {
            'lat': '6.9270',
            'lon': '79.8610',
            'max_distance': '5.0',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('recommended_parking', data)
        self.assertIn('recommendations', data)
        self.assertIn('weights_used', data)
        self.assertEqual(data['total_evaluated'], 3)
        self.assertEqual(data['recommended_parking']['id'], self.lot_b.id)

    def test_recommendation_with_invalid_location_inputs(self):
        """Invalid non-numeric coords should be handled safely with defaults."""
        url = reverse('parking:api_recommendations')
        response = self.client.get(url, {
            'lat': 'invalid_lat',
            'lon': 'invalid_lon',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNotNone(data['recommended_parking'])

    def test_recommendation_price_filter(self):
        """Price filter should restrict eligible candidate lots."""
        url = reverse('parking:api_recommendations')
        response = self.client.get(url, {
            'lat': '6.9270',
            'lon': '79.8610',
            'max_price': '120',  # Only Parking B (Rs. 100) qualifies
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_evaluated'], 1)
        self.assertEqual(data['recommended_parking']['name'], 'Parking B')

    def test_explainability_reasons_presence(self):
        """Recommendation response should include explainability reasons."""
        result = get_parking_recommendations(
            parking_lots=ParkingLot.objects.all(),
            user_lat=6.9270,
            user_lon=79.8610,
        )
        rec = result["recommended_parking"]
        self.assertIn("reasons", rec)
        self.assertIsInstance(rec["reasons"], list)
        self.assertGreater(len(rec["reasons"]), 0)
