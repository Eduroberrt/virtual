"""
5sim.net Purchase Views
Handles purchase o        if active_orders.count() >= 3:
            return JsonResponse({
                'success': False,
                'error': 'You can only have 3 active orders at a time.'
            })ions for SMS verification services using backend API
"""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.transaction import atomic
from django.core.paginator import Paginator
from django.conf import settings

from .models import FiveSimOrder, FiveSimSMS, UserProfile, Transaction
from .fivesim import FiveSimAPI

logger = logging.getLogger(__name__)

# Backend API key - set this in your settings
FIVESIM_API_KEY = getattr(settings, 'FIVESIM_API_KEY', None)

@login_required
@require_http_methods(["POST"])
def buy_activation_number(request):
    """Purchase an activation number using backend API"""
    
    try:
        if not FIVESIM_API_KEY:
            return JsonResponse({
                'success': False,
                'error': 'Service temporarily unavailable. Please try again later.'
            })
        
        # Purchase limit removed - users can now have unlimited active orders
        
        # Get purchase parameters
        country = request.POST.get('country', '').strip()
        operator = request.POST.get('operator', '').strip()
        product = request.POST.get('product', '').strip()
        
        # Optional parameters
        forwarding = request.POST.get('forwarding') == '1'
        forwarding_number = request.POST.get('forwarding_number', '').strip()
        reuse = request.POST.get('reuse') == '1'
        voice = request.POST.get('voice') == '1'
        ref = request.POST.get('ref', '').strip()
        max_price = request.POST.get('max_price', '').strip()
        
        # Debug logging
        logger.info(f"Purchase request - User: {request.user.username}, Country: '{country}', Operator: '{operator}', Product: '{product}'")
        
        # Validate required fields
        if not all([country, operator, product]):
            return JsonResponse({
                'success': False,
                'error': 'Country, operator, and product are required'
            })
        
        # Initialize API client with backend key
        api_client = FiveSimAPI(FIVESIM_API_KEY)
        
        # Prepare purchase parameters
        purchase_params = {
            'country': country,
            'operator': operator,
            'product': product,
            'forwarding': forwarding,
            'reuse': reuse,
            'voice': voice,
        }
        
        if forwarding and forwarding_number:
            purchase_params['number'] = forwarding_number
        if ref:
            purchase_params['ref'] = ref
        if max_price:
            try:
                purchase_params['max_price'] = float(max_price)
            except ValueError:
                pass
        
        # Make the purchase
        logger.info(f"Calling 5sim API with params: {purchase_params}")
        result = api_client.buy_activation_number(**purchase_params)
        logger.info(f"5sim API response: {result}")
        
        # Calculate price using admin-configured pricing
        from .models import SMSService, SMSOperator
        from django.conf import settings
        
        try:
            # Try to find admin-configured service
            service = SMSService.objects.filter(service_code=product, is_active=True).first()
            if service:
                # Try to find operator-specific pricing
                sms_operator = service.operators.filter(
                    country_code=country,
                    operator_code=operator,
                    is_active=True
                ).first()
                
                if sms_operator:
                    # Use operator-specific pricing
                    price_naira = Decimal(str(sms_operator.get_final_price_ngn()))
                else:
                    # Use service default pricing
                    price_naira = Decimal(str(service.get_final_price_ngn()))
            else:
                # Fallback to basic conversion if service not configured
                price_naira = Decimal(str(result['price'])) * settings.EXCHANGE_RATE_USD_TO_NGN
        except Exception as e:
            # Emergency fallback
            price_naira = Decimal(str(result['price'])) * settings.EXCHANGE_RATE_USD_TO_NGN
        
        # Parse expiration date
        expires_at = datetime.fromisoformat(result['expires'].replace('Z', '+00:00'))
        
        # Get user profile and check balance
        user_profile = UserProfile.objects.get(user=request.user)
        if user_profile.balance < price_naira:
            return JsonResponse({
                'success': False,
                'error': f'Insufficient balance. You need ₦{price_naira:.2f} but have ₦{user_profile.balance:.2f}'
            })
        
        # Create order record and deduct balance
        with atomic():
            # Deduct balance
            user_profile.balance -= price_naira
            user_profile.save()
            
            order = FiveSimOrder.objects.create(
                user=request.user,
                order_id=result['id'],
                order_type='ACTIVATION',
                phone_number=result['phone'],
                country=result.get('country', ''),
                operator=result.get('operator', ''),
                product=result['product'],
                price=Decimal(str(result['price'])),
                price_naira=price_naira,
                status=result['status'],
                expires_at=expires_at,
                forwarding=result.get('forwarding', False),
                forwarding_number=result.get('forwarding_number', ''),
                reuse_enabled=reuse,
                voice_enabled=voice,
                max_price=Decimal(str(max_price)) if max_price else None,
                referral_key=ref or None,
            )
            
            # Create transaction record
            Transaction.objects.create(
                user=request.user,
                amount=price_naira,
                transaction_type='RENTAL',
                description=f'5sim activation number: {product} ({result["phone"]})',
                rental=None,  # This is for 5sim, not old rental system
            )
        
        return JsonResponse({
            'success': True,
            'order_id': order.order_id,
            'phone_number': order.phone_number,
            'expires_at': order.expires_at.isoformat(),
            'status': order.status,
            'price': str(order.price_naira),
            'new_balance': float(user_profile.balance),
        })
        
    except Exception as e:
        logger.error(f"Purchase failed for user {request.user.username}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def check_order_status(request, order_id):
    """Check order status and update SMS messages"""
    
    try:
        if not FIVESIM_API_KEY:
            return JsonResponse({
                'success': False,
                'error': 'Service temporarily unavailable'
            })
        
        # Get the order
        order = get_object_or_404(FiveSimOrder, order_id=order_id, user=request.user)
        
        # Initialize API client
        api_client = FiveSimAPI(FIVESIM_API_KEY)
        
        # Check order status with 5sim
        result = api_client.check_order(order_id)
        
        # Update order status
        order.status = result['status']
        order.save()
        
        # Update SMS messages
        if result.get('sms'):
            existing_sms_ids = set(
                order.sms_messages.exclude(sms_id__isnull=True).values_list('sms_id', flat=True)
            )
            
            for sms_data in result['sms']:
                sms_id = sms_data.get('id')
                if sms_id and sms_id not in existing_sms_ids:
                    sms_date = datetime.fromisoformat(sms_data['date'].replace('Z', '+00:00'))
                    FiveSimSMS.objects.create(
                        order=order,
                        sms_id=sms_id,
                        sender=sms_data.get('sender', ''),
                        text=sms_data.get('text', ''),
                        code=sms_data.get('code', ''),
                        date=sms_date,
                    )
        
        # Get updated SMS messages
        sms_messages = order.sms_messages.all().order_by('-date')
        sms_data = []
        latest_sms_code = None
        
        for sms in sms_messages:
            sms_data.append({
                'sender': sms.sender,
                'text': sms.text,
                'code': sms.code,
                'date': sms.date.isoformat(),
            })
            # Get the latest SMS code for quick access
            if not latest_sms_code and (sms.code or sms.text):
                latest_sms_code = sms.code or sms.text
        
        return JsonResponse({
            'success': True,
            'status': order.status,
            'phone_number': order.phone_number,
            'expires_at': order.expires_at.isoformat(),
            'sms_code': latest_sms_code,
            'sms_messages': sms_data,
        })
        
    except Exception as e:
        logger.error(f"Order status check failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["POST"])
def finish_order(request, order_id):
    """Mark order as finished"""
    
    try:
        if not FIVESIM_API_KEY:
            return JsonResponse({
                'success': False,
                'error': 'Service temporarily unavailable'
            })
        
        # Get the order
        order = get_object_or_404(FiveSimOrder, order_id=order_id, user=request.user)
        
        # Initialize API client
        api_client = FiveSimAPI(FIVESIM_API_KEY)
        
        # Finish order with 5sim
        result = api_client.finish_order(order_id)
        
        # Update order status
        order.status = result['status']
        order.save()
        
        return JsonResponse({
            'success': True,
            'status': order.status,
        })
        
    except Exception as e:
        logger.error(f"Order finish failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["POST"])
def cancel_order(request, order_id):
    """Cancel an order and process refund"""
    
    try:
        if not FIVESIM_API_KEY:
            return JsonResponse({
                'success': False,
                'error': 'Service temporarily unavailable'
            })
        
        # Get the order
        order = get_object_or_404(FiveSimOrder, order_id=order_id, user=request.user)
        
        # Check if order can be cancelled
        if order.status in ['CANCELED', 'FINISHED']:
            return JsonResponse({
                'success': False,
                'error': f'Order is already {order.status.lower()} and cannot be cancelled'
            })
        
        # Check if order has already expired
        if order.expires_at <= timezone.now():
            return JsonResponse({
                'success': False,
                'error': 'Order has already expired'
            })
        
        # Initialize API client
        api_client = FiveSimAPI(FIVESIM_API_KEY)
        
        # Cancel order with 5sim
        result = api_client.cancel_order(order_id)
        
        # Process refund and update order status
        with atomic():
            # Update order status
            order.status = result['status']
            order.save()
            
            # Process refund
            user_profile = UserProfile.objects.get(user=request.user)
            refund_amount = order.price_naira
            
            # Credit user balance
            user_profile.balance += refund_amount
            user_profile.save()
            
            # Create refund transaction
            Transaction.objects.create(
                user=request.user,
                amount=refund_amount,
                transaction_type='REFUND',
                description=f'Refund for cancelled 5sim order: {order.product} ({order.phone_number})',
                rental=None,
            )
        
        return JsonResponse({
            'success': True,
            'status': order.status,
            'refund_amount': f'{refund_amount:.2f}',
            'new_balance': float(user_profile.balance),
            'message': f'Order cancelled successfully. ₦{refund_amount:.2f} has been refunded to your account.'
        })
        
    except Exception as e:
        logger.error(f"Order cancel failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["GET"])
def get_user_orders(request):
    """Get user's active orders and completed orders with SMS codes"""
    
    try:
        from django.db.models import Q, Exists, OuterRef
        
        # Get orders that are either:
        # 1. Still active (not expired and no SMS code)
        # 2. Have received SMS codes (regardless of expiry)
        current_time = timezone.now()
        
        # Subquery to check if order has SMS messages
        has_sms = FiveSimSMS.objects.filter(
            order=OuterRef('pk')
        ).exclude(
            Q(text__isnull=True) & Q(code__isnull=True)
        )
        
        orders = FiveSimOrder.objects.filter(
            user=request.user
        ).exclude(
            status__in=['CANCELED', 'EXPIRED', 'TIMEOUT']  # Exclude failed/cancelled orders
        ).filter(
            Q(status__in=['PENDING', 'RECEIVED']) |  # Active orders
            Q(Exists(has_sms)) |                     # Orders with SMS codes (successful)
            Q(status='FINISHED')                     # Finished orders
        ).order_by('-created_at')[:20]  # Limit to last 20 active/successful orders
        
        orders_data = []
        for order in orders:
            # Get the latest SMS code for this order
            latest_sms = order.sms_messages.exclude(
                Q(text__isnull=True) & Q(code__isnull=True)
            ).order_by('-created_at').first()
            
            sms_code = None
            if latest_sms:
                sms_code = latest_sms.code or latest_sms.text
            
            orders_data.append({
                'id': order.order_id,
                'phone_number': order.phone_number,
                'product': order.product.title() if order.product else 'Unknown',
                'country': order.country.title() if order.country else 'Unknown',
                'operator': order.operator,
                'status': order.status,
                'expires_at': order.expires_at.isoformat(),
                'sms_code': sms_code,
                'created_at': order.created_at.isoformat(),
                'price_naira': str(order.price_naira),
            })
        
        return JsonResponse({
            'success': True,
            'orders': orders_data
        })
        
    except Exception as e:
        logger.error(f"Failed to get orders for user {request.user.username}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to load orders'
        })
