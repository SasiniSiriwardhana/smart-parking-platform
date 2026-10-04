"""
Parking Lot Model — Day 03: Parking Data + Map-Based Parking Finder.

Represents a physical parking facility registered on the Smart Parking platform.
Real-time availability tracking (WebSockets/sensors) is a Day 04+ feature.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


def validate_latitude(value):
    """Latitude must be between -90 and 90."""
    if value < -90 or value > 90:
        raise ValidationError(
            _('%(value)s is not a valid latitude. Must be between -90 and 90.'),
            params={'value': value},
        )


def validate_longitude(value):
    """Longitude must be between -180 and 180."""
    if value < -180 or value > 180:
        raise ValidationError(
            _('%(value)s is not a valid longitude. Must be between -180 and 180.'),
            params={'value': value},
        )


def validate_positive(value):
    """Value must be greater than 0."""
    if value <= 0:
        raise ValidationError(
            _('%(value)s must be greater than 0.'),
            params={'value': value},
        )


def validate_non_negative(value):
    """Value must be >= 0."""
    if value < 0:
        raise ValidationError(
            _('%(value)s must be 0 or greater.'),
            params={'value': value},
        )


class ParkingLot(models.Model):
    """
    A physical parking facility on the Smart Parking platform.

    Owned by a Parking Provider user and discoverable by Customers
    via the map-based parking finder introduced in Day 03.

    NOTE: Day 03 uses stored available_slots only.
    Real-time availability, WebSockets, sensors and ML predictions are Day 04+.
    """

    # ── Ownership ────────────────────────────────────────────────────────────
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='parking_lots',
        verbose_name=_('Owner'),
        help_text=_('Parking Provider who manages this facility.')
    )

    # ── Identity ─────────────────────────────────────────────────────────────
    name = models.CharField(
        max_length=200,
        verbose_name=_('Parking Name'),
        help_text=_('Public display name of the parking facility.')
    )
    address = models.TextField(
        verbose_name=_('Address'),
        help_text=_('Full street address of the parking facility.')
    )

    # ── Geolocation ──────────────────────────────────────────────────────────
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name=_('Latitude'),
        validators=[validate_latitude],
        help_text=_('Geographic latitude (-90 to 90).')
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name=_('Longitude'),
        validators=[validate_longitude],
        help_text=_('Geographic longitude (-180 to 180).')
    )

    # ── Capacity ─────────────────────────────────────────────────────────────
    total_slots = models.PositiveIntegerField(
        verbose_name=_('Total Slots'),
        validators=[validate_positive],
        help_text=_('Total number of parking slots in this facility (must be > 0).')
    )
    available_slots = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Available Slots'),
        help_text=_(
            'Current number of available slots. '
            'Day 03: stored value only. Real-time sync is Day 04+.'
        )
    )

    # ── Pricing ──────────────────────────────────────────────────────────────
    price_per_hour = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_('Price per Hour (Rs.)'),
        validators=[validate_non_negative],
        help_text=_('Hourly parking rate in Sri Lankan Rupees.')
    )

    # ── Operating Hours ──────────────────────────────────────────────────────
    opening_time = models.TimeField(
        verbose_name=_('Opening Time'),
        help_text=_('Daily opening time of the parking facility.')
    )
    closing_time = models.TimeField(
        verbose_name=_('Closing Time'),
        help_text=_('Daily closing time of the parking facility.')
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
        verbose_name = _('Parking Lot')
        verbose_name_plural = _('Parking Lots')
        ordering = ['name']
        indexes = [
            models.Index(fields=['owner'], name='parking_owner_idx'),
            models.Index(fields=['latitude', 'longitude'], name='parking_geo_idx'),
            models.Index(fields=['price_per_hour'], name='parking_price_idx'),
            models.Index(fields=['available_slots'], name='parking_avail_idx'),
            models.Index(fields=['created_at'], name='parking_created_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(total_slots__gt=0),
                name='parking_total_slots_positive'
            ),
            models.CheckConstraint(
                check=models.Q(available_slots__gte=0),
                name='parking_available_slots_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(price_per_hour__gte=0),
                name='parking_price_non_negative'
            ),
        ]

    def clean(self):
        """Model-level validation: available_slots cannot exceed total_slots."""
        super().clean()
        if self.available_slots is not None and self.total_slots is not None:
            if self.available_slots > self.total_slots:
                raise ValidationError({
                    'available_slots': _(
                        'Available slots (%(avail)s) cannot exceed total slots (%(total)s).'
                    ) % {'avail': self.available_slots, 'total': self.total_slots}
                })

    def save(self, *args, **kwargs):
        """Run full validation before saving."""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_open_now(self):
        """Return True if the facility is currently within its opening hours."""
        from django.utils import timezone
        now = timezone.localtime().time()
        if self.opening_time <= self.closing_time:
            return self.opening_time <= now <= self.closing_time
        # Handles overnight facilities (e.g. opens 22:00, closes 06:00)
        return now >= self.opening_time or now <= self.closing_time

    @property
    def is_full(self):
        """Return True if the parking lot has 0 available slots."""
        return self.available_slots == 0

    @property
    def is_available(self):
        """Return True if at least 1 slot is currently available."""
        return self.available_slots > 0

    @property
    def occupied_slots(self):
        """Return number of currently occupied slots."""
        if self.slots.exists():
            return self.slots.filter(status=SlotStatus.OCCUPIED).count()
        return max(0, self.total_slots - self.available_slots)

    @property
    def occupancy_rate(self):
        """Alias for occupancy_percentage."""
        return self.occupancy_percentage

    @property
    def occupancy_percentage(self):
        """Return percentage of slots currently occupied."""
        if self.total_slots == 0:
            return 0.0
        occupied = self.occupied_slots
        return round((occupied / self.total_slots) * 100, 1)

    def sync_slot_counts(self):
        """
        Recalculate and update available_slots from individual ParkingSlot records.
        Ensures Total = Occupied + Available consistency.
        """
        if self.slots.exists():
            avail_count = self.slots.filter(status=SlotStatus.AVAILABLE).count()
            self.available_slots = avail_count
            self.save(update_fields=['available_slots', 'updated_at'])
        return self.available_slots

    def generate_default_slots(self):
        """
        Generate default parking slots (e.g. A01, A02...) for this parking lot.
        Preserves existing available/occupied counts if slots are being initialized.
        """
        if self.slots.exists():
            return list(self.slots.all())

        slots_to_create = []
        occupied_target = max(0, self.total_slots - self.available_slots)

        for i in range(1, self.total_slots + 1):
            letter_idx = (i - 1) // 50
            letter = chr(ord('A') + letter_idx)
            num = ((i - 1) % 50) + 1
            slot_num = f"{letter}{num:02d}"

            # Assign first N slots as OCCUPIED to match current state
            status = SlotStatus.OCCUPIED if i <= occupied_target else SlotStatus.AVAILABLE
            slots_to_create.append(
                ParkingSlot(
                    parking_lot=self,
                    slot_number=slot_num,
                    status=status
                )
            )

        created_slots = ParkingSlot.objects.bulk_create(slots_to_create)
        self.sync_slot_counts()
        return created_slots

    def get_realtime_status(self):
        """
        Return structured status dictionary for WebSocket broadcast and REST API.
        """
        return {
            'parking_id': self.pk,
            'name': self.name,
            'total_slots': self.total_slots,
            'occupied_slots': self.occupied_slots,
            'available_slots': self.available_slots,
            'occupancy_percentage': self.occupancy_percentage,
            'is_full': self.is_full,
            'is_available': self.is_available,
            'is_open_now': self.is_open_now,
        }

    def simulate_car_entry(self):
        """
        Simulate a car entering the parking lot.
        Finds the first available slot, marks it OCCUPIED, and recalculates availability.
        Returns tuple: (success: bool, message: str, slot: ParkingSlot | None)
        """
        # Ensure slots exist
        if not self.slots.exists():
            self.generate_default_slots()

        available_slot = self.slots.filter(status=SlotStatus.AVAILABLE).order_by('slot_number').first()
        if not available_slot:
            return False, "Parking is full.", None

        available_slot.occupy()
        self.sync_slot_counts()
        return True, f"Slot {available_slot.slot_number} occupied successfully.", available_slot

    def simulate_car_exit(self, slot_id=None):
        """
        Simulate a car exiting the parking lot.
        Finds an occupied slot (or specific slot_id), marks it AVAILABLE, and recalculates availability.
        Returns tuple: (success: bool, message: str, slot: ParkingSlot | None)
        """
        # Ensure slots exist
        if not self.slots.exists():
            self.generate_default_slots()

        if slot_id:
            occupied_slot = self.slots.filter(pk=slot_id, status=SlotStatus.OCCUPIED).first()
        else:
            occupied_slot = self.slots.filter(status=SlotStatus.OCCUPIED).order_by('slot_number').first()

        if not occupied_slot:
            return False, "No occupied slots available.", None

        occupied_slot.vacate()
        self.sync_slot_counts()
        return True, f"Slot {occupied_slot.slot_number} vacated successfully.", occupied_slot

    def __str__(self):
        return f"{self.name} ({self.available_slots}/{self.total_slots} available)"


# ══════════════════════════════════════════════════════════════════════════════
#  Day 04: Real-Time Parking Slot Model & Status Choices
# ══════════════════════════════════════════════════════════════════════════════

class SlotStatus(models.TextChoices):
    """Occupancy status for an individual parking slot."""
    AVAILABLE = 'AVAILABLE', _('Available')
    OCCUPIED = 'OCCUPIED', _('Occupied')


class ParkingSlot(models.Model):
    """
    An individual physical parking space in a ParkingLot (Day 04).

    Tracks real-time status (AVAILABLE 🟢 / OCCUPIED 🔴) and notifies
    connected clients via WebSockets when state changes.
    """
    parking_lot = models.ForeignKey(
        ParkingLot,
        on_delete=models.CASCADE,
        related_name='slots',
        verbose_name=_('Parking Lot'),
        help_text=_('Facility this slot belongs to.')
    )
    slot_number = models.CharField(
        max_length=20,
        verbose_name=_('Slot Number'),
        help_text=_('Designation of the slot (e.g. A01, A02, B05).')
    )
    status = models.CharField(
        max_length=20,
        choices=SlotStatus.choices,
        default=SlotStatus.AVAILABLE,
        verbose_name=_('Status'),
        help_text=_('Current occupancy state of the slot.')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        verbose_name = _('Parking Slot')
        verbose_name_plural = _('Parking Slots')
        ordering = ['slot_number']
        constraints = [
            models.UniqueConstraint(
                fields=['parking_lot', 'slot_number'],
                name='unique_slot_per_lot'
            )
        ]
        indexes = [
            models.Index(fields=['parking_lot', 'status'], name='slot_lot_status_idx'),
            models.Index(fields=['parking_lot', 'slot_number'], name='slot_lot_num_idx'),
            models.Index(fields=['status'], name='slot_status_idx'),
            models.Index(fields=['created_at'], name='slot_created_idx'),
        ]

    def __str__(self):
        return f"{self.parking_lot.name} - {self.slot_number} [{self.get_status_display()}]"

    @property
    def is_available(self):
        """Return True if this slot is available."""
        return self.status == SlotStatus.AVAILABLE

    @property
    def is_occupied(self):
        """Return True if this slot is occupied."""
        return self.status == SlotStatus.OCCUPIED

    def occupy(self):
        """Mark slot as OCCUPIED and save."""
        self.status = SlotStatus.OCCUPIED
        self.save(update_fields=['status', 'updated_at'])

    def vacate(self):
        """Mark slot as AVAILABLE and save."""
        self.status = SlotStatus.AVAILABLE
        self.save(update_fields=['status', 'updated_at'])

