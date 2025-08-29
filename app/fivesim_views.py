"""
5sim API Views
Django REST API endpoints that integrate with 5sim.net services
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
import json
import logging

from .fivesim import fivesim_api

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@cache_page(60 * 5)  # Cache for 5 minutes
def get_products(request, country=None, operator=None):
    """
    Get available products from 5sim
    GET /api/5sim/products/<country>/<operator>/
    """
    try:
        # Use URL parameters if provided, otherwise use query parameters
        if not country:
            country = request.GET.get('country', 'any')
        if not operator:
            operator = request.GET.get('operator', 'any')
        
        products = fivesim_api.get_products(country, operator)
        
        # Transform data for frontend
        transformed_products = []
        for product_name, product_data in products.items():
            transformed_products.append({
                'name': product_name,
                'category': product_data.get('Category', 'unknown'),
                'quantity': product_data.get('Qty', 0),
                'price': product_data.get('Price', 0),
                'price_formatted': f"₦{product_data.get('Price', 0) * 1:.2f}",  # Convert to Naira if needed
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'country': country,
                'operator': operator,
                'products': transformed_products,
                'total_products': len(transformed_products)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting products: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
@cache_page(60 * 10)  # Cache for 10 minutes
def get_all_prices(request):
    """
    Get all pricing data from 5sim
    GET /api/5sim/prices/
    """
    try:
        prices = fivesim_api.get_all_prices()
        
        # Transform data for easier frontend consumption
        transformed_data = {
            'countries': [],
            'products': set(),
            'operators': set(),
            'pricing': prices
        }
        
        for country, country_data in prices.items():
            country_info = {
                'name': country,
                'products': []
            }
            
            if isinstance(country_data, dict):
                for product, product_data in country_data.items():
                    transformed_data['products'].add(product)
                    
                    product_info = {
                        'name': product,
                        'operators': []
                    }
                    
                    if isinstance(product_data, dict):
                        for operator, operator_data in product_data.items():
                            transformed_data['operators'].add(operator)
                            
                            if isinstance(operator_data, dict):
                                product_info['operators'].append({
                                    'name': operator,
                                    'cost': operator_data.get('cost', 0),
                                    'count': operator_data.get('count', 0),
                                    'rate': operator_data.get('rate', 0),
                                    'cost_formatted': f"₦{operator_data.get('cost', 0) * 1:.2f}",
                                })
                    
                    country_info['products'].append(product_info)
            
            transformed_data['countries'].append(country_info)
        
        # Convert sets to lists for JSON serialization
        transformed_data['products'] = list(transformed_data['products'])
        transformed_data['operators'] = list(transformed_data['operators'])
        
        return JsonResponse({
            'success': True,
            'data': transformed_data
        })
        
    except Exception as e:
        logger.error(f"Error getting all prices: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
@cache_page(60 * 10)  # Cache for 10 minutes
def get_prices_by_country(request, country):
    """
    Get pricing data for a specific country
    GET /api/5sim/prices/country/<country>/
    """
    try:
        prices = fivesim_api.get_prices_by_country(country)
        
        if country not in prices:
            return JsonResponse({
                'success': False,
                'error': f'Country "{country}" not found'
            }, status=404)
        
        country_data = prices[country]
        
        # Transform data
        products = []
        for product_name, product_data in country_data.items():
            product_info = {
                'name': product_name,
                'operators': []
            }
            
            if isinstance(product_data, dict):
                for operator_name, operator_data in product_data.items():
                    if isinstance(operator_data, dict):
                        product_info['operators'].append({
                            'name': operator_name,
                            'cost': operator_data.get('cost', 0),
                            'count': operator_data.get('count', 0),
                            'rate': operator_data.get('rate', 0),
                            'cost_formatted': f"₦{operator_data.get('cost', 0) * 1:.2f}",
                            'available': operator_data.get('count', 0) > 0
                        })
            
            products.append(product_info)
        
        return JsonResponse({
            'success': True,
            'data': {
                'country': country,
                'products': products,
                'total_products': len(products)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting prices for country {country}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
@cache_page(60 * 10)  # Cache for 10 minutes
def get_prices_by_product(request, product):
    """
    Get pricing data for a specific product
    GET /api/5sim/prices/product/<product>/
    """
    try:
        prices = fivesim_api.get_prices_by_product(product)
        
        if product not in prices:
            return JsonResponse({
                'success': False,
                'error': f'Product "{product}" not found'
            }, status=404)
        
        product_data = prices[product]
        
        # Transform data
        countries = []
        for country_name, country_data in product_data.items():
            country_info = {
                'name': country_name,
                'operators': []
            }
            
            if isinstance(country_data, dict):
                for operator_name, operator_data in country_data.items():
                    if isinstance(operator_data, dict):
                        country_info['operators'].append({
                            'name': operator_name,
                            'cost': operator_data.get('cost', 0),
                            'count': operator_data.get('count', 0),
                            'rate': operator_data.get('rate', 0),
                            'cost_formatted': f"₦{operator_data.get('cost', 0) * 1:.2f}",
                            'available': operator_data.get('count', 0) > 0
                        })
            
            countries.append(country_info)
        
        return JsonResponse({
            'success': True,
            'data': {
                'product': product,
                'countries': countries,
                'total_countries': len(countries)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting prices for product {product}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
@cache_page(60 * 10)  # Cache for 10 minutes
def get_prices_by_country_and_product(request, country, product):
    """
    Get pricing data for a specific country and product combination
    GET /api/5sim/prices/<country>/<product>/
    """
    try:
        # Get actual pricing from 5sim API
        prices_data = fivesim_api.get_prices_by_country_and_product(country, product)
        
        # Extract operator pricing from the response
        operators = {}
        if prices_data and country in prices_data and product in prices_data[country]:
            product_data = prices_data[country][product]
            
            for operator_name, operator_data in product_data.items():
                if isinstance(operator_data, dict):
                    # Get admin-configured pricing for this service
                    from .models import SMSService, SMSOperator
                    from django.conf import settings
                    
                    try:
                        # Try to find admin-configured service
                        service = SMSService.objects.filter(service_code=product, is_active=True).first()
                        if service:
                            # Try to find operator-specific pricing
                            operator = service.operators.filter(
                                country_code=country,
                                operator_code=operator_name,
                                is_active=True
                            ).first()
                            
                            if operator:
                                # Use operator-specific pricing
                                final_price_ngn = operator.get_final_price_ngn()
                            else:
                                # Use service default pricing
                                final_price_ngn = service.get_final_price_ngn()
                        else:
                            # Fallback to basic conversion if service not configured
                            # 5sim returns prices in RUB, convert to NGN
                            cost_rub = operator_data.get('cost', 0)
                            final_price_ngn = cost_rub * settings.EXCHANGE_RATE_RUB_TO_NGN
                    except:
                        # Emergency fallback - 5sim prices are in RUB
                        cost_rub = operator_data.get('cost', 0)
                        final_price_ngn = cost_rub * settings.EXCHANGE_RATE_RUB_TO_NGN
                    
                    operators[operator_name] = {
                        'cost': int(final_price_ngn),
                        'count': operator_data.get('count', 0),
                        'rate': operator_data.get('rate', 0)
                    }
        
        if not operators:
            # No operators available - return empty result
            return JsonResponse({
                'success': True,
                'prices': {},
                'country': country,
                'product': product,
                'message': 'No operators available for this selection'
            })
        
        return JsonResponse({
            'success': True,
            'prices': operators,
            'country': country,
            'product': product,
            'total_operators': len(operators)
        })
        
    except Exception as e:
        logger.error(f"Error getting prices for {country}/{product}: {str(e)}")
        
        # For development/testing purposes, provide sample data
        if settings.DEBUG:
            logger.info(f"Returning sample data for {country}/{product} due to API error")
            sample_operators = {
                'operator1': {'cost': 45, 'count': 12, 'rate': 0.95},
                'operator2': {'cost': 52, 'count': 8, 'rate': 0.89},
                'operator3': {'cost': 38, 'count': 15, 'rate': 0.92},
                'operator4': {'cost': 61, 'count': 5, 'rate': 0.87}
            }
            
            return JsonResponse({
                'success': True,
                'prices': sample_operators,
                'country': country,
                'product': product,
                'total_operators': len(sample_operators),
                'note': 'Sample data - API connection issue'
            })
        
        # Return error response for production
        return JsonResponse({
            'success': False,
            'error': 'Unable to load pricing data at this time',
            'country': country,
            'product': product
        })


@require_http_methods(["GET"])
@cache_page(60 * 15)  # Cache for 15 minutes
def get_countries(request):
    """
    Get list of available countries
    GET /api/5sim/countries/
    """
    try:
        # Get actual countries from 5sim API
        countries_list = fivesim_api.get_available_countries()
        
        # Convert list to dictionary format expected by frontend
        countries_data = {}
        for country in countries_list:
            # Use the country name as both key and value for now
            # Later we can implement proper country code mapping
            countries_data[country] = country.title()
        
        return JsonResponse({
            'success': True,
            'countries': countries_data,
            'total': len(countries_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting countries: {str(e)}")
        # Return error response instead of sample data
        return JsonResponse({
            'success': False,
            'error': 'Unable to load countries at this time'
        })


@require_http_methods(["GET"])
@cache_page(60 * 15)  # Cache for 15 minutes
def get_products_list(request):
    """
    Get list of available products/services
    GET /api/5sim/products/
    """
    try:
        # Get actual products from 5sim API
        products_list = fivesim_api.get_available_products()
        
        # Convert list to dictionary format expected by frontend
        products_data = {}
        for product in products_list:
            # Use the product name as both key and value for now
            products_data[product] = product.title()
        
        return JsonResponse({
            'success': True,
            'products': products_data,
            'total': len(products_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting products: {str(e)}")
        # Return error response instead of sample data
        return JsonResponse({
            'success': False,
            'error': 'Unable to load products at this time'
        })


@require_http_methods(["GET"])
@cache_page(60 * 15)  # Cache for 15 minutes
def get_operators(request):
    """
    Get list of available operators
    GET /api/5sim/operators/
    """
    try:
        country = request.GET.get('country')
        product = request.GET.get('product')
        
        operators = fivesim_api.get_available_operators(country, product)
        
        return JsonResponse({
            'success': True,
            'data': {
                'operators': sorted(operators),
                'total': len(operators),
                'country': country,
                'product': product
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting operators: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
