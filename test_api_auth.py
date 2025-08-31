#!/usr/bin/env python3
"""
Test API key authentication
"""

import requests

def test_api_key():
    """Test if the API key works"""
    
    print("🔑 Testing API Key Authentication")
    print("=" * 40)
    
    # Correct API key from settings
    api_key = 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODU2NjUxOTYsImlhdCI6MTc1NDEyOTE5NiwicmF5IjoiNTRjNDVhOTUwYTEyNTZiMDUzNDZiNjgyNzc4YzExMDciLCJzdWIiOjM0MDcyODF9.fovz5P51ZwMJCriW6PeVnJxuz6nmU7R2Mb3C8D8a5w0Zhdx7D7f0IIKorsZkSSXeVu7In_k5zUQriExPg6r-A1F11QyR-HsdnvH6RznnQa4yqwK6RpwKVL7AS-6N3xwX29vHQJavuBORHBAKniG_TRgddO9-BhZggMh2WXivLJ-hh9knT3n-O-5gIle-oAv1HZvI62tz_fzumQ1yx-hIhLriyWj4CdqTWN1AgD9qa0mI6PIlGw9m-Oggvd0TzfI5M39x1sPy3DXpLrbHsLgZYo7gwz_WmG7L4SoN2W9kxcaiZca3PllwIqF9gAn1WCkrTppoqyi-IhH8PFv3JVeHAw'
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # Test 1: Check account profile
    print("\n📊 Test 1: Account Profile")
    try:
        response = requests.get('https://5sim.net/v1/user/profile', headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 2: Check pricing (guest endpoint)
    print("\n💰 Test 2: Guest Pricing")
    try:
        response = requests.get('https://5sim.net/v1/guest/prices?country=germany&product=signal', timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'germany' in data and 'signal' in data['germany']:
                operators = data['germany']['signal']
                print("Germany + Signal operators:")
                for op, info in operators.items():
                    count = info.get('count', 0)
                    cost = info.get('cost', 0)
                    print(f"  - {op}: ₽{cost} ({count} available)")
        else:
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 3: Try a test purchase with virtual38
    print("\n🛒 Test 3: Test Purchase (virtual38)")
    try:
        purchase_url = 'https://5sim.net/v1/user/buy/activation/germany/virtual38/signal'
        response = requests.get(purchase_url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Purchase successful!")
        elif response.status_code == 400:
            print("❌ Bad request - check response for details")
        elif response.status_code == 401:
            print("❌ Authentication failed")
        else:
            print(f"❌ Other error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_api_key()
