"""
Reservation Business Logic & Slot Allocation Service — Day 06.

Provides:
- Time & date parameter validation
- Operating hours checks
- Conflict detection across time windows
- Atomic slot allocation with concurrency controls
"""
import logging
from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple, Dict, Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.parking.models import ParkingLot, ParkingSlot, SlotStatus
from .models import Reservation, ReservationStatus

logger = logging.getLogger(__name__)


class ReservationValidationError(ValidationError):
    """Raised when reservation parameters fail validation."""
    pass


class SlotConflictError(ValidationError):
    """Raised when a specific slot or the whole lot has conflicting bookings."""
    pass


class NoAvailableSlotError(ValidationError):
    """Raised when no slot is free for the requested time window."""
    pass


def validate_reservation_times(
    reservation_date: date,
    start_time: time,
    duration_hours: int,
    parking_lot: Optional[ParkingLot] = None,
    allow_past: bool = False,
) -> Tuple[datetime, datetime, time]:
    """
    Validate reservation date, start time, duration, and operating hours.
    Returns:
        (start_datetime: datetime, end_datetime: datetime, end_time: time)
    """
    current_tz = timezone.get_current_timezone()
    now = timezone.localtime(timezone.now(), current_tz)

    if not reservation_date:
        raise ReservationValidationError(_("Reservation date is required."))

    if not start_time:
        raise ReservationValidationError(_("Start time is required."))

    if not duration_hours or int(duration_hours) < 1:
        raise ReservationValidationError(_("Reservation duration must be at least 1 hour."))

    if int(duration_hours) > 24:
        raise ReservationValidationError(_("Reservation duration cannot exceed 24 hours."))

    # Construct timezone-aware start datetime
    naive_start = datetime.combine(reservation_date, start_time)
    start_datetime = timezone.make_aware(naive_start, current_tz)
    end_datetime = start_datetime + timedelta(hours=int(duration_hours))
    end_time = timezone.localtime(end_datetime, current_tz).time()

    # Reject past reservations unless explicitly permitted in testing
    if not allow_past and start_datetime < now - timedelta(minutes=5):
        raise ReservationValidationError(
            _("Reservation time cannot be in the past. Please select a valid future time.")
        )

    # Check parking lot operating hours if lot is provided
    if parking_lot:
        lot_open = parking_lot.opening_time
        lot_close = parking_lot.closing_time

        # Check standard opening hours
        if lot_open and lot_close and lot_open <= lot_close:
            # Single day operation
            if start_time < lot_open or start_time > lot_close:
                raise ReservationValidationError(
                    _(f"Parking facility is open from {lot_open.strftime('%H:%M')} to {lot_close.strftime('%H:%M')}.")
                )

    return start_datetime, end_datetime, end_time


def find_available_slot(
    parking_lot: ParkingLot,
    start_datetime: datetime,
    end_datetime: datetime,
    preferred_slot_id: Optional[int] = None,
) -> Optional[ParkingSlot]:
    """
    Find an unreserved parking slot at the target parking lot for the specified time interval.
    If preferred_slot_id is passed and free, assigns it; otherwise returns the first available slot.
    """
    if not parking_lot.slots.exists():
        parking_lot.generate_default_slots()

    # Query all active reservations overlapping the target interval for this parking lot
    overlapping_res = Reservation.objects.filter(
        parking_lot=parking_lot,
        status__in=[ReservationStatus.CONFIRMED, ReservationStatus.PENDING],
        start_datetime__lt=end_datetime,
        end_datetime__gt=start_datetime,
    ).values_list('parking_slot_id', flat=True)

    # Exclude reserved slots
    candidate_slots = parking_lot.slots.exclude(id__in=overlapping_res).order_by('slot_number')

    if preferred_slot_id:
        preferred = candidate_slots.filter(id=preferred_slot_id).first()
        if preferred:
            return preferred

    return candidate_slots.first()


