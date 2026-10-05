"""
Parking Serializers — Day 03.

Provides DRF serializers for ParkingLot CRUD and list/detail display.
"""
from rest_framework import serializers
from django.contrib.auth.models import User

from .models import ParkingLot, ParkingSlot, SlotStatus


class ParkingSlotSerializer(serializers.ModelSerializer):
    """
    Serializer for individual ParkingSlot objects (Day 04).
    """
    parking_lot_name = serializers.CharField(source='parking_lot.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    is_occupied = serializers.BooleanField(read_only=True)

    class Meta:
        model = ParkingSlot
        fields = [
            'id',
            'parking_lot',
            'parking_lot_name',
            'slot_number',
            'status',
            'status_display',
            'is_available',
            'is_occupied',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'parking_lot_name',
            'status_display',
            'is_available',
            'is_occupied',
            'created_at',
            'updated_at',
        ]


class ParkingAvailabilitySerializer(serializers.Serializer):
    """
    Real-Time Availability Summary Serializer for WebSockets and REST (Day 04).
    """
    parking_id = serializers.IntegerField(source='pk')
    name = serializers.CharField()
    total_slots = serializers.IntegerField()
    occupied_slots = serializers.IntegerField()
    available_slots = serializers.IntegerField()
    occupancy_percentage = serializers.FloatField()
    is_full = serializers.BooleanField()
    is_available = serializers.BooleanField()
    is_open_now = serializers.BooleanField()


class ParkingLotSerializer(serializers.ModelSerializer):
    """
    Full serializer for creating and viewing a ParkingLot.

    Read-only fields:
        owner_username  – resolved from owner FK
        is_open_now     – computed property
        occupancy_pct   – computed property
        occupied_slots  – computed property
    """
    owner_username = serializers.SerializerMethodField()
    is_open_now = serializers.SerializerMethodField()
    occupancy_percentage = serializers.SerializerMethodField()
    occupied_slots = serializers.SerializerMethodField()
    slots = ParkingSlotSerializer(many=True, read_only=True)

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
            'occupied_slots',
            'price_per_hour',
            'opening_time',
            'closing_time',
            'is_open_now',
            'occupancy_percentage',
            'slots',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'owner',
            'owner_username',
            'is_open_now',
            'occupancy_percentage',
            'occupied_slots',
            'slots',
            'created_at',
            'updated_at',
        ]

    def get_owner_username(self, obj):
        return obj.owner.username

    def get_is_open_now(self, obj):
        return obj.is_open_now

    def get_occupancy_percentage(self, obj):
        return obj.occupancy_percentage

    def get_occupied_slots(self, obj):
        return obj.occupied_slots

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
    Includes distance_km and occupied_slots when serialized.
    """
    owner_username = serializers.SerializerMethodField()
    is_open_now = serializers.SerializerMethodField()
    occupancy_percentage = serializers.SerializerMethodField()
    occupied_slots = serializers.SerializerMethodField()
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
            'occupied_slots',
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

    def get_occupied_slots(self, obj):
        return obj.occupied_slots

    def get_distance_km(self, obj):
        """Return pre-calculated distance injected by the view, or None."""
        distances = self.context.get('distances', {})
        dist = distances.get(obj.pk)
        if dist is not None:
            return round(dist, 2)
        return None


class PredictionRangeSerializer(serializers.Serializer):
    """Serializer for uncertainty interval minimum and maximum bounds."""
    min = serializers.IntegerField()
    max = serializers.IntegerField()


class ModelMetricsSummarySerializer(serializers.Serializer):
    """Serializer for model evaluation summary metrics."""
    mae = serializers.FloatField()
    rmse = serializers.FloatField()
    r2_score = serializers.FloatField()


class ParkingPredictionSerializer(serializers.Serializer):
    """
    Serializer for ML-based 20-minute availability forecast response (Day 05).
    """
    parking_id = serializers.IntegerField()
    parking_name = serializers.CharField()
    total_slots = serializers.IntegerField()
    current_available = serializers.IntegerField()
    current_occupied = serializers.IntegerField()
    occupancy_rate = serializers.FloatField()
    prediction_minutes = serializers.IntegerField()
    target_time = serializers.CharField()
    target_day = serializers.CharField()
    predicted_available = serializers.IntegerField()
    predicted_occupied = serializers.IntegerField()
    predicted_range = PredictionRangeSerializer()
    confidence = serializers.CharField()
    status = serializers.CharField()
    warning_level = serializers.CharField()
    warning_message = serializers.CharField()
    factors = serializers.ListField(child=serializers.CharField())
    model_metrics = ModelMetricsSummarySerializer(required=False)


