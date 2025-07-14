#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the path
sys.path.append('c:/Users/WDN/Desktop/virtual')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from app.models import Service
from decimal import Decimal

def create_sample_services():
    """Create sample services for testing"""
    
    # Clear existing services
    Service.objects.all().delete()
    print("Cleared existing services")
    
    sample_services = [
        {
            'code': 'whatsapp',
            'name': 'WhatsApp',
            'price': Decimal('0.50'),
            'daily_price': Decimal('2.00'),
            'profit_margin': Decimal('15.00'),
            'available_numbers': 100,
            'supports_multiple_sms': True,
        },
        {
            'code': 'telegram',
            'name': 'Telegram',
            'price': Decimal('0.30'),
            'daily_price': Decimal('1.50'),
            'profit_margin': Decimal('15.00'),
            'available_numbers': 150,
            'supports_multiple_sms': True,
        },
        {
            'code': 'facebook',
            'name': 'Facebook',
            'price': Decimal('0.75'),
            'daily_price': Decimal('3.00'),
            'profit_margin': Decimal('15.00'),
            'available_numbers': 80,
            'supports_multiple_sms': False,
        },
        {
            'code': 'google',
            'name': 'Google',
            'price': Decimal('0.60'),
            'daily_price': Decimal('2.50'),
            'profit_margin': Decimal('15.00'),
            'available_numbers': 200,
            'supports_multiple_sms': True,
        },
        {
            'code': 'twitter',
            'name': 'Twitter/X',
            'price': Decimal('0.45'),
            'daily_price': Decimal('1.80'),
            'profit_margin': Decimal('15.00'),
            'available_numbers': 120,
            'supports_multiple_sms': False,
        },
        {
            'code': 'instagram',
            'name': 'Instagram',
            'price': Decimal('0.55'),
            'daily_price': Decimal('2.20'),
            'profit_margin': Decimal('15.00'),
            'available_numbers': 90,
            'supports_multiple_sms': False,
        },
        {
            'code': 'discord',
            'name': 'Discord',
            'price': Decimal('0.40'),
            'daily_price': Decimal('1.60'),
            'profit_margin': Decimal('15.00'),
            'available_numbers': 110,
            'supports_multiple_sms': True,
        },
        {
            'code': 'tiktok',
            'name': 'TikTok',
            'price': Decimal('0.65'),
            'daily_price': Decimal('2.60'),
            'profit_margin': Decimal('15.00'),
            'available_numbers': 70,
            'supports_multiple_sms': False,
        }
    ]
    
    created_count = 0
    for service_data in sample_services:
        service, created = Service.objects.get_or_create(
            code=service_data['code'],
            defaults=service_data
        )
        if created:
            created_count += 1
            naira_price = service.get_naira_price()
            print(f"Created: {service.name} - ${service.price} (₦{naira_price:,.2f})")
        else:
            print(f"Already exists: {service.name}")
    
    total_services = Service.objects.count()
    print(f"\nCreated {created_count} new services")
    print(f"Total services in database: {total_services}")

if __name__ == '__main__':
    create_sample_services()