def check_slot_conflict(
    parking_slot: ParkingSlot,
    start_datetime: datetime,
    end_datetime: datetime,
    exclude_reservation_id: Optional[int] = None,
) -> bool:
    """
    Check if a specific parking slot has any overlapping confirmed/pending reservation.
    Overlaps occur when:
        existing.start_datetime < new_end_datetime AND existing.end_datetime > new_start_datetime
    Boundary contacts (start == existing.end or end == existing.start) are non-conflicting.
    """
    qs = Reservation.objects.filter(
        parking_slot=parking_slot,
        status__in=[ReservationStatus.CONFIRMED, ReservationStatus.PENDING],
        start_datetime__lt=end_datetime,
        end_datetime__gt=start_datetime,
    )
    if exclude_reservation_id:
        qs = qs.exclude(id=exclude_reservation_id)
    return qs.exists()


@transaction.atomic
def create_reservation(
    user,
    parking_lot: ParkingLot,
    reservation_date: date,
    start_time: time,
    duration: int,
    preferred_slot_id: Optional[int] = None,
    allow_past: bool = False,
) -> Reservation:
    """
    Atomically allocate an available parking slot and create a confirmed reservation.
    Guarantees conflict prevention under concurrency using database transactions and locking.
    """
    start_dt, end_dt, end_tm = validate_reservation_times(
        reservation_date=reservation_date,
        start_time=start_time,
        duration_hours=duration,
        parking_lot=parking_lot,
        allow_past=allow_past,
    )

    if not parking_lot.slots.exists():
        parking_lot.generate_default_slots()

    # If user selected a specific preferred slot, verify it directly
    if preferred_slot_id:
        try:
            slot = ParkingSlot.objects.select_for_update().get(
                id=preferred_slot_id,
                parking_lot=parking_lot
            )
            if check_slot_conflict(slot, start_dt, end_dt):
                raise SlotConflictError(
                    _("This parking slot is already reserved for the selected time.")
                )
        except ParkingSlot.DoesNotExist:
            raise ReservationValidationError(_("Selected parking slot does not exist."))
    else:
        # Find candidate slots and obtain row lock on the chosen slot
        # Get list of currently booked slot IDs in target window
        booked_slot_ids = list(
            Reservation.objects.filter(
                parking_lot=parking_lot,
                status__in=[ReservationStatus.CONFIRMED, ReservationStatus.PENDING],
                start_datetime__lt=end_dt,
                end_datetime__gt=start_dt,
            ).values_list('parking_slot_id', flat=True)
        )

        available_slots_qs = parking_lot.slots.exclude(
            id__in=booked_slot_ids
        ).order_by('slot_number')

        slot = None
        # Select first free slot with row lock
        for candidate in available_slots_qs:
            locked_slot = ParkingSlot.objects.select_for_update().filter(id=candidate.id).first()
            if locked_slot and not check_slot_conflict(locked_slot, start_dt, end_dt):
                slot = locked_slot
                break

        if not slot:
            raise NoAvailableSlotError(
                _("No parking slots are available for this time.")
            )

    reservation = Reservation(
        user=user,
        parking_lot=parking_lot,
        parking_slot=slot,
        reservation_date=reservation_date,
        start_time=start_time,
        duration=int(duration),
        end_time=end_tm,
        start_datetime=start_dt,
        end_datetime=end_dt,
        status=ReservationStatus.CONFIRMED,
    )
    reservation.save()
    return reservation


def cancel_reservation(reservation: Reservation, user) -> Reservation:
    """
    Cancel an active reservation if user is the owner or staff.
    """
    if reservation.user_id != user.id and not (user.is_staff or user.is_superuser):
        raise ValidationError(_("You do not have permission to cancel this reservation."))

    if reservation.status == ReservationStatus.CANCELLED:
        raise ValidationError(_("This reservation is already cancelled."))

    if reservation.status == ReservationStatus.COMPLETED:
        raise ValidationError(_("Completed reservations cannot be cancelled."))

    reservation.status = ReservationStatus.CANCELLED
    reservation.save(update_fields=['status', 'updated_at'])
    return reservation


