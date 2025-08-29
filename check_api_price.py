#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from app.models import Service
from app.daisysms import DaisySMS
import requests

def check_real_api_price():
    print("=== Checking Real-time API Prices ===")
    
    # Get WhatsApp service
    wa = Service.objects.filter(code='wa').first()
    if wa:
        print(f"Database USD Price: ${wa.price}")
        print(f"Database Total: ₦{wa.get_naira_price()}")
        print()
        
        # Check real-time API price
        try:
            daisy = DaisySMS()
            
            # Get pricing from API
            response = requests.get(f"{daisy.base_url}/api/v1/pricing", 
                                  headers={"Authorization": f"Bearer {daisy.api_key}"})
            
            if response.status_code == 200:
                pricing_data = response.json()
                
                # Find WhatsApp pricing
                for service in pricing_data.get('data', []):
                    if service.get('code') == 'wa':
                        real_price = service.get('price', 0)
                        print(f"Real-time API Price: ${real_price}")
                        
                        if abs(float(wa.price) - float(real_price)) > 0.01:
                            print(f"⚠️  PRICE MISMATCH: Database shows ${wa.price}, API shows ${real_price}")
                            print("The database needs to be synced with the API!")
                        else:
                            print("✅ Database price matches API price")
                        break
                else:
                    print("WhatsApp service not found in API response")
            else:
                print(f"API request failed: {response.status_code}")
                
        except Exception as e:
            print(f"Error checking API: {e}")
    else:
        print("WhatsApp service not found in database")

if __name__ == "__main__":
    check_real_api_price()
