"""
Parking Views — Day 03: Parking Data + Map-Based Parking Finder.

Includes:
  - DRF API views: list, detail, create
  - Django Template views: parking finder, parking detail, provider management
"""
import datetime
import json
import math

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserRole
from .models import ParkingLot
from .serializers import ParkingLotListSerializer, ParkingLotSerializer
from .utils import haversine_distance, format_distance


# ══════════════════════════════════════════════════════════════════════════════
#  Helper / Permission utilities
# ══════════════════════════════════════════════════════════════════════════════

def is_parking_provider(user):
    """Return True if the user has Parking Provider role."""
    return (
        user.is_authenticated
        and hasattr(user, 'profile')
        and user.profile.role == UserRole.PARKING_PROVIDER
    )


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ══════════════════════════════════════════════════════════════════════════════
#  DRF API Views
# ══════════════════════════════════════════════════════════════════════════════

class ParkingListAPIView(APIView):
    """
    GET /api/parking/
    Returns a JSON list of all parking lots.
    Supports query params: ?lat=&lon=&distance=&min_price=&max_price=&min_slots=
    """
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = ParkingLot.objects.select_related('owner').all()

        # ── Text search ──────────────────────────────────────────────────────
        q = request.GET.get('q', '').strip()
        if q:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(address__icontains=q)
            )

        # ── Price filter ─────────────────────────────────────────────────────
        max_price = request.GET.get('max_price')
        min_price = request.GET.get('min_price')
        if max_price:
            try:
                queryset = queryset.filter(price_per_hour__lte=float(max_price))
            except ValueError:
                pass
        if min_price:
            try:
                queryset = queryset.filter(price_per_hour__gte=float(min_price))
            except ValueError:
                pass

        # ── Availability filter ──────────────────────────────────────────────
        min_slots = request.GET.get('min_slots')
        if min_slots:
            try:
                queryset = queryset.filter(available_slots__gte=int(min_slots))
            except ValueError:
                pass

        lots = list(queryset)

        # ── Distance calculation & filter ────────────────────────────────────
        distances = {}
        user_lat = request.GET.get('lat')
        user_lon = request.GET.get('lon')
        max_distance = request.GET.get('distance')  # in km

        if user_lat and user_lon:
            try:
                ulat = float(user_lat)
                ulon = float(user_lon)
                for lot in lots:
                    distances[lot.pk] = haversine_distance(
                        ulat, ulon, float(lot.latitude), float(lot.longitude)
                    )

                # Filter by max distance
                if max_distance:
                    max_km = float(max_distance)
                    lots = [l for l in lots if distances.get(l.pk, 999) <= max_km]

                # Sort by distance
                lots.sort(key=lambda l: distances.get(l.pk, 999))
            except (ValueError, TypeError):
                pass

        serializer = ParkingLotListSerializer(
            lots,
            many=True,
            context={'distances': distances, 'request': request}
        )
        return Response(serializer.data)


