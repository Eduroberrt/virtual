"""
Management command to check for expired rentals and issue refunds
Run this periodically via cron or task scheduler
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from app.models import Rental, Transaction, SMSMessage, UserProfile
from app.mtelsms import get_mtelsms_client, MTelSMSException


class Command(BaseCommand):
    help = 'Check for expired rentals and automatically issue refunds'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of rentals to check in one run'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be refunded without actually doing it',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get active rentals that might be expired
        active_rentals = Rental.objects.filter(
            status='WAITING',
            refunded=False  # Only non-refunded rentals
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
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f"[DRY RUN] Would refund expired: {rental.rental_id} - {rental.phone_number}"
                            )
                        )
                        expired_count += 1
                    else:
                        with transaction.atomic():
                            # Reload rental with lock to prevent race conditions
                            rental = Rental.objects.select_for_update().get(rental_id=rental.rental_id)
                            
                            # Check if already refunded (double-refund protection)
                            if rental.refunded:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"⚠ Already refunded: {rental.rental_id}"
                                    )
                                )
                                continue
                            
                            # Mark as expired
                            rental.status = 'EXPIRED'
                            rental.refunded = True
                            rental.save()
                            expired_count += 1
                            
                            # Issue refund with locked profile
                            profile = UserProfile.objects.select_for_update().get(user=rental.user)
                            profile.balance += rental.price
                            profile.save()
                            
                            # Log refund transaction
                            Transaction.objects.create(
                                user=rental.user,
                                amount=rental.price,
                                transaction_type='REFUND',
                                description=f'Automatic refund for expired rental {rental.phone_number}'
                            )
                            
                            refunded_count += 1
                                
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✓ Expired and refunded: {rental.rental_id} - {rental.phone_number}"
                                )
                            )
                
                elif status == 'RECEIVED' and code:
                    # Update status if SMS was received and save the SMS message
                    if not dry_run:
                        rental.status = 'RECEIVED'
                        rental.save()
                        
                        # Save SMS message if not already saved
                        SMSMessage.objects.get_or_create(
                            rental=rental,
                            code=code,
                            defaults={'full_text': code}
                        )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ SMS received: {rental.rental_id} - {code}"
                        )
                    )
                
            except MTelSMSException as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Error checking {rental.rental_id}: {str(e)}"
                    )
                )
            
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Unexpected error for {rental.rental_id}: {str(e)}"
                    )
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        if dry_run:
            self.stdout.write(self.style.WARNING(f"[DRY RUN] Checked: {active_rentals.count()} rentals"))
            self.stdout.write(self.style.WARNING(f"[DRY RUN] Would have refunded: {expired_count} expired rentals"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ Checked: {active_rentals.count()} rentals"))
            self.stdout.write(self.style.WARNING(f"⏰ Expired: {expired_count} rentals"))
            self.stdout.write(self.style.SUCCESS(f"💰 Refunded: {refunded_count} rentals"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"✗ Errors: {error_count}"))
        self.stdout.write("="*50)
