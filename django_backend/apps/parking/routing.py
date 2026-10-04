"""
WebSocket routing for Parking application (Day 04).
"""
from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # Individual parking lot availability channel
    path('ws/parking/<int:parking_id>/availability/', consumers.ParkingAvailabilityConsumer.as_asgi()),
    re_path(r'^ws/parking/(?P<parking_id>\d+)/availability/?$', consumers.ParkingAvailabilityConsumer.as_asgi()),
    # Global parking availability stream
    path('ws/parking/availability/', consumers.ParkingAvailabilityConsumer.as_asgi()),
    re_path(r'^ws/parking/availability/?$', consumers.ParkingAvailabilityConsumer.as_asgi()),
]
