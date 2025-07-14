from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import UserProfile, Transaction
from decimal import Decimal
import uuid

class Command(BaseCommand):
    help = 'Add balance to a specific user for testing purposes'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email address')
        parser.add_argument('amount', type=float, help='Amount to add in USD')
        parser.add_argument('--description', type=str, default='Test balance credit', help='Transaction description')

    def handle(self, *args, **options):
        email = options['email']
        amount = Decimal(str(options['amount']))
        description = options['description']

        try:
            # Get the user
            user = User.objects.get(email=email)
            self.stdout.write(f"Found user: {user.username} ({user.email})")

            # Get or create user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            if created:
                self.stdout.write(f"Created new user profile for {user.username}")
            
            # Store old balance
            old_balance = profile.balance
            old_balance_naira = profile.get_naira_balance()
            
            # Add the balance
            profile.balance += amount
            profile.save()
            
            # Create transaction record
            Transaction.objects.create(
                user=user,
                amount=amount,
                transaction_type='CREDIT',
                description=description
            )
            
            # Calculate new balances
            new_balance = profile.balance
            new_balance_naira = profile.get_naira_balance()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully added ${amount} to {user.username}\'s account\n'
                    f'Previous balance: ${old_balance} (₦{old_balance_naira})\n'
                    f'New balance: ${new_balance} (₦{new_balance_naira})'
                )
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email "{email}" not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error adding balance: {str(e)}')
            )
