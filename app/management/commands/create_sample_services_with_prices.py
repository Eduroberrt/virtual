from django.core.management.base import BaseCommand
from app.models import Service
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create sample services with prices and profit margins'

    def handle(self, *args, **options):
        services_data = [
            # Format: (name, code, price_usd, daily_price_usd, profit_margin_percent, supports_multiple_sms)
            ('WhatsApp', 'wa', Decimal('0.50'), Decimal('0.20'), Decimal('15.00'), True),
            ('Telegram', 'tg', Decimal('0.45'), Decimal('0.18'), Decimal('12.00'), True),
            ('Facebook', 'fb', Decimal('0.60'), Decimal('0.25'), Decimal('20.00'), True),
            ('Instagram', 'ig', Decimal('0.55'), Decimal('0.22'), Decimal('18.00'), True),
            ('Google', 'go', Decimal('0.75'), Decimal('0.30'), Decimal('25.00'), True),
            ('Amazon', 'am', Decimal('0.65'), Decimal('0.26'), Decimal('22.00'), True),
            ('Microsoft', 'ms', Decimal('0.70'), Decimal('0.28'), Decimal('20.00'), True),
            ('Apple', 'wx', Decimal('0.80'), Decimal('0.32'), Decimal('25.00'), True),
            ('Twitter/X', 'tw', Decimal('0.55'), Decimal('0.22'), Decimal('15.00'), True),
            ('Discord', 'ds', Decimal('0.40'), Decimal('0.16'), Decimal('10.00'), False),
            ('Uber', 'ub', Decimal('0.60'), Decimal('0.24'), Decimal('18.00'), True),
            ('Netflix', 'nf', Decimal('0.65'), Decimal('0.26'), Decimal('20.00'), False),
            ('Spotify', 'sp', Decimal('0.45'), Decimal('0.18'), Decimal('15.00'), False),
            ('PayPal', 'pp', Decimal('0.70'), Decimal('0.28'), Decimal('22.00'), True),
            ('Cash App', 'ca', Decimal('0.60'), Decimal('0.24'), Decimal('18.00'), True),
            ('Coinbase', 're', Decimal('0.75'), Decimal('0.30'), Decimal('25.00'), True),
            ('Binance', 'bn', Decimal('0.65'), Decimal('0.26'), Decimal('20.00'), True),
            ('TikTok', 'tt', Decimal('0.50'), Decimal('0.20'), Decimal('16.00'), True),
            ('YouTube', 'yt', Decimal('0.55'), Decimal('0.22'), Decimal('18.00'), True),
            ('LinkedIn', 'li', Decimal('0.70'), Decimal('0.28'), Decimal('22.00'), True),
        ]

        created_count = 0
        for name, code, price, daily_price, profit_margin, supports_sms in services_data:
            service, created = Service.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'price': price,
                    'daily_price': daily_price,
                    'profit_margin': profit_margin,
                    'supports_multiple_sms': supports_sms,
                    'is_active': True,
                    'available_numbers': 100,  # Default availability
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created service: {name} ({code}) - ₦{service.get_naira_price():.2f}')
                )
            else:
                # Update existing service with new profit margin if needed
                if service.profit_margin != profit_margin:
                    service.profit_margin = profit_margin
                    service.save()
                    self.stdout.write(
                        self.style.WARNING(f'Updated profit margin for: {name} ({code}) - ₦{service.get_naira_price():.2f}')
                    )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new services!')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total active services: {Service.objects.filter(is_active=True).count()}')
        )
