#!/usr/bin/env python3
"""
Test the new pricing logic - most expensive operator
"""

import requests
import json

def test_new_pricing_logic():
    """Test that we get the most expensive operator price"""
    
    print("🧪 Testing New Pricing Logic (Most Expensive Operator)")
    print("=" * 60)
    
    # API configuration
    api_key = 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODU2NjUxOTYsImlhdCI6MTc1NDEyOTE5NiwicmF5IjoiNTRjNDVhOTUwYTEyNTZiMDUzNDZiNjgyNzc4YzExMDciLCJzdWIiOjM0MDcyODF9.fovz5P51ZwMJCriW6PeVnJxuz6nmU7R2Mb3C8D8a5w0Zhdx7D7f0IIKorsZkSSXeVu7In_k5zUQriExPg6r-A1F11QyR-HsdnvH6RznnQa4yqwK6RpwKVL7AS-6N3xwX29vHQJavuBORHBAKniG_TRgddO9-BhZggMh2WXivLJ-hh9knT3n-O-5gIle-oAv1HZvI62tz_fzumQ1yx-hIhLriyWj4CdqTWN1AgD9qa0mI6PIlGw9m-Oggvd0TzfI5M39x1sPy3DXpLrbHsLgZYo7gwz_WmG7L4SoN2W9kxcaiZca3PllwIqF9gAn1WCkrTppoqyi-IhH8PFv3JVeHAw'
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    print("\n📊 Getting Germany + Signal pricing data...")
    try:
        response = requests.get('https://5sim.net/v1/guest/prices?country=germany&product=signal', timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'germany' in data and 'signal' in data['germany']:
                operators = data['germany']['signal']
                print("\nAll Germany + Signal operators:")
                
                available_prices = []
                all_prices = []
                
                for op, info in operators.items():
                    count = info.get('count', 0)
                    cost = info.get('cost', 0)
                    print(f"  - {op}: ₽{cost} ({count} available)")
                    
                    all_prices.append(cost)
                    if count > 0:  # Only available operators
                        available_prices.append(cost)
                
                print(f"\nPricing Analysis:")
                print(f"All prices: {sorted(all_prices)}")
                print(f"Available prices: {sorted(available_prices)}")
                
                if available_prices:
                    min_available = min(available_prices)
                    max_available = max(available_prices)
                    min_all = min(all_prices)
                    max_all = max(all_prices)
                    
                    print(f"\n📈 Price Comparison:")
                    print(f"Cheapest (all): ₽{min_all}")
                    print(f"Cheapest (available): ₽{min_available}")
                    print(f"Most expensive (available): ₽{max_available}")
                    print(f"Most expensive (all): ₽{max_all}")
                    
                    print(f"\n💰 Pricing Strategy Impact:")
                    print(f"OLD (cheapest): ₽{min_all} = ₦{min_all * 25}")
                    print(f"NEW (most expensive available): ₽{max_available} = ₦{max_available * 25}")
                    print(f"Price increase: ₦{(max_available - min_all) * 25}")
                    
                    # Show profit scenarios
                    user_pays_old = (min_all * 25) * 1.4  # 40% profit margin
                    user_pays_new = (max_available * 25) * 1.4  # 40% profit margin
                    actual_cost = max_available * 25
                    
                    print(f"\n🏦 Business Impact:")
                    print(f"User pays (OLD pricing): ₦{user_pays_old:.0f}")
                    print(f"User pays (NEW pricing): ₦{user_pays_new:.0f}")
                    print(f"Actual cost (worst case): ₦{actual_cost}")
                    print(f"Profit (OLD): ₦{user_pays_old - actual_cost:.0f}")
                    print(f"Profit (NEW): ₦{user_pays_new - actual_cost:.0f}")
                else:
                    print("❌ No available operators found!")
                    
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_new_pricing_logic()
