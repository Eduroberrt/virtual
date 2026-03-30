"""
Management command to check for expired rentals and issue refunds
Run this periodically via cron or task scheduler
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from app.models import Rental, Transaction
from app.mtelsms import get_mtelsms_client, MTelSMSException
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for expired rentals and automatically issue refunds'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of rentals to check in one run'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        # Get active rentals that might be expired
        active_rentals = Rental.objects.filter(
            status='WAITING'
        ).order_by('-created_at')[:limit]
        
        self.stdout.write(f"Checking {active_rentals.count()} active rentals for expiration...")
        
        expired_count = 0
        refunded_count = 0
        error_count = 0
        
        client = get_mtelsms_client()
        
        for rental in active_rentals:
            try:
                # Check status with MTelSMS
                status, code, phone_number, time_remaining = client.get_code(
                    rental_id=rental.rental_id
                )
                
                # Check if expired
                if time_remaining <= 0 and status == 'WAITING':
                    with transaction.atomic():
                        # Mark as expired
                        rental.status = 'EXPIRED'
                        rental.save()
                        expired_count += 1
                        
                        # Issue refund if not already refunded
                        if not rental.refund_issued:
                            profile = rental.user.profile
                            profile.balance += rental.price_paid
                            profile.save()
                            
                            # Log refund transaction
                            Transaction.objects.create(
                                user=rental.user,
                                amount=rental.price_paid,
                                transaction_type='REFUND',
                                description=f'Automatic refund for expired rental {rental.phone_number}'
                            )
                            
                            rental.refund_issued = True
                            rental.save()
                            refunded_count += 1
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✓ Expired and refunded: {rental.rental_id} - {rental.phone_number}"
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"⚠ Already refunded: {rental.rental_id}"
                                )
                            )
                
                elif status == 'RECEIVED' and code:
                    # Update status if SMS was received
                    rental.status = 'RECEIVED'
                    rental.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ SMS received: {rental.rental_id}"
                        )
                    )
                
            except MTelSMSException as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Error checking {rental.rental_id}: {str(e)}"
                    )
                )
                logger.error(f"Error checking rental {rental.rental_id}: {str(e)}")
            
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Unexpected error for {rental.rental_id}: {str(e)}"
                    )
                )
                logger.error(f"Unexpected error checking rental {rental.rental_id}: {str(e)}")
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"✓ Checked: {active_rentals.count()} rentals"))
        self.stdout.write(self.style.WARNING(f"⏰ Expired: {expired_count} rentals"))
        self.stdout.write(self.style.SUCCESS(f"💰 Refunded: {refunded_count} rentals"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"✗ Errors: {error_count}"))
        self.stdout.write("="*50)
