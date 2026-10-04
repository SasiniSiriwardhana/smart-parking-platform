"""
Day 03 — Parking App Tests.

Comprehensive test coverage for:
- ParkingLot Model & properties
- Haversine distance calculation and formatting
- Serializers (List & Detail)
- DRF API Views (List, Detail, Create, Provider My Lots, Filters)
- Django Template Views (Finder, Detail, Provider List, Create)
"""
import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import UserProfile, UserRole
from apps.parking.models import ParkingLot
from apps.parking.serializers import ParkingLotListSerializer, ParkingLotSerializer
from apps.parking.utils import haversine_distance, format_distance

User = get_user_model()


class ParkingLotModelTest(TestCase):
    """Test ParkingLot model attributes, properties, and validations."""

    def setUp(self):
        self.provider_user = User.objects.create_user(
            username='provider1',
            email='provider1@example.com',
            password='Password123!'
        )
        self.provider_profile = UserProfile.objects.create(
            user=self.provider_user,
            role=UserRole.PARKING_PROVIDER,
            phone_number='1234567890'
        )
        self.lot = ParkingLot.objects.create(
            name='Central Plaza Parking',
            address='123 Main Street, Downtown',
            latitude=Decimal('6.9271000'),
            longitude=Decimal('79.8612000'),
            total_slots=100,
            available_slots=40,
            price_per_hour=Decimal('150.00'),
            opening_time=datetime.time(6, 0),
            closing_time=datetime.time(22, 0),
            owner=self.provider_user,
        )

    def test_parking_lot_creation(self):
        """Test parking lot fields are stored correctly."""
        self.assertEqual(self.lot.name, 'Central Plaza Parking')
        self.assertEqual(self.lot.total_slots, 100)
        self.assertEqual(self.lot.available_slots, 40)
        self.assertEqual(self.lot.price_per_hour, Decimal('150.00'))
        self.assertEqual(str(self.lot), 'Central Plaza Parking (40/100 available)')

    def test_occupancy_rate_calculation(self):
        """Occupancy rate should calculate correctly."""
        # 100 total, 40 available => 60 occupied => 60.0%
        self.assertEqual(self.lot.occupancy_rate, 60.0)

    def test_occupancy_rate_zero_total_slots(self):
        """Occupancy rate handles zero total slots gracefully."""
        lot = ParkingLot(
            name='Empty',
            address='Test',
            latitude=Decimal('6.9'),
            longitude=Decimal('79.8'),
            total_slots=0,
            available_slots=0,
            price_per_hour=Decimal('10.00'),
            opening_time=datetime.time(6, 0),
            closing_time=datetime.time(22, 0),
            owner=self.provider_user
        )
        self.assertEqual(lot.occupancy_rate, 0.0)

    def test_is_full_and_is_available_properties(self):
        """Check is_full and is_available flags."""
        self.assertFalse(self.lot.is_full)
        self.assertTrue(self.lot.is_available)

        self.lot.available_slots = 0
        self.lot.save()
        self.assertTrue(self.lot.is_full)
        self.assertFalse(self.lot.is_available)

    def test_available_slots_cannot_exceed_total(self):
        """available_slots > total_slots should raise ValidationError."""
        lot = ParkingLot(
            name='Invalid Lot',
            address='456 Test Ave',
            latitude=Decimal('6.9000000'),
            longitude=Decimal('79.8000000'),
            total_slots=50,
            available_slots=60,
            price_per_hour=Decimal('100.00'),
            opening_time=datetime.time(6, 0),
            closing_time=datetime.time(22, 0),
            owner=self.provider_user
        )
        with self.assertRaises(ValidationError):
            lot.full_clean()


