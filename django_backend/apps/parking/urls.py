"""
Parking URL Configuration — Day 03.
"""
from django.urls import path

from . import views

app_name = 'parking'

urlpatterns = [
    # ── Customer-facing template views ────────────────────────────────────────
    path('parking/', views.ParkingFinderView.as_view(), name='finder'),
    path('parking/<int:pk>/', views.ParkingDetailView.as_view(), name='detail'),

    # ── Parking Provider template views ───────────────────────────────────────
    path('parking/manage/', views.ProviderParkingListView.as_view(), name='provider_list'),
    path('parking/create/', views.ParkingCreateView.as_view(), name='create'),

    # ── DRF API endpoints ─────────────────────────────────────────────────────
    path('api/parking/', views.ParkingListAPIView.as_view(), name='api_list'),
    path('api/parking/<int:pk>/', views.ParkingDetailAPIView.as_view(), name='api_detail'),
    path('api/parking/create/', views.ParkingCreateAPIView.as_view(), name='api_create'),
    path('api/parking/my/', views.ProviderParkingListAPIView.as_view(), name='api_my'),

    # ── Day 04 Real-Time Availability & Simulation API endpoints ──────────────
    path('api/parking/<int:pk>/availability/', views.ParkingAvailabilityAPIView.as_view(), name='api_availability'),
    path('api/parking/<int:pk>/slots/', views.ParkingSlotsAPIView.as_view(), name='api_slots'),
    path('api/parking/<int:pk>/simulate-entry/', views.SimulateCarEntryAPIView.as_view(), name='api_simulate_entry'),
    path('api/parking/<int:pk>/simulate-exit/', views.SimulateCarExitAPIView.as_view(), name='api_simulate_exit'),
    path('api/parking/<int:pk>/slots/<int:slot_pk>/toggle/', views.SlotToggleAPIView.as_view(), name='api_slot_toggle'),

    # ── Day 05 ML Availability Prediction API endpoint ───────────────────────
    path('api/parking/<int:pk>/prediction/', views.ParkingPredictionAPIView.as_view(), name='api_prediction'),
]

