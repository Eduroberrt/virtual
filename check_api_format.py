#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from app.models import Service
from decimal import Decimal

# Test API response formatting
print("Testing API Response Formatting with New Profit Margin System")
print("=" * 65)

service = Service.objects.first()
if service:
    print(f"Service: {service.name}")
    print(f"Base price (USD): ${service.price}")
    print(f"Profit margin (NGN): ₦{service.profit_margin}")
    print("")
    
    # Test naira price calculation
    naira_price = service.get_naira_price()
    naira_daily_price = service.get_naira_daily_price()
    usd_price = service.get_usd_price()
    
    print(f"Calculated prices:")
    print(f"  Naira price: ₦{naira_price}")
    print(f"  Naira daily price: ₦{naira_daily_price}")
    print(f"  USD price (for API): ${usd_price}")
    
    print("")
    print("API Response format (what users will see):")
    print(f"  price_naira: {naira_price:,.2f}")
    print(f"  daily_price_naira: {naira_daily_price:,.2f}")
    
    print("")
    print("Admin will see:")
    print(f"  Base price: ${service.price}")
    print(f"  Profit margin: ₦{service.profit_margin}")
    print(f"  Final price: ₦{naira_price}")
    
else:
    print("No services found")
