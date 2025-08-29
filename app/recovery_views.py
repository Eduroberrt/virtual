"""
Manual Recovery View for 5sim Purchases
This handles cases where purchases succeed on 5sim but fail to save locally due to API issues
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.transaction import atomic
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from .models import FiveSimOrder, UserProfile, Transaction
from .fivesim import FiveSimAPI
from django.conf import settings

logger = logging.getLogger(__name__)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def recover_purchase(request):
    """
    Manually recover a purchase that succeeded on 5sim but failed to save locally
    """
    try:
        # Get the order ID from the request
        order_id = request.POST.get('order_id', '').strip()
        
        if not order_id:
            return JsonResponse({
                'success': False,
                'error': 'Order ID is required'
            })
        
        # Check if this order already exists in our system
        existing_order = FiveSimOrder.objects.filter(order_id=order_id, user=request.user).first()
        if existing_order:
            return JsonResponse({
                'success': False,
                'error': 'This order already exists in your account'
            })
        
        # Initialize API client
        api_client = FiveSimAPI(settings.FIVESIM_API_KEY)
        
        # Get order details from 5sim
        try:
            order_data = api_client.check_order(order_id)
            logger.info(f"Manual recovery - got order data: {order_data}")
        except Exception as api_error:
            logger.error(f"Failed to get order data from 5sim: {api_error}")
            return JsonResponse({
                'success': False,
                'error': f'Could not retrieve order from 5sim: {str(api_error)}'
            })
        
        # Validate order data
        if not isinstance(order_data, dict) or 'id' not in order_data:
            return JsonResponse({
                'success': False,
                'error': 'Invalid order data received from 5sim'
            })
        
        # Calculate price in Naira (use a reasonable conversion rate)
        price_usd = float(order_data.get('price', 0))
        price_naira = Decimal(price_usd) * getattr(settings, 'EXCHANGE_RATE_USD_TO_NGN', Decimal('1650'))
        
        # Parse expiration date
        expires_str = order_data.get('expires', '')
        if expires_str:
            try:
                expires_at = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
            except:
                expires_at = timezone.now() + timedelta(minutes=20)  # Default 20 minutes
        else:
            expires_at = timezone.now() + timedelta(minutes=20)
        
        # Create the order record
        with atomic():
            order = FiveSimOrder.objects.create(
                user=request.user,
                order_id=order_data['id'],
                order_type='ACTIVATION',
                phone_number=order_data.get('phone', ''),
                country=order_data.get('country', ''),
                operator=order_data.get('operator', ''),
                product=order_data.get('product', ''),
                price=Decimal(str(price_usd)),
                price_naira=price_naira,
                status=order_data.get('status', 'PENDING'),
                expires_at=expires_at,
                forwarding=False,
                forwarding_number='',
                reuse_enabled=False,
                voice_enabled=False,
                max_price=None,
                referral_key=None,
            )
            
            # Note: We don't deduct balance since this was already charged by 5sim
            # Create a transaction record for tracking
            Transaction.objects.create(
                user=request.user,
                amount=price_naira,
                transaction_type='RENTAL',
                description=f'Manual recovery - 5sim order: {order_data.get("product", "")} ({order_data.get("phone", "")})',
                rental=None,
            )
        
        logger.info(f"Manual recovery successful for order {order_id} by user {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'order_id': order.order_id,
            'phone_number': order.phone_number,
            'status': order.status,
            'message': 'Order successfully recovered and added to your account'
        })
        
    except Exception as e:
        logger.error(f"Manual recovery failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Recovery failed: {str(e)}'
        })

@login_required
def recovery_page(request):
    """Show the manual recovery page"""
    return render(request, 'recovery.html')
