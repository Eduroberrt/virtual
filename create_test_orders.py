"""
Create Test Expired Orders
This script creates fake expired orders for testing the refund system
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import FiveSimOrder, UserProfile
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

def create_test_expired_orders():
    """Create some test expired orders for refund testing"""
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.username}")
    else:
        print(f"✅ Using existing user: {user.username}")
    
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'balance': Decimal('1000.00')}
    )
    
    if created:
        print(f"✅ Created user profile with ₦{profile.balance} balance")
    else:
        print(f"✅ User has ₦{profile.balance} balance")
    
    # Create expired orders (expired 5 minutes ago)
    expired_time = timezone.now() - timedelta(minutes=5)
    
    test_orders = [
        {
            'order_id': 12345001,
            'phone_number': '+79991234567',
            'product': 'telegram',
            'price': Decimal('5.50'),
            'price_naira': Decimal('137.50'),
        },
        {
            'order_id': 12345002,
            'phone_number': '+79991234568',
            'product': 'whatsapp',
            'price': Decimal('4.00'),
            'price_naira': Decimal('100.00'),
        },
        {
            'order_id': 12345003,
            'phone_number': '+79991234569',
            'product': 'instagram',
            'price': Decimal('6.00'),
            'price_naira': Decimal('150.00'),
        }
    ]
    
    created_orders = []
    for order_data in test_orders:
        # Check if order already exists
        existing = FiveSimOrder.objects.filter(order_id=order_data['order_id']).first()
        if existing:
            print(f"⚠️  Order {order_data['order_id']} already exists")
            continue
            
        order = FiveSimOrder.objects.create(
            user=user,
            order_id=order_data['order_id'],
            order_type='ACTIVATION',
            phone_number=order_data['phone_number'],
            country='russia',
            operator='any',
            product=order_data['product'],
            price=order_data['price'],
            price_naira=order_data['price_naira'],
            status='PENDING',
            expires_at=expired_time,  # Already expired!
            forwarding=False,
            reuse_enabled=False,
            voice_enabled=False,
        )
        created_orders.append(order)
        print(f"✅ Created expired order: {order.product} ({order.phone_number}) - ₦{order.price_naira}")
    
    if created_orders:
        total_refund = sum(order.price_naira for order in created_orders)
        print(f"\n🎯 Created {len(created_orders)} expired orders")
        print(f"💰 Total refund amount: ₦{total_refund}")
        print(f"📱 User current balance: ₦{profile.balance}")
        print(f"💳 Expected balance after refund: ₦{profile.balance + total_refund}")
        
        print(f"\n🧪 Now run:")
        print(f"   python manage.py auto_refund_expired_fivesim --dry-run")
        print(f"   python manage.py auto_refund_expired_fivesim")
    else:
        print("\n⚠️  No new orders created (they may already exist)")

if __name__ == "__main__":
    create_test_expired_orders()
