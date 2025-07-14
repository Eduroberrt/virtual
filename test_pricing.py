#!/usr/bin/env python
"""
Simple test script to verify admin pricing logic
"""
import os
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from app.models import Service, UserProfile

def test_pricing():
    print("Testing Admin Pricing Logic")
    print("=" * 40)
    
    # Test service pricing
    test_service = Service(
        code='test',
        name='Test Service',
        price=Decimal('0.50'),  # $0.50 base price
        profit_margin=Decimal('15.00')  # 15% profit margin
    )
    
    print(f"Base price (USD): ${test_service.price}")
    print(f"Profit margin: {test_service.profit_margin}%")
    
    # Calculate admin price
    admin_price_naira = test_service.get_naira_price()
    print(f"Admin price (Naira): ₦{admin_price_naira:,.2f}")
    
    # Convert back to USD for storage
    admin_price_usd = admin_price_naira / UserProfile.USD_TO_NGN_RATE
    print(f"Admin price (USD): ${admin_price_usd:.4f}")
    
    # Calculate expected values
    base_naira = test_service.price * UserProfile.USD_TO_NGN_RATE
    margin_amount = base_naira * (test_service.profit_margin / 100)
    expected_admin_naira = base_naira + margin_amount
    
    print(f"\nExpected calculation:")
    print(f"Base price in Naira: ₦{base_naira:,.2f}")
    print(f"Margin amount: ₦{margin_amount:,.2f}")
    print(f"Expected admin price: ₦{expected_admin_naira:,.2f}")
    
    # Verify calculations
    if abs(admin_price_naira - expected_admin_naira) < 0.01:
        print("\n✅ Pricing calculation is correct!")
    else:
        print("\n❌ Pricing calculation error!")
    
    print(f"\nProfit earned per rental: ₦{margin_amount:,.2f}")
    print(f"Profit percentage: {test_service.profit_margin}%")

if __name__ == "__main__":
    test_pricing()
