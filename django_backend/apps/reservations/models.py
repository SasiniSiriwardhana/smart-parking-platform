"""
Parking Reservation Model — Day 06: Smart Recommendation + Reservation.

Represents a customer's advance reservation for a specific parking slot at a designated
parking facility, bounded by start/end times with status tracking and conflict prevention.
"""
from datetime import datetime, timedelta, time
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.parking.models import ParkingLot, ParkingSlot


class ReservationStatus(models.TextChoices):
    """Lifecycle status for a parking slot reservation."""
    PENDING = 'PENDING', _('Pending')
    CONFIRMED = 'CONFIRMED', _('Confirmed')
    CANCELLED = 'CANCELLED', _('Cancelled')
    COMPLETED = 'COMPLETED', _('Completed')


class Reservation(models.Model):
    """
    A time-bounded parking reservation created by a customer.
    Guarantees conflict-free slot allocation via backend overlap validation.
    """
    # ── Relationships ────────────────────────────────────────────────────────
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('Customer'),
        help_text=_('User who booked this parking reservation.')
    )
    parking_lot = models.ForeignKey(
        ParkingLot,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('Parking Lot'),
        help_text=_('Facility where the slot is reserved.')
    )
    parking_slot = models.ForeignKey(
        ParkingSlot,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('Parking Slot'),
        help_text=_('Designated parking space allocated for this reservation.')
    )

    # ── Time Parameters ──────────────────────────────────────────────────────
    reservation_date = models.DateField(
        verbose_name=_('Reservation Date'),
        help_text=_('Calendar date of the reservation.')
    )
    start_time = models.TimeField(
        verbose_name=_('Start Time'),
        help_text=_('Scheduled start time.')
    )
    duration = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        verbose_name=_('Duration (Hours)'),
        help_text=_('Reservation duration in whole hours (1 to 24 hours).')
    )
    end_time = models.TimeField(
        verbose_name=_('End Time'),
        help_text=_('Scheduled end time calculated from start time + duration.')
    )

    # ── Timezone-Aware DateTime Stamps for Precise Overlap Queries ───────────
    start_datetime = models.DateTimeField(
        verbose_name=_('Start DateTime'),
        help_text=_('Timezone-aware start timestamp.')
    )
    end_datetime = models.DateTimeField(
        verbose_name=_('End DateTime'),
        help_text=_('Timezone-aware end timestamp.')
    )

    # ── Lifecycle Status ─────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.CONFIRMED,
        verbose_name=_('Status'),
        help_text=_('Current lifecycle state of the reservation.')
    )

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        verbose_name = _('Reservation')
        verbose_name_plural = _('Reservations')
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['user', 'status'], name='res_user_status_idx'),
            models.Index(fields=['parking_lot', 'status'], name='res_lot_status_idx'),
            models.Index(fields=['parking_slot', 'status'], name='res_slot_status_idx'),
            models.Index(fields=['start_datetime', 'end_datetime'], name='res_time_range_idx'),
            models.Index(fields=['reservation_date', 'start_time'], name='res_date_time_idx'),
            models.Index(fields=['created_at'], name='res_created_idx'),
        ]

    def __str__(self):
        return (
            f"Reservation #{self.pk}: {self.parking_lot.name} [{self.parking_slot.slot_number}] "
            f"by {self.user.username} on {self.reservation_date} {self.start_time.strftime('%H:%M')}-"
            f"{self.end_time.strftime('%H:%M')} [{self.status}]"
        )

    def calculate_timestamps(self):
        """
        Calculate and populate start_datetime, end_datetime, and end_time
        using proper timezone-aware datetime manipulation.
        """
        if not self.reservation_date or not self.start_time or not self.duration:
            return

        current_tz = timezone.get_current_timezone()
        
        # Construct naive start datetime and make timezone-aware
        naive_start = datetime.combine(self.reservation_date, self.start_time)
        if timezone.is_naive(naive_start):
            aware_start = timezone.make_aware(naive_start, current_tz)
        else:
            aware_start = naive_start

        aware_end = aware_start + timedelta(hours=int(self.duration))

        self.start_datetime = aware_start
        self.end_datetime = aware_end
        
        # Local end time
        local_end = timezone.localtime(aware_end, current_tz)
        self.end_time = local_end.time()
