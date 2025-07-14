#!/usr/bin/env python
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from app.models import UserProfile, Service
import json

def test_services_api():
    print("Testing Services API...")
    
    # Check if services exist
    services_count = Service.objects.count()
    print(f"Services in database: {services_count}")
    
    if services_count > 0:
        first_service = Service.objects.first()
        print(f"First service: {first_service.name} - ${first_service.price}")
    
    # Create test client
    client = Client()
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'password': 'testpass123'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("Created test user")
    
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    # Login
    login_success = client.login(username='testuser', password='testpass123')
    print(f"Login successful: {login_success}")
    
    # Test API endpoint
    response = client.get('/api/services/')
    print(f"API Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        services_data = data.get('services', [])
        print(f"Services returned: {len(services_data)}")
        
        if services_data:
            print(f"First service from API: {services_data[0]['name']} - ${services_data[0]['price']}")
            print("API is working correctly!")
        else:
            print("No services returned from API")
    else:
        print(f"API Error: {response.content}")

if __name__ == "__main__":
    test_services_api()
