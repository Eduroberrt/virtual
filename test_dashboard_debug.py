#!/usr/bin/env python3

import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.append('c:\\Users\\WDN\\Desktop\\virtual')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import FiveSimOrder, FiveSimSMS
from django.utils import timezone

def debug_dashboard():
    print("🔍 DASHBOARD DEBUG REPORT")
    print("=" * 50)
    
    # Check users
    users = User.objects.all()
    print(f"👥 Total users: {users.count()}")
    for user in users:
        print(f"   - {user.username} (ID: {user.id})")
    
    # Check orders
    orders = FiveSimOrder.objects.all()
    print(f"\n📦 Total orders: {orders.count()}")
    
    if orders.exists():
        print("\n📋 Orders breakdown:")
        for order in orders.order_by('-created_at')[:10]:
            print(f"   - Order {order.order_id}")
            print(f"     User: {order.user.username}")
            print(f"     Phone: {order.phone_number}")
            print(f"     Country: {order.country}")
            print(f"     Product: {order.product}")
            print(f"     Status: {order.status}")
            print(f"     Created: {order.created_at}")
            print(f"     Expires: {order.expires_at}")
            
            # Check SMS messages for this order
            sms_messages = order.sms_messages.all()
            print(f"     SMS messages: {sms_messages.count()}")
            for sms in sms_messages:
                print(f"       - Text: {sms.text}")
                print(f"       - Code: {sms.code}")
            print()
    
    # Check current time
    print(f"⏰ Current time: {timezone.now()}")
    
    # Check active orders
    current_time = timezone.now()
    active_orders = FiveSimOrder.objects.filter(
        expires_at__gt=current_time
    ).exclude(status='CANCELED')
    print(f"🔄 Active orders: {active_orders.count()}")
    
    # Check orders with SMS
    orders_with_sms = FiveSimOrder.objects.filter(
        sms_messages__isnull=False
    ).distinct()
    print(f"📱 Orders with SMS: {orders_with_sms.count()}")

if __name__ == "__main__":
    debug_dashboard()
