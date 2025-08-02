from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from app.models import Rental, UserProfile, Transaction
from app.daisysms import get_daisysms_client, DaisySMSException
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatically cancel rentals that are older than 5 minutes and have not received SMS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cancelled without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find rentals that are exactly 5+ minutes old and still waiting
        cutoff_time = timezone.now() - timedelta(minutes=5)
        
        expired_rentals = Rental.objects.filter(
            status='WAITING',
            created_at__lte=cutoff_time,
            refunded=False
        ).exclude(
            # Don't cancel if SMS messages already received
            messages__isnull=False
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would cancel {expired_rentals.count()} rentals')
            )
            for rental in expired_rentals[:10]:  # Show first 10
                self.stdout.write(f'  - {rental.user.username}: {rental.service.name} ({rental.phone_number})')
            return
        
        cancelled_count = 0
        error_count = 0
        
        for rental in expired_rentals:
            try:
                # Use the same logic as the X button cancel functionality
                success = self.cancel_rental(rental)
                if success:
                    cancelled_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'SUCCESS: Cancelled {rental.user.username}: {rental.service.name} ({rental.phone_number})'
                        )
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'ERROR: Failed to cancel {rental.user.username}: {rental.service.name} ({rental.phone_number})'
                        )
                    )
            except Exception as e:
                error_count += 1
                logger.error(f"Error auto-cancelling rental {rental.rental_id}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(
                        f'ERROR: Error cancelling {rental.user.username}: {rental.service.name} - {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Auto-cancel completed: {cancelled_count} cancelled, {error_count} errors'
            )
        )

    def cancel_rental(self, rental):
        """
        Reuse the exact same logic as the X button cancel functionality
        This ensures consistency with manual cancellations
        """
        try:
            # Call DaisySMS API to cancel the rental (same as X button)
            client = get_daisysms_client()
            success = client.cancel_rental(rental_id=rental.rental_id, user=rental.user)
            
            if success:
                with transaction.atomic():
                    # Get rental with row-level lock to prevent race conditions
                    rental = Rental.objects.select_for_update().get(rental_id=rental.rental_id)
                    
                    # Check if already refunded (race condition protection)
                    if rental.refunded:
                        logger.warning(f"Rental {rental.rental_id} already refunded")
                        return False
                    
                    # Update rental status to CANCELLED (same as X button)
                    rental.status = 'CANCELLED'
                    rental.refunded = True
                    rental.save()
                    
                    # Calculate refund amount (same logic as X button)
                    refund_amount_naira = rental.get_naira_price()
                    
                    # Create refund transaction
                    Transaction.objects.create(
                        user=rental.user,
                        amount=refund_amount_naira,
                        transaction_type='REFUND',
                        description=f"Auto-refund for cancelled rental {rental.phone_number} (5min timeout)",
                        rental=rental
                    )
                    
                    # Update user balance (add money back)
                    profile = UserProfile.objects.select_for_update().get(user=rental.user)
                    profile.balance += refund_amount_naira
                    profile.save()
                    
                    logger.info(f"Auto-cancelled rental {rental.rental_id} for user {rental.user.username}, refunded ₦{refund_amount_naira}")
                    return True
            else:
                logger.error(f"DaisySMS API failed to cancel rental {rental.rental_id}")
                return False
                
        except DaisySMSException as e:
            logger.error(f"DaisySMS error cancelling rental {rental.rental_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error cancelling rental {rental.rental_id}: {str(e)}")
            return False
