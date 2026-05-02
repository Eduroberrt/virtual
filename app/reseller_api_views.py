"""
Reseller API Views
Public API endpoints for external developers to integrate SMS verification
Uses MTelSMS as backend provider
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import time
import json
import logging

from .api_keys import require_api_key, check_api_permission
from .api_models import APIRequest, APIOrderMapping
from .models import UserProfile, Rental, SMSMessage, Service, Transaction
from .mtelsms import get_mtelsms_client, MTelSMSException
from django.conf import settings

logger = logging.getLogger(__name__)


def log_api_request(api_key, endpoint, method, status_code, response_time_ms, order_id=None, amount=None, request=None):
    """Helper to log API requests"""
    try:
        APIRequest.objects.create(
            api_key=api_key,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            order_id=order_id,
            amount=amount,
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
        )
    except Exception as e:
        logger.error(f"Failed to log API request: {str(e)}")


@require_http_methods(["GET"])
@require_api_key
@check_api_permission('balance')
def api_get_balance(request):
    """
    GET /api/v1/balance
    Get current account balance
    """
    start_time = time.time()
    
    try:
        user = request.api_user
        profile = UserProfile.objects.get(user=user)
        
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, '/api/v1/balance', 'GET', 200, response_time_ms, request=request)
        
        return JsonResponse({
            'success': True,
            'balance': float(profile.balance),
            'currency': 'NGN',
            'formatted': f"₦{profile.balance:,.2f}"
        })
        
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, '/api/v1/balance', 'GET', 500, response_time_ms, request=request)
        
        logger.error(f"API balance error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@require_http_methods(["GET"])
@require_api_key
@check_api_permission('services')
def api_get_countries(request):
    """
    GET /api/v1/countries
    Get list of available countries (MTelSMS supports USA)
    """
    start_time = time.time()
    
    try:
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, '/api/v1/countries', 'GET', 200, response_time_ms, request=request)
        
        return JsonResponse({
            'success': True,
            'countries': {
                'usa': 'United States'
            },
            'total': 1
        })
        
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, '/api/v1/countries', 'GET', 500, response_time_ms, request=request)
        
        logger.error(f"API countries error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch countries'
        }, status=500)


@require_http_methods(["GET"])
@require_api_key
@check_api_permission('services')
def api_get_services(request):
    """
    GET /api/v1/services
    Get list of available services from MTelSMS
    """
    start_time = time.time()
    
    try:
        # Get active services from database
        services = Service.objects.filter(is_active=True, available_numbers__gt=0)
        
        # Apply user's markup
        markup_percentage = request.api_key_obj.markup_percentage
        
        services_list = []
        for service in services:
            base_price_ngn = service.get_naira_price()
            markup_amount = base_price_ngn * (markup_percentage / 100)
            final_price = base_price_ngn + markup_amount
            
            services_list.append({
                'code': service.code,
                'name': service.name,
                'price': float(final_price),
                'currency': 'NGN',
                'available': service.available_numbers,
                'supports_multiple_sms': service.supports_multiple_sms
            })
        
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, '/api/v1/services', 'GET', 200, response_time_ms, request=request)
        
        return JsonResponse({
            'success': True,
            'services': services_list,
            'total': len(services_list),
            'country': 'usa'
        })
        
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, '/api/v1/services', 'GET', 500, response_time_ms, request=request)
        
        logger.error(f"API services error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch services'
        }, status=500)


@require_http_methods(["GET"])
@require_api_key
@check_api_permission('prices')
def api_get_service_price(request):
    """
    GET /api/v1/price?service=<service_code>
    Get pricing for specific service with user's markup applied
    """
    start_time = time.time()
    
    try:
        service_code = request.GET.get('service')
        
        if not service_code:
            response_time_ms = int((time.time() - start_time) * 1000)
            log_api_request(request.api_key_obj, '/api/v1/price', 'GET', 400, response_time_ms, request=request)
            
            return JsonResponse({
                'success': False,
                'error': 'service parameter is required'
            }, status=400)
        
        # Get service from database
        try:
            service = Service.objects.get(code=service_code, is_active=True)
        except Service.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Service "{service_code}" not found'
            }, status=404)
        
        # Calculate price with user's markup
        base_price_ngn = service.get_naira_price()
        markup_percentage = request.api_key_obj.markup_percentage
        markup_amount = base_price_ngn * (markup_percentage / 100)
        final_price = base_price_ngn + markup_amount
        
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, '/api/v1/price', 'GET', 200, response_time_ms, request=request)
        
        return JsonResponse({
            'success': True,
            'service': service.code,
            'name': service.name,
            'price': float(final_price),
            'base_price': float(base_price_ngn),
            'markup': float(markup_amount),
            'currency': 'NGN',
            'available': service.available_numbers,
            'supports_multiple_sms': service.supports_multiple_sms
        })
        
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, '/api/v1/price', 'GET', 500, response_time_ms, request=request)
        
        logger.error(f"API price error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch price'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@require_api_key
@check_api_permission('purchase')
def api_purchase_number(request):
    """
    POST /api/v1/purchase
    Purchase a phone number via MTelSMS
    
    Body: {
        "service": "wa",
        "max_price": 10.50
    }
    
    Note: MTelSMS doesn't support area_codes, carriers, or specific number selection.
    These parameters are accepted for backward compatibility but ignored.
    """
    start_time = time.time()
    
    try:
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON in request body'
            }, status=400)
        
        service_code = data.get('service')
        max_price_ngn = data.get('max_price')
        # MTelSMS doesn't support area_codes, carriers, or specific numbers
        # These parameters are ignored if provided
        
        if not service_code:
            response_time_ms = int((time.time() - start_time) * 1000)
            log_api_request(request.api_key_obj, '/api/v1/purchase', 'POST', 400, response_time_ms, request=request)
            
            return JsonResponse({
                'success': False,
                'error': 'service code is required'
            }, status=400)
        
        # Get service
        try:
            service = Service.objects.get(code=service_code, is_active=True)
        except Service.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Service "{service_code}" not found'
            }, status=404)
        
        # Get user profile and check balance
        user = request.api_user
        profile = UserProfile.objects.get(user=user)
        
        # Calculate base price (service price + our profit margin)
        base_service_price_ngn = service.get_naira_price()
        
        # Use base service price directly (no premium filters for MTelSMS)
        service_price_ngn = base_service_price_ngn
        
        # Apply user's API markup
        markup_percentage = request.api_key_obj.markup_percentage
        markup_amount = service_price_ngn * (markup_percentage / 100)
        final_price = service_price_ngn + markup_amount
        
        # Check balance
        if profile.balance < final_price:
            response_time_ms = int((time.time() - start_time) * 1000)
            log_api_request(request.api_key_obj, '/api/v1/purchase', 'POST', 402, response_time_ms, request=request)
            
            return JsonResponse({
                'success': False,
                'error': 'Insufficient balance',
                'required': float(final_price),
                'available': float(profile.balance)
            }, status=402)
        
        # Calculate max_price for MTelSMS (in USD)
        max_price_usd = None
        if max_price_ngn:
            max_price_usd = Decimal(str(max_price_ngn)) / UserProfile.USD_TO_NGN_RATE
        else:
            # Use calculated price as max
            max_price_usd = final_price / UserProfile.USD_TO_NGN_RATE
        
        # Make the purchase via MTelSMS
        try:
            with transaction.atomic():
                # Lock user profile to prevent race conditions
                profile = UserProfile.objects.select_for_update().get(user=user)
                
                # Double-check balance
                if profile.balance < final_price:
                    return JsonResponse({
                        'success': False,
                        'error': 'Insufficient balance'
                    }, status=402)
                
                # Call MTelSMS API
                client = get_mtelsms_client()
                
                # Validate service has MTelSMS ID
                service_id = service.mtelsms_service_id
                if not service_id or service_id.strip() == '':
                    return JsonResponse({
                        'success': False,
                        'error': f'Service "{service.name}" is not available. Please contact support.'
                    }, status=400)
                
                rental_id, phone_number, actual_price_usd, time_remaining = client.get_number(
                    service_id=service_id,
                    max_price=max_price_usd,
                    wholesale=False
                )
                
                # Create rental record
                rental = Rental.objects.create(
                    user=user,
                    rental_id=rental_id,
                    service=service,
                    phone_number=phone_number,
                    price=final_price,  # Store final price in NGN
                    max_price=Decimal(str(max_price_ngn)) if max_price_ngn else None
                )
                
                # Create API order mapping
                import uuid
                api_order_id = f"api_{uuid.uuid4().hex[:16]}"
                
                api_order = APIOrderMapping.objects.create(
                    api_key=request.api_key_obj,
                    rental=rental,
                    api_order_id=api_order_id,
                    api_price=final_price,
                    base_price=service_price_ngn,
                    markup_amount=markup_amount,
                    status='WAITING'
                )
                
                # Deduct balance
                profile.balance -= final_price
                profile.save()
                
                # Create transaction record
                Transaction.objects.create(
                    user=user,
                    amount=-final_price,
                    transaction_type='RENTAL',
                    description=f"API rental: {service.name} - {phone_number}",
                    rental=rental
                )
                
                # Update API key stats
                request.api_key_obj.total_purchases += 1
                request.api_key_obj.total_revenue += markup_amount
                request.api_key_obj.save(update_fields=['total_purchases', 'total_revenue'])
        
        except MTelSMSException as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            log_api_request(request.api_key_obj, '/api/v1/purchase', 'POST', 400, response_time_ms, request=request)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(
            request.api_key_obj, '/api/v1/purchase', 'POST', 200, response_time_ms,
            order_id=api_order_id, amount=float(final_price), request=request
        )
        
        return JsonResponse({
            'success': True,
            'order_id': api_order_id,
            'rental_id': rental_id,
            'phone_number': phone_number,
            'service': service.code,
            'service_name': service.name,
            'price': float(final_price),
            'currency': 'NGN',
            'status': 'WAITING'
        })
        
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, '/api/v1/purchase', 'POST', 500, response_time_ms, request=request)
        
        logger.error(f"API purchase error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Purchase failed. Please try again.'
        }, status=500)


@require_http_methods(["GET"])
@require_api_key
def api_check_order(request, order_id):
    """
    GET /api/v1/order/<order_id>
    Check order status and get SMS messages
    """
    start_time = time.time()
    
    try:
        # Find the API order
        try:
            api_order = APIOrderMapping.objects.select_related('rental', 'api_key').get(
                api_order_id=order_id,
                api_key=request.api_key_obj
            )
        except APIOrderMapping.DoesNotExist:
            response_time_ms = int((time.time() - start_time) * 1000)
            log_api_request(request.api_key_obj, f'/api/v1/order/{order_id}', 'GET', 404, response_time_ms, request=request)
            
            return JsonResponse({
                'success': False,
                'error': 'Order not found'
            }, status=404)
        
        rental = api_order.rental
        
        # AUTO-CANCEL AFTER 5 MINUTES IF NO SMS RECEIVED
        # Check if rental has been waiting for 5+ minutes
        from datetime import timedelta
        if rental.status == 'WAITING':
            time_since_creation = timezone.now() - rental.created_at
            if time_since_creation >= timedelta(minutes=5):
                logger.info(f"API Order {order_id}: Rental {rental.rental_id} has been waiting for {time_since_creation.total_seconds()/60:.1f} minutes - attempting auto-cancel")
                
                # Before auto-cancelling, check MTelSMS one more time to ensure SMS wasn't just received
                try:
                    client = get_mtelsms_client()
                    status, code, phone_number, time_remaining = client.get_code(rental_id=rental.rental_id)
                    
                    # If SMS was received, save it and return success (no cancel)
                    if status == 'RECEIVED' and code:
                        rental.status = 'RECEIVED'
                        api_order.status = 'RECEIVED'
                        rental.save()
                        api_order.save()
                        
                        SMSMessage.objects.get_or_create(
                            rental=rental,
                            code=code,
                            defaults={'full_text': code}
                        )
                        
                        logger.info(f"API Order {order_id}: SMS received just before auto-cancel - saved code")
                        
                        messages = [{
                            'code': msg.code,
                            'text': msg.full_text,
                            'received_at': msg.received_at.isoformat()
                        } for msg in rental.messages.all()]
                        
                        response_time_ms = int((time.time() - start_time) * 1000)
                        log_api_request(request.api_key_obj, f'/api/v1/order/{order_id}', 'GET', 200, response_time_ms, request=request)
                        
                        return JsonResponse({
                            'success': True,
                            'order_id': order_id,
                            'rental_id': rental.rental_id,
                            'phone_number': rental.phone_number,
                            'status': 'RECEIVED',
                            'messages': messages
                        })
                    
                    # SMS still not received after 5 minutes - proceed with auto-cancel
                    elif status == 'WAITING':
                        logger.info(f"API Order {order_id}: Auto-cancelling after 5 minutes with no SMS")
                        
                        # Attempt to cancel with MTelSMS
                        cancel_success = client.cancel_rental(rental_id=rental.rental_id)
                        
                        if cancel_success:
                            with transaction.atomic():
                                # Reload rental with lock
                                rental = Rental.objects.select_for_update().get(rental_id=rental.rental_id)
                                api_order = APIOrderMapping.objects.select_for_update().get(api_order_id=order_id)
                                
                                # Check if already refunded (race condition protection)
                                if rental.refunded:
                                    response_time_ms = int((time.time() - start_time) * 1000)
                                    log_api_request(request.api_key_obj, f'/api/v1/order/{order_id}', 'GET', 200, response_time_ms, request=request)
                                    
                                    return JsonResponse({
                                        'success': True,
                                        'order_id': order_id,
                                        'status': 'CANCELLED',
                                        'refunded': True,
                                        'messages': []
                                    })
                                
                                # Update rental and API order status
                                rental.status = 'CANCELLED'
                                rental.refunded = True
                                rental.save()
                                
                                api_order.status = 'CANCELLED'
                                api_order.save()
                                
                                # Issue refund
                                user = request.api_user
                                profile = UserProfile.objects.select_for_update().get(user=user)
                                profile.balance += api_order.api_price
                                profile.save()
                                
                                # Create refund transaction
                                Transaction.objects.create(
                                    user=user,
                                    amount=api_order.api_price,
                                    transaction_type='REFUND',
                                    description=f'Auto-refund: API order {order_id} - No SMS after 5 minutes',
                                    rental=rental
                                )
                                
                                logger.info(f"API Order {order_id}: Auto-cancelled and refunded ₦{api_order.api_price}")
                            
                            response_time_ms = int((time.time() - start_time) * 1000)
                            log_api_request(request.api_key_obj, f'/api/v1/order/{order_id}', 'GET', 200, response_time_ms, request=request)
                            
                            return JsonResponse({
                                'success': True,
                                'order_id': order_id,
                                'rental_id': rental.rental_id,
                                'status': 'CANCELLED',
                                'refunded': True,
                                'messages': []
                            })
                        else:
                            logger.warning(f"API Order {order_id}: Failed to cancel with MTelSMS after 5 minutes")
                            # Continue with normal flow if cancel failed
                    
                except MTelSMSException as e:
                    logger.error(f"API Order {order_id}: MTelSMS error during auto-cancel check: {str(e)}")
                    # Continue with normal flow if API call failed
        
        # Check with MTelSMS for updates
        try:
            client = get_mtelsms_client()
            status, code, phone_number, time_remaining = client.get_code(
                rental_id=rental.rental_id
            )
            
            # Check if rental has expired (time_remaining = 0)
            if time_remaining <= 0 and status == 'WAITING':
                with transaction.atomic():
                    # Reload rental and API order with locks to prevent race conditions
                    rental = Rental.objects.select_for_update().get(rental_id=rental.rental_id)
                    api_order = APIOrderMapping.objects.select_for_update().get(api_order_id=order_id)
                    
                    # Check if already refunded (double-refund protection)
                    if rental.refunded:
                        logger.info(f"API Order {order_id}: Rental already refunded, skipping")
                        response_time_ms = int((time.time() - start_time) * 1000)
                        log_api_request(request.api_key_obj, f'/api/v1/order/{order_id}', 'GET', 200, response_time_ms, request=request)
                        
                        return JsonResponse({
                            'success': True,
                            'order_id': order_id,
                            'rental_id': rental.rental_id,
                            'phone_number': rental.phone_number,
                            'status': 'EXPIRED',
                            'service': rental.service.code,
                            'service_name': rental.service.name,
                            'sms': [],
                            'created_at': rental.created_at.isoformat()
                        })
                    
                    # Mark as expired
                    rental.status = 'EXPIRED'
                    rental.refunded = True
                    api_order.status = 'EXPIRED'
                    rental.save()
                    api_order.save()
                    
                    # Issue refund
                    user = request.api_user
                    profile = UserProfile.objects.select_for_update().get(user=user)
                    profile.balance += rental.price
                    profile.save()
                    
                    # Log refund transaction
                    Transaction.objects.create(
                        user=user,
                        amount=rental.price,
                        transaction_type='REFUND',
                        description=f'Automatic refund for expired rental {rental.phone_number}'
                    )
                    
                    logger.info(f"Automatic refund issued for expired rental {rental.rental_id}")
            else:
                # Update rental status normally
                rental.status = status
                rental.save()
                
                # Update API order status
                api_order.status = status
                api_order.save()
            
            # Save message if received
            if status == 'RECEIVED' and code:
                SMSMessage.objects.get_or_create(
                    rental=rental,
                    code=code,
                    defaults={'full_text': code}
                )
        except MTelSMSException as e:
            logger.error(f"MTelSMS status check error: {str(e)}")
        
        # Get SMS messages
        sms_messages = []
        for msg in rental.messages.all():
            sms_messages.append({
                'code': msg.code,
                'text': msg.full_text,
                'received_at': msg.received_at.isoformat()
            })
        
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, f'/api/v1/order/{order_id}', 'GET', 200, response_time_ms, request=request)
        
        return JsonResponse({
            'success': True,
            'order_id': order_id,
            'rental_id': rental.rental_id,
            'phone_number': rental.phone_number,
            'status': rental.status,
            'service': rental.service.code,
            'service_name': rental.service.name,
            'sms': sms_messages,
            'created_at': rental.created_at.isoformat()
        })
        
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, f'/api/v1/order/{order_id}', 'GET', 500, response_time_ms, request=request)
        
        logger.error(f"API check order error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to check order status'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@require_api_key
@check_api_permission('cancel')
def api_cancel_order(request, order_id):
    """
    POST /api/v1/order/<order_id>/cancel
    Cancel an order and get refund
    """
    start_time = time.time()
    
    try:
        # Find the API order
        try:
            api_order = APIOrderMapping.objects.select_related('rental', 'api_key').get(
                api_order_id=order_id,
                api_key=request.api_key_obj
            )
        except APIOrderMapping.DoesNotExist:
            response_time_ms = int((time.time() - start_time) * 1000)
            log_api_request(request.api_key_obj, f'/api/v1/order/{order_id}/cancel', 'POST', 404, response_time_ms, request=request)
            
            return JsonResponse({
                'success': False,
                'error': 'Order not found'
            }, status=404)
        
        rental = api_order.rental
        
        # Check if already cancelled
        if rental.status in ['CANCELLED', 'DONE', 'RECEIVED']:
            return JsonResponse({
                'success': False,
                'error': f'Cannot cancel order with status: {rental.status}'
            }, status=400)
        
        # Cancel with MTelSMS
        try:
            client = get_mtelsms_client()
            success = client.cancel_rental(rental_id=rental.rental_id)
            
            if not success:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to cancel with provider'
                }, status=400)
        except MTelSMSException as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
        # Process refund
        with transaction.atomic():
            # Reload rental and API order with locks to prevent race conditions
            rental = Rental.objects.select_for_update().get(rental_id=rental.rental_id)
            api_order = APIOrderMapping.objects.select_for_update().get(api_order_id=order_id)
            
            # Check if already refunded (double-refund protection)
            if rental.refunded:
                response_time_ms = int((time.time() - start_time) * 1000)
                log_api_request(request.api_key_obj, f'/api/v1/order/{order_id}/cancel', 'POST', 200, response_time_ms, request=request)
                
                return JsonResponse({
                    'success': True,
                    'order_id': order_id,
                    'status': 'CANCELLED',
                    'refund_amount': float(api_order.api_price),
                    'currency': 'NGN',
                    'message': 'Already refunded'
                })
            
            # Mark as cancelled
            rental.status = 'CANCELLED'
            rental.refunded = True
            rental.save()
            
            api_order.status = 'CANCELLED'
            api_order.save()
            
            # Refund to user
            user = request.api_user
            profile = UserProfile.objects.select_for_update().get(user=user)
            profile.balance += api_order.api_price
            profile.save()
            
            # Create transaction record
            Transaction.objects.create(
                user=user,
                amount=api_order.api_price,
                transaction_type='REFUND',
                description=f'API order {order_id} cancelled and refunded',
                rental=rental
            )
        
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, f'/api/v1/order/{order_id}/cancel', 'POST', 200, response_time_ms, request=request)
        
        return JsonResponse({
            'success': True,
            'order_id': order_id,
            'status': 'CANCELLED',
            'refund_amount': float(api_order.api_price),
            'currency': 'NGN'
        })
        
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, f'/api/v1/order/{order_id}/cancel', 'POST', 500, response_time_ms, request=request)
        
        logger.error(f"API cancel order error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to cancel order'
        }, status=500)


@require_http_methods(["GET"])
@require_api_key
def api_get_orders(request):
    """
    GET /api/v1/orders?limit=20&status=WAITING
    Get list of user's orders
    """
    start_time = time.time()
    
    try:
        limit = int(request.GET.get('limit', 20))
        limit = min(limit, 100)  # Max 100
        
        status = request.GET.get('status')
        
        orders_query = APIOrderMapping.objects.filter(
            api_key=request.api_key_obj
        ).select_related('rental', 'rental__service').order_by('-created_at')
        
        if status:
            orders_query = orders_query.filter(status=status)
        
        orders_query = orders_query[:limit]
        
        orders_list = []
        for api_order in orders_query:
            rental = api_order.rental
            
            # Get latest SMS if any
            latest_sms = rental.messages.first()
            
            orders_list.append({
                'order_id': api_order.api_order_id,
                'rental_id': rental.rental_id,
                'phone_number': rental.phone_number,
                'service': rental.service.code,
                'service_name': rental.service.name,
                'status': api_order.status,
                'price': float(api_order.api_price),
                'has_sms': rental.messages.exists(),
                'sms_code': latest_sms.code if latest_sms else None,
                'created_at': api_order.created_at.isoformat()
            })
        
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, '/api/v1/orders', 'GET', 200, response_time_ms, request=request)
        
        return JsonResponse({
            'success': True,
            'orders': orders_list,
            'total': len(orders_list)
        })
        
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request.api_key_obj, '/api/v1/orders', 'GET', 500, response_time_ms, request=request)
        
        logger.error(f"API get orders error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch orders'
        }, status=500)
