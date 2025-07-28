#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from app.models import Service
from decimal import Decimal

# Test NEW profit margin calculation (absolute Naira amounts)
print("Testing NEW Profit Margin System (Absolute Naira Amounts)")
print("=" * 60)

service = Service.objects.first()
if service:
    print(f"Service: {service.name}")
    print(f"Base price (stored): ${service.price}")
    print(f"Profit margin (Naira): ₦{service.profit_margin}")
    print(f"Calculated Naira price: ₦{service.get_naira_price()}")
    print("")
    print("Manual calculation:")
    
    # Check if it's USD or NGN
    if service.price < 100:
        base_ngn = service.price * Decimal('1650')
        print(f"  USD to NGN: ${service.price} * 1650 = ₦{base_ngn}")
    else:
        base_ngn = service.price
        print(f"  Price already in NGN: ₦{base_ngn}")
    
    # Calculate NEW absolute margin
    absolute_margin = service.profit_margin
    expected_total = base_ngn + absolute_margin
    
    print(f"  Absolute margin: ₦{absolute_margin}")
    print(f"  Expected total: ₦{base_ngn} + ₦{absolute_margin} = ₦{expected_total}")
    print(f"  Actual result: ₦{service.get_naira_price()}")
    
    # Check if they match
    if abs(float(expected_total) - float(service.get_naira_price())) < 0.01:
        print("✅ Calculation is correct!")
    else:
        print("❌ Calculation mismatch!")
        
    print("")
    print("Testing with different profit margins:")
    
    # Simulate different margin amounts
    print(f"  With ₦100 margin: ₦{base_ngn} + ₦100 = ₦{base_ngn + Decimal('100')}")
    print(f"  With ₦200 margin: ₦{base_ngn} + ₦200 = ₦{base_ngn + Decimal('200')}")
    print(f"  With ₦50 margin: ₦{base_ngn} + ₦50 = ₦{base_ngn + Decimal('50')}")
    
    print("")
    print("IMPORTANT: You can now set profit margins like:")
    print("  - 100.00 for ₦100 profit")
    print("  - 250.00 for ₦250 profit") 
    print("  - 75.50 for ₦75.50 profit")
    
else:
    print("No services found")
