"""
Django management command to update only pricing data from 5sim API
This is faster than full sync and can run more frequently
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from app.models import SMSService
from app.fivesim import FiveSimAPI
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update pricing data from 5sim API (faster than full sync)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--services',
            nargs='+',
            help='Specific service codes to update (optional)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of services to update per batch',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting 5sim price update...'))
        
        try:
            # Initialize 5sim API client
            api_key = getattr(settings, 'FIVESIM_API_KEY', None)
            if not api_key:
                raise CommandError('FIVESIM_API_KEY not found in settings')
            
            client = FiveSimAPI(api_key)
            
            # Get current pricing data
            self.stdout.write('Fetching latest pricing data from 5sim API...')
            pricing_data = client.get_all_prices()
            
            if not pricing_data:
                raise CommandError('Failed to fetch pricing data from 5sim API')
            
            # Get services to update
            if options['services']:
                services = SMSService.objects.filter(
                    service_code__in=options['services'],
                    is_active=True
                )
            else:
                services = SMSService.objects.filter(is_active=True)
            
            # Update prices in batches
            batch_size = options['batch_size']
            updated_count = 0
            
            for i in range(0, services.count(), batch_size):
                batch = services[i:i + batch_size]
                
                for service in batch:
                    try:
                        old_price_usd = float(service.base_price_usd)
                        old_price_naira = float(service.base_price_naira)
                        
                        # Get pricing data from API (returns RUB)
                        new_price_rub = self.get_service_price_from_api(
                            service.service_code, 
                            pricing_data
                        )
                        
                        if new_price_rub > 0:
                            # Convert RUB to NGN (5sim uses RUB, not USD!)
                            new_price_naira = float(new_price_rub * settings.EXCHANGE_RATE_RUB_TO_NGN)
                            
                            # Check if price actually changed (force update if it's a big difference from old USD-based pricing)
                            price_difference = abs(new_price_naira - old_price_naira)
                            if price_difference > 0.01 or old_price_naira > new_price_naira * 2:  # Force update if old price is much higher
                                # Update prices
                                service.base_price_rub = new_price_rub
                                service.base_price_naira = round(new_price_naira, 2)
                                service.last_price_update = timezone.now()
                                service.price_update_count += 1
                                service.save()
                                
                                updated_count += 1
                                
                                self.stdout.write(
                                    f'  Updated {service.service_name}: '
                                    f'₦{old_price_naira:,.2f} → ₦{service.base_price_naira:,.2f} '
                                    f'({new_price_rub} RUB)'
                                )
                    
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  Warning: Could not update {service.service_code}: {str(e)}'
                            )
                        )
                
                # Small delay between batches to be API-friendly
                if i + batch_size < services.count():
                    import time
                    time.sleep(1)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Price update completed! Updated {updated_count} services out of {services.count()}'
                )
            )
            
        except Exception as e:
            logger.error(f'Error updating prices: {str(e)}')
            raise CommandError(f'Failed to update prices: {str(e)}')

    def get_service_price_from_api(self, service_code, pricing_data):
        """Extract price for a specific service from pricing data - uses MOST EXPENSIVE operator"""
        if not pricing_data:
            return 0
        
        try:
            # Method 1: Direct service lookup
            if service_code in pricing_data:
                service_prices = pricing_data[service_code]
                if isinstance(service_prices, dict):
                    # Find the MOST EXPENSIVE price across countries/operators with availability
                    max_price = 0
                    for country_data in service_prices.values():
                        if isinstance(country_data, dict):
                            for operator_data in country_data.values():
                                if isinstance(operator_data, dict) and 'cost' in operator_data:
                                    price = float(operator_data['cost'])
                                    count = int(operator_data.get('count', 0))
                                    # Only consider operators with available phones
                                    if price > 0 and count > 0 and price > max_price:
                                        max_price = price
                                elif isinstance(operator_data, (int, float)):
                                    price = float(operator_data)
                                    if price > 0 and price > max_price:
                                        max_price = price
                    
                    if max_price > 0:
                        return max_price
            
            # Method 2: Search through all pricing data
            max_price = 0
            for country_name, country_data in pricing_data.items():
                if isinstance(country_data, dict) and service_code in country_data:
                    service_prices = country_data[service_code]
                    if isinstance(service_prices, dict):
                        for operator_name, price_data in service_prices.items():
                            if isinstance(price_data, dict) and 'cost' in price_data:
                                price = float(price_data['cost'])
                                count = int(price_data.get('count', 0))
                                # Only consider operators with available phones
                                if price > 0 and count > 0 and price > max_price:
                                    max_price = price
                            elif isinstance(price_data, (int, float)):
                                price = float(price_data)
                                if price > 0 and price > max_price:
                                    max_price = price
            
            if max_price > 0:
                return max_price
            
        except Exception:
            pass
        
        return 0  # Return 0 if no price found
