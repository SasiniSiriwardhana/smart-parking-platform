"""
Django Management Command: predict_parking_availability
Runs ML inference for future parking slot availability (~20 minutes ahead).
Usage:
    python manage.py predict_parking_availability --parking-id 1
"""

from django.core.management.base import BaseCommand
from apps.parking.models import ParkingLot
from ml.src.predict import predict_availability


class Command(BaseCommand):
    help = "Predict future available parking spaces for a given parking lot."

    def add_arguments(self, parser):
        parser.add_argument(
            "--parking-id",
            "--lot-id",
            type=int,
            default=None,
            help="ID of the ParkingLot to predict availability for.",
        )
        parser.add_argument(
            "--name",
            type=str,
            default="Downtown Grand Plaza",
            help="Name of the parking lot (if ID not provided or for standalone testing).",
        )
        parser.add_argument(
            "--total-slots",
            type=int,
            default=100,
            help="Total slots for standalone test.",
        )
        parser.add_argument(
            "--occupied-slots",
            type=int,
            default=92,
            help="Current occupied slots for standalone test.",
        )
        parser.add_argument(
            "--has-event",
            action="store_true",
            help="Flag indicating nearby event.",
        )
        parser.add_argument(
            "--is-holiday",
            action="store_true",
            help="Flag indicating holiday schedule.",
        )

    def handle(self, *args, **options):
        parking_id = options.get("parking_id")
        lot_name = options.get("name")
        total_slots = options.get("total_slots", 100)
        occupied_slots = options.get("occupied_slots", 92)
        has_event = options.get("has_event", False)
        is_holiday = options.get("is_holiday", False)

        if parking_id is not None:
            try:
                lot = ParkingLot.objects.get(pk=parking_id)
                lot_name = lot.name
                total_slots = lot.total_slots
                # Derive live occupancy from slots
                occupied_slots = lot.slots.filter(is_occupied=True).count()
                if total_slots == 0 and lot.slots.count() > 0:
                    total_slots = lot.slots.count()
            except ParkingLot.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"ParkingLot with ID {parking_id} not found."))
                return

        available_slots = max(0, total_slots - occupied_slots)

        self.stdout.write(self.style.NOTICE(f"\n[PREDICTION] Computing 20-minute availability forecast for: {lot_name}"))
        
        result = predict_availability(
            parking_lot_name=lot_name,
            total_slots=total_slots,
            current_occupied=occupied_slots,
            current_available=available_slots,
            nearby_event=has_event,
            holiday=is_holiday,
        )

        r_min = result["predicted_range"]["min"]
        r_max = result["predicted_range"]["max"]

        self.stdout.write("=" * 50)
        self.stdout.write(f"Parking: {result['parking_name']}")
        self.stdout.write(f"Total Slots: {result['total_slots']}")
        self.stdout.write(f"Current Occupied: {result['current_occupied']}")
        self.stdout.write(f"Current Available: {result['current_available']}")
        self.stdout.write(f"Target Time: {result['target_time']} ({result['target_day']})")
        self.stdout.write(f"Predicted in {result['prediction_minutes']} minutes: {result['predicted_available']}")
        self.stdout.write(f"Estimated Range: {r_min}-{r_max} spaces")
        self.stdout.write(f"Confidence: {result['confidence']}")
        self.stdout.write(f"Status: {result['status']}")
        self.stdout.write(f"Warning: {result['warning_message']}")
        self.stdout.write("=" * 50)
