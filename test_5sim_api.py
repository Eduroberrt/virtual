#!/usr/bin/env python3
"""
Quick test of 5sim guest API endpoints
"""

import requests
import json

def test_5sim_api():
    """Test the 5sim guest API endpoints directly"""
    
    headers = {
        'Accept': 'application/json',
    }
    
    print("=== Testing 5sim Guest API ===\n")
    
    # Test 1: Get all prices
    print("1. Testing /guest/prices endpoint...")
    try:
        response = requests.get('https://5sim.net/v1/guest/prices', headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            countries = list(data.keys())[:5]  # First 5 countries
            print(f"✅ Success! Found {len(data)} countries")
            print(f"Sample countries: {countries}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 2: Get products for a specific country
    print("2. Testing /guest/products/england/any endpoint...")
    try:
        response = requests.get('https://5sim.net/v1/guest/products/england/any', headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            products = list(data.keys())[:5]  # First 5 products
            print(f"✅ Success! Found {len(data)} products for England")
            print(f"Sample products: {products}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 3: Get prices for specific country and product
    print("3. Testing /guest/prices?country=england&product=facebook endpoint...")
    try:
        params = {'country': 'england', 'product': 'facebook'}
        response = requests.get('https://5sim.net/v1/guest/prices', headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Got pricing data")
            print(f"Response structure: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_5sim_api()