class ParkingDetailAPIView(APIView):
    """
    GET /api/parking/<id>/
    Returns JSON detail for a single parking lot.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        lot = get_object_or_404(ParkingLot, pk=pk)

        # Optionally calculate distance if user coords provided
        user_lat = request.GET.get('lat')
        user_lon = request.GET.get('lon')
        distances = {}
        if user_lat and user_lon:
            try:
                dist = haversine_distance(
                    float(user_lat), float(user_lon),
                    float(lot.latitude), float(lot.longitude)
                )
                distances[lot.pk] = dist
            except (ValueError, TypeError):
                pass

        serializer = ParkingLotListSerializer(
            lot,
            context={'distances': distances, 'request': request}
        )
        return Response(serializer.data)


class ParkingCreateAPIView(APIView):
    """
    POST /api/parking/create/
    Provider-only endpoint to create a new parking lot.
    Unauthenticated users → 401.
    Non-provider users   → 403.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Server-side role check — never trust frontend only
        if not is_parking_provider(request.user) and not is_admin(request.user):
            return Response(
                {'detail': 'Only Parking Providers can create parking lots.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ParkingLotSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProviderParkingListAPIView(APIView):
    """
    GET /api/parking/my/
    Returns parking lots owned by the authenticated provider.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_parking_provider(request.user) and not is_admin(request.user):
            return Response(
                {'detail': 'Only Parking Providers can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN
            )
        lots = ParkingLot.objects.filter(owner=request.user).order_by('-created_at')
        serializer = ParkingLotListSerializer(lots, many=True, context={'request': request})
        return Response(serializer.data)


# ══════════════════════════════════════════════════════════════════════════════
#  Django Template Views
# ══════════════════════════════════════════════════════════════════════════════

class ParkingFinderView(TemplateView):
    """
    GET /parking/
    Customer-facing parking finder with map and filter UI.
    """
    template_name = 'parking/parking_finder.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Find Parking'
        # All lots serialized as JSON for the map JS
        lots = ParkingLot.objects.select_related('owner').all()
        lots_data = []
        for lot in lots:
            lots_data.append({
                'id': lot.pk,
                'name': lot.name,
                'address': lot.address,
                'latitude': float(lot.latitude),
                'longitude': float(lot.longitude),
                'total_slots': lot.total_slots,
                'available_slots': lot.available_slots,
                'price_per_hour': float(lot.price_per_hour),
                'opening_time': lot.opening_time.strftime('%H:%M'),
                'closing_time': lot.closing_time.strftime('%H:%M'),
                'is_open_now': lot.is_open_now,
            })
        ctx['lots_json'] = json.dumps(lots_data)
        ctx['lots'] = lots
        return ctx


class ParkingDetailView(View):
    """
    GET /parking/<pk>/
    Customer-facing detail page for a single parking lot.
    """
    template_name = 'parking/parking_detail.html'

    def get(self, request, pk):
        lot = get_object_or_404(ParkingLot, pk=pk)

        # Calculate distance if user provided coords
        user_lat = request.GET.get('lat')
        user_lon = request.GET.get('lon')
        distance_str = None
        if user_lat and user_lon:
            try:
                dist_km = haversine_distance(
                    float(user_lat), float(user_lon),
                    float(lot.latitude), float(lot.longitude)
                )
                distance_str = format_distance(dist_km)
            except (ValueError, TypeError):
                pass

        return render(request, self.template_name, {
            'lot': lot,
            'distance_str': distance_str,
            'page_title': lot.name,
            'lot_json': json.dumps({
                'id': lot.pk,
                'name': lot.name,
                'latitude': float(lot.latitude),
                'longitude': float(lot.longitude),
            }),
        })


class ProviderParkingListView(LoginRequiredMixin, View):
    """
    GET /parking/manage/
    Provider-facing list of their parking lots.
    """
    template_name = 'parking/provider_parking_list.html'
    login_url = 'accounts:login'

    def get(self, request):
        if not is_parking_provider(request.user) and not is_admin(request.user):
            messages.error(request, 'Access denied. Parking Providers only.')
            return redirect('accounts:dashboard')

        lots = ParkingLot.objects.filter(owner=request.user).order_by('-created_at')
        return render(request, self.template_name, {
            'lots': lots,
            'page_title': 'My Parking Locations',
        })


class ParkingCreateView(LoginRequiredMixin, View):
    """
    GET/POST /parking/create/
    Provider-only form to create a new parking lot.
    """
    template_name = 'parking/parking_create.html'
    login_url = 'accounts:login'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not is_parking_provider(request.user) and not is_admin(request.user):
                messages.error(request, 'Only Parking Providers can create parking lots.')
                return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {'page_title': 'Add Parking Location'})

    def post(self, request):
        # Server-side role check
        if not is_parking_provider(request.user) and not is_admin(request.user):
            messages.error(request, 'Only Parking Providers can create parking lots.')
            return redirect('accounts:dashboard')

        data = request.POST
        errors = {}

        name = data.get('name', '').strip()
        address = data.get('address', '').strip()
        latitude_str = data.get('latitude', '').strip()
        longitude_str = data.get('longitude', '').strip()
        total_slots_str = data.get('total_slots', '').strip()
        available_slots_str = data.get('available_slots', '0').strip()
        price_str = data.get('price_per_hour', '').strip()
        opening_time = data.get('opening_time', '').strip()
        closing_time = data.get('closing_time', '').strip()

        from decimal import Decimal

        # Validate required fields
        if not name:
            errors['name'] = 'Parking name is required.'
        if not address:
            errors['address'] = 'Address is required.'

        # Validate opening/closing times
        parsed_open = None
        parsed_close = None
        if not opening_time:
            errors['opening_time'] = 'Opening time is required.'
        else:
            try:
                if ':' in opening_time:
                    parts = opening_time.split(':')
                    parsed_open = datetime.time(int(parts[0]), int(parts[1]))
                else:
                    parsed_open = datetime.time.fromisoformat(opening_time)
            except Exception:
                errors['opening_time'] = 'Enter a valid opening time (HH:MM).'

        if not closing_time:
            errors['closing_time'] = 'Closing time is required.'
        else:
            try:
                if ':' in closing_time:
                    parts = closing_time.split(':')
                    parsed_close = datetime.time(int(parts[0]), int(parts[1]))
                else:
                    parsed_close = datetime.time.fromisoformat(closing_time)
            except Exception:
                errors['closing_time'] = 'Enter a valid closing time (HH:MM).'

        # Validate latitude
        latitude = None
        try:
            latitude_val = float(latitude_str)
            if not (-90 <= latitude_val <= 90):
                errors['latitude'] = 'Latitude must be between -90 and 90.'
            else:
                latitude = Decimal(str(latitude_str))
        except (ValueError, TypeError):
            errors['latitude'] = 'Enter a valid latitude (-90 to 90).'

        # Validate longitude
        longitude = None
        try:
            longitude_val = float(longitude_str)
            if not (-180 <= longitude_val <= 180):
                errors['longitude'] = 'Longitude must be between -180 and 180.'
            else:
                longitude = Decimal(str(longitude_str))
        except (ValueError, TypeError):
            errors['longitude'] = 'Enter a valid longitude (-180 to 180).'

        # Validate total_slots
        try:
            total_slots = int(total_slots_str)
            if total_slots <= 0:
                errors['total_slots'] = 'Total slots must be greater than 0.'
        except (ValueError, TypeError):
            errors['total_slots'] = 'Enter a valid number of slots.'
            total_slots = None

        # Validate available_slots
        try:
            available_slots = int(available_slots_str)
            if available_slots < 0:
                errors['available_slots'] = 'Available slots cannot be negative.'
        except (ValueError, TypeError):
            errors['available_slots'] = 'Enter a valid number of available slots.'
            available_slots = 0

        # Validate price
        price_per_hour = None
        try:
            price_val = float(price_str)
            if price_val < 0:
                errors['price_per_hour'] = 'Price per hour cannot be negative.'
            else:
                price_per_hour = Decimal(str(price_str))
        except (ValueError, TypeError):
            errors['price_per_hour'] = 'Enter a valid price.'

        # Cross-field: available <= total
        if total_slots and available_slots is not None and available_slots > total_slots:
            errors['available_slots'] = (
                f'Available slots ({available_slots}) cannot exceed total slots ({total_slots}).'
            )

        if errors:
            return render(request, self.template_name, {
                'page_title': 'Add Parking Location',
                'errors': errors,
                'form_data': data,
            })

        try:
            lot = ParkingLot(
                owner=request.user,
                name=name,
                address=address,
                latitude=latitude,
                longitude=longitude,
                total_slots=total_slots,
                available_slots=available_slots,
                price_per_hour=price_per_hour,
                opening_time=parsed_open,
                closing_time=parsed_close,
            )
            lot.save()
            messages.success(
                request,
                f'✅ Parking lot "{lot.name}" has been created successfully!'
            )
            return redirect('parking:provider_list')
        except Exception as e:
            messages.error(request, f'Error creating parking lot: {e}')
            return render(request, self.template_name, {
                'page_title': 'Add Parking Location',
                'errors': {'general': str(e)},
                'form_data': data,
            })
