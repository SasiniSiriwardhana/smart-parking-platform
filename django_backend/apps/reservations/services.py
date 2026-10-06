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
