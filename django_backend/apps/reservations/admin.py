"""
Admin Configuration for Parking Reservations (Day 06).
"""
from django.contrib import admin
from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'parking_lot',
        'parking_slot',
        'reservation_date',
        'start_time',
        'end_time',
        'duration',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'reservation_date', 'parking_lot']
    search_fields = [
        'user__username',
        'user__email',
        'parking_lot__name',
        'parking_slot__slot_number',
    ]
    readonly_fields = ['created_at', 'updated_at', 'start_datetime', 'end_datetime']
    date_hierarchy = 'reservation_date'
