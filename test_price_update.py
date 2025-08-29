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

def test_price_update():
    print("=== Testing Price Update Behavior ===")
    
    # Get WhatsApp service
    wa = Service.objects.filter(code='wa').first()
    if wa:
        print(f"Original Price: ${wa.price}")
        print(f"Original Total: ₦{wa.get_naira_price()}")
        print()
        
        # Update price to $0.8
        wa.price = Decimal('0.8')
        wa.save()
        print(f"Updated Price to: ${wa.price}")
        print(f"New Total: ₦{wa.get_naira_price()}")
        
        expected = (0.8 * 1650) + 500
        print(f"Expected Total: ₦{expected}")
        print()
        
        # Test with $0.7
        wa.price = Decimal('0.7')
        wa.save()
        print(f"Updated Price to: ${wa.price}")
        print(f"New Total: ₦{wa.get_naira_price()}")
        
        expected = (0.7 * 1650) + 500
        print(f"Expected Total: ₦{expected}")
        print()
        
        # Restore original price
        wa.price = Decimal('1.0')
        wa.save()
        print(f"Restored to: ${wa.price}")
        print(f"Final Total: ₦{wa.get_naira_price()}")
        
    else:
        print("WhatsApp service not found")

if __name__ == "__main__":
    test_price_update()
