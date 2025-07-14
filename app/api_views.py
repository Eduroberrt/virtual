from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db import models
from decimal import Decimal
import json
import logging

from .models import UserProfile, Service, Rental, SMSMessage, Transaction
from .daisysms import get_daisysms_client, DaisySMSException

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
        
        # Check if user has sufficient balance using admin price (with profit margin)
        service_price_naira = service.get_naira_price()
        service_price_usd = service_price_naira / UserProfile.USD_TO_NGN_RATE
        
        if profile.balance < service_price_usd:
            return error_response("Insufficient balance")
        
        # Convert max_price to Decimal if provided
        if max_price:
            max_price = Decimal(str(max_price))
        
        try:
            client = get_daisysms_client(request.user)
            rental_id, phone_number, actual_price = client.get_number(
                service_code=service_code,
                user=request.user,
                max_price=max_price,
                ltr=is_ltr,
                auto_renew=auto_renew,
                area_codes=area_codes if area_codes else None,
                carriers=carriers if carriers else None,
                specific_number=specific_number
            )
            
            # Create rental record
            with transaction.atomic():
                # Use admin price (with profit margin) instead of API price
                admin_price_naira = service.get_naira_price()
                admin_price_usd = admin_price_naira / UserProfile.USD_TO_NGN_RATE
                
                rental = Rental.objects.create(
                    user=request.user,
                    rental_id=rental_id,
                    service=service,
                    phone_number=phone_number,
                    price=admin_price_usd,  # Store admin price instead of actual API price
                    is_ltr=is_ltr,
                    auto_renew=auto_renew,
                    area_codes=','.join(area_codes) if area_codes else None,
                    carriers=','.join(carriers) if carriers else None,
                    max_price=max_price,
                    paid_until=timezone.now() + timezone.timedelta(days=1) if is_ltr else None
                )
                
                # Create transaction record using admin price
                Transaction.objects.create(
                    user=request.user,
                    amount=-admin_price_usd,  # Deduct admin price from balance
                    transaction_type='RENTAL',
                    description=f"Rented {service.name} number {phone_number}",
                    rental=rental
                )
                
                # Update user balance using admin price
                profile.balance -= admin_price_usd
                profile.save()
            
            return json_response({
                'success': True,
                'rental_id': rental_id,
                'phone_number': phone_number,
                'price': str(admin_price_usd),  # Return admin price
                'is_ltr': is_ltr
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
                    
                    # Create refund transaction
                    Transaction.objects.create(
                        user=request.user,
                        amount=rental.price,
                        transaction_type='REFUND',
                        description=f"Refund for cancelled rental {rental.phone_number}",
                        rental=rental
                    )
                    
                    # Update user balance
                    profile = UserProfile.objects.get(user=request.user)
                    profile.balance += rental.price
                    profile.save()
                
                return json_response({
                    'success': True,
                    'refund_amount': str(rental.price)
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
    """Get user's rentals with pagination"""
    try:
        from django.core.paginator import Paginator
        
        rentals = Rental.objects.filter(user=request.user).select_related('service')
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(rentals, 20)
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
                'price_naira': f"{float(rental.price * UserProfile.USD_TO_NGN_RATE):,.2f}",
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
