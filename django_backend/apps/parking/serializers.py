"""
Parking Serializers — Day 03.

Provides DRF serializers for ParkingLot CRUD and list/detail display.
"""
from rest_framework import serializers
from django.contrib.auth.models import User

from .models import ParkingLot


class ParkingLotSerializer(serializers.ModelSerializer):
    """
    Full serializer for creating and viewing a ParkingLot.

    Read-only fields:
        owner_username  – resolved from owner FK
        is_open_now     – computed property
        occupancy_pct   – computed property
    """
    owner_username = serializers.SerializerMethodField()
    is_open_now = serializers.SerializerMethodField()
    occupancy_percentage = serializers.SerializerMethodField()

    class Meta:
        model = ParkingLot
        fields = [
            'id',
            'owner',
            'owner_username',
            'name',
            'address',
            'latitude',
            'longitude',
            'total_slots',
            'available_slots',
            'price_per_hour',
            'opening_time',
            'closing_time',
            'is_open_now',
            'occupancy_percentage',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'owner',
            'owner_username',
            'is_open_now',
            'occupancy_percentage',
            'created_at',
            'updated_at',
        ]

    def get_owner_username(self, obj):
        return obj.owner.username

    def get_is_open_now(self, obj):
        return obj.is_open_now

    def get_occupancy_percentage(self, obj):
        return obj.occupancy_percentage

    def validate(self, data):
        """Cross-field validation: available_slots <= total_slots."""
        total = data.get('total_slots', getattr(self.instance, 'total_slots', None))
        available = data.get('available_slots', getattr(self.instance, 'available_slots', 0))
        if total is not None and available is not None:
            if available > total:
                raise serializers.ValidationError({
                    'available_slots': (
                        f'Available slots ({available}) cannot exceed '
                        f'total slots ({total}).'
                    )
                })
        return data

    def validate_total_slots(self, value):
        if value <= 0:
            raise serializers.ValidationError('Total slots must be greater than 0.')
        return value

    def validate_price_per_hour(self, value):
        if value < 0:
            raise serializers.ValidationError('Price per hour cannot be negative.')
        return value

    def validate_latitude(self, value):
        if not (-90 <= value <= 90):
            raise serializers.ValidationError('Latitude must be between -90 and 90.')
        return value

    def validate_longitude(self, value):
        if not (-180 <= value <= 180):
            raise serializers.ValidationError('Longitude must be between -180 and 180.')
        return value


class ParkingLotListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for parking list/finder views.
    Includes distance_km when provided by the view context.
    """
    owner_username = serializers.SerializerMethodField()
    is_open_now = serializers.SerializerMethodField()
    occupancy_percentage = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = ParkingLot
        fields = [
            'id',
            'name',
            'address',
            'latitude',
            'longitude',
            'total_slots',
            'available_slots',
            'price_per_hour',
            'opening_time',
            'closing_time',
            'is_open_now',
            'occupancy_percentage',
            'owner_username',
            'distance_km',
        ]

    def get_owner_username(self, obj):
        return obj.owner.username

    def get_is_open_now(self, obj):
        return obj.is_open_now

    def get_occupancy_percentage(self, obj):
        return obj.occupancy_percentage

    def get_distance_km(self, obj):
        """Return pre-calculated distance injected by the view, or None."""
        distances = self.context.get('distances', {})
        dist = distances.get(obj.pk)
        if dist is not None:
            return round(dist, 2)
        return None