class HaversineUtilsTest(TestCase):
    """Test Haversine distance formula and format_distance utility."""

    def test_haversine_distance_known_points(self):
        """Test distance between Colombo Fort (6.9344, 79.8428) and Bambalapitiya (6.8920, 79.8550)."""
        dist = haversine_distance(6.9344, 79.8428, 6.8920, 79.8550)
        # Expected is around 4.9 km
        self.assertAlmostEqual(dist, 4.9, delta=0.5)

    def test_haversine_distance_same_point(self):
        """Distance to same coordinate should be 0.0."""
        dist = haversine_distance(6.9271, 79.8612, 6.9271, 79.8612)
        self.assertEqual(dist, 0.0)

    def test_format_distance(self):
        """Format distance returns meters when <1km, kilometers when >=1km."""
        self.assertEqual(format_distance(0.45), '450 m')
        self.assertEqual(format_distance(2.35), '2.4 km')
        self.assertEqual(format_distance(10.0), '10.0 km')


class ParkingLotSerializerTest(TestCase):
    """Test ParkingLot serializers."""

    def setUp(self):
        self.provider = User.objects.create_user(
            username='provider2',
            email='provider2@example.com',
            password='Password123!'
        )
        UserProfile.objects.create(user=self.provider, role=UserRole.PARKING_PROVIDER)
        self.lot = ParkingLot.objects.create(
            name='Metro Hub',
            address='77 Galle Road',
            latitude=Decimal('6.9000000'),
            longitude=Decimal('79.8500000'),
            total_slots=80,
            available_slots=25,
            price_per_hour=Decimal('200.00'),
            opening_time=datetime.time(7, 0),
            closing_time=datetime.time(23, 0),
            owner=self.provider,
        )

    def test_list_serializer_fields(self):
        """Verify fields in ParkingLotListSerializer."""
        serializer = ParkingLotListSerializer(self.lot)
        data = serializer.data
        self.assertEqual(data['id'], self.lot.id)
        self.assertEqual(data['name'], 'Metro Hub')
        self.assertEqual(data['total_slots'], 80)
        self.assertEqual(data['available_slots'], 25)
        self.assertEqual(data['occupancy_percentage'], 68.8)
        self.assertEqual(data['owner_username'], 'provider2')

    def test_detail_serializer_validation(self):
        """Verify ParkingLotSerializer deserialization validation."""
        valid_data = {
            'name': 'City Center Park',
            'address': '55 Union Place',
            'latitude': '6.9150000',
            'longitude': '79.8600000',
            'total_slots': 50,
            'available_slots': 50,
            'price_per_hour': '120.00',
            'opening_time': '06:00:00',
            'closing_time': '22:00:00',
        }
        serializer = ParkingLotSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_detail_serializer_invalid_slots(self):
        """available_slots > total_slots should trigger serializer error."""
        invalid_data = {
            'name': 'Bad Slots Park',
            'address': '55 Union Place',
            'latitude': '6.9150000',
            'longitude': '79.8600000',
            'total_slots': 20,
            'available_slots': 30,
            'price_per_hour': '120.00',
            'opening_time': '06:00:00',
            'closing_time': '22:00:00',
        }
        serializer = ParkingLotSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('available_slots', serializer.errors)


