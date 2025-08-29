"""
Debug views for testing 5sim API
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.conf import settings
import logging

from .fivesim import FiveSimAPI

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["GET"])
def test_5sim_api(request):
    """Test 5sim API connectivity"""
    try:
        api_client = FiveSimAPI()
        
        # Test basic connectivity with products endpoint
        products = api_client.get_products("russia", "any")
        
        return JsonResponse({
            'success': True,
            'message': 'API connection successful',
            'sample_products': list(products.keys())[:5] if products else []
        })
        
    except Exception as e:
        logger.error(f"5sim API test failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required  
@require_http_methods(["GET"])
def test_5sim_purchase_params(request):
    """Test purchase parameters without actually purchasing"""
    try:
        country = request.GET.get('country', 'russia')
        operator = request.GET.get('operator', 'any')
        product = request.GET.get('product', 'facebook')
        
        api_client = FiveSimAPI()
        
        # Get pricing for this combination
        prices = api_client.get_prices_by_country_and_product(country, product)
        
        return JsonResponse({
            'success': True,
            'country': country,
            'operator': operator, 
            'product': product,
            'pricing_available': bool(prices),
            'sample_prices': prices
        })
        
    except Exception as e:
        logger.error(f"5sim parameter test failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
