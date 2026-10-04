"""
Management command to populate sample parking lots for Day 03 demonstration.
Creates a default parking provider if needed and registers realistic parking locations across Colombo.
"""
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile, UserRole
from apps.parking.models import ParkingLot

User = get_user_model()

SAMPLE_LOTS = [
    {
        'name': 'Colombo City Centre Parking',
        'address': '137 Sir James Pieris Mawatha, Colombo 02',
        'latitude': Decimal('6.9175000'),
        'longitude': Decimal('79.8569000'),
        'total_slots': 150,
        'available_slots': 42,
        'price_per_hour': Decimal('150.00'),
        'opening_time': datetime.time(6, 0),
        'closing_time': datetime.time(23, 30),
    },
    {
        'name': 'One Galle Face Mall Parking',
        'address': '1A Centre Road, Galle Face, Colombo 02',
        'latitude': Decimal('6.9272000'),
        'longitude': Decimal('79.8453000'),
        'total_slots': 300,
        'available_slots': 118,
        'price_per_hour': Decimal('200.00'),
        'opening_time': datetime.time(6, 0),
        'closing_time': datetime.time(23, 0),
    },
    {
        'name': 'Fort Railway Station Public Park',
        'address': 'Station Road, Fort, Colombo 01',
        'latitude': Decimal('6.9344000'),
        'longitude': Decimal('79.8504000'),
        'total_slots': 80,
        'available_slots': 8,
        'price_per_hour': Decimal('80.00'),
        'opening_time': datetime.time(5, 0),
        'closing_time': datetime.time(23, 0),
    },
    {
        'name': 'Liberty Plaza Multi-Story Parking',
        'address': '250 R. A. De Mel Mawatha, Colombo 03',
        'latitude': Decimal('6.9068000'),
        'longitude': Decimal('79.8519000'),
        'total_slots': 120,
        'available_slots': 35,
        'price_per_hour': Decimal('120.00'),
        'opening_time': datetime.time(7, 0),
        'closing_time': datetime.time(22, 0),
    },
    {
        'name': 'Majestic City Car Park',
        'address': '10 Station Road, Bambalapitiya, Colombo 04',
        'latitude': Decimal('6.8938000'),
        'longitude': Decimal('79.8553000'),
        'total_slots': 180,
        'available_slots': 0,
        'price_per_hour': Decimal('100.00'),
        'opening_time': datetime.time(8, 0),
        'closing_time': datetime.time(22, 0),
    },
    {
        'name': 'Havelock City Mall Parking',
        'address': 'Havelock Road, Colombo 05',
        'latitude': Decimal('6.8785000'),
        'longitude': Decimal('79.8655000'),
        'total_slots': 250,
        'available_slots': 95,
        'price_per_hour': Decimal('160.00'),
        'opening_time': datetime.time(6, 30),
        'closing_time': datetime.time(23, 0),
    },
    {
        'name': 'Galle Face Green Promenade Parking',
        'address': 'Galle Road, Galle Face, Colombo 03',
        'latitude': Decimal('6.9234000'),
        'longitude': Decimal('79.8432000'),
        'total_slots': 90,
        'available_slots': 22,
        'price_per_hour': Decimal('90.00'),
        'opening_time': datetime.time(6, 0),
        'closing_time': datetime.time(23, 59),
    },
    {
        'name': 'Town Hall & Viharamahadevi Park Lot',
        'address': 'F. R. Senanayake Mawatha, Colombo 07',
        'latitude': Decimal('6.9150000'),
        'longitude': Decimal('79.8638000'),
        'total_slots': 110,
        'available_slots': 64,
        'price_per_hour': Decimal('100.00'),
        'opening_time': datetime.time(6, 0),
        'closing_time': datetime.time(21, 0),
    },
]


class Command(BaseCommand):
    help = 'Seeds sample parking lot facilities across Colombo for Day 03 demonstration'

    def handle(self, *args, **options):
        # 1. Ensure a default provider account exists
        provider_user, created = User.objects.get_or_create(
            username='provider_demo',
            defaults={
                'email': 'provider@smartparking.lk',
                'first_name': 'Colombo',
                'last_name': 'Parking Services'
            }
        )
        if created:
            provider_user.set_password('Provider123!')
            provider_user.save()
            UserProfile.objects.create(
                user=provider_user,
                role=UserRole.PARKING_PROVIDER,
                phone_number='+94 11 234 5678'
            )
            self.stdout.write(self.style.SUCCESS('Created sample provider: provider_demo (password: Provider123!)'))
        else:
            profile, _ = UserProfile.objects.get_or_create(user=provider_user)
            profile.role = UserRole.PARKING_PROVIDER
            profile.save()

        # 2. Seed parking lots
        count = 0
        for data in SAMPLE_LOTS:
            lot, created = ParkingLot.objects.get_or_create(
                name=data['name'],
                defaults={
                    'owner': provider_user,
                    'address': data['address'],
                    'latitude': data['latitude'],
                    'longitude': data['longitude'],
                    'total_slots': data['total_slots'],
                    'available_slots': data['available_slots'],
                    'price_per_hour': data['price_per_hour'],
                    'opening_time': data['opening_time'],
                    'closing_time': data['closing_time'],
                }
            )
            if created:
                count += 1
                lot.generate_default_slots()
                self.stdout.write(f"  + Added: {lot.name} ({lot.available_slots}/{lot.total_slots} slots, {lot.slots.count()} slot records created)")
            else:
                if not lot.slots.exists():
                    lot.generate_default_slots()
                self.stdout.write(f"  - Already exists: {lot.name} ({lot.slots.count()} slots)")

        self.stdout.write(self.style.SUCCESS(f'\nSeeding complete! Added {count} new parking lots. Total in DB: {ParkingLot.objects.count()}'))

