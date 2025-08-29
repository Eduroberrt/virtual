"""
Management command to recover orphaned 5sim purchases
Use this when purchases succeed on 5sim but fail to save locally due to API response issues
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.transaction import atomic
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from app.models import FiveSimOrder, UserProfile, Transaction
from app.fivesim import FiveSimAPI
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Recover orphaned 5sim purchases that succeeded on 5sim but failed to save locally'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be recovered without making changes',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Check only for specific user (username)',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Check orders from last N hours (default: 24)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        username = options.get('user')
        hours = options['hours']
        
        self.stdout.write(f"🔍 Checking for orphaned purchases from last {hours} hours...")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        try:
            # Initialize 5sim API
            api_client = FiveSimAPI(settings.FIVESIM_API_KEY)
            
            # Get recent orders from 5sim
            recent_orders = api_client.get_recent_orders(limit=50)
            
            if not recent_orders:
                self.stdout.write(self.style.WARNING("No recent orders found on 5sim"))
                return
            
            self.stdout.write(f"📋 Found {len(recent_orders)} recent orders on 5sim")
            
            # Filter orders from specified time range
            cutoff_time = timezone.now() - timedelta(hours=hours)
            orphaned_orders = []
            
            for order in recent_orders:
                try:
                    # Parse order creation time
                    created_at_str = order.get('created_at', '')
                    if created_at_str:
                        # Try different datetime formats
                        for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S']:
                            try:
                                created_at = datetime.strptime(created_at_str, fmt)
                                if created_at.tzinfo is None:
                                    created_at = timezone.make_aware(created_at)
                                break
                            except ValueError:
                                continue
                        else:
                            # Couldn't parse date, skip this order
                            continue
                        
                        # Skip orders older than cutoff
                        if created_at < cutoff_time:
                            continue
                    
                    # Check if this order exists in our database
                    order_id = order.get('id')
                    if not order_id:
                        continue
                    
                    if not FiveSimOrder.objects.filter(order_id=order_id).exists():
                        orphaned_orders.append(order)
                        
                except Exception as e:
                    logger.error(f"Error processing order {order}: {e}")
                    continue
            
            if not orphaned_orders:
                self.stdout.write(self.style.SUCCESS("✅ No orphaned orders found"))
                return
            
            self.stdout.write(f"🚨 Found {len(orphaned_orders)} orphaned orders:")
            
            recovered_count = 0
            for order in orphaned_orders:
                try:
                    order_id = order.get('id')
                    phone = order.get('phone', '')
                    product = order.get('product', '')
                    price = order.get('price', 0)
                    status = order.get('status', 'PENDING')
                    
                    self.stdout.write(f"  - Order {order_id}: {product} ({phone}) - ${price} - {status}")
                    
                    if not dry_run:
                        # Try to determine which user this belongs to
                        # This is tricky since we don't have user info in the 5sim order
                        # For now, we'll skip auto-recovery and require manual intervention
                        self.stdout.write(self.style.WARNING(f"    ⚠️  Cannot auto-recover without user info. Manual intervention required."))
                        
                except Exception as e:
                    logger.error(f"Error processing orphaned order {order}: {e}")
                    continue
            
            if dry_run:
                self.stdout.write(self.style.WARNING(f"DRY RUN: Would attempt to recover {len(orphaned_orders)} orders"))
            else:
                self.stdout.write(self.style.SUCCESS(f"✅ Recovery check completed. Found {len(orphaned_orders)} orphaned orders requiring manual intervention."))
                self.stdout.write("💡 To recover these orders, please:")
                self.stdout.write("   1. Check the 5sim dashboard to see which user made each purchase")
                self.stdout.write("   2. Manually create FiveSimOrder records for each orphaned purchase")
                self.stdout.write("   3. Ensure user balances are correctly adjusted")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error during recovery check: {str(e)}"))
            logger.error(f"Recovery command failed: {e}")
