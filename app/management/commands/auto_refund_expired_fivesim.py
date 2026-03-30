from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from app.models import FiveSimOrder, UserProfile, Transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatically refund expired 5sim orders that never received SMS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be refunded without actually doing it',
        )
        parser.add_argument(
            '--max-age-hours',
            type=int,
            default=24,
            help='Maximum age of orders to check (default: 24 hours)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        max_age_hours = options['max_age_hours']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get expired orders that haven't been refunded
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
        
        expired_orders = FiveSimOrder.objects.filter(
            status='PENDING',  # Still waiting for SMS
            refunded=False,
            created_at__gte=cutoff_time
        ).select_related('user')
        
        total_expired = expired_orders.count()
        
        if total_expired == 0:
            self.stdout.write(self.style.SUCCESS('No expired orders to refund'))
            return
        
        self.stdout.write(f'Found {total_expired} expired orders to process')
        
        refunded_count = 0
        error_count = 0
        
        for order in expired_orders:
            # Check if order is truly expired (> 20 minutes old)
            age = timezone.now() - order.created_at
            if age < timedelta(minutes=20):
                continue
            
            try:
                if dry_run:
                    self.stdout.write(
                        f'[DRY RUN] Would refund Order #{order.id}: '
                        f'{order.service} - ₦{order.price} to {order.user.username}'
                    )
                else:
                    with transaction.atomic():
                        # Update order status
                        order.status = 'EXPIRED'
                        order.refunded = True
                        order.save()
                        
                        # Refund user
                        profile, _ = UserProfile.objects.get_or_create(user=order.user)
                        profile.balance += order.price
                        profile.save()
                        
                        # Log transaction
                        Transaction.objects.create(
                            user=order.user,
                            amount=order.price,
                            transaction_type='REFUND',
                            description=f'Auto-refund: Expired 5sim order #{order.id} - {order.service}'
                        )
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Refunded Order #{order.id}: ₦{order.price} to {order.user.username}'
                            )
                        )
                
                refunded_count += 1
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error refunding Order #{order.id}: {str(e)}')
                )
                logger.error(f'Auto-refund error for order {order.id}: {str(e)}')
        
        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'[DRY RUN] Would have refunded {refunded_count} orders'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully refunded {refunded_count} orders'))
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed to refund {error_count} orders'))
