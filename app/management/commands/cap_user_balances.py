"""
Management command to cap all user balances at a maximum amount
Useful for testing or cleanup purposes
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from app.models import UserProfile
from decimal import Decimal


class Command(BaseCommand):
    help = 'Cap all user wallet balances at a maximum amount (default: 3000 NGN)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-balance',
            type=float,
            default=3000.0,
            help='Maximum allowed balance (default: 3000)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        max_balance = Decimal(str(options['max_balance']))
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find all users with balance > max_balance
        affected_users = UserProfile.objects.filter(balance__gt=max_balance).select_related('user')
        
        total_count = affected_users.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No users found with balance above the cap'))
            return
        
        # Calculate total reduction
        total_reduction = Decimal('0')
        for profile in affected_users:
            reduction = profile.balance - max_balance
            total_reduction += reduction
        
        # Show summary
        self.stdout.write(f'Users affected: {total_count}')
        self.stdout.write(f'Cap amount: ₦{max_balance}')
        self.stdout.write(f'Total reduction: ₦{total_reduction}')
        self.stdout.write('')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Would cap {total_count} user balances to ₦{max_balance}'
                )
            )
            return
        
        # Ask for confirmation
        confirm = input(f'Cap {total_count} user balances to ₦{max_balance}? (yes/no): ')
        
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('Operation cancelled'))
            return
        
        # Apply the cap
        updated_count = 0
        
        with transaction.atomic():
            for profile in UserProfile.objects.filter(balance__gt=max_balance).select_for_update():
                profile.balance = max_balance
                profile.save()
                updated_count += 1
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Successfully capped {updated_count} user balances to ₦{max_balance}'
            )
        )
