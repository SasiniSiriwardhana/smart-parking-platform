"""
Core views for Smart Parking Availability Platform:
- HomeView: Renders the primary landing page with Tailwind CSS
- HealthCheckView: Django REST Framework health check endpoint (Day 1 contract)
"""

from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class HomeView(TemplateView):
    """
    Renders the public landing page showcasing the Smart Parking Availability Platform.
    Utilizes Django Templates integrated with Tailwind CSS.
    """
    template_name = 'home.html'


class HealthCheckView(APIView):
    """
    Health check endpoint for the Django backend.
    
    Contract:
        GET /api/health/
        Response 200 OK:
        {
            "status": "ok",
            "service": "django-backend"
        }
    """
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "status": "ok",
                "service": "django-backend"
            },
            status=status.HTTP_200_OK
        )