class ParkingAPITestCase(TestCase):
    """Test DRF Parking API endpoints: List, Detail, Create, Provider My Lots."""

    def setUp(self):
        self.client = APIClient()
        self.provider = User.objects.create_user(
            username='provider_api',
            email='provider_api@example.com',
            password='Password123!'
        )
        UserProfile.objects.create(user=self.provider, role=UserRole.PARKING_PROVIDER)

        self.customer = User.objects.create_user(
            username='customer_api',
            email='customer_api@example.com',
            password='Password123!'
        )
        UserProfile.objects.create(user=self.customer, role=UserRole.CUSTOMER)

        self.lot1 = ParkingLot.objects.create(
            name='Alpha Parking',
            address='10 Alpha Way',
            latitude=Decimal('6.9200000'),
            longitude=Decimal('79.8600000'),
            total_slots=100,
            available_slots=50,
            price_per_hour=Decimal('100.00'),
            opening_time=datetime.time(6, 0),
            closing_time=datetime.time(22, 0),
            owner=self.provider,
        )
        self.lot2 = ParkingLot.objects.create(
            name='Beta Express Parking',
            address='20 Beta Road',
            latitude=Decimal('6.9300000'),
            longitude=Decimal('79.8700000'),
            total_slots=50,
            available_slots=5,
            price_per_hour=Decimal('250.00'),
            opening_time=datetime.time(8, 0),
            closing_time=datetime.time(20, 0),
            owner=self.provider,
        )

    def test_api_list_all_lots(self):
        """GET /api/parking/ returns 200 and list of lots."""
        url = reverse('parking:api_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_api_list_filter_search(self):
        """Search query ?q=Alpha should return only Alpha Parking."""
        url = reverse('parking:api_list')
        response = self.client.get(url, {'q': 'Alpha'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Alpha Parking')

    def test_api_list_filter_price(self):
        """Filter max_price=150 should only return Alpha Parking."""
        url = reverse('parking:api_list')
        response = self.client.get(url, {'max_price': '150'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Alpha Parking')

    def test_api_list_filter_min_slots(self):
        """Filter min_slots=20 should exclude lot2 (only 5 slots available)."""
        url = reverse('parking:api_list')
        response = self.client.get(url, {'min_slots': '20'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Alpha Parking')

    def test_api_list_with_lat_lon_distance(self):
        """Providing lat/lon returns distance in responses."""
        url = reverse('parking:api_list')
        response = self.client.get(url, {'lat': '6.9200', 'lon': '79.8600'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('distance_km', response.data[0])
        # Lot 1 is at 6.9200, 79.8600 so distance is 0.0
        self.assertEqual(response.data[0]['distance_km'], 0.0)

    def test_api_detail(self):
        """GET /api/parking/<id>/ returns parking lot details."""
        url = reverse('parking:api_detail', kwargs={'pk': self.lot1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Alpha Parking')

    def test_api_detail_not_found(self):
        """GET /api/parking/99999/ returns 404."""
        url = reverse('parking:api_detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_create_unauthenticated_forbidden(self):
        """Anonymous user cannot create a parking lot."""
        url = reverse('parking:api_create')
        data = {'name': 'Unauthorized Lot', 'total_slots': 50}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_create_customer_forbidden(self):
        """Customer cannot create a parking lot (403 Forbidden)."""
        self.client.force_authenticate(user=self.customer)
        url = reverse('parking:api_create')
        data = {
            'name': 'Customer Park',
            'address': 'Test Road',
            'latitude': '6.9200000',
            'longitude': '79.8600000',
            'total_slots': 30,
            'available_slots': 30,
            'price_per_hour': '100.00',
            'opening_time': '06:00:00',
            'closing_time': '22:00:00'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_create_provider_success(self):
        """Parking provider can create a parking lot."""
        self.client.force_authenticate(user=self.provider)
        url = reverse('parking:api_create')
        data = {
            'name': 'Provider New Lot',
            'address': '99 New Ave',
            'latitude': '6.9123000',
            'longitude': '79.8567000',
            'total_slots': 45,
            'available_slots': 45,
            'price_per_hour': '180.00',
            'opening_time': '06:00:00',
            'closing_time': '22:00:00'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Provider New Lot')
        self.assertTrue(ParkingLot.objects.filter(name='Provider New Lot').exists())

    def test_api_provider_my_lots(self):
        """GET /api/parking/my/ returns only the provider's owned lots."""
        self.client.force_authenticate(user=self.provider)
        url = reverse('parking:api_my')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class ParkingTemplateViewsTest(TestCase):
    """Test Django HTML Template views."""

    def setUp(self):
        self.client = Client()
        self.provider = User.objects.create_user(
            username='provider_tmpl',
            email='provider_tmpl@example.com',
            password='Password123!'
        )
        UserProfile.objects.create(user=self.provider, role=UserRole.PARKING_PROVIDER)

        self.lot = ParkingLot.objects.create(
            name='Seaside Parking',
            address='1 Marine Drive',
            latitude=Decimal('6.9300000'),
            longitude=Decimal('79.8400000'),
            total_slots=60,
            available_slots=30,
            price_per_hour=Decimal('120.00'),
            opening_time=datetime.time(6, 0),
            closing_time=datetime.time(22, 0),
            owner=self.provider,
        )

    def test_parking_finder_view_accessible(self):
        """GET /parking/ renders the finder page with Leaflet map."""
        url = reverse('parking:finder')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'parking/parking_finder.html')
        self.assertContains(response, 'Seaside Parking')

    def test_parking_detail_view_accessible(self):
        """GET /parking/<id>/ renders parking detail page."""
        url = reverse('parking:detail', kwargs={'pk': self.lot.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'parking/parking_detail.html')
        self.assertContains(response, 'Seaside Parking')
        self.assertContains(response, '1 Marine Drive')

    def test_provider_parking_list_requires_login(self):
        """GET /parking/manage/ redirects anonymous user to login."""
        url = reverse('parking:provider_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_provider_parking_list_accessible_to_provider(self):
        """GET /parking/manage/ accessible when logged in as provider."""
        self.client.login(username='provider_tmpl', password='Password123!')
        url = reverse('parking:provider_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'parking/provider_parking_list.html')
        self.assertContains(response, 'Seaside Parking')

    def test_parking_create_post_success(self):
        """POST /parking/create/ creates a new parking lot."""
        self.client.login(username='provider_tmpl', password='Password123!')
        url = reverse('parking:create')
        post_data = {
            'name': 'Galle Face Green Park',
            'address': 'Galle Face, Colombo',
            'latitude': '6.9244000',
            'longitude': '79.8443000',
            'total_slots': '75',
            'available_slots': '75',
            'price_per_hour': '150.00',
            'opening_time': '06:00',
            'closing_time': '22:00'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ParkingLot.objects.filter(name='Galle Face Green Park').exists())


# ══════════════════════════════════════════════════════════════════════════════
#  Day 04: Real-Time Parking Availability & WebSockets Test Suite
# ══════════════════════════════════════════════════════════════════════════════

from channels.testing import WebsocketCommunicator
from config.asgi import application
from apps.parking.models import ParkingSlot, SlotStatus


class Day04RealTimeAvailabilityTest(TestCase):
    """
    Comprehensive tests for Day 04:
    - ParkingSlot model & status choices
    - Dynamic occupancy & availability calculations
    - Simulated car entry & exit logic
    - Edge cases (full parking, empty parking)
    - REST API endpoints for availability and simulation
    - Provider & Customer authorization enforcement
    - WebSocket consumers & live broadcasts
    """

    def setUp(self):
        # 1. Provider 1
        self.provider = User.objects.create_user(
            username='provider_d4',
            email='provider_d4@example.com',
            password='Password123!'
        )
        UserProfile.objects.create(
            user=self.provider,
            role=UserRole.PARKING_PROVIDER,
            phone_number='0771234567'
        )

        # 2. Provider 2 (other provider)
        self.other_provider = User.objects.create_user(
            username='other_provider_d4',
            email='other_d4@example.com',
            password='Password123!'
        )
        UserProfile.objects.create(
            user=self.other_provider,
            role=UserRole.PARKING_PROVIDER,
            phone_number='0777654321'
        )

        # 3. Customer
        self.customer = User.objects.create_user(
            username='customer_d4',
            email='customer_d4@example.com',
            password='Password123!'
        )
        UserProfile.objects.create(
            user=self.customer,
            role=UserRole.CUSTOMER,
            phone_number='0779998888'
        )

        # 4. Parking Lot: Total = 5, initial available = 3 (2 occupied)
        self.lot = ParkingLot.objects.create(
            owner=self.provider,
            name='Day 04 Test Plaza',
            address='100 Tech Park, Colombo 03',
            latitude=Decimal('6.9200000'),
            longitude=Decimal('79.8600000'),
            total_slots=5,
            available_slots=3,
            price_per_hour=Decimal('100.00'),
            opening_time=datetime.time(6, 0),
            closing_time=datetime.time(22, 0)
        )
        self.lot.generate_default_slots()

        self.api_client = APIClient()

    # 1. Parking slot creation
    def test_parking_slot_creation(self):
        """ParkingSlot instances are created with proper attributes."""
        slot = self.lot.slots.first()
        self.assertIsNotNone(slot)
        self.assertEqual(slot.parking_lot, self.lot)
        self.assertTrue(slot.slot_number.startswith('A'))
        self.assertIn(slot.status, [SlotStatus.AVAILABLE, SlotStatus.OCCUPIED])

    # 2. Slot status AVAILABLE property and methods
    def test_slot_status_available(self):
        """Slot is_available returns True and is_occupied returns False for AVAILABLE slot."""
        slot = self.lot.slots.filter(status=SlotStatus.AVAILABLE).first()
        self.assertIsNotNone(slot)
        self.assertTrue(slot.is_available)
        self.assertFalse(slot.is_occupied)

    # 3. Slot status OCCUPIED property and methods
    def test_slot_status_occupied(self):
        """Slot is_occupied returns True and is_available returns False for OCCUPIED slot."""
        slot = self.lot.slots.filter(status=SlotStatus.OCCUPIED).first()
        self.assertIsNotNone(slot)
        self.assertTrue(slot.is_occupied)
        self.assertFalse(slot.is_available)

    # 4. Occupancy count calculation
    def test_occupied_count_calculation(self):
        """Occupied slots count equals number of slots with OCCUPIED status."""
        occupied_count = self.lot.slots.filter(status=SlotStatus.OCCUPIED).count()
        self.assertEqual(self.lot.occupied_slots, 2)
        self.assertEqual(self.lot.occupied_slots, occupied_count)

    # 5. Available count calculation
    def test_available_count_calculation(self):
        """Available slots count equals number of slots with AVAILABLE status."""
        available_count = self.lot.slots.filter(status=SlotStatus.AVAILABLE).count()
        self.assertEqual(self.lot.available_slots, 3)
        self.assertEqual(self.lot.available_slots, available_count)

    # 6. Total = Occupied + Available
    def test_total_slots_equals_occupied_plus_available(self):
        """The invariant Total = Occupied + Available must always hold."""
        self.assertEqual(
            self.lot.total_slots,
            self.lot.occupied_slots + self.lot.available_slots
        )

    # 7. Car entry changes AVAILABLE -> OCCUPIED
    def test_car_entry_changes_slot_to_occupied(self):
        """Simulating car entry flips first available slot to OCCUPIED and updates count."""
        initial_avail = self.lot.available_slots
        initial_occ = self.lot.occupied_slots

        success, msg, slot = self.lot.simulate_car_entry()
        self.assertTrue(success)
        self.assertIsNotNone(slot)
        self.assertEqual(slot.status, SlotStatus.OCCUPIED)

        self.assertEqual(self.lot.available_slots, initial_avail - 1)
        self.assertEqual(self.lot.occupied_slots, initial_occ + 1)

    # 8. Car exit changes OCCUPIED -> AVAILABLE
    def test_car_exit_changes_slot_to_available(self):
        """Simulating car exit flips an occupied slot to AVAILABLE and updates count."""
        initial_avail = self.lot.available_slots
        initial_occ = self.lot.occupied_slots

        success, msg, slot = self.lot.simulate_car_exit()
        self.assertTrue(success)
        self.assertIsNotNone(slot)
        self.assertEqual(slot.status, SlotStatus.AVAILABLE)

        self.assertEqual(self.lot.available_slots, initial_avail + 1)
        self.assertEqual(self.lot.occupied_slots, initial_occ - 1)

    # 9. Car entry when parking is full
    def test_car_entry_when_full(self):
        """Car entry on a full parking lot returns False and 'Parking is full.'"""
        # Fill all slots
        for s in self.lot.slots.all():
            s.occupy()
        self.lot.sync_slot_counts()

        self.assertEqual(self.lot.available_slots, 0)
        self.assertTrue(self.lot.is_full)

        success, msg, slot = self.lot.simulate_car_entry()
        self.assertFalse(success)
        self.assertEqual(msg, "Parking is full.")
        self.assertIsNone(slot)
        self.assertEqual(self.lot.available_slots, 0)

    # 10. Car exit when no occupied slots
    def test_car_exit_when_no_occupied_slots(self):
        """Car exit on an empty parking lot returns False and 'No occupied slots available.'"""
        # Vacate all slots
        for s in self.lot.slots.all():
            s.vacate()
        self.lot.sync_slot_counts()

        self.assertEqual(self.lot.occupied_slots, 0)

        success, msg, slot = self.lot.simulate_car_exit()
        self.assertFalse(success)
        self.assertEqual(msg, "No occupied slots available.")
        self.assertIsNone(slot)
        self.assertEqual(self.lot.occupied_slots, 0)

    # 11. Unauthorized availability modification (Customer forbidden)
    def test_unauthorized_customer_cannot_simulate_entry(self):
        """Customers cannot trigger simulation endpoints (403 Forbidden)."""
        self.api_client.force_authenticate(user=self.customer)
        url = reverse('parking:api_simulate_entry', kwargs={'pk': self.lot.pk})
        response = self.api_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 12. Provider authorization (Cannot simulate other provider's lot)
    def test_provider_cannot_simulate_other_provider_lot(self):
        """A provider cannot trigger simulation for another provider's parking lot (403 Forbidden)."""
        self.api_client.force_authenticate(user=self.other_provider)
        url = reverse('parking:api_simulate_entry', kwargs={'pk': self.lot.pk})
        response = self.api_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 13. Availability API
    def test_availability_api_endpoint(self):
        """GET /api/parking/<id>/availability/ returns current status summary."""
        url = reverse('parking:api_availability', kwargs={'pk': self.lot.pk})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['parking_id'], self.lot.pk)
        self.assertEqual(response.data['total_slots'], 5)
        self.assertEqual(response.data['available_slots'], 3)
        self.assertEqual(response.data['occupied_slots'], 2)

    # 14. Provider simulation entry via API
    def test_provider_simulate_entry_api_success(self):
        """Owner can simulate car entry via POST /api/parking/<id>/simulate-entry/."""
        self.api_client.force_authenticate(user=self.provider)
        url = reverse('parking:api_simulate_entry', kwargs={'pk': self.lot.pk})
        response = self.api_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['availability']['available_slots'], 2)
        self.assertEqual(response.data['availability']['occupied_slots'], 3)

    # 15. Provider simulation exit via API
    def test_provider_simulate_exit_api_success(self):
        """Owner can simulate car exit via POST /api/parking/<id>/simulate-exit/."""
        self.api_client.force_authenticate(user=self.provider)
        url = reverse('parking:api_simulate_exit', kwargs={'pk': self.lot.pk})
        response = self.api_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['availability']['available_slots'], 4)
        self.assertEqual(response.data['availability']['occupied_slots'], 1)

    # 16. Slots API endpoint
    def test_slots_api_endpoint(self):
        """GET /api/parking/<id>/slots/ returns individual slot records."""
        url = reverse('parking:api_slots', kwargs={'pk': self.lot.pk})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['slots']), 5)

    # 17. WebSocket connection & initial snapshot
    async def test_websocket_availability_connection(self):
        """WebSocket client connects and receives initial availability snapshot."""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/parking/{self.lot.pk}/availability/"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # First message should be the initial snapshot
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'availability_snapshot')
        self.assertEqual(response['data']['parking_id'], self.lot.pk)
        self.assertEqual(response['data']['total_slots'], 5)
        self.assertEqual(len(response['data']['slots']), 5)

        await communicator.disconnect()

    # 18. WebSocket rejects non-existent parking lot
    async def test_websocket_invalid_parking_id(self):
        """WebSocket connection with invalid parking lot ID closes with 4004."""
        communicator = WebsocketCommunicator(
            application,
            "/ws/parking/999999/availability/"
        )
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4004)

