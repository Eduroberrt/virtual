from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from app.models import Service, UserProfile
from app.daisysms import get_daisysms_client, DaisySMSException
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync services and pricing from DaisySMS API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='API key to use for syncing (if not provided, uses first available user key)'
        )

    def handle(self, *args, **options):
        api_key = options.get('api_key')
        
        # Get API key from user if not provided
        if not api_key:
            try:
                profile = UserProfile.objects.filter(api_key__isnull=False).first()
                if not profile:
                    self.stdout.write(
                        self.style.ERROR("No API key found. Please configure an API key first.")
                    )
                    return
                api_key = profile.api_key
                user = profile.user
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error getting API key: {str(e)}")
                )
                return
        else:
            user = None
        
        try:
            from app.daisysms import DaisySMSClient
            client = DaisySMSClient(api_key)
            
            self.stdout.write("Syncing services from DaisySMS...")
            
            # Get services data
            updated_count = client.sync_services(user=user)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully synced {updated_count} services"
                )
            )
            
            # Display summary
            total_services = Service.objects.count()
            active_services = Service.objects.filter(is_active=True).count()
            
            self.stdout.write(f"Total services in database: {total_services}")
            self.stdout.write(f"Active services: {active_services}")
            
        except DaisySMSException as e:
            self.stdout.write(
                self.style.ERROR(f"DaisySMS API error: {str(e)}")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Unexpected error: {str(e)}")
            )
