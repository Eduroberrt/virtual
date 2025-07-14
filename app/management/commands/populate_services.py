from django.core.management.base import BaseCommand
from app.models import Service
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate database with sample SMS verification services'

    def handle(self, *args, **options):
        services_data = [
            {
                'name': 'WhatsApp',
                'code': 'wa',
                'price': Decimal('0.50'),
                'daily_price': Decimal('0.20'),
                'profit_margin': Decimal('15.00'),
                'supports_multiple_sms': True,
                'is_active': True,
            },
            {
                'name': 'Google / Gmail / Youtube',
                'code': 'go',
                'price': Decimal('0.45'),
                'daily_price': Decimal('0.18'),
                'profit_margin': Decimal('20.00'),
                'supports_multiple_sms': True,
                'is_active': True,
            },
            {
                'name': 'Instagram',
                'code': 'ig',
                'price': Decimal('0.60'),
                'daily_price': Decimal('0.25'),
                'profit_margin': Decimal('10.00'),
                'supports_multiple_sms': True,
                'is_active': True,
            },
            {
                'name': 'Facebook',
                'code': 'fb',
                'price': Decimal('0.75'),
                'daily_price': Decimal('0.30'),
                'profit_margin': Decimal('12.00'),
                'supports_multiple_sms': True,
                'is_active': True,
            },
            {
                'name': 'Discord',
                'code': 'ds',
                'price': Decimal('0.55'),
                'daily_price': Decimal('0.22'),
                'profit_margin': Decimal('18.00'),
                'supports_multiple_sms': False,
                'is_active': True,
            },
            {
                'name': 'Twitter',
                'code': 'tw',
                'price': Decimal('0.65'),
                'daily_price': Decimal('0.28'),
                'profit_margin': Decimal('15.00'),
                'supports_multiple_sms': True,
                'is_active': True,
            },
            {
                'name': 'Telegram',
                'code': 'tg',
                'price': Decimal('0.40'),
                'daily_price': Decimal('0.15'),
                'profit_margin': Decimal('25.00'),
                'supports_multiple_sms': True,
                'is_active': True,
            },
            {
                'name': 'Microsoft',
                'code': 'mm',
                'price': Decimal('0.70'),
                'daily_price': Decimal('0.32'),
                'profit_margin': Decimal('14.00'),
                'supports_multiple_sms': False,
                'is_active': True,
            },
            {
                'name': 'Amazon / AWS',
                'code': 'am',
                'price': Decimal('0.80'),
                'daily_price': Decimal('0.35'),
                'profit_margin': Decimal('16.00'),
                'supports_multiple_sms': True,
                'is_active': True,
            },
            {
                'name': 'Apple',
                'code': 'wx',
                'price': Decimal('0.85'),
                'daily_price': Decimal('0.40'),
                'profit_margin': Decimal('13.00'),
                'supports_multiple_sms': True,
                'is_active': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                code=service_data['code'],
                defaults=service_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created service: {service.name}')
                )
            else:
                # Update existing service
                for key, value in service_data.items():
                    setattr(service, key, value)
                service.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated service: {service.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} services and updated {updated_count} services.'
            )
        )
        
        # Display price calculations
        self.stdout.write('\nPrice calculations (with profit margin):')
        for service in Service.objects.filter(is_active=True):
            naira_price = service.get_naira_price()
            self.stdout.write(
                f'{service.name}: ${service.price} → ₦{naira_price:.2f} (includes {service.profit_margin}% margin)'
            )
