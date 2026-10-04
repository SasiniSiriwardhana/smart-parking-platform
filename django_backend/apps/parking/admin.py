"""
Django Admin registration for the Parking app (Day 03).

Provides full CRUD, search, filtering and list display for ParkingLot objects.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ParkingLot, ParkingSlot, SlotStatus


class ParkingSlotInline(admin.TabularInline):
    """Inline view of slots on the ParkingLot admin page."""
    model = ParkingSlot
    extra = 0
    fields = ('slot_number', 'status', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    """Admin interface for ParkingLot management."""
    inlines = [ParkingSlotInline]

    # ── List display ─────────────────────────────────────────────────────────
    list_display = [
        'name',
        'owner_username',
        'address_short',
        'total_slots',
        'available_slots',
        'price_per_hour',
        'opening_time',
        'closing_time',
        'created_at',
    ]
    list_display_links = ['name']
    list_per_page = 25

    # ── Filters ───────────────────────────────────────────────────────────────
    list_filter = [
        'owner',
        'opening_time',
        'closing_time',
        ('price_per_hour', admin.EmptyFieldListFilter),
    ]

    # ── Search ────────────────────────────────────────────────────────────────
    search_fields = [
        'name',
        'address',
        'owner__username',
        'owner__email',
    ]

    # ── Ordering ─────────────────────────────────────────────────────────────
    ordering = ['name']

    # ── Fieldsets ────────────────────────────────────────────────────────────
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('owner', 'name', 'address'),
        }),
        (_('Location'), {
            'fields': ('latitude', 'longitude'),
            'description': _('Latitude (-90 to 90), Longitude (-180 to 180)'),
        }),
        (_('Capacity & Availability'), {
            'fields': ('total_slots', 'available_slots'),
            'description': _(
                'Day 04: Real-time availability synchronized with individual parking slots.'
            ),
        }),
        (_('Pricing'), {
            'fields': ('price_per_hour',),
        }),
        (_('Operating Hours'), {
            'fields': ('opening_time', 'closing_time'),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    # ── Custom display helpers ───────────────────────────────────────────────
    @admin.display(description=_('Owner'), ordering='owner__username')
    def owner_username(self, obj):
        return obj.owner.username

    @admin.display(description=_('Address'))
    def address_short(self, obj):
        return obj.address[:60] + '…' if len(obj.address) > 60 else obj.address


@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    """Admin interface for individual parking slot management (Day 04)."""
    list_display = [
        'slot_number',
        'parking_lot',
        'status_badge',
        'status',
        'created_at',
        'updated_at',
    ]
    list_filter = ['status', 'parking_lot']
    search_fields = ['slot_number', 'parking_lot__name']
    ordering = ['parking_lot', 'slot_number']
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description=_('Status Badge'))
    def status_badge(self, obj):
        return "🟢 Available" if obj.status == SlotStatus.AVAILABLE else "🔴 Occupied"


