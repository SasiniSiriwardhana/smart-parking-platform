"""
Reservation URL Configuration — Day 06.
"""
from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    # ── Customer UI Dashboard ────────────────────────────────────────────────
    path('reservations/', views.MyReservationsView.as_view(), name='my_reservations'),

    # ── DRF REST API Endpoints ───────────────────────────────────────────────
    path('api/reservations/', views.ReservationListCreateAPIView.as_view(), name='api_list_create'),
    path('api/reservations/<int:pk>/', views.ReservationDetailAPIView.as_view(), name='api_detail'),
    path('api/reservations/<int:pk>/cancel/', views.ReservationCancelAPIView.as_view(), name='api_cancel'),
]
