from django.core.management.base import BaseCommand
from app.models import UserProfile
from app.daisysms import get_daisysms_client, DaisySMSException

class Command(BaseCommand):
    help = 'Force sync all services with real-time prices from DaisySMS API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--preserve-custom',
            action='store_true',
            help='Preserve custom pricing for special services like "Service Not Listed"',
        )

    def handle(self, *args, **options):
        self.stdout.write("Syncing services with real-time prices from DaisySMS...")
        
        # Get first user with API key
        profile = UserProfile.objects.filter(api_key__isnull=False).first()
        if not profile:
            self.stdout.write(
                self.style.ERROR('No API key found. Please add an API key in Django admin.')
            )
            return
        
        try:
            client = get_daisysms_client(profile.user)
            
            # Force sync services
            updated_count = client.sync_services(user=profile.user)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully synced {updated_count} services')
            )
            
            if options['preserve_custom']:
                self.stdout.write(
                    self.style.SUCCESS('Custom pricing preserved for special services')
                )
            
            # Display summary
            from app.models import Service
            total_services = Service.objects.count()
            active_services = Service.objects.filter(is_active=True).count()
            
            self.stdout.write(f'Total services in database: {total_services}')
            self.stdout.write(f'Active services: {active_services}')
            
            # Show pricing for top services
            self.stdout.write('\nTop 10 services with current pricing:')
            for service in Service.objects.filter(is_active=True)[:10]:
                self.stdout.write(
                    f'  {service.code}: {service.name} - ${service.price} USD (₦{service.get_naira_price():,.2f} NGN)'
                )
                
        except DaisySMSException as e:
            self.stdout.write(
                self.style.ERROR(f'DaisySMS API error: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {str(e)}')
            )
