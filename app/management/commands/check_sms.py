from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from app.models import Rental, SMSMessage, UserProfile
from app.daisysms import get_daisysms_client, DaisySMSException
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check for SMS messages on active rentals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-checks',
            type=int,
            default=100,
            help='Maximum number of rentals to check per run'
        )

    def handle(self, *args, **options):
        max_checks = options['max_checks']
        
        # Get active rentals waiting for SMS
        active_rentals = Rental.objects.filter(
            status='WAITING'
        ).select_related('user', 'service')[:max_checks]
        
        self.stdout.write(f"Checking {active_rentals.count()} active rentals for SMS...")
        
        checked_count = 0
        messages_received = 0
        
        for rental in active_rentals:
            try:
                # Get user's API client
                try:
                    client = get_daisysms_client(rental.user)
                except DaisySMSException as e:
                    logger.warning(f"No API key for user {rental.user.username}: {str(e)}")
                    continue
                
                # Check SMS status
                status, code, full_text = client.get_status(
                    rental_id=rental.rental_id,
                    user=rental.user,
                    get_full_text=True
                )
                
                # Update rental status
                if status != rental.status:
                    rental.status = status
                    rental.save()
                    
                    self.stdout.write(
                        f"Updated rental {rental.rental_id} status to {status}"
                    )
                
                # Save message if received
                if status == 'RECEIVED' and code:
                    message, created = SMSMessage.objects.get_or_create(
                        rental=rental,
                        code=code,
                        defaults={'full_text': full_text}
                    )
                    
                    if created:
                        messages_received += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Received SMS for {rental.phone_number}: {code}"
                            )
                        )
                
                checked_count += 1
                
            except DaisySMSException as e:
                logger.error(f"API error checking rental {rental.rental_id}: {str(e)}")
                
            except Exception as e:
                logger.error(f"Unexpected error checking rental {rental.rental_id}: {str(e)}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Checked {checked_count} rentals, received {messages_received} new messages"
            )
        )
