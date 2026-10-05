"""
Django Management Command: train_parking_model
Trains the RandomForestRegressor ML model for 20-minute parking availability prediction.
"""

from django.core.management.base import BaseCommand
from ml.src.evaluate import format_metrics_report
from ml.src.train_model import train_model


class Command(BaseCommand):
    help = "Train and serialize the Random Forest parking availability prediction model."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-path",
            type=str,
            default=None,
            help="Custom path to historical parking CSV dataset.",
        )
        parser.add_argument(
            "--test-size",
            type=float,
            default=0.2,
            help="Test set fraction (default: 0.2).",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting Parking Availability Model Training..."))
        
        try:
            pipeline, metrics = train_model(
                data_path=options.get("data_path"),
                test_size=options.get("test_size", 0.2),
            )
            self.stdout.write(self.style.SUCCESS("\n" + format_metrics_report(metrics)))
            self.stdout.write(
                self.style.SUCCESS("[SUCCESS] Successfully trained and serialized ML model artifact.")
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Model training failed: {str(e)}"))
            raise e
