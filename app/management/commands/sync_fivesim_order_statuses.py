"""
Sync 5sim order statuses from the API
This command checks active orders with 5sim and updates their statuses
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import logging

from app.models import FiveSimOrder, FiveSimSMS
from app.fivesim import FiveSimAPI

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync order statuses from 5sim API to keep database up-to-date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )
        parser.add_argument(
            '--max-age-hours',
            type=int,
            default=48,
            help='Maximum age of orders to sync (default: 48 hours)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        max_age_hours = options['max_age_hours']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get API key
        api_key = getattr(settings, 'FIVESIM_API_KEY', None)
        if not api_key:
            self.stdout.write(self.style.ERROR('FIVESIM_API_KEY not configured'))
            return
        
        api_client = FiveSimAPI(api_key)
        
        # Get orders that might need status updates
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
        
        # Only sync orders that are not in a final state
        active_orders = FiveSimOrder.objects.filter(
            created_at__gte=cutoff_time,
            status__in=['PENDING', 'RECEIVED']  # Exclude FINISHED, CANCELED, TIMEOUT, EXPIRED, BANNED
        ).order_by('-created_at')
        
        total_orders = active_orders.count()
        
        if total_orders == 0:
            self.stdout.write(self.style.SUCCESS('No active orders to sync'))
            return
        
        self.stdout.write(f'Found {total_orders} active orders to sync')
        
        synced_count = 0
        status_changed_count = 0
        error_count = 0
        
        for order in active_orders:
            try:
                # Call 5sim API to get current status
                result = api_client.check_order(order.order_id)
                
                old_status = order.status
                new_status = result['status']
                
                if dry_run:
                    if old_status != new_status:
                        self.stdout.write(
                            f'[DRY RUN] Would update Order #{order.id} (5sim:{order.order_id}): '
                            f'{old_status} → {new_status}'
                        )
                        status_changed_count += 1
                else:
                    # Update order status
                    order.status = new_status
                    order.save()
                    
                    # Update SMS messages if present
                    if result.get('sms'):
                        # Clear existing SMS messages
                        order.sms_messages.all().delete()
                        
                        # Create new SMS records
                        for sms_data in result['sms']:
                            from datetime import datetime
                            sms_date = datetime.fromisoformat(sms_data['date'].replace('Z', '+00:00'))
                            FiveSimSMS.objects.create(
                                order=order,
                                sender=sms_data.get('sender', ''),
                                text=sms_data.get('text', ''),
                                code=sms_data.get('code', ''),
                                date=sms_date,
                            )
                    
                    if old_status != new_status:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Updated Order #{order.id} (5sim:{order.order_id}): '
                                f'{old_status} → {new_status}'
                            )
                        )
                        status_changed_count += 1
                
                synced_count += 1
                
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                
                # Handle specific API errors
                if 'order not found' in error_msg.lower() or '404' in error_msg:
                    if not dry_run:
                        # Mark as expired if 5sim says it doesn't exist
                        order.status = 'EXPIRED'
                        order.save()
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Order #{order.id} (5sim:{order.order_id}) not found on 5sim, marked as EXPIRED'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Error syncing Order #{order.id} (5sim:{order.order_id}): {error_msg}'
                        )
                    )
                    logger.error(f'Status sync error for order {order.id}: {error_msg}')
        
        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY RUN] Would have synced {synced_count} orders')
            )
            self.stdout.write(
                self.style.WARNING(f'[DRY RUN] Would have updated {status_changed_count} statuses')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully synced {synced_count} orders')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Updated {status_changed_count} order statuses')
            )
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed to sync {error_count} orders'))
