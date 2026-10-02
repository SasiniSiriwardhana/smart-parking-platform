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
]
