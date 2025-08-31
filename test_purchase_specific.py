#!/usr/bin/env python3
"""
Test actual purchase attempt with virtual38 operator specifically
"""

import requests

def test_purchase_virtual38():
    """Test purchasing with the specific operator that has phones available"""
    
    print("🧪 Testing purchase with virtual38 operator (570 available)")
    print("=" * 60)
    
    # API configuration
    api_key = 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODU2NjUxOTYsImlhdCI6MTc1NDEyOTE5NiwicmF5IjoiNTRjNDVhOTUwYTEyNTZiMDUzNDZiNjgyNzc4YzExMDciLCJzdWIiOjM0MDcyODF9.fovz5P51ZwMJCriW6PeVnJxuz6nmU7R2Mb3C8D8a5w0Zhdx7D7f0IIKorsZkSSXeVu7In_k5zUQriExPg6r-A1F11QyR-HsdnvH6RznnQa4yqwK6RpwKVL7AS-6N3xwX29vHQJavuBORHBAKniG_TRgddO9-BhZggMh2WXivLJ-hh9knT3n-O-5gIle-oAv1HZvI62tz_fzumQ1yx-hIhLriyWj4CdqTWN1AgD9qa0mI6PIlGw9m-Oggvd0TzfI5M39x1sPy3DXpLrbHsLgZYo7gwz_WmG7L4SoN2W9kxcaiZca3PllwIqF9gAn1WCkrTppoqyi-IhH8PFv3JVOJZh'
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # Test 1: Try with specific operator (virtual38)
    print("\n📞 Test 1: Purchase with virtual38 (has 570 phones)")
    try:
        purchase_url = 'https://5sim.net/v1/user/buy/activation/germany/virtual38/signal'
        response = requests.get(purchase_url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Purchase successful!")
        elif response.status_code == 400:
            print("❌ Bad request - maybe no phones available now")
        elif response.status_code == 401:
            print("❌ Authentication error")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 2: Try with 'any' operator  
    print("\n📞 Test 2: Purchase with 'any' operator")
    try:
        purchase_url = 'https://5sim.net/v1/user/buy/activation/germany/any/signal'
        response = requests.get(purchase_url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 3: Check account balance
    print("\n💰 Test 3: Check account balance")
    try:
        balance_url = 'https://5sim.net/v1/user/profile'
        response = requests.get(balance_url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Balance info: {response.text}")
        
    except Exception as e:
        print(f"❌ Balance check failed: {e}")

if __name__ == "__main__":
    test_purchase_virtual38()
