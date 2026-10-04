"""
Real-Time Availability Broadcasting Services — Day 04.

Provides centralized methods for dispatching WebSocket notifications
via Django Channels channel layers when parking lot or slot states change.
"""
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import ParkingLot, ParkingSlot, SlotStatus

logger = logging.getLogger(__name__)


def broadcast_parking_availability(parking_lot: ParkingLot):
    """
    Broadcast updated parking lot availability to all connected WebSocket clients.
    Sends to:
      1. Specific lot channel group: 'parking_<id>_availability'
      2. Global availability channel group: 'parking_all_availability'
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        # Prepare slot snapshots
        slots_data = [
            {
                'id': slot.pk,
                'slot_number': slot.slot_number,
                'status': slot.status,
                'is_available': slot.is_available,
                'is_occupied': slot.is_occupied,
            }
            for slot in parking_lot.slots.all().order_by('slot_number')
        ]

        status_payload = parking_lot.get_realtime_status()
        status_payload['slots'] = slots_data

        # 1. Send to lot-specific group
        lot_group = f"parking_{parking_lot.pk}_availability"
        async_to_sync(channel_layer.group_send)(
            lot_group,
            {
                'type': 'availability_update',
                'data': status_payload,
            }
        )

        # 2. Send to global finder/dashboard group
        async_to_sync(channel_layer.group_send)(
            'parking_all_availability',
            {
                'type': 'availability_update',
                'data': status_payload,
            }
        )
    except Exception as e:
        logger.error(f"Error broadcasting parking availability for lot {parking_lot.pk}: {e}")


def broadcast_slot_update(slot: ParkingSlot):
    """
    Broadcast an individual slot status transition to WebSocket clients.
    Also syncs and broadcasts the updated parking lot availability totals.
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        slot_payload = {
            'slot_id': slot.pk,
            'parking_lot_id': slot.parking_lot_id,
            'slot_number': slot.slot_number,
            'status': slot.status,
            'is_available': slot.is_available,
            'is_occupied': slot.is_occupied,
        }

        lot_group = f"parking_{slot.parking_lot_id}_availability"
        async_to_sync(channel_layer.group_send)(
            lot_group,
            {
                'type': 'slot_update',
                'data': slot_payload,
            }
        )

        # Broadcast the new totals
        broadcast_parking_availability(slot.parking_lot)
    except Exception as e:
        logger.error(f"Error broadcasting slot update for slot {slot.pk}: {e}")
