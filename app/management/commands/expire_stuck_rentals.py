"""
Management command to find and expire rentals that are stuck in WAITING status
even though they've expired on MTelSMS
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from app.models import Rental, Transaction
from app.mtelsms import get_mtelsms_client, MTelSMSException
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check all WAITING rentals and expire those that have expired on MTelSMS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of rentals to check'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        # Get all WAITING rentals
        waiting_rentals = Rental.objects.filter(status='WAITING')[:limit]
        
        self.stdout.write(f'Found {waiting_rentals.count()} WAITING rentals to check')
        
        client = get_mtelsms_client()
        expired_count = 0
        error_count = 0
        
        for rental in waiting_rentals:
            try:
                # Try to get code/status from MTelSMS
                status, code, phone_number, time_remaining = client.get_code(
                    rental_id=rental.rental_id
                )
                
                # Check if expired
                if time_remaining <= 0:
                    self.stdout.write(f'Expiring rental {rental.rental_id} - time_remaining: {time_remaining}')
                    self._expire_rental(rental)
                    expired_count += 1
                    
            except MTelSMSException as e:
                error_msg = str(e)
                
                # If MTelSMS says it's invalid/expired, mark it as expired
                if 'Invalid Service ID' in error_msg or 'Record Expired' in error_msg or 'expired' in error_msg.lower():
                    self.stdout.write(f'Expiring rental {rental.rental_id} - MTelSMS error: {error_msg}')
                    self._expire_rental(rental)
                    expired_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f'Error checking {rental.rental_id}: {error_msg}'))
                    error_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Expired {expired_count} rentals, {error_count} errors'))
    
    def _expire_rental(self, rental):
        """Expire a rental and issue refund"""
        from app.models import UserProfile
        
        with transaction.atomic():
            # Reload rental with lock to prevent race conditions
            rental = Rental.objects.select_for_update().get(rental_id=rental.rental_id)
            
            # Check if already refunded (double-refund protection)
            if rental.refunded:
                return
            
            # Mark as expired and refunded
            rental.status = 'EXPIRED'
            rental.refunded = True
            rental.save()
            
            # Issue refund with locked profile
            profile = UserProfile.objects.select_for_update().get(user=rental.user)
            profile.balance += rental.price
            profile.save()
            
            Transaction.objects.create(
                user=rental.user,
                amount=rental.price,
                transaction_type='REFUND',
                description=f'Auto-refund: Expired rental - {rental.phone_number}'
            )
            
            self.stdout.write(f'  Refunded ₦{rental.price} to {rental.user.username}')
