"""
URL patterns for the Accounts app (Authentication & User Profile).
"""

from django.urls import path
from .views import RegisterView, RegisterAPIView

app_name = 'accounts'

urlpatterns = [
    # UI Pages (Day 2)
    path('register/', RegisterView.as_view(), name='register'),

    # Auth API Endpoints (Day 2)
    path('api/auth/register/', RegisterAPIView.as_view(), name='api-register'),
]
