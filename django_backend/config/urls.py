"""
URL Configuration for Smart Parking Availability Platform.
"""

from django.contrib import admin
from django.urls import path, include
from apps.core.views import HomeView, HealthCheckView

urlpatterns = [
    # Landing Page (Django Templates + Tailwind CSS)
    path('', HomeView.as_view(), name='home'),

    # Platform Health Check Endpoint (Django REST Framework)
    # Required Day 1 contract: GET /api/health/ -> {"status": "ok", "service": "django-backend"}
    path('api/health/', HealthCheckView.as_view(), name='api-health'),

    # Authentication & User Profiles (Day 2)
    path('', include('apps.accounts.urls', namespace='accounts')),

    # Django Admin Site
    path('admin/', admin.site.urls),
]
