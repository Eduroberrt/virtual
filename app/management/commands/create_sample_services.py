from django.core.management.base import BaseCommand
from app.models import Service
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create sample services for testing'

    def handle(self, *args, **options):
        # Sample services data
        sample_services = [
            {
                'code': 'whatsapp',
                'name': 'WhatsApp',
                'price': Decimal('0.50'),
                'available_numbers': 150,
                'supports_multiple_sms': True,
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg'
            },
            {
                'code': 'telegram',
                'name': 'Telegram',
                'price': Decimal('0.30'),
                'available_numbers': 200,
                'supports_multiple_sms': True,
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg'
            },
            {
                'code': 'discord',
                'name': 'Discord',
                'price': Decimal('0.25'),
                'available_numbers': 75,
                'supports_multiple_sms': False,
                'icon_url': 'https://assets-global.website-files.com/6257adef93867e50d84d30e2/636e0a6918e57475a843f59f_icon_clyde_black_RGB.svg'
            },
            {
                'code': 'instagram',
                'name': 'Instagram',
                'price': Decimal('0.40'),
                'available_numbers': 120,
                'supports_multiple_sms': False,
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png'
            },
            {
                'code': 'twitter',
                'name': 'Twitter (X)',
                'price': Decimal('0.35'),
                'available_numbers': 0,  # Sold out
                'supports_multiple_sms': False,
                'icon_url': 'https://abs.twimg.com/responsive-web/client-web/icon-ios.77d25eba.png'
            },
            {
                'code': 'facebook',
                'name': 'Facebook',
                'price': Decimal('0.45'),
                'available_numbers': 90,
                'supports_multiple_sms': True,
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg'
            },
            {
                'code': 'google',
                'name': 'Google',
                'price': Decimal('0.20'),
                'available_numbers': 300,
                'supports_multiple_sms': True,
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg'
            },
            {
                'code': 'tiktok',
                'name': 'TikTok',
                'price': Decimal('0.60'),
                'available_numbers': 60,
                'supports_multiple_sms': False,
                'icon_url': 'https://sf16-website-login.neutral.ttwstatic.com/obj/tiktok_web_login_static/tiktok/webapp/main/webapp-desktop/8152caf0c8e8bc67ae0d.png'
            }
        ]

        created_count = 0
        updated_count = 0

        for service_data in sample_services:
            service, created = Service.objects.get_or_create(
                code=service_data['code'],
                defaults=service_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"Created service: {service.name}")
            else:
                # Update existing service
                for key, value in service_data.items():
                    setattr(service, key, value)
                service.save()
                updated_count += 1
                self.stdout.write(f"Updated service: {service.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {created_count + updated_count} services "
                f"({created_count} created, {updated_count} updated)"
            )
        )
