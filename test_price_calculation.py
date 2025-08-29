#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from app.models import Service
from decimal import Decimal

def test_price_calculation():
    print("=== Testing Service Price Calculation ===")
    
    # Get WhatsApp service
    wa = Service.objects.filter(code='wa').first()
    if wa:
        print(f"Service: {wa.name}")
        print(f"USD Price: ${wa.price}")
        print(f"Profit Margin: ₦{wa.profit_margin}")
        print(f"Calculated Total: ₦{wa.get_naira_price()}")
        print()
        
        # Test calculation manually
        usd_price = float(wa.price)
        profit = float(wa.profit_margin)
        calculated = (usd_price * 1650) + profit
        print(f"Manual calculation: ${usd_price} * 1650 + ₦{profit} = ₦{calculated}")
        print()
        
        # Test with different prices
        print("Testing different USD prices:")
        test_prices = [0.8, 0.7, 0.6, 0.5]
        for test_price in test_prices:
            test_total = (test_price * 1650) + profit
            print(f"  If price was ${test_price}: ₦{test_total}")
        
        print()
        print("=== Issue Analysis ===")
        print(f"Current method result: ₦{wa.get_naira_price()}")
        print(f"Expected result: ₦{calculated}")
        
        if abs(float(wa.get_naira_price()) - calculated) > 0.01:
            print("❌ ISSUE FOUND: Calculated values don't match!")
        else:
            print("✅ Calculation is correct!")
            
    else:
        print("WhatsApp service not found")

if __name__ == "__main__":
    test_price_calculation()
