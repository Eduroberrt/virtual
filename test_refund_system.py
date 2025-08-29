"""
Test script to verify the refund system implementation
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import FiveSimOrder, UserProfile, Transaction
from django.utils import timezone
from decimal import Decimal

def test_refund_system():
    print("=== Testing Refund System Implementation ===\n")
    
    # Test 1: Check if EXPIRED status is available
    print("1. Testing EXPIRED status option...")
    status_choices = dict(FiveSimOrder.STATUS_CHOICES)
    if 'EXPIRED' in status_choices:
        print("✅ EXPIRED status is available:", status_choices['EXPIRED'])
    else:
        print("❌ EXPIRED status is NOT available")
        print("Available statuses:", list(status_choices.keys()))
    
    # Test 2: Check Transaction REFUND type
    print("\n2. Testing REFUND transaction type...")
    transaction_types = dict(Transaction.TRANSACTION_TYPES)
    if 'REFUND' in transaction_types:
        print("✅ REFUND transaction type is available:", transaction_types['REFUND'])
    else:
        print("❌ REFUND transaction type is NOT available")
        print("Available types:", list(transaction_types.keys()))
    
    # Test 3: Check user balance functionality
    print("\n3. Testing UserProfile balance functionality...")
    try:
        # Get first user or create test user
        user = User.objects.first()
        if user:
            profile = UserProfile.objects.get_or_create(user=user)[0]
            print(f"✅ User balance functionality works. Balance: ₦{profile.balance}")
        else:
            print("⚠️  No users found in database")
    except Exception as e:
        print(f"❌ Error testing balance: {e}")
    
    # Test 4: Check active orders count functionality
    print("\n4. Testing active orders count...")
    try:
        current_time = timezone.now()
        if user:
            active_count = FiveSimOrder.objects.filter(
                user=user,
                status__in=['PENDING', 'RECEIVED'],
                expires_at__gt=current_time
            ).count()
            print(f"✅ Active orders count works. User has {active_count} active orders")
        else:
            print("⚠️  No user to test with")
    except Exception as e:
        print(f"❌ Error counting active orders: {e}")
    
    # Test 5: Summary of recent orders
    print("\n5. Recent orders summary...")
    try:
        recent_orders = FiveSimOrder.objects.all()[:5]
        if recent_orders:
            print("Recent orders:")
            for order in recent_orders:
                print(f"  - {order.user.username}: {order.product} ({order.status}) - ₦{order.price_naira}")
        else:
            print("⚠️  No orders found in database")
    except Exception as e:
        print(f"❌ Error getting recent orders: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_refund_system()
