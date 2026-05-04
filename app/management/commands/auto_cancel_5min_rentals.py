"""
Management command to auto-cancel MTelSMS rentals after 5 minutes if no SMS received
This ensures users don't wait the full MTelSMS timeout period (10-20 minutes)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from app.models import Rental, UserProfile, Transaction, SMSMessage
from app.mtelsms import get_mtelsms_client, MTelSMSException


class Command(BaseCommand):
    help = 'Auto-cancel MTelSMS rentals after 5 minutes if no SMS received'

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
        
        # Find rentals waiting for > 5 minutes
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        
        # Only check WAITING rentals (active status)
        waiting_rentals = Rental.objects.filter(
            status='WAITING',
            created_at__lte=five_minutes_ago,
            refunded=False  # Only non-refunded rentals
        ).select_related('user', 'service').prefetch_related('messages')
        
        total_rentals = waiting_rentals.count()
        
        if total_rentals == 0:
            self.stdout.write(self.style.SUCCESS('No rentals waiting > 5 minutes'))
            return
        
        self.stdout.write(f'Found {total_rentals} rentals waiting > 5 minutes')
        
        cancelled_count = 0
        skipped_sms_count = 0
        skipped_already_refunded = 0
        error_count = 0
        
        client = get_mtelsms_client()
        
        for rental in waiting_rentals:
            # Calculate wait time
            wait_time = timezone.now() - rental.created_at
            wait_minutes = wait_time.total_seconds() / 60
            
            try:
                # IMPORTANT: Check MTelSMS one final time before cancelling
                # This prevents cancelling if SMS just arrived
                try:
                    status, code, phone_number, time_remaining = client.get_code(
                        rental_id=rental.rental_id
                    )
                    
                    # If SMS was received, save it and skip cancellation
                    if status == 'RECEIVED' and code:
                        if not dry_run:
                            rental.status = 'RECEIVED'
                            rental.save()
                            
                            SMSMessage.objects.get_or_create(
                                rental=rental,
                                code=code,
                                defaults={'full_text': code}
                            )
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ SMS received for Rental #{rental.id}: Skipping cancel (code: {code})'
                            )
                        )
                        skipped_sms_count += 1
                        continue
                    
                    # SMS still not received - proceed with cancellation
                    if status == 'WAITING':
                        if dry_run:
                            self.stdout.write(
                                f'[DRY RUN] Would cancel Rental #{rental.id} (mtelsms:{rental.rental_id}): '
                                f'{rental.service.name} - ₦{rental.price} to {rental.user.username} '
                                f'(waiting {wait_minutes:.1f} minutes)'
                            )
                            cancelled_count += 1
                        else:
                            # Call MTelSMS API to cancel (same as cancel button)
                            try:
                                cancel_success = client.cancel_rental(rental_id=rental.rental_id)
                                
                                if not cancel_success:
                                    error_count += 1
                                    continue
                            except MTelSMSException as api_error:
                                # Continue even if API call fails - we'll still refund
                                pass
                            
                            # Process refund with triple protection
                            with transaction.atomic():
                                # Reload rental with lock to prevent race conditions
                                rental = Rental.objects.select_for_update().get(rental_id=rental.rental_id)
                                
                                # Check if already refunded (double-refund protection)
                                if rental.refunded:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'⚠ Rental #{rental.id} (mtelsms:{rental.rental_id}) already refunded, skipping'
                                        )
                                    )
                                    skipped_already_refunded += 1
                                    continue
                                
                                # Update rental status to CANCELLED and mark as refunded
                                rental.status = 'CANCELLED'
                                rental.refunded = True
                                rental.save()
                                
                                # Refund user with locked profile
                                refund_amount_naira = rental.get_naira_price()
                                profile = UserProfile.objects.select_for_update().get(user=rental.user)
                                profile.balance += refund_amount_naira
                                profile.save()
                                
                                # Log transaction
                                Transaction.objects.create(
                                    user=rental.user,
                                    amount=refund_amount_naira,
                                    transaction_type='REFUND',
                                    description=f'Auto-cancel: No SMS after 5 minutes - {rental.phone_number}',
                                    rental=rental
                                )
                                
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'✓ Cancelled Rental #{rental.id} (mtelsms:{rental.rental_id}): '
                                        f'₦{refund_amount_naira} to {rental.user.username} '
                                        f'(waited {wait_minutes:.1f} minutes)'
                                    )
                                )
                            
                            cancelled_count += 1
                    
                except MTelSMSException as e:
                    error_count += 1
                    continue
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing Rental #{rental.id}: {str(e)}')
                )
        
        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'[DRY RUN] Would have cancelled {cancelled_count} rentals'))
            self.stdout.write(self.style.WARNING(f'[DRY RUN] Would have skipped {skipped_sms_count} rentals (SMS received)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully cancelled {cancelled_count} rentals'))
            self.stdout.write(f'Skipped {skipped_sms_count} rentals (SMS received just in time)')
            self.stdout.write(f'Skipped {skipped_already_refunded} rentals (already refunded)')
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed to process {error_count} rentals'))
