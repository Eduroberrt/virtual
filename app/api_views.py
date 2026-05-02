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
from .mtelsms import get_mtelsms_client, MTelSMSException
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

        return json_response({
            'success': True,
            'balance': str(profile.balance),
            'balance_naira': f"{profile.get_naira_balance():,.2f}",
        })
    except Exception as e:
        logger.error(f"Error getting balance for {request.user.username}: {str(e)}")
        return error_response("Failed to get balance", 500)

@login_required
@require_http_methods(["GET"])
def get_services(request):
    """Get available services with pricing"""
    try:
        services = Service.objects.filter(is_active=True)
        
        services_data = []
        for service in services:
            services_data.append({
                'id': service.id,
                'code': service.code,
                'name': service.name,
                'icon_url': service.icon_url,
                'price': str(service.price),
                'price_naira': f"{service.get_naira_price():,.2f}",
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
        
        if not service_code:
            return error_response("Service code is required")
        
        service = get_object_or_404(Service, code=service_code, is_active=True)
        
        # Get service price (USD converted to NGN + profit margin)
        service_price_naira = service.get_naira_price()
        service_price_usd = service.get_usd_price()
        
        try:
            # Get user profile (SQLite doesn't support row-level locking well)
            with transaction.atomic():
                # Get or create user profile
                profile, created = UserProfile.objects.get_or_create(user=request.user)
                
                # Check balance
                user_balance_naira = profile.get_naira_balance()
                if user_balance_naira < service_price_naira:
                    return error_response("Insufficient balance")
                
                # Call MTelSMS API while holding the lock
                client = get_mtelsms_client()
                try:
                    # Get service_id from service model
                    service_id = service.mtelsms_service_id
                    
                    # Validate that we have a valid numeric service_id
                    if not service_id or service_id.strip() == '':
                        logger.error(f"Service {service.name} ({service.code}) has no MTelSMS service_id")
                        return error_response(f"Service '{service.name}' is not available. Please contact support.")
                    
                    rental_id, phone_number, actual_price, time_remaining = client.get_number(
                        service_id=service_id,
                        max_price=service_price_usd,
                        wholesale=False
                    )
                    logger.info(f"MTelSMS API success: rental_id={rental_id}, phone={phone_number}")
                except MTelSMSException as e:
                    logger.error(f"MTelSMS API failed: {str(e)}")
                    return error_response(str(e))
                except Exception as api_error:
                    logger.error(f"Unexpected MTelSMS error: {str(api_error)}")
                    return error_response(f"API communication error: {str(api_error)}")
                
                # MTelSMS call succeeded, now handle database operations
                try:
                    rental = Rental.objects.create(
                        user=request.user,
                        rental_id=rental_id,
                        service=service,
                        phone_number=phone_number,
                        price=service_price_naira,
                        area_codes=None,
                        carriers=None,
                        max_price=None
                    )
                    logger.info(f"Rental record created: {rental.id}, price=₦{service_price_naira}")
                    
                    # Create transaction record
                    Transaction.objects.create(
                        user=request.user,
                        amount=-service_price_naira,
                        transaction_type='RENTAL',
                        description=f"Rented {service.name} number {phone_number}",
                        rental=rental
                    )
                    logger.info(f"Transaction record created for rental {rental_id}")
                    
                    # Update user balance
                    old_balance = profile.balance
                    profile.balance -= service_price_naira
                    profile.save()
                    logger.info(f"Balance updated: {old_balance} -> {profile.balance} (deducted {service_price_naira})")
                    
                    logger.info(f"Rental process completed successfully: {rental_id}")
                    
                except Exception as db_error:
                    logger.error(f"DATABASE ERROR after MTelSMS success! rental_id={rental_id}, phone={phone_number}, error={str(db_error)}")
                    raise db_error
            
            # Transaction completed successfully
            return json_response({
                'success': True,
                'rental_id': rental_id,
                'phone_number': phone_number,
                'price': str(service_price_naira),
                'price_naira': str(service_price_naira),
                'profit_margin': str(service.profit_margin),
                # Include full rental data for immediate display
                'rental': {
                    'rental_id': rental_id,
                    'service_name': service.name,
                    'service_code': service.code,
                    'phone_number': phone_number,
                    'status': 'WAITING',
                    'price': str(service_price_naira),
                    'price_naira': f"{float(service_price_naira):,.2f}",
                    'code': None,
                    'full_text': None,
                    'created_at': rental.created_at.isoformat()
                }
            })
            
        except Exception as e:
            # Check if we have rental_id (meaning MTelSMS succeeded but DB failed)
            if 'rental_id' in locals():
                logger.error(f"Database transaction failed after MTelSMS success! Attempting to cancel rental_id={rental_id}")
                try:
                    client = get_mtelsms_client()
                    cancel_success = client.cancel_rental(rental_id=rental_id)
                    if cancel_success:
                        logger.info(f"Successfully cancelled rental_id={rental_id} on MTelSMS after database failure")
                    else:
                        logger.error(f"Failed to cancel rental_id={rental_id} on MTelSMS - MANUAL INTERVENTION REQUIRED!")
                except Exception as cancel_error:
                    logger.error(f"Error cancelling rental_id={rental_id}: {str(cancel_error)} - MANUAL INTERVENTION REQUIRED!")
            
            logger.error(f"Final error in rent_number: {str(e)}")
            return error_response(f"Rental failed: {str(e)}", 500)
    
    except Exception as e:
        logger.error(f"Error renting number: {str(e)}")
        return error_response("Failed to rent number", 500)

@login_required
@require_http_methods(["GET"])
def check_sms(request, rental_id):
    """Check for SMS messages on a rental"""
    try:
        rental = get_object_or_404(Rental, rental_id=rental_id, user=request.user)
        
        # For already completed/cancelled rentals, return stored messages
        if rental.status in ['CANCELLED', 'DONE', 'EXPIRED']:
            messages = []
            for msg in rental.messages.all():
                messages.append({
                    'code': msg.code,
                    'full_text': msg.full_text,
                    'received_at': msg.received_at.isoformat()
                })
            return json_response({
                'status': rental.status,
                'messages': messages,
                'refunded': rental.refunded
            })
        
        # AUTO-CANCEL AFTER 5 MINUTES IF NO SMS RECEIVED
        # Check if rental has been waiting for 5+ minutes
        from datetime import timedelta
        if rental.status == 'WAITING':
            time_since_creation = timezone.now() - rental.created_at
            if time_since_creation >= timedelta(minutes=5):
                logger.info(f"Rental {rental_id} has been waiting for {time_since_creation.total_seconds()/60:.1f} minutes - attempting auto-cancel")
                
                # Before auto-cancelling, check MTelSMS one more time to ensure SMS wasn't just received
                try:
                    client = get_mtelsms_client()
                    status, code, phone_number, time_remaining = client.get_code(rental_id=rental_id)
                    
                    # If SMS was received, save it and return success (no cancel)
                    if status == 'RECEIVED' and code:
                        rental.status = 'RECEIVED'
                        rental.save()
                        
                        message, created = SMSMessage.objects.get_or_create(
                            rental=rental,
                            code=code,
                            defaults={'full_text': code}
                        )
                        
                        logger.info(f"SMS received for rental {rental_id} just before auto-cancel - saved code")
                        
                        return json_response({
                            'status': 'RECEIVED',
                            'messages': [{
                                'code': code,
                                'full_text': code,
                                'received_at': message.created_at.isoformat()
                            }],
                            'time_remaining': time_remaining
                        })
                    
                    # SMS still not received after 5 minutes - proceed with auto-cancel
                    elif status == 'WAITING':
                        logger.info(f"Auto-cancelling rental {rental_id} after 5 minutes with no SMS")
                        
                        # Attempt to cancel with MTelSMS
                        cancel_success = client.cancel_rental(rental_id=rental_id)
                        
                        if cancel_success:
                            with transaction.atomic():
                                # Reload rental with lock
                                rental = Rental.objects.select_for_update().get(rental_id=rental_id, user=request.user)
                                
                                # Check if already refunded (race condition protection)
                                if rental.refunded:
                                    return json_response({
                                        'status': 'CANCELLED',
                                        'messages': [],
                                        'refunded': True
                                    })
                                
                                # Update rental status
                                rental.status = 'CANCELLED'
                                rental.refunded = True
                                rental.save()
                                
                                # Issue refund
                                refund_amount_naira = rental.get_naira_price()
                                
                                profile = UserProfile.objects.select_for_update().get(user=request.user)
                                profile.balance += refund_amount_naira
                                profile.save()
                                
                                # Create refund transaction
                                Transaction.objects.create(
                                    user=request.user,
                                    amount=refund_amount_naira,
                                    transaction_type='REFUND',
                                    description=f'Auto-refund: No SMS after 5 minutes - {rental.phone_number}',
                                    rental=rental
                                )
                                
                                logger.info(f"Auto-cancelled rental {rental_id} and refunded ₦{refund_amount_naira}")
                            
                            return json_response({
                                'status': 'CANCELLED',
                                'messages': [],
                                'refunded': True
                            })
                        else:
                            logger.warning(f"Failed to cancel rental {rental_id} with MTelSMS after 5 minutes")
                            # Continue with normal flow if cancel failed
                    
                except MTelSMSException as e:
                    logger.error(f"MTelSMS error during auto-cancel check for {rental_id}: {str(e)}")
                    # Continue with normal flow if API call failed
        
        try:
            client = get_mtelsms_client()
            # MTelSMS uses get_code() instead of get_status() for retrieving SMS
            status, code, phone_number, time_remaining = client.get_code(
                rental_id=rental_id
            )
            
            # Check if rental has expired (time_remaining = 0 or negative)
            if time_remaining <= 0 and status == 'WAITING':
                logger.info(f"Rental {rental_id} has expired (time_remaining={time_remaining})")
                
                with transaction.atomic():
                    # Reload rental with lock to prevent race conditions
                    rental = Rental.objects.select_for_update().get(rental_id=rental_id, user=request.user)
                    
                    # Check if already refunded (double-refund protection)
                    if rental.refunded:
                        logger.info(f"Rental {rental_id} already refunded, skipping")
                        return json_response({
                            'status': 'EXPIRED',
                            'messages': [],
                            'refunded': True
                        })
                    
                    # Mark as expired
                    rental.status = 'EXPIRED'
                    rental.refunded = True
                    rental.save()
                    
                    # Issue refund
                    profile = UserProfile.objects.select_for_update().get(user=rental.user)
                    profile.balance += rental.price
                    profile.save()
                    
                    # Log refund transaction
                    Transaction.objects.create(
                        user=rental.user,
                        amount=rental.price,
                        transaction_type='REFUND',
                        description=f'Automatic refund for expired rental {rental.phone_number}'
                    )
                    
                    logger.info(f"Automatic refund issued for expired rental {rental_id}, user received ₦{rental.price}")
                
                return json_response({
                    'status': 'EXPIRED',
                    'messages': [],
                    'refunded': True
                })
            
            # Update rental status
            rental.status = status
            rental.save()
            
            # Save message if received
            if status == 'RECEIVED' and code:
                message, created = SMSMessage.objects.get_or_create(
                    rental=rental,
                    code=code,
                    defaults={'full_text': code}  # MTelSMS returns code only, not full text
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
                'messages': messages,
                'time_remaining': time_remaining
            })
        
        except MTelSMSException as e:
            error_msg = str(e).lower()
            
            # Log the full error for debugging
            logger.warning(f"MTelSMS error for rental {rental_id}: {error_msg}")
            
            # Check if rental is expired/invalid on MTelSMS side
            # MTelSMS might return various error messages for expired rentals
            expired_keywords = [
                'invalid service id',
                'record expired',
                'expired',
                'not found',
                'invalid id',
                'invalid request',
                'no such',
                'does not exist'
            ]
            
            is_expired = any(keyword in error_msg for keyword in expired_keywords)
            
            if is_expired:
                logger.info(f"Detected expired rental {rental_id} from error: {error_msg}")
                
                with transaction.atomic():
                    # Reload rental with lock to prevent race conditions
                    rental = Rental.objects.select_for_update().get(rental_id=rental_id, user=request.user)
                    
                    # Check if already refunded (double-refund protection)
                    if rental.refunded:
                        logger.info(f"Rental {rental_id} already refunded, skipping")
                        return json_response({
                            'status': 'EXPIRED',
                            'messages': [],
                            'refunded': True
                        })
                    
                    # Mark as expired
                    rental.status = 'EXPIRED'
                    rental.refunded = True
                    rental.save()
                    
                    # Issue refund
                    profile = UserProfile.objects.select_for_update().get(user=rental.user)
                    profile.balance += rental.price
                    profile.save()
                    
                    Transaction.objects.create(
                        user=rental.user,
                        amount=rental.price,
                        transaction_type='REFUND',
                        description=f'Automatic refund: Rental expired on provider - {rental.phone_number}'
                    )
                    
                    logger.info(f"Rental {rental_id} expired on MTelSMS, user refunded ₦{rental.price}")
                
                return json_response({
                    'status': 'EXPIRED',
                    'messages': [],
                    'refunded': True
                })
            
            # For other errors, return the original error message
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
            client = get_mtelsms_client()
            success = client.cancel_rental(rental_id=rental_id)
            
            if success:
                with transaction.atomic():
                    # Check if already refunded
                    rental = Rental.objects.select_for_update().get(rental_id=rental_id, user=request.user)
                    if rental.refunded:
                        return error_response("Rental already refunded")
                    
                    # Update rental status
                    rental.status = 'CANCELLED'
                    rental.refunded = True
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
                    
                    # Update user balance (all balances are in NGN)
                    profile = UserProfile.objects.select_for_update().get(user=request.user)
                    profile.balance += refund_amount_naira
                    profile.save()
                
                return json_response({
                    'success': True,
                    'refund_amount': str(rental.price),  # Keep raw price for compatibility
                    'refund_amount_naira': f"{refund_amount_naira:.2f}"  # Add proper Naira amount
                })
            else:
                return error_response("Failed to cancel rental")
        
        except MTelSMSException as e:
            return error_response(str(e))
    
    except Exception as e:
        logger.error(f"Error cancelling rental: {str(e)}")
        return error_response("Failed to cancel rental", 500)

@login_required
@require_http_methods(["GET"])
def get_rentals(request):
    """Get user's active rentals for dashboard display"""
    try:
        from django.core.paginator import Paginator
        from django.utils import timezone
        from django.db.models import Q
        
        # Get rentals that should be shown in the dashboard:
        # 1. All WAITING rentals (actively waiting for SMS)
        # 2. All RECEIVED rentals (got the SMS code)
        # 3. Recent EXPIRED/CANCELLED rentals (within last hour for user awareness)
        recent_threshold = timezone.now() - timezone.timedelta(hours=1)
        
        rentals = Rental.objects.filter(
            user=request.user
        ).filter(
            Q(status__in=['WAITING', 'RECEIVED']) |  # Active rentals
            Q(
                status__in=['EXPIRED', 'CANCELLED'],  # Recent expired/cancelled
                created_at__gt=recent_threshold
            )
        ).select_related('service').prefetch_related('messages').order_by('-created_at')
        
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
                'supports_multiple': rental.service.supports_multiple_sms,
                'code': latest_message.code if latest_message else None,
                'full_text': latest_message.full_text if latest_message else None,
                'created_at': rental.created_at.isoformat()
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
    """Sync services from MTelSMS API"""
    try:
        from app.mtelsms import get_mtelsms_client
        from django.conf import settings
        
        # Get MTelSMS client
        client = get_mtelsms_client()
        
        # Test balance first
        try:
            balance = client.get_balance()
            logger.info(f"MTelSMS balance: ${balance}")
        except Exception as e:
            return error_response(f"Failed to connect to MTelSMS API: {str(e)}")
        
        # Sync services from MTelSMS
        updated_count = client.sync_services()
        total_services = Service.objects.count()
        
        logger.info(f"Synced {updated_count} services from MTelSMS")
        return json_response({
            'success': True,
            'count': updated_count,
            'total': total_services,
            'balance': str(balance)
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
                'price_naira': f"{float(rental.get_naira_price()):,.2f}",
                'code': latest_message.code if latest_message else None,
                'full_text': latest_message.full_text if latest_message else None,
                'created_at': rental.created_at.isoformat()
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
                'total_spent_naira': f"{float(total_spent):,.2f}",
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting rental history: {str(e)}")
        return error_response("Failed to get rental history", 500)

@login_required
@require_http_methods(["GET"])
def get_realtime_prices(request):
    """Get real-time prices from MTelSMS API"""
    try:
        client = get_mtelsms_client()
        
        # Get real-time prices from MTelSMS
        prices_data = client.get_prices_verification()
        
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
        
    except MTelSMSException as e:
        return error_response(str(e))
    except Exception as e:
        logger.error(f"Error getting realtime prices: {str(e)}")
        return error_response("Failed to get realtime prices", 500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
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
