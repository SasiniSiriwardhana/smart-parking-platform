"""
Parking Availability WebSocket Consumers — Day 04: Real-Time Availability.

Provides real-time bi-directional WebSocket communication using Django Channels.
Connects users to live parking slot availability updates without requiring page refreshes.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from .models import ParkingLot, ParkingSlot, SlotStatus


class ParkingAvailabilityConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time parking lot availability updates.

    Routes:
        ws://<host>/ws/parking/<parking_id>/availability/
        ws://<host>/ws/parking/availability/  (global feed for finder/dashboard)
    """

    async def connect(self):
        self.parking_id = self.scope['url_route']['kwargs'].get('parking_id')
        
        if self.parking_id is not None:
            self.room_group_name = f"parking_{self.parking_id}_availability"
            # Verify that the parking lot exists
            lot_exists = await self.check_parking_lot_exists(self.parking_id)
            if not lot_exists:
                await self.close(code=4004)
                return
        else:
            self.room_group_name = "parking_all_availability"

        # Join the channel group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial snapshot upon successful connection
        if self.parking_id is not None:
            initial_data = await self.get_lot_snapshot(self.parking_id)
            if initial_data:
                await self.send(text_data=json.dumps({
                    'type': 'availability_snapshot',
                    'data': initial_data
                }))
        else:
            all_data = await self.get_all_lots_snapshot()
            await self.send(text_data=json.dumps({
                'type': 'all_availability_snapshot',
                'data': all_data
            }))

    async def disconnect(self, close_code):
        # Leave channel group cleanly
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming messages from client (e.g. ping, refresh request)."""
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
            action = payload.get('action')

            if action == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            elif action == 'get_status':
                if self.parking_id is not None:
                    data = await self.get_lot_snapshot(self.parking_id)
                    await self.send(text_data=json.dumps({
                        'type': 'availability_snapshot',
                        'data': data
                    }))
                else:
                    data = await self.get_all_lots_snapshot()
                    await self.send(text_data=json.dumps({
                        'type': 'all_availability_snapshot',
                        'data': data
                    }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format.'
            }))

    async def availability_update(self, event):
        """Handler for 'availability_update' group broadcasts."""
        await self.send(text_data=json.dumps({
            'type': 'availability_update',
            'data': event['data']
        }))

    async def slot_update(self, event):
        """Handler for 'slot_update' individual slot broadcasts."""
        await self.send(text_data=json.dumps({
            'type': 'slot_update',
            'data': event['data']
        }))

    # ── Database synchronization helpers ──────────────────────────────────────

    @database_sync_to_async
    def check_parking_lot_exists(self, lot_id):
        try:
            return ParkingLot.objects.filter(pk=lot_id).exists()
        except (ValueError, TypeError):
            return False

    @database_sync_to_async
    def get_lot_snapshot(self, lot_id):
        try:
            lot = ParkingLot.objects.get(pk=lot_id)
            if not lot.slots.exists():
                lot.generate_default_slots()
            slots = [
                {
                    'id': slot.pk,
                    'slot_number': slot.slot_number,
                    'status': slot.status,
                    'is_available': slot.is_available,
                    'is_occupied': slot.is_occupied,
                }
                for slot in lot.slots.all().order_by('slot_number')
            ]
            status_dict = lot.get_realtime_status()
            status_dict['slots'] = slots
            return status_dict
        except ParkingLot.DoesNotExist:
            return None

    @database_sync_to_async
    def get_all_lots_snapshot(self):
        lots = ParkingLot.objects.all()
        return [lot.get_realtime_status() for lot in lots]
