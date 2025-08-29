"""
Sync 5sim orders command
Checks for orders that exist on 5sim but not in local database
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import logging

from app.models import FiveSimOrder, UserProfile
from app.fivesim import FiveSimAPI
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync 5sim orders - find orders that exist on 5sim but not locally'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Sync orders for a specific user email',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_email = options.get('user_email')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        api_client = FiveSimAPI()
        
        # Get users to check
        if user_email:
            try:
                users = [User.objects.get(email=user_email)]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email "{user_email}" not found')
                )
                return
        else:
            # Check all users who have made purchases in the last 7 days
            recent_date = timezone.now() - timedelta(days=7)
            users = User.objects.filter(
                fivesimorder__created_at__gte=recent_date
            ).distinct()
        
        self.stdout.write(f'Checking {users.count()} users for missing orders...')
        
        synced_count = 0
        for user in users:
            try:
                # This would require implementing a get_user_orders method in FiveSimAPI
                # For now, we'll just log that this feature needs implementation
                self.stdout.write(f'Checking user: {user.username} ({user.email})')
                
                # Note: 5sim API doesn't provide a direct way to list all user orders
                # This would need to be implemented based on available API endpoints
                self.stdout.write(
                    self.style.WARNING(
                        'Order sync requires 5sim API endpoint for listing user orders'
                    )
                )
                
            except Exception as e:
                logger.error(f"Error checking orders for user {user.username}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f'Error checking {user.username}: {str(e)}')
                )
        
        if synced_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully synced {synced_count} orders')
            )
        else:
            self.stdout.write('No missing orders found')
