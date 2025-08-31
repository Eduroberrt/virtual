#!/usr/bin/env python3
"""
Test Germany + Signal on 5sim API
"""

import requests
import json

def test_germany_signal():
    """Test Germany + Signal availability"""
    
    print("🧪 Testing Germany + Signal on 5sim")
    print("=" * 40)
    
    # API configuration
    api_key = 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODU2NjUxOTYsImlhdCI6MTc1NDEyOTE5NiwicmF5IjoiNTRjNDVhOTUwYTEyNTZiMDUzNDZiNjgyNzc4YzExMDciLCJzdWIiOjM0MDcyODF9.fovz5P51ZwMJCriW6PeVnJxuz6nmU7R2Mb3C8D8a5w0Zhdx7D7f0IIKorsZkSSXeVu7In_k5zUQriExPg6r-A1F11QyR-HsdnvH6RznnQa4yqwK6RpwKVL7AS-6N3xwX29vHQJavuBORHBAKniG_TRgddO9-BhZggMh2WXivLJ-hh9knT3n-O-5gIle-oAv1HZvI62tz_fzumQ1yx-hIhLriyWj4CdqTWN1AgD9qa0mI6PIlGw9m-Oggvd0TzfI5M39x1sPy3DXpLrbHsLgZYo7gwz_WmG7L4SoN2W9kxcaiZca3PllwIqF9gAn1WCkrTppoqyi-IhH8PFv3JVOJZh'
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # Step 1: Get all countries
    print("\n📡 Step 1: Getting all countries...")
    try:
        response = requests.get('https://5sim.net/v1/guest/prices', headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            countries = list(data.keys())
            print(f"✅ Found {len(countries)} countries")
            
            # Look for Germany variations
            germany_variations = [c for c in countries if 'german' in c.lower()]
            print(f"Germany variations found: {germany_variations}")
            
            # Check if 'germany' exists
            if 'germany' in countries:
                print(f"✅ 'germany' found in countries")
                germany_data = data['germany']
                
                # Check for Signal
                if 'signal' in germany_data:
                    print(f"✅ 'signal' found in Germany")
                    signal_data = germany_data['signal']
                    print(f"Available operators: {list(signal_data.keys())}")
                    
                    # Show counts
                    for operator, op_data in signal_data.items():
                        count = op_data.get('count', 0)
                        cost = op_data.get('cost', 0)
                        print(f"  - {operator}: ₽{cost} (Available: {count})")
                        
                else:
                    print(f"❌ 'signal' not found in Germany")
                    print(f"Available services in Germany: {list(germany_data.keys())[:10]}...")
                    
            else:
                print(f"❌ 'germany' not found")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Step 2: Try to buy Germany + Signal
    print(f"\n📡 Step 2: Testing purchase...")
    try:
        # Try with 'any' operator first
        purchase_url = 'https://5sim.net/v1/user/buy/activation/germany/any/signal'
        response = requests.get(purchase_url, headers=headers, timeout=10)
        print(f"Purchase Status: {response.status_code}")
        print(f"Purchase Response: {response.text[:200]}...")
        
    except Exception as e:
        print(f"❌ Purchase test failed: {e}")

if __name__ == "__main__":
    test_germany_signal()
