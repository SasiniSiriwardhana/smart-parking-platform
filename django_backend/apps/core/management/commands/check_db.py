"""
Django management command to test connectivity to the configured Oracle Database.
Usage: python manage.py check_db
"""

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
from django.conf import settings


class Command(BaseCommand):
    help = 'Tests and verifies live connection to the configured Oracle Database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('----------------------------------------------------'))
        self.stdout.write(self.style.NOTICE('Smart Parking Availability Platform - DB Diagnostics'))
        self.stdout.write(self.style.NOTICE('----------------------------------------------------'))
        
        db_settings = settings.DATABASES.get('default', {})
        engine = db_settings.get('ENGINE', '')
        name = db_settings.get('NAME', '')
        user = db_settings.get('USER', '')
        host = db_settings.get('HOST', '')
        port = db_settings.get('PORT', '')

        self.stdout.write(f"Configured Engine : {engine}")
        self.stdout.write(f"Host / Port       : {host}:{port}")
        self.stdout.write(f"Database / Service: {name}")
        self.stdout.write(f"User              : {user}")
        self.stdout.write(self.style.NOTICE('Attempting connection to Oracle Database...'))

        try:
            connection = connections['default']
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1 FROM DUAL')
                row = cursor.fetchone()
                if row and row[0] == 1:
                    self.stdout.write(
                        self.style.SUCCESS('[SUCCESS] Successfully connected to Oracle Database!')
                    )
                    self.stdout.write(
                        self.style.SUCCESS('You can now safely run: python manage.py migrate')
                    )
                    return
        except OperationalError as e:
            self.stdout.write(
                self.style.ERROR(f'\n[CONNECTION FAILED] Could not connect to Oracle Database:\n{e}')
            )
            self.stdout.write(
                self.style.WARNING(
                    '\nTroubleshooting steps:\n'
                    '1. Ensure your Oracle Database service / listener is running locally or in Docker.\n'
                    '2. Verify credentials in your django_backend/.env file (ORACLE_DB_NAME, ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST, ORACLE_PORT).\n'
                    '3. Once the database is reachable, run:\n'
                    '   python manage.py check_db\n'
                    '   python manage.py migrate\n'
                )
            )
        except Exception as ex:
            self.stdout.write(
                self.style.ERROR(f'\n[UNEXPECTED ERROR] An error occurred while testing connection:\n{ex}')
            )
