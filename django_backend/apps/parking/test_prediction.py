"""
Django Tests for ML-Based Parking Availability Prediction API (Day 05).
"""

import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import UserProfile, UserRole
from apps.parking.models import ParkingLot, ParkingSlot, SlotStatus

User = get_user_model()


class ParkingPredictionAPITest(TestCase):
    """Test suite for /api/parking/<id>/prediction/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.provider = User.objects.create_user(
            username="provider_day05",
            email="provider05@example.com",
            password="Password123!",
        )
        UserProfile.objects.create(
            user=self.provider,
            role=UserRole.PARKING_PROVIDER,
            phone_number="0771234567",
        )
        # Create a sample parking lot with 50 slots
        self.lot = ParkingLot.objects.create(
            owner=self.provider,
            name="Downtown Grand Plaza",
            address="100 Innovation Way",
            latitude=Decimal("6.9271"),
            longitude=Decimal("79.8612"),
            total_slots=50,
            available_slots=5,
            price_per_hour=Decimal("120.00"),
            opening_time=datetime.time(6, 0),
            closing_time=datetime.time(23, 0),
        )
        self.lot.generate_default_slots()

    def test_prediction_endpoint_get_success(self):
        """Test GET /api/parking/<id>/prediction/ returns 200 with complete payload."""
        url = reverse("parking:api_prediction", kwargs={"pk": self.lot.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data["parking_id"], self.lot.pk)
        self.assertEqual(data["parking_name"], self.lot.name)
        self.assertEqual(data["total_slots"], 50)
        self.assertEqual(data["prediction_minutes"], 20)
        self.assertIn("target_time", data)
        self.assertIn("target_day", data)
        self.assertIn("predicted_available", data)
        self.assertIn("predicted_range", data)
        self.assertIn("confidence", data)
        self.assertIn("status", data)
        self.assertIn("warning_level", data)
        self.assertIn("warning_message", data)
        self.assertIn("factors", data)

        # Bounds check
        self.assertTrue(0 <= data["predicted_available"] <= 50)
        self.assertTrue(
            0 <= data["predicted_range"]["min"] <= data["predicted_range"]["max"] <= 50
        )
        self.assertIn(data["confidence"], ["High", "Medium", "Low"])
        self.assertIn(data["warning_level"], ["red", "yellow", "green"])

    def test_prediction_endpoint_post_with_context(self):
        """Test POST /api/parking/<id>/prediction/ with event and holiday parameters."""
        url = reverse("parking:api_prediction", kwargs={"pk": self.lot.pk})
        payload = {
            "has_event": True,
            "is_holiday": False,
            "avg_duration": 45.0,
        }
        response = self.client.post(url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["parking_id"], self.lot.pk)
        self.assertTrue(0 <= data["predicted_available"] <= 50)

    def test_prediction_invalid_parking_id(self):
        """Test prediction endpoint with non-existent parking lot ID returns 404."""
        url = reverse("parking:api_prediction", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_prediction_respects_custom_capacity(self):
        """Test prediction bounds properly clamp to smaller/larger parking lot capacities."""
        small_lot = ParkingLot.objects.create(
            owner=self.provider,
            name="Small Harbor Bay",
            address="12 Coastal Road",
            latitude=Decimal("6.9300"),
            longitude=Decimal("79.8500"),
            total_slots=20,
            available_slots=2,
            price_per_hour=Decimal("100.00"),
            opening_time=datetime.time(7, 0),
            closing_time=datetime.time(21, 0),
        )
        small_lot.generate_default_slots()

        url = reverse("parking:api_prediction", kwargs={"pk": small_lot.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_slots"], 20)
        self.assertTrue(0 <= response.data["predicted_available"] <= 20)
        self.assertTrue(response.data["predicted_range"]["max"] <= 20)

    def test_prediction_factors_populated(self):
        """Test explanation factors list is non-empty and contains descriptive text."""
        url = reverse("parking:api_prediction", kwargs={"pk": self.lot.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        factors = response.data["factors"]
        self.assertIsInstance(factors, list)
        self.assertGreater(len(factors), 0)
