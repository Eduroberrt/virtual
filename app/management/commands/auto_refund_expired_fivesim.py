from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from app.models import FiveSimOrder, UserProfile, Transaction

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
            default=72,
            help='Maximum age of orders to check (default: 72 hours)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        max_age_hours = options['max_age_hours']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get expired orders that haven't been refunded
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
        
        # Include PENDING, TIMEOUT, and CANCELED orders (but NOT FINISHED, RECEIVED, BANNED)
        # EXPIRED status means we already processed the refund
        expired_orders = FiveSimOrder.objects.filter(
            status__in=['PENDING', 'TIMEOUT', 'CANCELED'],
            created_at__gte=cutoff_time,
            refunded=False  # Only non-refunded orders
        ).select_related('user').prefetch_related('sms_messages')
        
        total_expired = expired_orders.count()
        
        if total_expired == 0:
            self.stdout.write(self.style.SUCCESS('No expired orders to refund'))
            return
        
        self.stdout.write(f'Found {total_expired} potentially refundable orders to process')
        
        refunded_count = 0
        skipped_count = 0
        error_count = 0
        
        for order in expired_orders:
            # Check if order has truly expired using the actual expires_at field
            if timezone.now() <= order.expires_at:
                # Order hasn't expired yet, skip it
                skipped_count += 1
                continue
            
            # Check if SMS was received - if yes, don't refund
            if order.sms_messages.exists():
                if dry_run:
                    self.stdout.write(
                        f'[DRY RUN] Skipping Order #{order.id}: Has SMS messages, no refund needed'
                    )
                skipped_count += 1
                continue
            
            # Calculate how long ago it expired
            time_since_expiry = timezone.now() - order.expires_at
            
            try:
                if dry_run:
                    self.stdout.write(
                        f'[DRY RUN] Would refund Order #{order.id} (5sim:{order.order_id}): '
                        f'{order.product} - ₦{order.price_naira} to {order.user.username} '
                        f'(expired {int(time_since_expiry.total_seconds() / 60)} min ago, status: {order.status})'
                    )
                else:
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
                        
                        # Update order status to EXPIRED and mark as refunded
                        order.status = 'EXPIRED'
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
                            description=f'Auto-refund: Expired Dashboard 1 order #{order.id} - {order.product} ({order.phone_number})'
                        )
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Refunded Order #{order.id} (5sim:{order.order_id}): '
                                f'₦{order.price_naira} to {order.user.username} '
                                f'(expired {int(time_since_expiry.total_seconds() / 60)} min ago)'
                            )
                        )
                
                refunded_count += 1
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error refunding Order #{order.id}: {str(e)}')
                )
        
        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'[DRY RUN] Would have refunded {refunded_count} orders'))
            self.stdout.write(self.style.WARNING(f'[DRY RUN] Would have skipped {skipped_count} orders (not expired or has SMS)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully refunded {refunded_count} orders'))
            self.stdout.write(f'Skipped {skipped_count} orders (not expired or has SMS)')
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed to refund {error_count} orders'))
