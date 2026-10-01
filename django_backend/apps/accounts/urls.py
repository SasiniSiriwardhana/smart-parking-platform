"""
URL patterns for the Accounts app — Authentication & User Profile (Day 2).
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, RegisterAPIView,
    LoginView, LoginAPIView,
    LogoutView, LogoutAPIView,
    DashboardView,
    ProfileView, ProfileAPIView,
)

app_name = 'accounts'

urlpatterns = [
    # ── Web UI Pages ─────────────────────────────────────────────────
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('profile/', ProfileView.as_view(), name='profile'),

    # ── Auth REST API Endpoints ───────────────────────────────────────
    path('api/auth/register/', RegisterAPIView.as_view(), name='api-register'),
    path('api/auth/login/', LoginAPIView.as_view(), name='api-login'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('api/auth/logout/', LogoutAPIView.as_view(), name='api-logout'),
    path('api/auth/profile/', ProfileAPIView.as_view(), name='api-profile'),
]
