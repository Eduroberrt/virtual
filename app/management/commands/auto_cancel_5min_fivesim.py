"""
Management command to auto-cancel 5sim orders after 5 minutes if no SMS received
This ensures users don't wait the full 20-minute timeout period
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from app.models import FiveSimOrder, UserProfile, Transaction
from app.fivesim import FiveSimAPI
from django.conf import settings


class Command(BaseCommand):
    help = 'Auto-cancel 5sim orders after 5 minutes if no SMS received'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cancelled without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get API key
        api_key = getattr(settings, 'FIVESIM_API_KEY', None)
        if not api_key:
            self.stdout.write(self.style.ERROR('FIVESIM_API_KEY not configured'))
            return
        
        api_client = FiveSimAPI(api_key)
        
        # Find orders waiting for > 5 minutes without SMS
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        
        # Only check PENDING and RECEIVED orders (active statuses)
        waiting_orders = FiveSimOrder.objects.filter(
            status__in=['PENDING', 'RECEIVED'],
            created_at__lte=five_minutes_ago,
            refunded=False  # Only non-refunded orders
        ).select_related('user').prefetch_related('sms_messages')
        
        total_orders = waiting_orders.count()
        
        if total_orders == 0:
            self.stdout.write(self.style.SUCCESS('No orders waiting > 5 minutes'))
            return
        
        self.stdout.write(f'Found {total_orders} orders waiting > 5 minutes')
        
        cancelled_count = 0
        skipped_count = 0
        error_count = 0
        
        for order in waiting_orders:
            # Check if SMS was received - if yes, skip
            if order.sms_messages.exists():
                if dry_run:
                    self.stdout.write(
                        f'[DRY RUN] Skipping Order #{order.id}: Has SMS messages'
                    )
                skipped_count += 1
                continue
            
            # Calculate wait time
            wait_time = timezone.now() - order.created_at
            wait_minutes = wait_time.total_seconds() / 60
            
            try:
                if dry_run:
                    self.stdout.write(
                        f'[DRY RUN] Would cancel Order #{order.id} (5sim:{order.order_id}): '
                        f'{order.product} - ₦{order.price_naira} to {order.user.username} '
                        f'(waiting {wait_minutes:.1f} minutes)'
                    )
                    cancelled_count += 1
                else:
                    # Call 5sim API to cancel (same as cancel button)
                    try:
                        result = api_client.cancel_order(order.order_id)
                    except Exception as api_error:
                        # Continue even if API call fails - we'll still refund
                        pass
                    
                    # Process refund with triple protection
                    with transaction.atomic():
                        # Reload order with lock to prevent race conditions
                        order = FiveSimOrder.objects.select_for_update().get(order_id=order.order_id)
                        
                        # Check if already refunded (double-refund protection)
                        if order.refunded:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'⚠ Order #{order.id} (5sim:{order.order_id}) already refunded, skipping'
                                )
                            )
                            skipped_count += 1
                            continue
                        
                        # Update order status to CANCELLED and mark as refunded
                        order.status = 'CANCELED'
                        order.refunded = True
                        order.save()
                        
                        # Refund user with locked profile
                        profile = UserProfile.objects.select_for_update().get(user=order.user)
                        profile.balance += order.price_naira
                        profile.save()
                        
                        # Log transaction
                        Transaction.objects.create(
                            user=order.user,
                            amount=order.price_naira,
                            transaction_type='REFUND',
                            description=f'Auto-cancel: No SMS after 5 minutes - {order.product} ({order.phone_number})'
                        )
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Cancelled Order #{order.id} (5sim:{order.order_id}): '
                                f'₦{order.price_naira} to {order.user.username} '
                                f'(waited {wait_minutes:.1f} minutes)'
                            )
                        )
                    
                    cancelled_count += 1
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error cancelling Order #{order.id}: {str(e)}')
                )
        
        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'[DRY RUN] Would have cancelled {cancelled_count} orders'))
            self.stdout.write(self.style.WARNING(f'[DRY RUN] Would have skipped {skipped_count} orders (has SMS)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully cancelled {cancelled_count} orders'))
            self.stdout.write(f'Skipped {skipped_count} orders (has SMS)')
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed to cancel {error_count} orders'))
