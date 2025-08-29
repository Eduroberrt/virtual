#!/usr/bin/env python3
"""
Test 5sim API connectivity
"""

import requests
import json

def test_5sim_api():
    """Test 5sim API connectivity"""
    
    print("🧪 Testing 5sim API Connectivity")
    print("=" * 40)
    
    # API configuration
    api_key = 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODU2NjUxOTYsImlhdCI6MTc1NDEyOTE5NiwicmF5IjoiNTRjNDVhOTUwYTEyNTZiMDUzNDZiNjgyNzc4YzExMDciLCJzdWIiOjM0MDcyODF9.fovz5P51ZwMJCriW6PeVnJxuz6nmU7R2Mb3C8D8a5w0Zhdx7D7f0IIKorsZkSSXeVu7In_k5zUQriExPg6r-A1F11QyR-HsdnvH6RznnQa4yqwK6RpwKVL7AS-6N3xwX29vHQJavuBORHBAKniG_TRgddO9-BhZggMh2WXivLJ-hh9knT3n-O-5gIle-oAv1HZvI62tz_fzumQ1yx-hIhLriyWj4CdqTWN1AgD9qa0mI6PIlGw9m-Oggvd0TzfI5M39x1sPy3DXpLrbHsLgZYo7gwz_WmG7L4SoN2W9kxcaiZca3PllwIqF9gAn1WCkrTppoqyi-IhH8PFv3JVOJZh'
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # Test 1: Get all prices
    print("\n📡 Test 1: Getting all prices...")
    try:
        response = requests.get('https://5sim.net/v1/guest/prices', headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Got pricing data")
            
            # Check if Russia/WhatsApp exists
            if 'russia' in data and 'whatsapp' in data['russia']:
                print(f"✅ Russia/WhatsApp data found")
                whatsapp_data = data['russia']['whatsapp']
                print(f"Available operators: {list(whatsapp_data.keys())}")
                
                # Show sample operator data
                for operator, op_data in list(whatsapp_data.items())[:3]:  # First 3
                    print(f"  - {operator}: ₽{op_data.get('cost', 0)} (Available: {op_data.get('count', 0)})")
            else:
                print(f"❌ Russia/WhatsApp data not found")
                print(f"Available countries: {list(data.keys())[:5]}...")  # First 5
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 2: Test with guest endpoint (no auth)
    print("\n📡 Test 2: Testing guest endpoint...")
    try:
        guest_headers = {'Accept': 'application/json'}
        response = requests.get('https://5sim.net/v1/guest/prices', headers=guest_headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Guest endpoint works!")
        else:
            print(f"❌ Guest endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Guest request failed: {e}")

if __name__ == "__main__":
    test_5sim_api()
