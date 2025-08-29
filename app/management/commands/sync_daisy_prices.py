"""
Django management command to sync services and prices from DaisySMS API
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from app.daisysms import get_daisysms_client, DaisySMSException
from app.models import Service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync services and prices from DaisySMS API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        
        try:
            self.stdout.write(
                self.style.SUCCESS(f"Starting DaisySMS services sync at {start_time}")
            )
            
            # Get DaisySMS client
            client = get_daisysms_client()
            
            # Get current service count before sync
            services_before = Service.objects.count()
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING("DRY RUN MODE - No changes will be made")
                )
                
                # Get prices data to show what would be updated
                prices_data = client.get_prices_verification()
                usa_services = []
                for service_code, countries in prices_data.items():
                    if '187' in countries:  # USA country code
                        service_data = countries['187']
                        usa_services.append({
                            'code': service_code,
                            'name': service_data.get('name', service_code),
                            'price': service_data.get('cost', 0),
                            'count': service_data.get('count', 0),
                            'multi': service_data.get('multi', False)
                        })
                
                self.stdout.write(f"Would process {len(usa_services)} services:")
                for service in usa_services[:10]:  # Show first 10
                    self.stdout.write(f"  - {service['name']} ({service['code']}): ${service['price']}")
                if len(usa_services) > 10:
                    self.stdout.write(f"  ... and {len(usa_services) - 10} more")
                
                return
            
            # Perform actual sync
            updated_count = client.sync_services()
            
            # Get service count after sync
            services_after = Service.objects.count()
            new_services = services_after - services_before
            
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully synced {updated_count} services in {duration:.2f} seconds"
                )
            )
            
            if new_services > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"Added {new_services} new services")
                )
            
            if options['verbose']:
                # Show some sample updated services
                recent_services = Service.objects.filter(
                    updated_at__gte=start_time
                ).order_by('-updated_at')[:5]
                
                if recent_services:
                    self.stdout.write("\nRecently updated services:")
                    for service in recent_services:
                        naira_price = service.get_naira_price()
                        self.stdout.write(
                            f"  - {service.name}: ${service.price} USD (₦{naira_price:.2f} NGN)"
                        )
            
            # Log the sync
            logger.info(f"DaisySMS sync completed: {updated_count} services updated, {new_services} new services")
            
        except DaisySMSException as e:
            error_msg = f"DaisySMS API error: {str(e)}"
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg)
            raise CommandError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error during sync: {str(e)}"
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg)
            raise CommandError(error_msg)
