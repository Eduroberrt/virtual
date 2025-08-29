"""
Management command to sync SMS services from 5sim API
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from app.models import SMSService, SMSOperator, SMSServiceCategory
from app.fivesim import FiveSimAPI
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync SMS services and operators from 5sim API'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update all services even if recently updated'
        )
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Create missing services and operators from 5sim API'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting 5sim services sync...'))
        
        # Initialize 5sim API client
        api = FiveSimAPI(settings.FIVESIM_API_KEY)
        
        try:
            # Get all products/services from 5sim
            products_data = api.get_products_list()
            if not products_data.get('success'):
                self.stdout.write(self.style.ERROR('Failed to fetch products from 5sim API'))
                return
            
            products = products_data.get('products', {})
            self.stdout.write(f'Found {len(products)} products from 5sim API')
            
            # Get all countries and operators
            countries_data = api.get_countries()
            operators_data = api.get_operators()
            
            if not countries_data.get('success') or not operators_data.get('success'):
                self.stdout.write(self.style.ERROR('Failed to fetch countries/operators from 5sim API'))
                return
            
            countries = countries_data.get('countries', {})
            operators = operators_data.get('operators', {})
            
            # Create default category if it doesn't exist
            default_category, created = SMSServiceCategory.objects.get_or_create(
                name='General Services',
                defaults={'description': 'Auto-imported services from 5sim API'}
            )
            
            services_created = 0
            services_updated = 0
            operators_created = 0
            operators_updated = 0
            
            # Process each product/service
            for product_code, product_info in products.items():
                service_name = product_info.get('name', product_code.title())
                
                # Get or create service
                service, service_created = SMSService.objects.get_or_create(
                    service_code=product_code,
                    defaults={
                        'service_name': service_name,
                        'category': default_category,
                        'profit_margin_percent': settings.DEFAULT_PROFIT_MARGIN_PERCENT,
                        'description': f'Auto-imported from 5sim API'
                    }
                )
                
                if service_created:
                    services_created += 1
                    self.stdout.write(f'Created service: {service_name}')
                
                # Get pricing data for this service
                try:
                    # Get prices for all countries for this product
                    prices_data = api.get_prices_by_product(product_code)
                    if prices_data.get('success') and prices_data.get('prices'):
                        service_prices = prices_data['prices']
                        
                        # Calculate average base price
                        all_prices = []
                        for country_data in service_prices.values():
                            if isinstance(country_data, dict):
                                for operator_data in country_data.values():
                                    if isinstance(operator_data, dict):
                                        price = operator_data.get('cost', 0)
                                        if price > 0:
                                            all_prices.append(price)
                        
                        if all_prices:
                            avg_price = sum(all_prices) / len(all_prices)
                            # Update service base price if significantly different or forced
                            if options['force'] or abs(float(service.base_price_usd) - avg_price) > 0.01:
                                service.update_base_price(avg_price)
                                services_updated += 1
                                self.stdout.write(f'Updated price for {service_name}: ${avg_price:.4f}')
                        
                        # Process operators for this service
                        for country_code, country_operators in service_prices.items():
                            if isinstance(country_operators, dict):
                                country_name = countries.get(country_code, country_code.title())
                                
                                for operator_code, operator_data in country_operators.items():
                                    if isinstance(operator_data, dict):
                                        # Get operator name from operators data
                                        operator_name = operator_code
                                        if country_code in operators and operator_code in operators[country_code]:
                                            operator_name = operators[country_code][operator_code]
                                        
                                        # Get or create operator
                                        operator, op_created = SMSOperator.objects.get_or_create(
                                            country_code=country_code,
                                            operator_code=operator_code,
                                            service=service,
                                            defaults={
                                                'country_name': country_name,
                                                'operator_name': operator_name,
                                                'base_price_usd': operator_data.get('cost', 0),
                                                'available_count': operator_data.get('count', 0),
                                                'success_rate': operator_data.get('rate', 95.0),
                                            }
                                        )
                                        
                                        if op_created:
                                            operators_created += 1
                                        else:
                                            # Update existing operator
                                            operator.available_count = operator_data.get('count', 0)
                                            operator.success_rate = operator_data.get('rate', 95.0)
                                            operator.last_update = timezone.now()
                                            
                                            # Update price if significantly different or forced
                                            new_price = operator_data.get('cost', 0)
                                            if options['force'] or (operator.base_price_usd and abs(float(operator.base_price_usd) - new_price) > 0.01):
                                                operator.base_price_usd = new_price
                                                operators_updated += 1
                                            
                                            operator.save()
                
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Failed to process pricing for {service_name}: {str(e)}'))
                    continue
            
            # Summary
            self.stdout.write(self.style.SUCCESS(
                f'\nSync completed!\n'
                f'Services: {services_created} created, {services_updated} updated\n'
                f'Operators: {operators_created} created, {operators_updated} updated'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Sync failed: {str(e)}'))
            logger.error(f'5sim sync failed: {str(e)}')
