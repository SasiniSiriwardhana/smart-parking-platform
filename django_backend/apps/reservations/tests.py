"""
Day 06 Tests — Parking Reservation Engine & Conflict Prevention.
"""
from datetime import date, time, timedelta
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import UserProfile, UserRole
from apps.parking.models import ParkingLot, ParkingSlot, SlotStatus
from apps.reservations.models import Reservation, ReservationStatus
from apps.reservations.services import (
    create_reservation,
    cancel_reservation,
    check_slot_conflict,
    validate_reservation_times,
    ReservationValidationError,
    SlotConflictError,
    NoAvailableSlotError,
)


class ReservationModelAndServiceTests(TestCase):
    """
    Unit tests for Reservation model, validation, slot assignment, and conflict prevention logic.
    """

    def setUp(self):
        # 1. Provider
        self.provider = User.objects.create_user(
            username='provider_res',
            email='provider_res@test.com',
            password='Password123!'
        )
        UserProfile.objects.create(
            user=self.provider,
            role=UserRole.PARKING_PROVIDER,
            phone_number='0771234567'
        )

        # 2. Customer
        self.customer1 = User.objects.create_user(
            username='customer_one',
            email='customer_one@test.com',
            password='Password123!'
        )
        UserProfile.objects.create(
            user=self.customer1,
            role=UserRole.CUSTOMER,
            phone_number='0779998881'
        )

        # 3. Customer 2
        self.customer2 = User.objects.create_user(
            username='customer_two',
            email='customer_two@test.com',
            password='Password123!'
        )
        UserProfile.objects.create(
            user=self.customer2,
            role=UserRole.CUSTOMER,
            phone_number='0779998882'
        )

        # 4. Parking Lot with capacity 2 (Slots A01, A02)
        self.lot = ParkingLot.objects.create(
            owner=self.provider,
            name="City Centre Plaza",
            address="100 Main Street",
            latitude=Decimal("6.9271"),
            longitude=Decimal("79.8612"),
            total_slots=2,
            available_slots=2,
            price_per_hour=Decimal("150.00"),
            opening_time=time(6, 0),
            closing_time=time(23, 0),
        )
        self.lot.generate_default_slots()

    def test_reservation_end_time_and_timestamps_calculation(self):
        """End time and timezone-aware timestamps must be calculated accurately from duration."""
        target_date = timezone.localdate() + timedelta(days=2)
        start_t = time(14, 0)  # 2:00 PM
        duration = 2           # 2 hours

        res = create_reservation(
            user=self.customer1,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=start_t,
            duration=duration,
        )

        self.assertEqual(res.status, ReservationStatus.CONFIRMED)
        self.assertEqual(res.end_time, time(16, 0))  # 4:00 PM
        self.assertEqual(res.duration, 2)
        self.assertEqual(res.parking_slot.slot_number, 'A01')
        self.assertIsNotNone(res.start_datetime)
        self.assertIsNotNone(res.end_datetime)
        self.assertEqual(res.end_datetime - res.start_datetime, timedelta(hours=2))

    def test_slot_assigned_automatically(self):
        """First available slot in the lot must be automatically allocated."""
        target_date = timezone.localdate() + timedelta(days=2)
        
        res1 = create_reservation(
            user=self.customer1,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=time(10, 0),
            duration=1,
        )
        self.assertEqual(res1.parking_slot.slot_number, 'A01')

        res2 = create_reservation(
            user=self.customer2,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=time(10, 0),
            duration=1,
        )
        self.assertEqual(res2.parking_slot.slot_number, 'A02')

    def test_overlapping_reservation_is_rejected_on_backend(self):
        """
        When all slots (A01 and A02) are booked for an overlapping time,
        a 3rd booking must be rejected with NoAvailableSlotError.
        """
        target_date = timezone.localdate() + timedelta(days=2)

        # Book slot 1 (A01): 2:00 PM - 4:00 PM
        create_reservation(
            user=self.customer1,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=time(14, 0),
            duration=2,
        )

        # Book slot 2 (A02): 2:00 PM - 4:00 PM
        create_reservation(
            user=self.customer2,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=time(14, 0),
            duration=2,
        )

        # 3rd user attempts overlapping booking: 3:00 PM - 5:00 PM (overlaps with 2:00-4:00)
        with self.assertRaises(NoAvailableSlotError):
            create_reservation(
                user=self.customer1,
                parking_lot=self.lot,
                reservation_date=target_date,
                start_time=time(15, 0),
                duration=2,
            )

    def test_non_overlapping_adjacent_reservation_is_allowed(self):
        """
        Adjacent bookings on boundary times (e.g. 2:00-4:00 PM and 4:00-6:00 PM)
        do not overlap and must be allowed for the same slot.
        """
        target_date = timezone.localdate() + timedelta(days=2)
        slot_a1 = self.lot.slots.get(slot_number='A01')

        # Existing: 2:00 PM - 4:00 PM
        res1 = create_reservation(
            user=self.customer1,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=time(14, 0),
            duration=2,
            preferred_slot_id=slot_a1.id,
        )
        self.assertEqual(res1.parking_slot, slot_a1)

        # New: 4:00 PM - 6:00 PM (adjacent boundary - no overlap)
        res2 = create_reservation(
            user=self.customer2,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=time(16, 0),
            duration=2,
            preferred_slot_id=slot_a1.id,
        )
        self.assertEqual(res2.parking_slot, slot_a1)

    def test_past_reservation_rejected(self):
        """Past reservation date/time must be rejected."""
        past_date = timezone.localdate() - timedelta(days=1)
        with self.assertRaises(ReservationValidationError):
            create_reservation(
                user=self.customer1,
                parking_lot=self.lot,
                reservation_date=past_date,
                start_time=time(10, 0),
                duration=1,
            )

    def test_invalid_duration_rejected(self):
        """Duration < 1 or > 24 hours must be rejected."""
        target_date = timezone.localdate() + timedelta(days=2)
        with self.assertRaises(ReservationValidationError):
            create_reservation(
                user=self.customer1,
                parking_lot=self.lot,
                reservation_date=target_date,
                start_time=time(10, 0),
                duration=0,
            )
        with self.assertRaises(ReservationValidationError):
            create_reservation(
                user=self.customer1,
                parking_lot=self.lot,
                reservation_date=target_date,
                start_time=time(10, 0),
                duration=25,
            )

    def test_cancel_reservation(self):
        """Customer can cancel their active reservation."""
        target_date = timezone.localdate() + timedelta(days=2)
        res = create_reservation(
            user=self.customer1,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=time(10, 0),
            duration=2,
        )
        self.assertEqual(res.status, ReservationStatus.CONFIRMED)

        cancelled = cancel_reservation(res, self.customer1)
        self.assertEqual(cancelled.status, ReservationStatus.CANCELLED)

        # Once cancelled, the slot becomes free for that time window again
        new_res = create_reservation(
            user=self.customer2,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=time(10, 0),
            duration=2,
            preferred_slot_id=res.parking_slot_id,
        )
        self.assertEqual(new_res.status, ReservationStatus.CONFIRMED)


