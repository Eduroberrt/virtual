from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.db import transaction
from django.db import models
from decimal import Decimal
import json
import logging

from .models import UserProfile, Service, Rental, SMSMessage, Transaction
from .daisysms import get_daisysms_client, DaisySMSException
from .korapay import KoraPayClient

logger = logging.getLogger(__name__)

def json_response(data, status=200):
    """Helper function for JSON responses"""
    return JsonResponse(data, status=status)

def error_response(message, status=400):
    """Helper function for error responses"""
    return JsonResponse({'error': message}, status=status)

@login_required
@require_http_methods(["GET"])
def get_user_balance(request):
    """Get user's current balance"""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        # Sync with DaisySMS if API key is available
        if profile.api_key:
            try:
                client = get_daisysms_client(request.user)
                remote_balance = client.get_balance(user=request.user)
                profile.balance = remote_balance
                profile.save()
            except DaisySMSException as e:
                logger.warning(f"Failed to sync balance for {request.user.username}: {str(e)}")
        return json_response({
            'success': True,
            'balance': str(profile.balance),
            'balance_naira': f"{profile.get_naira_balance():,.2f}",
            'has_api_key': bool(profile.api_key)
        })
    except Exception as e:
        logger.error(f"Error getting balance for {request.user.username}: {str(e)}")
        return error_response("Failed to get balance", 500)

