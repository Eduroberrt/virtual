from django.core.management.base import BaseCommand
from app.models import Service
from app.daisysms import DaisySMSClient, DaisySMSException
from django.conf import settings

class Command(BaseCommand):
    help = 'Clear sample services and sync real services from DaisySMS API'

    def handle(self, *args, **options):
        try:
            # Clear existing services
            self.stdout.write("Clearing existing sample services...")
            Service.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared existing services"))
            
            # Get API key from settings
            api_key = getattr(settings, 'DAISYSMS_API_KEY', None)
            if not api_key:
                self.stdout.write(
                    self.style.ERROR("No DAISYSMS_API_KEY found in settings")
                )
                return
            
            # Create client and sync
            self.stdout.write("Connecting to DaisySMS API...")
            client = DaisySMSClient(api_key)
            
            # Test balance first
            try:
                balance = client.get_balance()
                self.stdout.write(f"API Balance: ${balance}")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to get balance: {str(e)}")
                )
                return
            
            # Sync services
            self.stdout.write("Syncing services from DaisySMS...")
            updated_count = client.sync_services()
            
            total_services = Service.objects.count()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully synced {updated_count} services. "
                    f"Total services in database: {total_services}"
                )
            )
            
            # Show first 10 services
            services = Service.objects.all()[:10]
            self.stdout.write("\nFirst 10 services:")
            for service in services:
                self.stdout.write(
                    f"  - {service.name} ({service.code}): "
                    f"${service.price} (one-time)"
                )
                
        except DaisySMSException as e:
            self.stdout.write(
                self.style.ERROR(f"DaisySMS API error: {str(e)}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Unexpected error: {str(e)}")
            )
