#!/usr/bin/env python3
"""
Test script to verify auto-operator selection functionality
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('c:\\Users\\WDN\\Desktop\\virtual')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

import requests
import json

def test_auto_selection():
    """Test that the 5sim prices API returns data for auto-selection"""
    
    print("🧪 Testing Auto-Operator Selection Functionality")
    print("=" * 50)
    
    # Test URL
    base_url = "http://127.0.0.1:8000"
    test_url = f"{base_url}/api/5sim/prices/russia/whatsapp/"
    
    try:
        print(f"📡 Making request to: {test_url}")
        response = requests.get(test_url)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received successfully")
            print(f"📦 Response data structure:")
            print(f"   - success: {data.get('success')}")
            print(f"   - prices: {type(data.get('prices'))}")
            
            if data.get('success') and data.get('prices'):
                prices = data['prices']
                print(f"\n🎯 Available operators:")
                
                cheapest_operator = None
                cheapest_price = float('inf')
                
                for operator, operator_data in prices.items():
                    cost = operator_data.get('cost', 0)
                    count = operator_data.get('count', 0)
                    
                    print(f"   - {operator}: ₦{cost} (Available: {count})")
                    
                    if count > 0 and cost < cheapest_price:
                        cheapest_price = cost
                        cheapest_operator = {
                            'name': operator,
                            'cost': cost,
                            'count': count
                        }
                
                if cheapest_operator:
                    print(f"\n🎯 Auto-Selection Result:")
                    print(f"   - Cheapest Operator: {cheapest_operator['name']}")
                    print(f"   - Price: ₦{cheapest_operator['cost']}")
                    print(f"   - Available Numbers: {cheapest_operator['count']}")
                    print(f"\n✅ Auto-selection would work correctly!")
                    
                    # Also show what the frontend would display
                    print(f"\n📱 Frontend would show:")
                    print(f"   - Selected Operator: {cheapest_operator['name']} 🎯")
                    print(f"   - Price: ₦{cheapest_operator['cost']}")
                    print(f"   - Toast: '✅ Auto-selected cheapest operator: {cheapest_operator['name']} (₦{cheapest_operator['cost']})'")
                else:
                    print(f"\n❌ No operators with available numbers found")
            else:
                print(f"❌ API returned unsuccessful response or no prices")
                print(f"Raw response: {data}")
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to Django server at {base_url}")
        print(f"   Make sure Django server is running with: python manage.py runserver")
    except Exception as e:
        print(f"❌ Error testing auto-selection: {e}")

if __name__ == "__main__":
    test_auto_selection()