@login_required
@require_http_methods(["GET"])
def get_services(request):
    """Get available services with pricing"""
    try:
        # Sync services from API if possible
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.api_key:
                client = get_daisysms_client(request.user)
                client.sync_services(user=request.user)
        except (UserProfile.DoesNotExist, DaisySMSException) as e:
            logger.warning(f"Could not sync services: {str(e)}")
        
        services = Service.objects.filter(is_active=True)
        
        services_data = []
        for service in services:
            services_data.append({
                'id': service.id,
                'code': service.code,
                'name': service.name,
                'icon_url': service.icon_url,
                'price': str(service.price),
                'daily_price': str(service.daily_price),
                'price_naira': f"{service.get_naira_price():,.2f}",
                'daily_price_naira': f"{service.get_naira_daily_price():,.2f}",
                'profit_margin': str(service.profit_margin),
                'available_numbers': service.available_numbers,
                'supports_multiple_sms': service.supports_multiple_sms
            })
        
        return json_response({
            'services': services_data
        })
    
    except Exception as e:
        logger.error(f"Error getting services: {str(e)}")
        return error_response("Failed to get services", 500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def rent_number(request):
    """Rent a new phone number"""
    try:
        data = json.loads(request.body)
        service_code = data.get('service_code')
        max_price = data.get('max_price')
        is_ltr = data.get('ltr', False)
        auto_renew = data.get('auto_renew', False)
        area_codes = data.get('area_codes', [])
        carriers = data.get('carriers', [])
        specific_number = data.get('number')
        
        if not service_code:
            return error_response("Service code is required")
        
        service = get_object_or_404(Service, code=service_code, is_active=True)
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Check if user has sufficient balance using service price in NGN
        service_price_naira = service.get_naira_price()
        
        # Apply 20% premium for filters (area codes, carriers, or specific number)
        has_premium_filters = bool(area_codes or carriers or specific_number)
        if has_premium_filters:
            service_price_naira *= Decimal('1.2')  # 20% increase
        
        # Compare using the user's Naira balance (handles USD/NGN conversion automatically)
        user_balance_naira = profile.get_naira_balance()
        if user_balance_naira < service_price_naira:
            return error_response("Insufficient balance")
        
        # Convert max_price to Decimal if provided (max_price is in NGN)
        if max_price:
            max_price = Decimal(str(max_price))
        
        # Convert NGN prices to USD for DaisySMS API call
        service_price_usd = service_price_naira / UserProfile.USD_TO_NGN_RATE
        max_price_usd = max_price / UserProfile.USD_TO_NGN_RATE if max_price else None
        
        try:
            client = get_daisysms_client(request.user)
            rental_id, phone_number, actual_price = client.get_number(
                service_code=service_code,
                user=request.user,
                max_price=max_price_usd,  # Pass USD price to DaisySMS API
                # Removed LTR parameters since we don't use long-term rentals
                # ltr=is_ltr,
                # auto_renew=auto_renew,
                area_codes=area_codes if area_codes else None,
                carriers=carriers if carriers else None,
                specific_number=specific_number
            )
            
            # Create rental record
            with transaction.atomic():
                # Use service price in NGN (with profit margin) and apply premium filters surcharge
                final_price_naira = service_price_naira  # Already includes margin and premium
                
                rental = Rental.objects.create(
                    user=request.user,
                    rental_id=rental_id,
                    service=service,
                    phone_number=phone_number,
                    price=final_price_naira,  # Store NGN price
                    is_ltr=False,  # We don't use LTR
                    auto_renew=False,  # We don't use auto-renew
                    area_codes=','.join(area_codes) if area_codes else None,
                    carriers=','.join(carriers) if carriers else None,
                    max_price=max_price,  # NGN
                    paid_until=None  # No LTR, so no paid_until date
                )
                
                # Create transaction record using NGN price
                Transaction.objects.create(
                    user=request.user,
                    amount=-final_price_naira,  # Deduct NGN price from balance
                    transaction_type='RENTAL',
                    description=f"Rented {service.name} number {phone_number}",
                    rental=rental
                )
                
                # Update user balance - handle USD/NGN format properly
                if profile.balance < 100 and profile.balance > 0:
                    # Balance is in USD format - deduct in USD
                    final_price_usd = final_price_naira / UserProfile.USD_TO_NGN_RATE
                    profile.balance -= final_price_usd
                else:
                    # Balance is in NGN format - deduct in NGN
                    profile.balance -= final_price_naira
                profile.save()
            
            return json_response({
                'success': True,
                'rental_id': rental_id,
                'phone_number': phone_number,
                'price': str(final_price_naira),  # Return NGN price
                'price_naira': str(final_price_naira),  # Return NGN price
                'has_premium_filters': has_premium_filters,  # Indicate if premium pricing was applied
                'is_ltr': False  # We don't use LTR
            })
        
        except DaisySMSException as e:
            return error_response(str(e))
    
    except Exception as e:
        logger.error(f"Error renting number: {str(e)}")
        return error_response("Failed to rent number", 500)

@login_required
@require_http_methods(["GET"])
def check_sms(request, rental_id):
    """Check for SMS messages on a rental"""
    try:
        rental = get_object_or_404(Rental, rental_id=rental_id, user=request.user)
        
        if rental.status in ['CANCELLED', 'DONE']:
            return json_response({
                'status': rental.status,
                'messages': []
            })
        
        try:
            client = get_daisysms_client(request.user)
            status, code, full_text = client.get_status(
                rental_id=rental_id, 
                user=request.user, 
                get_full_text=True
            )
            
            # Update rental status
            rental.status = status
            rental.save()
            
            # Save message if received
            if status == 'RECEIVED' and code:
                message, created = SMSMessage.objects.get_or_create(
                    rental=rental,
                    code=code,
                    defaults={'full_text': full_text}
                )
            
            # Get all messages for this rental
            messages = []
            for msg in rental.messages.all():
                messages.append({
                    'code': msg.code,
                    'full_text': msg.full_text,
                    'received_at': msg.received_at.isoformat()
                })
            
            return json_response({
                'status': status,
                'messages': messages
            })
        
        except DaisySMSException as e:
            return error_response(str(e))
    
    except Exception as e:
        logger.error(f"Error checking SMS: {str(e)}")
        return error_response("Failed to check SMS", 500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def cancel_rental(request):
    """Cancel a rental and get refund"""
    try:
        data = json.loads(request.body)
        rental_id = data.get('id')
        
        if not rental_id:
            return error_response("Rental ID is required")
        
        rental = get_object_or_404(Rental, rental_id=rental_id, user=request.user)
        
        if rental.status in ['CANCELLED', 'DONE', 'RECEIVED']:
            return error_response("Cannot cancel this rental")
        
        try:
            client = get_daisysms_client(request.user)
            success = client.cancel_rental(rental_id=rental_id, user=request.user)
            
            if success:
                with transaction.atomic():
                    # Update rental status
                    rental.status = 'CANCELLED'
                    rental.save()
                    
                    # Get proper refund amounts for both display and balance update
                    refund_amount_naira = rental.get_naira_price()
                    
                    # Create refund transaction in NGN
                    Transaction.objects.create(
                        user=request.user,
                        amount=refund_amount_naira,
                        transaction_type='REFUND',
                        description=f"Refund for cancelled rental {rental.phone_number}",
                        rental=rental
                    )
                    
                    # Update user balance - handle USD/NGN format properly
                    profile = UserProfile.objects.get(user=request.user)
                    if profile.balance < 100 and profile.balance > 0:
                        # Balance is in USD format - add USD amount
                        refund_amount_usd = refund_amount_naira / UserProfile.USD_TO_NGN_RATE
                        profile.balance += refund_amount_usd
                    else:
                        # Balance is in NGN format - add NGN amount
                        profile.balance += refund_amount_naira
                    profile.save()
                
                return json_response({
                    'success': True,
                    'refund_amount': str(rental.price),  # Keep raw price for compatibility
                    'refund_amount_naira': f"{refund_amount_naira:.2f}"  # Add proper Naira amount
                })
            else:
                return error_response("Failed to cancel rental")
        
        except DaisySMSException as e:
            return error_response(str(e))
    
    except Exception as e:
        logger.error(f"Error cancelling rental: {str(e)}")
        return error_response("Failed to cancel rental", 500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def set_auto_renew(request):
    """Set auto-renew for long-term rental"""
    try:
        data = json.loads(request.body)
        rental_id = data.get('id')
        checked = data.get('checked', False)
        
        if not rental_id:
            return error_response("Rental ID is required")
        
        rental = get_object_or_404(Rental, rental_id=rental_id, user=request.user)
        
        if not rental.is_ltr:
            return error_response("Not a long-term rental")
        
        try:
            client = get_daisysms_client(request.user)
            success = client.set_auto_renew(
                rental_id=rental_id, 
                auto_renew=checked, 
                user=request.user
            )
            
            if success:
                rental.auto_renew = checked
                rental.save()
                
                return json_response({
                    'success': True,
                    'auto_renew': checked
                })
            else:
                return error_response("Failed to update auto-renew")
        
        except DaisySMSException as e:
            return error_response(str(e))
    
    except Exception as e:
        logger.error(f"Error setting auto-renew: {str(e)}")
        return error_response("Failed to set auto-renew", 500)

@login_required
@require_http_methods(["GET"])
def get_rentals(request):
    """Get user's active rentals for dashboard display"""
    try:
        from django.core.paginator import Paginator
        from django.utils import timezone
        from django.db.models import Q
        
        # Get rentals that should be shown in the dashboard:
        # 1. Active waiting rentals (not expired, not cancelled)
        # 2. Rentals that have received SMS (regardless of status)
        expiry_threshold = timezone.now() - timezone.timedelta(minutes=7)
        
        rentals = Rental.objects.filter(
            user=request.user
        ).filter(
            # Include rentals that:
            Q(messages__isnull=False) |  # Have received SMS messages
            Q(
                status__in=['WAITING', 'RECEIVED'],  # Are active
                created_at__gt=expiry_threshold  # And not expired
            )
        ).select_related('service').distinct()
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(rentals, 20)  # Show 20 rentals per page
        page_obj = paginator.get_page(page)
        
        rentals_data = []
        for rental in page_obj:
            latest_message = rental.messages.first()
            rentals_data.append({
                'rental_id': rental.rental_id,
                'service_name': rental.service.name,
                'service_code': rental.service.code,
                'phone_number': rental.phone_number,
                'status': rental.status,
                'price': str(rental.price),
                'price_naira': f"{float(rental.get_naira_price()):,.2f}",
                'is_ltr': rental.is_ltr,
                'auto_renew': rental.auto_renew,
                'supports_multiple': rental.service.supports_multiple_sms,
                'code': latest_message.code if latest_message else None,
                'full_text': latest_message.full_text if latest_message else None,
                'created_at': rental.created_at.isoformat(),
                'paid_until': rental.paid_until.isoformat() if rental.paid_until else None
            })
        
        return json_response({
            'success': True,
            'rentals': rentals_data,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count
        })
    
    except Exception as e:
        logger.error(f"Error getting rentals: {str(e)}")
        return error_response("Failed to get rentals", 500)

@login_required
@require_http_methods(["GET"])
def get_transactions(request):
    """Get user's transaction history"""
    try:
        from django.core.paginator import Paginator
        
        transactions = Transaction.objects.filter(user=request.user).select_related('rental__service')
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(transactions, 50)
        page_obj = paginator.get_page(page)
        
        transactions_data = []
        for trans in page_obj:
            transaction_data = {
                'id': str(trans.transaction_id),
                'amount': str(trans.amount),
                'transaction_type': trans.transaction_type,
                'description': trans.description,
                'created_at': trans.created_at.isoformat(),
            }
            
            if trans.rental:
                transaction_data['rental'] = {
                    'phone_number': trans.rental.phone_number,
                    'service_name': trans.rental.service.name
                }
            
            transactions_data.append(transaction_data)
        
        return json_response({
            'transactions': transactions_data,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count
        })
    
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        return error_response("Failed to get transactions", 500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def sync_services(request):
    """Sync services from DaisySMS API"""
    try:
        from app.daisysms import DaisySMSClient
        from django.conf import settings
        
        # Get API key from settings
        api_key = getattr(settings, 'DAISYSMS_API_KEY', None)
        if not api_key:
            return error_response("No DaisySMS API key configured in settings")
        
        # Create client and test connection
        client = DaisySMSClient(api_key)
        
        # Test balance first
        try:
            balance = client.get_balance()
            logger.info(f"DaisySMS balance: ${balance}")
        except Exception as e:
            return error_response(f"Failed to connect to DaisySMS API: {str(e)}")
        
        # Clear existing services
        Service.objects.all().delete()
        logger.info("Cleared existing services")
        
        # Sync new services
        updated_count = client.sync_services()
        total_services = Service.objects.count()
        
        logger.info(f"Synced {updated_count} services from DaisySMS")
        return json_response({
            'success': True,
            'count': updated_count,
            'total': total_services,
            'balance': balance
        })
        
    except Exception as e:
        logger.error(f"Error syncing services: {str(e)}")
        return error_response(f"Failed to sync services: {str(e)}")

@login_required
@require_http_methods(["GET"])
def get_rental_history(request):
    """Get user's rental history with SMS codes and details"""
    try:
        from django.core.paginator import Paginator
        from datetime import datetime, timedelta
        
        # Get rentals from the last 365 days
        one_year_ago = timezone.now() - timedelta(days=365)
        rentals = Rental.objects.filter(
            user=request.user,
            created_at__gte=one_year_ago
        ).select_related('service').prefetch_related('messages').order_by('-created_at')
        
        # Apply filters if provided
        service_filter = request.GET.get('service')
        status_filter = request.GET.get('status')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        if service_filter:
            rentals = rentals.filter(service__name__icontains=service_filter)
        
        if status_filter:
            rentals = rentals.filter(status=status_filter)
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                rentals = rentals.filter(created_at__date__gte=from_date)
            except ValueError:
                pass
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                rentals = rentals.filter(created_at__date__lte=to_date)
            except ValueError:
                pass
        
        # Pagination
        page = request.GET.get('page', 1)
        limit = int(request.GET.get('limit', 20))
        paginator = Paginator(rentals, limit)
        page_obj = paginator.get_page(page)
        
        rentals_data = []
        for rental in page_obj:
            # Get the first SMS message (code)
            latest_message = rental.messages.first()
            
            rentals_data.append({
                'rental_id': rental.rental_id,
                'service_name': rental.service.name,
                'service_code': rental.service.code,
                'phone_number': rental.phone_number,
                'status': rental.status,
                'price': str(rental.price),
                'price_naira': f"{float(rental.price * UserProfile.USD_TO_NGN_RATE):,.2f}",
                'code': latest_message.code if latest_message else None,
                'full_text': latest_message.full_text if latest_message else None,
                'created_at': rental.created_at.isoformat(),
                'is_ltr': rental.is_ltr,
                'auto_renew': rental.auto_renew,
            })
        
        # Calculate statistics
        all_user_rentals = Rental.objects.filter(
            user=request.user,
            created_at__gte=one_year_ago
        )
        
        total_rentals = all_user_rentals.count()
        successful_rentals = all_user_rentals.filter(status='RECEIVED').count()
        cancelled_rentals = all_user_rentals.filter(status='CANCELLED').count()
        expired_rentals = all_user_rentals.filter(status='EXPIRED').count()
        total_spent = all_user_rentals.aggregate(
            total=models.Sum('price')
        )['total'] or 0
        
        return json_response({
            'success': True,
            'rentals': rentals_data,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'statistics': {
                'total_rentals': total_rentals,
                'successful_rentals': successful_rentals,
                'cancelled_rentals': cancelled_rentals,
                'expired_rentals': expired_rentals,
                'total_spent_usd': str(total_spent),
                'total_spent_naira': f"{float(total_spent * UserProfile.USD_TO_NGN_RATE):,.2f}",
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting rental history: {str(e)}")
        return error_response("Failed to get rental history", 500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def expire_rental(request):
    """Expire a rental and issue refund for rentals that didn't receive SMS"""
    try:
        data = json.loads(request.body)
        rental_id = data.get('id')
        
        if not rental_id:
            return error_response("Rental ID is required")
        
        rental = get_object_or_404(Rental, rental_id=rental_id, user=request.user)
        
        # Check if rental is in a state that can be expired
        if rental.status in ['CANCELLED', 'DONE', 'RECEIVED']:
            return error_response("Cannot expire this rental")
        
        # Check if rental has received any SMS messages
        has_received_sms = rental.messages.exists()
        
        # Check if rental is actually expired (more than 7 minutes old)
        from django.utils import timezone
        expiry_time = rental.created_at + timezone.timedelta(minutes=7)
        if timezone.now() < expiry_time:
            return error_response("Rental has not expired yet")
        
        try:
            with transaction.atomic():
                # Update rental status
                rental.status = 'EXPIRED'
                rental.save()
                
                refund_amount = Decimal('0.00')
                
                # Only issue refund if no SMS was received
                if not has_received_sms:
                    # Get proper refund amounts
                    refund_amount_naira = rental.get_naira_price()
                    
                    # Create refund transaction in NGN
                    Transaction.objects.create(
                        user=request.user,
                        amount=refund_amount_naira,
                        transaction_type='REFUND',
                        description=f"Refund for expired rental {rental.phone_number} (no SMS received)",
                        rental=rental
                    )
                    
                    # Update user balance - handle USD/NGN format properly
                    profile = UserProfile.objects.get(user=request.user)
                    if profile.balance < 100 and profile.balance > 0:
                        # Balance is in USD format - add USD amount
                        refund_amount_usd = refund_amount_naira / UserProfile.USD_TO_NGN_RATE
                        profile.balance += refund_amount_usd
                        refund_amount = refund_amount_usd  # For response compatibility
                    else:
                        # Balance is in NGN format - add NGN amount
                        profile.balance += refund_amount_naira
                        refund_amount = refund_amount_naira
                    profile.save()
                else:
                    refund_amount = Decimal('0.00')
                
                return json_response({
                    'success': True,
                    'refund_amount': str(refund_amount),
                    'had_sms': has_received_sms
                })
        
        except Exception as e:
            logger.error(f"Error expiring rental {rental_id}: {str(e)}")
            return error_response("Failed to process rental expiration")
    
    except Exception as e:
        logger.error(f"Error expiring rental: {str(e)}")
        return error_response("Failed to expire rental", 500)

@login_required
@require_http_methods(["GET"])
def get_realtime_prices(request):
    """Get real-time prices from DaisySMS API"""
    try:
        client = get_daisysms_client(request.user)
        
        # Get real-time prices from DaisySMS
        prices_data = client.get_prices_verification(user=request.user)
        
        realtime_prices = {}
        for service_code, countries in prices_data.items():
            if '187' in countries:  # USA country code
                service_data = countries['187']
                realtime_prices[service_code] = {
                    'cost': str(service_data.get('cost', 0)),
                    'ltr': str(service_data.get('ltr', 0)),
                    'count': int(service_data.get('count', 0)),
                    'name': service_data.get('name', service_code)
                }
        
        return json_response({
            'success': True,
            'realtime_prices': realtime_prices,
            'timestamp': timezone.now().isoformat()
        })
        
    except DaisySMSException as e:
        return error_response(str(e))
    except Exception as e:
        logger.error(f"Error getting realtime prices: {str(e)}")
        return error_response("Failed to get realtime prices", 500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_service_not_listed(request):
    """Create the Service Not Listed service"""
    try:
        # Check if user is admin
        if not request.user.is_staff:
            return error_response("Admin access required", 403)
        
        from decimal import Decimal
        
        # Check if service already exists
        try:
            service = Service.objects.get(code='service_not_listed')
            return json_response({
                'success': True,
                'message': 'Service Not Listed already exists',
                'service': {
                    'id': service.id,
                    'name': service.name,
                    'code': service.code,
                    'price': str(service.price),
                    'price_naira': f"{service.get_naira_price():,.2f}",
                    'is_active': service.is_active
                }
            })
        except Service.DoesNotExist:
            pass
        
        # Create the service
        service = Service.objects.create(
            name='Service Not Listed',
            code='service_not_listed',
            price=Decimal('2.50'),
            daily_price=Decimal('0.00'),
            profit_margin=Decimal('30.00'),
            available_numbers=999,
            supports_multiple_sms=True,
            is_active=True,
        )
        
        return json_response({
            'success': True,
            'message': 'Service Not Listed created successfully',
            'service': {
                'id': service.id,
                'name': service.name,
                'code': service.code,
                'price': str(service.price),
                'price_naira': f"{service.get_naira_price():,.2f}",
                'is_active': service.is_active
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating service not listed: {str(e)}")
        return error_response("Failed to create service", 500)

@login_required
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def initiate_korapay_payment(request):
    """Initiate a Kora Pay payment for wallet funding"""
    try:
        data = json.loads(request.body)
        amount = data.get('amount')
        
        if not amount:
            return error_response("Amount is required")
        
        try:
            amount = Decimal(str(amount))
            if amount < 100:
                return error_response("Minimum amount is ₦100")
            if amount > 1000000:
                return error_response("Maximum amount is ₦1,000,000")
        except (ValueError, TypeError):
            return error_response("Invalid amount format")
        
        # Validate user email
        if not request.user.email:
            return error_response("User email is required for payment")
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Initialize Kora Pay client
        korapay_client = KoraPayClient()
        
        # Create payment transaction record
        from django.utils import timezone
        import uuid
        from datetime import datetime
        
        # Generate truly unique reference with timestamp
        tx_ref = f"YPG_{request.user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        # Initiate payment
        # Use separate URLs: redirect for user, webhook for automatic processing
        from django.conf import settings
        
        # Redirect URL - just redirects user to wallet (no processing)
        redirect_url = f"{request.scheme}://{request.get_host()}/api/korapay/unified/"
        
        # Webhook URL - processes the payment automatically 
        webhook_url = f"{request.scheme}://{request.get_host()}/api/korapay/unified/"
        
        logger.info(f"Redirect URL: {redirect_url}")
        logger.info(f"Webhook URL: {webhook_url}")
        
        payment_result = korapay_client.initiate_payment(
            user=request.user,
            amount=amount,
            currency='NGN',
            redirect_url=redirect_url,  # User redirect (GET)
            notification_url=webhook_url,  # Webhook processing (POST)
            narration=f"Wallet funding for {request.user.username}"
        )
        
        if payment_result['success']:
            # Create pending transaction record - store amount in NGN to avoid conversion loss
            Transaction.objects.create(
                user=request.user,
                amount=amount,  # Store in NGN to preserve exact amount paid
                transaction_type='DEPOSIT',
                description=f"Wallet funding via Kora Pay - ₦{amount:,.2f} (Pending: {payment_result['tx_ref']})"
            )
            
            return json_response({
                'success': True,
                'payment_link': payment_result['payment_link'],
                'tx_ref': payment_result['tx_ref'],
                'amount': str(amount)
            })
        else:
            return error_response(payment_result['error'])
    
    except Exception as e:
        logger.error(f"Error initiating Kora Pay payment: {str(e)}")
        return error_response("Failed to initiate payment", 500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def korapay_callback(request):
    """Handle Kora Pay payment callback - DISABLED, use unified endpoint"""
    logger.warning("korapay_callback called but DISABLED - redirecting to unified handler")
    
    # Extract reference and redirect to unified handler
    if request.method == 'GET':
        tx_ref = request.GET.get('reference')
        if tx_ref:
            return redirect(f'/api/korapay/unified/?reference={tx_ref}&status=success')
        else:
            return redirect('/wallet/?error=callback_error')
    else:
        return JsonResponse({
            'error': 'This endpoint is disabled. Use /api/korapay/unified/ instead'
        }, status=410)

@csrf_exempt
@require_http_methods(["POST"])
def korapay_webhook(request):
    """Handle Kora Pay webhook notifications - DISABLED, use unified endpoint"""
    logger.warning("korapay_webhook called but DISABLED")
    return JsonResponse({
        'error': 'This endpoint is disabled. Use /api/korapay/unified/ instead'
    }, status=410)

@login_required
@require_http_methods(["GET"])
def get_transactions(request):
    """Get user's transaction history with pagination"""
    try:
        page = int(request.GET.get('page', 1))
        per_page = 10
        
        # Get user's transactions
        transactions = Transaction.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        # Calculate pagination
        total_count = transactions.count()
        total_pages = (total_count + per_page - 1) // per_page
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_transactions = transactions[start_idx:end_idx]
        
        # Serialize transactions
        transactions_data = []
        for tx in page_transactions:
            tx_data = {
                'id': tx.id,
                'transaction_type': tx.transaction_type,
                'amount': str(tx.amount),
                'description': tx.description,
                'created_at': tx.created_at.isoformat(),
                'rental': None
            }
            
            # Add rental info if this is a rental transaction
            if tx.rental:
                tx_data['rental'] = {
                    'id': tx.rental.id,
                    'phone_number': tx.rental.phone_number,
                    'service_name': tx.rental.service.name if tx.rental.service else 'Unknown Service',
                    'status': tx.rental.status
                }
            
            transactions_data.append(tx_data)
        
        return json_response({
            'success': True,
            'transactions': transactions_data,
            'current_page': page,
            'total_pages': total_pages,
            'total_count': total_count,
            'has_next': page < total_pages,
            'has_prev': page > 1
        })
    
    except ValueError:
        return error_response("Invalid page number", 400)
    except Exception as e:
        logger.error(f"Error getting transactions for {request.user.username}: {str(e)}")
        return error_response("Failed to get transactions", 500)
