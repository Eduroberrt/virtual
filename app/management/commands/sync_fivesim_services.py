"""
Django management command to sync services from 5sim API
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from app.models import SMSService, SMSServiceCategory, SMSOperator
from app.fivesim import FiveSimAPI
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync services from 5sim API to local database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing services',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting 5sim services sync...'))
        
        try:
            # Initialize 5sim API client
            api_key = getattr(settings, 'FIVESIM_API_KEY', None)
            if not api_key:
                raise CommandError('FIVESIM_API_KEY not found in settings')
            
            client = FiveSimAPI(api_key)
            
            # Get products from 5sim API
            self.stdout.write('Fetching products from 5sim API...')
            products = client.get_products()
            
            # Get pricing data from 5sim API
            self.stdout.write('Fetching pricing data from 5sim API...')
            pricing_data = client.get_all_prices()
            
            if not products:
                raise CommandError('Failed to fetch products from 5sim API')
            
            # Sync categories, operators, and services
            self.sync_categories(products)
            self.sync_operators(client)
            self.sync_services(products, pricing_data, options['force'])
            
            self.stdout.write(
                self.style.SUCCESS('Successfully synced services from 5sim API')
            )
            
        except Exception as e:
            logger.error(f'Error syncing services: {str(e)}')
            raise CommandError(f'Failed to sync services: {str(e)}')

    def sync_categories(self, products):
        """Sync service categories"""
        self.stdout.write('Syncing categories...')
        
        categories = set()
        # products is a dict with product codes as keys
        for service_code in products.keys():
            # Create a simple category mapping
            category_name = self.get_category_name(service_code)
            categories.add(category_name)
        
        for category_name in categories:
            category, created = SMSServiceCategory.objects.get_or_create(
                name=category_name,
                defaults={
                    'description': f'Services for {category_name}',
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  Created category: {category_name}')

    def sync_operators(self, client):
        """Sync operators from 5sim API"""
        self.stdout.write('Syncing operators...')
        
        try:
            # Get available operators
            operators = client.get_available_operators()
            
            if operators:
                for op_name in operators:
                    operator, created = SMSOperator.objects.get_or_create(
                        name=op_name,
                        defaults={
                            'is_active': True,
                            'profit_margin_percent': settings.DEFAULT_PROFIT_MARGIN_PERCENT
                        }
                    )
                    if created:
                        self.stdout.write(f'  Created operator: {op_name}')
                        
        except Exception as e:
            self.stdout.write(f'  Warning: Could not sync operators: {str(e)}')

    def sync_services(self, products, pricing_data, force_update=False):
        """Sync services from products with real pricing data"""
        self.stdout.write('Syncing services...')
        
        synced_count = 0
        created_count = 0
        
        # products is a dict with service codes as keys
        for service_code, service_data in products.items():
            try:
                category_name = self.get_category_name(service_code)
                category = SMSServiceCategory.objects.get(name=category_name)
                
                # Get actual price from pricing data (in RUB)
                base_price_rub = self.get_service_price_from_api(service_code, pricing_data)
                base_price_naira = base_price_rub * settings.EXCHANGE_RATE_RUB_TO_NGN
                
                # Calculate default profit margin in Naira (40% of wholesale price)
                default_profit_margin_naira = base_price_naira * settings.DEFAULT_PROFIT_MARGIN_PERCENT / 100
                
                service, created = SMSService.objects.get_or_create(
                    service_code=service_code,
                    defaults={
                        'service_name': service_code.replace('_', ' ').title(),
                        'category': category,
                        'base_price_rub': base_price_rub,
                        'base_price_naira': round(base_price_naira, 2),
                        'profit_margin_naira': round(default_profit_margin_naira, 2),
                        'is_active': True
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  Created service: {service.service_name} ({service.service_code}) - Wholesale: ₦{service.base_price_naira:,.2f} ({base_price_rub} RUB), Final: ₦{service.get_final_price_ngn():,.2f}')
                elif force_update:
                    # Update prices but preserve custom profit margins
                    service.base_price_rub = base_price_rub
                    service.base_price_naira = round(base_price_naira, 2)
                    service.save()
                    self.stdout.write(f'  Updated service: {service.service_name} ({service.service_code}) - New Wholesale: ₦{service.base_price_naira:,.2f} ({base_price_rub} RUB)')
                
                synced_count += 1
                
            except Exception as e:
                self.stdout.write(f'  Error syncing {service_code}: {str(e)}')
        
        self.stdout.write(f'Synced {synced_count} services ({created_count} created)')
    
    def get_service_price_from_api(self, service_code, pricing_data):
        """Extract price for a specific service from pricing data - uses MOST EXPENSIVE operator"""
        if not pricing_data:
            return 0.5  # Default fallback
        
        # Try to find the service in pricing data
        # The structure might be different, so we'll try multiple approaches
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
            
        except Exception as e:
            self.stdout.write(f'    Warning: Could not extract price for {service_code}: {str(e)}')
        
        # Default fallback price in RUB
        return 0.5

    def get_category_name(self, service_code):
        """Map service codes to categories"""
        social_media = ['whatsapp', 'telegram', 'viber', 'facebook', 'instagram', 'twitter', 'tiktok', 'snapchat']
        messaging = ['sms', 'voice', 'call']
        gaming = ['steam', 'discord', 'twitch', 'xbox', 'playstation']
        finance = ['paypal', 'coinbase', 'binance', 'revolut']
        shopping = ['amazon', 'ebay', 'alibaba', 'shopify']
        
        service_lower = service_code.lower()
        
        for keyword in social_media:
            if keyword in service_lower:
                return 'Social Media'
        
        for keyword in messaging:
            if keyword in service_lower:
                return 'Messaging'
                
        for keyword in gaming:
            if keyword in service_lower:
                return 'Gaming'
                
        for keyword in finance:
            if keyword in service_lower:
                return 'Finance'
                
        for keyword in shopping:
            if keyword in service_lower:
                return 'Shopping'
        
        return 'Other'
