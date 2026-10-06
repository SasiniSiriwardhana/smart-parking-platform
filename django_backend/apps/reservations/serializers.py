"""
Reservation Serializers — Day 06.
"""
from rest_framework import serializers
from apps.parking.models import ParkingLot, ParkingSlot
from .models import Reservation, ReservationStatus
from .services import validate_reservation_times, ReservationValidationError


class ReservationSerializer(serializers.ModelSerializer):
    """
    Detailed read serializer for Parking Reservations.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    parking_lot_name = serializers.CharField(source='parking_lot.name', read_only=True)
    parking_lot_address = serializers.CharField(source='parking_lot.address', read_only=True)
    slot_number = serializers.CharField(source='parking_slot.slot_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    price_per_hour = serializers.DecimalField(
        source='parking_lot.price_per_hour',
        max_digits=8,
        decimal_places=2,
        read_only=True
    )
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id',
            'user',
            'user_username',
            'parking_lot',
            'parking_lot_name',
            'parking_lot_address',
            'parking_slot',
            'slot_number',
            'reservation_date',
            'start_time',
            'end_time',
            'duration',
            'start_datetime',
            'end_datetime',
            'status',
            'status_display',
            'price_per_hour',
            'total_cost',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'user_username',
            'parking_lot_name',
            'parking_lot_address',
            'slot_number',
            'end_time',
            'start_datetime',
            'end_datetime',
            'status',
            'status_display',
            'created_at',
            'updated_at',
        ]

    def get_total_cost(self, obj):
        try:
            return float(obj.parking_lot.price_per_hour * obj.duration)
        except Exception:
            return 0.0


class ReservationCreateSerializer(serializers.Serializer):
    """
    Input serializer for booking a parking slot reservation.
    """
    parking_lot = serializers.PrimaryKeyRelatedField(queryset=ParkingLot.objects.all())
    reservation_date = serializers.DateField()
    start_time = serializers.TimeField()
    duration = serializers.IntegerField(min_value=1, max_value=24, default=1)
    preferred_slot_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        try:
            validate_reservation_times(
                reservation_date=attrs['reservation_date'],
                start_time=attrs['start_time'],
                duration_hours=attrs.get('duration', 1),
                parking_lot=attrs.get('parking_lot'),
            )
        except ReservationValidationError as e:
            raise serializers.ValidationError({'detail': str(e.message if hasattr(e, 'message') else e)})
        return attrs
