#!/usr/bin/env python3
"""
Explore 5sim API data structure
"""

import requests
import json

def explore_5sim_data():
    """Explore 5sim API data structure"""
    
    print("🔍 Exploring 5sim API Data Structure")
    print("=" * 45)
    
    try:
        headers = {'Accept': 'application/json'}
        response = requests.get('https://5sim.net/v1/guest/prices', headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully got data")
            
            # Show available countries
            countries = list(data.keys())
            print(f"\n📍 Available countries ({len(countries)} total):")
            for i, country in enumerate(countries[:10]):  # First 10
                print(f"  {i+1}. {country}")
            if len(countries) > 10:
                print(f"  ... and {len(countries) - 10} more")
            
            # Check for Russia variations
            russia_variants = [c for c in countries if 'russia' in c.lower() or 'russ' in c.lower()]
            print(f"\n🇷🇺 Russia-related countries: {russia_variants}")
            
            # Check the first country's structure
            first_country = countries[0]
            first_country_data = data[first_country]
            print(f"\n📋 Sample country structure ({first_country}):")
            
            if isinstance(first_country_data, dict):
                products = list(first_country_data.keys())
                print(f"  Products ({len(products)} total): {products[:5]}...")
                
                # Check for WhatsApp variations
                whatsapp_variants = [p for p in products if 'whatsapp' in p.lower() or 'whats' in p.lower()]
                print(f"  WhatsApp-related products: {whatsapp_variants}")
                
                # Show structure of first product
                if products:
                    first_product = products[0]
                    first_product_data = first_country_data[first_product]
                    print(f"\n🎯 Sample product structure ({first_product}):")
                    
                    if isinstance(first_product_data, dict):
                        operators = list(first_product_data.keys())
                        print(f"    Operators: {operators[:3]}...")
                        
                        # Show first operator data
                        if operators:
                            first_operator = operators[0]
                            operator_data = first_product_data[first_operator]
                            print(f"    Sample operator data ({first_operator}): {operator_data}")
            
            # Try to find a working combination
            print(f"\n🔍 Looking for working country/product combinations...")
            working_combinations = []
            
            for country in countries[:3]:  # Check first 3 countries
                country_data = data[country]
                if isinstance(country_data, dict):
                    for product in list(country_data.keys())[:3]:  # Check first 3 products
                        product_data = country_data[product]
                        if isinstance(product_data, dict) and len(product_data) > 0:
                            # Check if any operator has available numbers
                            for operator, op_data in product_data.items():
                                if isinstance(op_data, dict) and op_data.get('count', 0) > 0:
                                    working_combinations.append((country, product, operator))
                                    break
                        if len(working_combinations) >= 3:
                            break
                if len(working_combinations) >= 3:
                    break
            
            print(f"💡 Working combinations found:")
            for country, product, operator in working_combinations:
                op_data = data[country][product][operator]
                print(f"  - {country}/{product}/{operator}: ₽{op_data.get('cost')} (Available: {op_data.get('count')})")
        
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    explore_5sim_data()
