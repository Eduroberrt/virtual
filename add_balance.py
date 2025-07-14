#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the path
sys.path.append('c:/Users/WDN/Desktop/virtual')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import UserProfile, Transaction
from decimal import Decimal

def add_balance():
    email = 'Nwabuezematthew6@gmail.com'
    amount = Decimal('10.00')
    
    try:
        # Try to get existing user
        user = User.objects.get(email=email)
        print(f'Found user: {user.username} ({user.email})')
    except User.DoesNotExist:
        # Create the user if it doesn't exist
        user = User.objects.create_user(
            username='testuser',
            email=email,
            password='testpass123'
        )
        print(f'Created new user: {user.username} ({user.email})')
    
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    if created:
        print(f'Created user profile for {user.username}')
    
    # Add balance
    old_balance = profile.balance
    old_balance_naira = profile.get_naira_balance()
    
    profile.balance += amount
    profile.save()
    
    # Create transaction
    Transaction.objects.create(
        user=user,
        amount=amount,
        transaction_type='CREDIT',
        description='Test balance for service testing'
    )
    
    new_balance = profile.balance
    new_balance_naira = profile.get_naira_balance()
    
    print(f'Successfully added ${amount} to account')
    print(f'Previous balance: ${old_balance} (₦{old_balance_naira:.2f})')
    print(f'New balance: ${new_balance} (₦{new_balance_naira:.2f})')

if __name__ == '__main__':
    add_balance()
