from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from app.models import FiveSimOrder, UserProfile, Transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatically refund expired 5sim orders that have not received SMS codes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be refunded without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find orders that have expired and are still pending (no SMS received)
        current_time = timezone.now()
        
        expired_orders = FiveSimOrder.objects.filter(
            status__in=['PENDING', 'RECEIVED'],  # Orders waiting for SMS
            expires_at__lte=current_time,  # Already expired
        ).exclude(
            # Don't refund if SMS messages already received
            sms_messages__text__isnull=False
        ).exclude(
            # Don't refund if already cancelled/finished
            status__in=['CANCELED', 'FINISHED']
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would refund {expired_orders.count()} expired orders')
            )
            for order in expired_orders[:10]:  # Show first 10
                self.stdout.write(
                    f'  - {order.user.username}: {order.product} ({order.phone_number}) - ₦{order.price_naira:.2f}'
                )
            return
        
        refunded_count = 0
        error_count = 0
        total_refunded = 0
        
        for order in expired_orders:
            try:
                with transaction.atomic():
                    # Get user profile
                    user_profile = UserProfile.objects.get(user=order.user)
                    
                    # Credit the refund amount
                    refund_amount = order.price_naira
                    user_profile.balance += refund_amount
                    user_profile.save()
                    
                    # Create refund transaction
                    Transaction.objects.create(
                        user=order.user,
                        amount=refund_amount,
                        transaction_type='REFUND',
                        description=f'Auto-refund for expired 5sim order: {order.product} ({order.phone_number})',
                        rental=None,
                    )
                    
                    # Update order status to indicate it was auto-cancelled due to expiry
                    order.status = 'EXPIRED'
                    order.save()
                    
                    refunded_count += 1
                    total_refunded += refund_amount
                    
                    self.stdout.write(
                        f'Refunded ₦{refund_amount:.2f} to {order.user.username} for expired order {order.order_id}'
                    )
                    
            except Exception as e:
                error_count += 1
                logger.error(f'Failed to refund expired order {order.order_id}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(f'ERROR refunding order {order.order_id}: {str(e)}')
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Auto-refund completed: {refunded_count} orders refunded, '
                f'₦{total_refunded:.2f} total refunded, {error_count} errors'
            )
        )
