#!/usr/bin/env python
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from app.daisysms import DaisySMSClient, DaisySMSException
from app.models import Service
import json

def test_daisysms_api():
    api_key = '8sERSxfFLvfqnvyAjdwOSJhJRKRhrC'
    
    try:
        print("Testing DaisySMS API connection...")
        client = DaisySMSClient(api_key)
        
        # Test balance first
        print("1. Testing balance...")
        try:
            balance = client.get_balance()
            print(f"   Balance: ${balance}")
        except Exception as e:
            print(f"   Balance error: {e}")
            return
        
        # Test get_prices_verification
        print("2. Testing get_prices_verification...")
        try:
            prices_data = client.get_prices_verification()
            print(f"   Found {len(prices_data)} services")
            
            # Show first few services
            service_codes = list(prices_data.keys())[:5]
            for code in service_codes:
                if '187' in prices_data[code]:  # USA
                    usa_data = prices_data[code]['187']
                    print(f"   - {code}: {usa_data.get('name', code)} - ${usa_data.get('cost', 0)}")
                else:
                    print(f"   - {code}: No USA pricing")
        except Exception as e:
            print(f"   Prices error: {e}")
            return
        
        # Test sync
        print("3. Testing sync_services...")
        try:
            updated_count = client.sync_services()
            print(f"   Synced {updated_count} services")
            
            # Show services in database
            services = Service.objects.all()[:10]
            print(f"   Database now has {Service.objects.count()} services:")
            for service in services:
                print(f"     - {service.name} ({service.code}): ${service.price}")
                
        except Exception as e:
            print(f"   Sync error: {e}")
            
    except Exception as e:
        print(f"API Client error: {e}")

if __name__ == "__main__":
    test_daisysms_api()
