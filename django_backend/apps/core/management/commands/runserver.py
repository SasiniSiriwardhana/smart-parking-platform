"""
Custom runserver management command for Smart Parking Availability Platform.

Allows development server to start gracefully even if Oracle Database
is not currently reachable, while maintaining full Oracle configuration.
"""

from django.contrib.staticfiles.management.commands.runserver import Command as StaticFilesRunserverCommand
from django.db.utils import OperationalError


class Command(StaticFilesRunserverCommand):
    def check_migrations(self):
        try:
            super().check_migrations()
        except OperationalError:
            self.stdout.write(
                self.style.WARNING(
                    "\n[ORACLE DB NOTICE] Oracle Database is not reachable at the configured host/port.\n"
                    "The development server is running in offline-DB mode.\n"
                    "To test your database connection at any time, run: python manage.py check_db\n"
                    "Once connected, run: python manage.py migrate\n"
                )
            )