class ReservationAPITests(TestCase):
    """
    Integration tests for DRF Reservation API endpoints and authorization rules.
    """

    def setUp(self):
        self.client = APIClient()

        # Customer 1
        self.customer1 = User.objects.create_user(
            username='api_cust1', email='cust1@test.com', password='Password123!'
        )
        UserProfile.objects.create(user=self.customer1, role=UserRole.CUSTOMER, phone_number='0771111111')

        # Customer 2
        self.customer2 = User.objects.create_user(
            username='api_cust2', email='cust2@test.com', password='Password123!'
        )
        UserProfile.objects.create(user=self.customer2, role=UserRole.CUSTOMER, phone_number='0772222222')

        # Provider
        self.provider = User.objects.create_user(
            username='api_prov', email='prov@test.com', password='Password123!'
        )
        UserProfile.objects.create(user=self.provider, role=UserRole.PARKING_PROVIDER, phone_number='0773333333')

        # Parking Lot (1 slot only to test conflict behavior via API)
        self.lot = ParkingLot.objects.create(
            owner=self.provider,
            name="Single Slot Garage",
            address="50 Lake Road",
            latitude=Decimal("6.9200"),
            longitude=Decimal("79.8600"),
            total_slots=1,
            available_slots=1,
            price_per_hour=Decimal("200.00"),
            opening_time=time(6, 0),
            closing_time=time(23, 0),
        )
        self.lot.generate_default_slots()

    def test_unauthenticated_user_cannot_reserve(self):
        """Unauthenticated POST to /api/reservations/ must return 401 Unauthorized."""
        url = reverse('reservations:api_list_create')
        response = self.client.post(url, {
            'parking_lot': self.lot.id,
            'reservation_date': str(timezone.localdate() + timedelta(days=2)),
            'start_time': '14:00',
            'duration': 2,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_customer_can_reserve(self):
        """Authenticated customer can create a reservation via API."""
        self.client.force_authenticate(user=self.customer1)
        url = reverse('reservations:api_list_create')
        target_date = str(timezone.localdate() + timedelta(days=2))

        response = self.client.post(url, {
            'parking_lot': self.lot.id,
            'reservation_date': target_date,
            'start_time': '14:00',
            'duration': 2,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('reservation', data)
        self.assertEqual(data['reservation']['parking_lot_name'], "Single Slot Garage")
        self.assertEqual(data['reservation']['slot_number'], "A01")
        self.assertEqual(data['reservation']['duration'], 2)
        self.assertEqual(data['reservation']['status'], "CONFIRMED")

    def test_api_rejects_overlapping_reservation(self):
        """API returns 400/409 when attempting to book an occupied slot time window."""
        self.client.force_authenticate(user=self.customer1)
        url = reverse('reservations:api_list_create')
        target_date = str(timezone.localdate() + timedelta(days=2))

        # Booking 1: 14:00 - 16:00
        res1 = self.client.post(url, {
            'parking_lot': self.lot.id,
            'reservation_date': target_date,
            'start_time': '14:00',
            'duration': 2,
        })
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Booking 2 from customer 2: 15:00 - 17:00 (overlaps)
        self.client.force_authenticate(user=self.customer2)
        res2 = self.client.post(url, {
            'parking_lot': self.lot.id,
            'reservation_date': target_date,
            'start_time': '15:00',
            'duration': 2,
        })
        self.assertIn(res2.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT])

    def test_customer_only_sees_own_reservations(self):
        """GET /api/reservations/ returns strictly current customer's bookings."""
        target_date = timezone.localdate() + timedelta(days=2)
        
        # Cust 1 booking
        r1 = create_reservation(
            user=self.customer1,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=time(8, 0),
            duration=1,
        )

        # Cust 2 booking
        r2 = create_reservation(
            user=self.customer2,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=time(18, 0),
            duration=1,
        )

        # Cust 1 requests list
        self.client.force_authenticate(user=self.customer1)
        url = reverse('reservations:api_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.json()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['id'], r1.id)

    def test_customer_cannot_view_another_users_reservation_detail(self):
        """GET /api/reservations/<id>/ returns 403 Forbidden for unauthorized users."""
        target_date = timezone.localdate() + timedelta(days=2)
        r1 = create_reservation(
            user=self.customer1,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=time(8, 0),
            duration=1,
        )

        self.client.force_authenticate(user=self.customer2)
        detail_url = reverse('reservations:api_detail', kwargs={'pk': r1.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_api_endpoint(self):
        """POST /api/reservations/<id>/cancel/ cancels the reservation."""
        target_date = timezone.localdate() + timedelta(days=2)
        r1 = create_reservation(
            user=self.customer1,
            parking_lot=self.lot,
            reservation_date=target_date,
            start_time=time(8, 0),
            duration=1,
        )

        self.client.force_authenticate(user=self.customer1)
        cancel_url = reverse('reservations:api_cancel', kwargs={'pk': r1.id})
        response = self.client.post(cancel_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['reservation']['status'], 'CANCELLED')
