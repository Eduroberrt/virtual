from django.core.management.base import BaseCommand
from decimal import Decimal
from app.models import Service

class Command(BaseCommand):
    help = 'Add "Service Not Listed" option to services'

    def handle(self, *args, **options):
        # Use a unique service code for "Service Not Listed" to avoid conflicts
        service_code = 'service_not_listed'
        service_name = 'Service Not Listed'
        
        self.stdout.write("Creating 'Service Not Listed' option...")
        
        # Check if service already exists
        service, created = Service.objects.get_or_create(
            code=service_code,
            defaults={
                'name': service_name,
                'price': Decimal('2.50'),  # Base price for unlisted services
                'daily_price': Decimal('0.00'),
                'profit_margin': Decimal('30.00'),  # Profit margin
                'available_numbers': 999,
                'supports_multiple_sms': True,
                'is_active': True,
            }
        )
        
        # Update name if needed (but this should be a unique service)
        if service.name != service_name:
            service.name = service_name
            service.save()
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created "{service_name}" service'
                )
            )
            self.stdout.write(
                f'Base price: ${service.price} USD'
            )
            self.stdout.write(
                f'Price with margin: ₦{service.get_naira_price():,.2f} NGN'
            )
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(
                    'You can adjust the price and profit margin in the Django admin:'
                )
            )
            self.stdout.write('1. Go to Django Admin > Services')
            self.stdout.write('2. Find "Service Not Listed"')
            self.stdout.write('3. Adjust price and profit_margin as needed')
            self.stdout.write('4. The frontend will automatically use the updated price')
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Service "{service_name}" already exists'
                )
            )
            self.stdout.write(
                f'Current price: ₦{service.get_naira_price():,.2f} NGN'
            )
            self.stdout.write('')
            self.stdout.write(
                'You can update the price in Django Admin > Services'
            )
