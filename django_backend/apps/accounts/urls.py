"""
URL patterns for the Accounts app (Authentication & User Profile).
"""

from django.urls import path
from .views import RegisterAPIView

app_name = 'accounts'

urlpatterns = [
    # Auth API Endpoints (Day 2)
    path('api/auth/register/', RegisterAPIView.as_view(), name='api-register'),
]
