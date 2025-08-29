from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from app.models import Rental, UserProfile, Transaction, SMSMessage
from app.daisysms import get_daisysms_client, DaisySMSException
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync active Daisy SMS rental statuses and process expired/received ones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually doing it',
        )
        parser.add_argument(
            '--max-age-hours',
            type=int,
            default=24,
            help='Maximum age of rentals to check (default: 24 hours)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        max_age_hours = options['max_age_hours']
        
        # Find active Daisy SMS rentals to check status (not older than max_age_hours)
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
        
        active_rentals = Rental.objects.filter(
            status='WAITING',
            created_at__gte=cutoff_time,
            refunded=False
        ).exclude(
            # Don't check if SMS messages already received
            messages__isnull=False
        )
        
        # Also check for rentals that are marked as CANCELLED/EXPIRED but not refunded
        unrefunded_rentals = Rental.objects.filter(
            status__in=['CANCELLED', 'EXPIRED'],
            created_at__gte=cutoff_time,
            refunded=False
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would check status for {active_rentals.count()} active rentals')
            )
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would fix {unrefunded_rentals.count()} unrefunded rentals')
            )
            for rental in active_rentals[:10]:  # Show first 10
                self.stdout.write(f'  - {rental.user.username}: {rental.service.name} ({rental.phone_number})')
            for rental in unrefunded_rentals[:5]:  # Show first 5 unrefunded
                self.stdout.write(f'  - FIX: {rental.user.username}: {rental.service.name} ({rental.phone_number}) - Status: {rental.status}')
            return
        
        received_count = 0
        expired_count = 0
        cancelled_count = 0
        fixed_count = 0
        error_count = 0
        
        self.stdout.write(f'Checking Daisy SMS status for {active_rentals.count()} active rentals...')
        self.stdout.write(f'Fixing {unrefunded_rentals.count()} unrefunded rentals...')
        
        # Process unrefunded rentals first (fix orphaned cancelled/expired)
        for rental in unrefunded_rentals:
            try:
                success = self.fix_unrefunded_rental(rental)
                if success:
                    fixed_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"Error fixing rental {rental.rental_id}: {str(e)}")
        
        # Then process active rentals
        for rental in active_rentals:
            try:
                # Check status with Daisy SMS
                result = self.check_and_process_rental(rental)
                if result == 'received':
                    received_count += 1
                elif result == 'expired':
                    expired_count += 1
                elif result == 'cancelled':
                    cancelled_count += 1
                    
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
                f'Daisy SMS sync completed: {received_count} received, {expired_count} expired, {cancelled_count} cancelled, {fixed_count} fixed, {error_count} errors'
            )
        )

    def check_and_process_rental(self, rental):
        """
        Check rental status with Daisy SMS and process accordingly
        Returns: 'received', 'expired', 'cancelled', or None
        """
        try:
            client = get_daisysms_client()
            status, code, full_text = client.get_status(
                rental_id=rental.rental_id, 
                user=rental.user, 
                get_full_text=True
            )
            
            if status == 'RECEIVED' and code:
                # SMS received - save message and update rental
                return self.process_received_sms(rental, code, full_text)
                
            elif status == 'EXPIRED':
                # Rental expired by Daisy SMS
                return self.process_expired_rental(rental)
                
            elif status == 'CANCELLED':
                # Rental cancelled by Daisy SMS
                return self.process_cancelled_rental(rental)
                
            elif status == 'WAITING':
                # Still waiting - no action needed
                return None
                
            else:
                logger.warning(f"Unknown status '{status}' for rental {rental.rental_id}")
                return None
                
        except DaisySMSException as e:
            # If rental not found, treat as expired
            if "Rental not found" in str(e):
                return self.process_expired_rental(rental)
            else:
                logger.error(f"DaisySMS error for rental {rental.rental_id}: {str(e)}")
                raise

    def process_received_sms(self, rental, code, full_text):
        """Process a rental that received SMS"""
        with transaction.atomic():
            # Get rental with lock
            rental = Rental.objects.select_for_update().get(rental_id=rental.rental_id)
            
            # Check if already processed
            if rental.status != 'WAITING':
                return None
                
            # Update rental status
            rental.status = 'RECEIVED'
            rental.save()
            
            # Save SMS message
            message, created = SMSMessage.objects.get_or_create(
                rental=rental,
                code=code,
                defaults={'full_text': full_text}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'SMS RECEIVED: {rental.user.username}: {rental.service.name} ({rental.phone_number}) - Code: {code}'
                    )
                )
                logger.info(f"SMS received for rental {rental.rental_id}: {code}")
                
            return 'received'

    def process_expired_rental(self, rental):
        """Process a rental that expired on Daisy SMS"""
        with transaction.atomic():
            # Get rental with lock
            rental = Rental.objects.select_for_update().get(rental_id=rental.rental_id)
            
            # Check if already processed
            if rental.refunded or rental.status != 'WAITING':
                return None
                
            # Update rental status
            rental.status = 'EXPIRED'
            rental.refunded = True
            rental.save()
            
            # Calculate refund amount
            refund_amount_naira = rental.get_naira_price()
            
            # Create refund transaction
            Transaction.objects.create(
                user=rental.user,
                amount=refund_amount_naira,
                transaction_type='REFUND',
                description=f"Auto-refund for expired rental {rental.phone_number} (Daisy SMS expired)",
                rental=rental
            )
            
            # Update user balance
            profile = UserProfile.objects.select_for_update().get(user=rental.user)
            profile.balance += refund_amount_naira
            profile.save()
            
            self.stdout.write(
                self.style.WARNING(
                    f'EXPIRED: {rental.user.username}: {rental.service.name} ({rental.phone_number}) - Refunded ₦{refund_amount_naira}'
                )
            )
            logger.info(f"Rental {rental.rental_id} expired by Daisy SMS, refunded ₦{refund_amount_naira}")
            
            return 'expired'

    def process_cancelled_rental(self, rental):
        """Process a rental that was cancelled on Daisy SMS"""
        with transaction.atomic():
            # Get rental with lock
            rental = Rental.objects.select_for_update().get(rental_id=rental.rental_id)
            
            # Check if already processed
            if rental.refunded or rental.status != 'WAITING':
                return None
                
            # Update rental status
            rental.status = 'CANCELLED'
            rental.refunded = True
            rental.save()
            
            # Calculate refund amount
            refund_amount_naira = rental.get_naira_price()
            
            # Create refund transaction
            Transaction.objects.create(
                user=rental.user,
                amount=refund_amount_naira,
                transaction_type='REFUND',
                description=f"Auto-refund for cancelled rental {rental.phone_number} (Daisy SMS cancelled)",
                rental=rental
            )
            
            # Update user balance
            profile = UserProfile.objects.select_for_update().get(user=rental.user)
            profile.balance += refund_amount_naira
            profile.save()
            
            self.stdout.write(
                self.style.WARNING(
                    f'CANCELLED: {rental.user.username}: {rental.service.name} ({rental.phone_number}) - Refunded ₦{refund_amount_naira}'
                )
            )
            logger.info(f"Rental {rental.rental_id} cancelled by Daisy SMS, refunded ₦{refund_amount_naira}")
            
            return 'cancelled'

    def fix_unrefunded_rental(self, rental):
        """Fix a rental that should be refunded but isn't"""
        with transaction.atomic():
            # Get rental with lock
            rental = Rental.objects.select_for_update().get(rental_id=rental.rental_id)
            
            # Check if already processed (race condition protection)
            if rental.refunded:
                return False
            
            # Check if refund transaction already exists
            existing_refund = Transaction.objects.filter(
                rental=rental,
                transaction_type='REFUND'
            ).first()
            
            if existing_refund:
                # Refund transaction exists but flag not set - just fix the flag
                rental.refunded = True
                rental.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'FLAG FIXED: {rental.user.username}: {rental.service.name} ({rental.phone_number}) - Status: {rental.status} - Already refunded ₦{existing_refund.amount}'
                    )
                )
                logger.info(f"Fixed refunded flag for rental {rental.rental_id}, was already refunded ₦{existing_refund.amount}")
                return True
            
            # No refund transaction exists - create one
            # Calculate refund amount
            refund_amount_naira = rental.get_naira_price()
            
            # Create refund transaction
            Transaction.objects.create(
                user=rental.user,
                amount=refund_amount_naira,
                transaction_type='REFUND',
                description=f"Auto-refund for {rental.status.lower()} rental {rental.phone_number} (Fix orphaned)",
                rental=rental
            )
            
            # Update user balance
            profile = UserProfile.objects.select_for_update().get(user=rental.user)
            profile.balance += refund_amount_naira
            profile.save()
            
            # Mark as refunded
            rental.refunded = True
            rental.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'REFUNDED: {rental.user.username}: {rental.service.name} ({rental.phone_number}) - Status: {rental.status} - Refunded ₦{refund_amount_naira}'
                )
            )
            logger.info(f"Fixed unrefunded rental {rental.rental_id}, refunded ₦{refund_amount_naira}")
            
            return True
