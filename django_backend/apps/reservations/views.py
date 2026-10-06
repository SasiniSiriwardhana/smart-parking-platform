"""
Reservation Views — Day 06: Smart Recommendation + Reservation.

Includes:
- DRF API views for booking, viewing, and cancelling parking reservations.
- Template views for customer reservation management dashboard.
"""
import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserRole
from apps.parking.models import ParkingLot
from .models import Reservation, ReservationStatus
from .serializers import ReservationSerializer, ReservationCreateSerializer
from .services import (
    create_reservation,
    cancel_reservation,
    ReservationValidationError,
    SlotConflictError,
    NoAvailableSlotError,
)

logger = logging.getLogger(__name__)


def is_lot_owner_or_admin(user, lot):
    return user.is_authenticated and (lot.owner_id == user.id or user.is_staff or user.is_superuser)


class ReservationListCreateAPIView(APIView):
    """
    GET /api/reservations/
    Lists reservations. Regular customers see only their own bookings.
    Parking providers see bookings for their parking lots.
    Admins see all bookings.

    POST /api/reservations/
    Creates a new confirmed reservation for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        queryset = Reservation.objects.select_related(
            'user', 'parking_lot', 'parking_slot'
        ).all()

        if user.is_staff or user.is_superuser:
            # Admins can filter by user or lot
            target_user = request.query_params.get('user_id')
            target_lot = request.query_params.get('lot_id')
            if target_user:
                queryset = queryset.filter(user_id=target_user)
            if target_lot:
                queryset = queryset.filter(parking_lot_id=target_lot)
        elif hasattr(user, 'profile') and user.profile.role == UserRole.PARKING_PROVIDER:
            # Provider sees reservations for their managed lots
            queryset = queryset.filter(parking_lot__owner=user)
        else:
            # Customer sees strictly their own bookings
            queryset = queryset.filter(user=user)

        # Status filter
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        serializer = ReservationSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ReservationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        try:
            reservation = create_reservation(
                user=request.user,
                parking_lot=validated_data['parking_lot'],
                reservation_date=validated_data['reservation_date'],
                start_time=validated_data['start_time'],
                duration=validated_data.get('duration', 1),
                preferred_slot_id=validated_data.get('preferred_slot_id'),
            )
            response_serializer = ReservationSerializer(reservation)
            return Response(
                {
                    'message': 'Reservation confirmed successfully.',
                    'reservation': response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except SlotConflictError as e:
            return Response(
                {
                    'error': 'SLOT_CONFLICT',
                    'detail': str(e.message if hasattr(e, 'message') else e),
                },
                status=status.HTTP_409_CONFLICT,
            )
        except NoAvailableSlotError as e:
            return Response(
                {
                    'error': 'NO_SLOTS_AVAILABLE',
                    'detail': str(e.message if hasattr(e, 'message') else e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except (ReservationValidationError, ValidationError) as e:
            msg = e.message if hasattr(e, 'message') else str(e)
            return Response(
                {
                    'error': 'VALIDATION_ERROR',
                    'detail': msg,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception("Unexpected error during reservation booking")
            return Response(
                {
                    'error': 'SERVER_ERROR',
                    'detail': 'An error occurred while creating your reservation. Please try again.',
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReservationDetailAPIView(APIView):
    """
    GET /api/reservations/<id>/
    Retrieve details for a single reservation.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        reservation = get_object_or_404(
            Reservation.objects.select_related('user', 'parking_lot', 'parking_slot'),
            pk=pk
        )

        user = request.user
        is_owner = reservation.user_id == user.id
        is_provider = (
            hasattr(user, 'profile')
            and user.profile.role == UserRole.PARKING_PROVIDER
            and reservation.parking_lot.owner_id == user.id
        )
        is_staff = user.is_staff or user.is_superuser

        if not (is_owner or is_provider or is_staff):
            return Response(
                {'detail': 'You do not have permission to view this reservation.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ReservationSerializer(reservation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReservationCancelAPIView(APIView):
    """
    POST /api/reservations/<id>/cancel/
    Cancel an existing reservation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)

        try:
            cancelled = cancel_reservation(reservation, request.user)
            serializer = ReservationSerializer(cancelled)
            return Response(
                {
                    'message': 'Reservation cancelled successfully.',
                    'reservation': serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {'detail': str(e.message if hasattr(e, 'message') else e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {'detail': f'Unable to cancel reservation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ══════════════════════════════════════════════════════════════════════════════
#  Customer Template View — My Reservations Dashboard
# ══════════════════════════════════════════════════════════════════════════════

class MyReservationsView(LoginRequiredMixin, TemplateView):
    """
    GET /reservations/
    Customer dashboard displaying upcoming, past, and cancelled reservations.
    """
    template_name = 'reservations/my_reservations.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()

        all_reservations = Reservation.objects.filter(
            user=user
        ).select_related('parking_lot', 'parking_slot').order_by('-start_datetime')

        ctx['upcoming_reservations'] = all_reservations.filter(
            status=ReservationStatus.CONFIRMED,
            end_datetime__gte=now,
        ).order_by('start_datetime')

        ctx['past_reservations'] = all_reservations.filter(
            status=ReservationStatus.CONFIRMED,
            end_datetime__lt=now,
        )

        ctx['cancelled_reservations'] = all_reservations.filter(
            status=ReservationStatus.CANCELLED
        )

        ctx['total_count'] = all_reservations.count()
        return ctx

    def post(self, request, *args, **kwargs):
        """Handle cancellation from template form."""
        reservation_id = request.POST.get('reservation_id')
        if reservation_id:
            reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)
            try:
                cancel_reservation(reservation, request.user)
                messages.success(request, f"Reservation #{reservation.pk} has been cancelled.")
            except Exception as e:
                messages.error(request, f"Failed to cancel reservation: {str(e)}")
        return redirect('reservations:my_reservations')
