from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from app.models import Rental, UserProfile, Transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix rentals that are marked as CANCELLED/EXPIRED but not refunded'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually doing it',
        )
        parser.add_argument(
            '--max-age-hours',
            type=int,
            default=72,
            help='Maximum age of rentals to check (default: 72 hours)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        max_age_hours = options['max_age_hours']
        
        # Find cancelled/expired rentals that haven't been refunded
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
        
        unrefunded_rentals = Rental.objects.filter(
            status__in=['CANCELLED', 'EXPIRED'],
            created_at__gte=cutoff_time,
            refunded=False
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would refund {unrefunded_rentals.count()} rentals')
            )
            for rental in unrefunded_rentals:
                refund_amount = rental.get_naira_price()
                self.stdout.write(f'  - {rental.user.username}: {rental.service.name} ({rental.phone_number}) - Status: {rental.status} - Would refund ₦{refund_amount}')
            return

        refunded_count = 0
        error_count = 0
        
        self.stdout.write(f'Processing {unrefunded_rentals.count()} unrefunded rentals...')
        
        for rental in unrefunded_rentals:
            try:
                success = self.process_unrefunded_rental(rental)
                if success:
                    refunded_count += 1
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing rental {rental.rental_id}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(
                        f'ERROR: Error processing {rental.user.username}: {rental.service.name} - {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Fix completed: {refunded_count} refunded, {error_count} errors'
            )
        )

    def process_unrefunded_rental(self, rental):
        """Process a rental that should be refunded"""
        with transaction.atomic():
            # Get rental with lock
            rental = Rental.objects.select_for_update().get(rental_id=rental.rental_id)
            
            # Check if already processed (race condition protection)
            if rental.refunded:
                return False
                
            # Mark as refunded
            rental.refunded = True
            rental.save()
            
            # Calculate refund amount
            refund_amount_naira = rental.get_naira_price()
            
            # Create refund transaction
            Transaction.objects.create(
                user=rental.user,
                amount=refund_amount_naira,
                transaction_type='REFUND',
                description=f"Auto-refund for {rental.status.lower()} rental {rental.phone_number} (Fix unrefunded)",
                rental=rental
            )
            
            # Update user balance
            profile = UserProfile.objects.select_for_update().get(user=rental.user)
            profile.balance += refund_amount_naira
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'FIXED: {rental.user.username}: {rental.service.name} ({rental.phone_number}) - Status: {rental.status} - Refunded ₦{refund_amount_naira}'
                )
            )
            logger.info(f"Fixed unrefunded rental {rental.rental_id}, refunded ₦{refund_amount_naira}")
            
            return True
