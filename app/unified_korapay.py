from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect
from django.db import transaction
from decimal import Decimal
import json
import logging

from .models import UserProfile, Transaction
from .korapay import KoraPayClient

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def unified_korapay_handler(request):
    """
    Unified handler for both KoraPay webhook and callback
    This handles both redirect (GET) and webhook (POST) from KoraPay
    """
    # Write to a debug file so we can see what's happening
    debug_file = open('korapay_debug.txt', 'a')
    debug_file.write(f"\n=== KORAPAY UNIFIED CALLED ===\n")
    debug_file.write(f"Method: {request.method}\n")
    debug_file.write(f"Time: {str(__import__('datetime').datetime.now())}\n")
    
    try:
        logger.info(f"=== KORAPAY UNIFIED HANDLER CALLED ===")
        logger.info(f"Method: {request.method}")
        logger.info(f"Full URL: {request.build_absolute_uri()}")
        logger.info(f"User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
        logger.info(f"Remote IP: {request.META.get('REMOTE_ADDR', 'Unknown')}")
        
        if request.method == 'GET':
            # This is a user redirect - don't process payment, just redirect to success
            tx_ref = request.GET.get('reference')
            logger.info(f"GET redirect for reference: {tx_ref} - redirecting user to wallet")
            debug_file.write(f"GET redirect: {tx_ref} - NO PROCESSING, just redirect\n")
            debug_file.close()
            
            if tx_ref:
                # Redirect to wallet with success message
                return redirect('/wallet/?success=1&message=Payment completed successfully')
            else:
                return redirect('/wallet/?error=callback_error')
        
        # POST method - this is the webhook from KoraPay, process the payment
        logger.info("POST webhook - PROCESSING PAYMENT")
        debug_file.write("POST webhook - PROCESSING PAYMENT\n")
        
        # Extract transaction reference and amount from webhook
        try:
            body_raw = request.body.decode('utf-8')
            logger.info(f"POST body raw: {body_raw}")
            debug_file.write(f"POST body: {body_raw}\n")
            
            if body_raw:
                body_data = json.loads(body_raw)
                # Extract from KoraPay webhook format
                if 'data' in body_data:
                    # KoraPay webhook format
                    data = body_data['data']
                    tx_ref = data.get('reference')
                    status = data.get('status')
                    verification_data = {
                        'status': status,
                        'amount': data.get('amount'),  # Real amount paid by user
                        'fee': data.get('fee')
                    }
                    logger.info(f"Webhook data - Amount: ₦{data.get('amount')}, Fee: ₦{data.get('fee')}")
                else:
                    # Simple format
                    tx_ref = body_data.get('reference')
                    status = body_data.get('status')
                    verification_data = {'status': status}
                
                logger.info(f"POST body parsed: {body_data}")
            else:
                # Empty body, try form data
                tx_ref = request.POST.get('reference')
                status = request.POST.get('status')
                verification_data = {'status': status}
                logger.info(f"POST form data: {dict(request.POST)}")
                debug_file.write(f"POST form: {dict(request.POST)}\n")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            # Try to get from form data
            tx_ref = request.POST.get('reference')
            status = request.POST.get('status')
            verification_data = {'status': status}
            logger.info(f"POST form data fallback: {dict(request.POST)}")
            debug_file.write(f"POST form fallback: {dict(request.POST)}\n")
        
        debug_file.write(f"Reference: {tx_ref}, Status: {status}\n")
        logger.info(f"Extracted - Reference: {tx_ref}, Status: {status}")
        
        if not tx_ref:
            logger.error("❌ No transaction reference found in webhook")
            debug_file.write("ERROR: No reference found\n")
            debug_file.close()
            return JsonResponse({'error': 'No reference found'}, status=400)
        
        logger.info(f"✅ Processing webhook payment: {tx_ref}")
        debug_file.write(f"PROCESSING WEBHOOK: {tx_ref}\n")
        
        # Process the payment via webhook
        success = process_successful_payment(tx_ref, verification_data)
        debug_file.write(f"Result: {'SUCCESS' if success else 'FAILED'}\n")
        
        if success:
            logger.info(f"✅ Webhook payment {tx_ref} processed successfully")
            debug_file.write("FINAL: Webhook payment processed successfully\n")
            debug_file.close()
            return JsonResponse({'status': 'success', 'message': 'Payment processed via webhook'})
        else:
            logger.error(f"❌ Failed to process webhook payment {tx_ref}")
            debug_file.write("FINAL: Webhook processing failed\n")
            debug_file.close()
            return JsonResponse({'status': 'error', 'message': 'Webhook processing failed'})
                
    except Exception as e:
        logger.error(f"💥 EXCEPTION in unified handler: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        debug_file.write(f"EXCEPTION: {str(e)}\n")
        debug_file.close()
        
        if request.method == 'GET':
            return redirect('/wallet/?error=callback_error')
        else:
            return JsonResponse({'error': str(e)}, status=500)

def process_successful_payment(tx_ref, verification_result):
    """Process a successful payment and update user balance"""
    try:
        # Extract user ID from transaction reference
        user_id = None
        if tx_ref.startswith('YPG_'):
            try:
                user_id = int(tx_ref.split('_')[1])
            except (IndexError, ValueError):
                logger.warning(f"Could not extract user ID from tx_ref: {tx_ref}")
        
        # Find the pending transaction
        pending_transaction = Transaction.objects.filter(
            transaction_type='DEPOSIT',
            description__icontains=tx_ref
        ).first()
        
        if not pending_transaction and user_id:
            # Fallback search by user ID
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(id=user_id)
                pending_transaction = Transaction.objects.filter(
                    user=user,
                    transaction_type='DEPOSIT',
                    description__icontains='Pending'
                ).order_by('-id').first()
            except User.DoesNotExist:
                logger.error(f"User with ID {user_id} not found")
        
        if not pending_transaction:
            logger.error(f"No pending transaction found for {tx_ref}")
            return False
        
        # Check if already processed
        if pending_transaction.description.startswith("Wallet funded via Kora Pay - ₦"):
            logger.info(f"Transaction {tx_ref} already processed")
            return True
        
        # Process the payment
        with transaction.atomic():
            profile = UserProfile.objects.get(user=pending_transaction.user)
            
            # Determine the correct amount to credit
            if verification_result.get('amount'):
                # Use the exact amount from KoraPay webhook (what user actually paid)
                amount_ngn = float(verification_result['amount'])
                logger.info(f"Using KoraPay webhook amount: ₦{amount_ngn}")
            else:
                # Fallback to transaction amount (from initiation)
                amount_ngn = float(pending_transaction.amount)
                logger.info(f"Using transaction amount: ₦{amount_ngn}")
            
            # Credit balance - exact amount paid
            amount_decimal = Decimal(str(amount_ngn))
            
            # Credit in NGN (the exact amount user paid)
            profile.balance += amount_decimal
            profile.save()
            
            # Update transaction description to prevent double processing
            pending_transaction.description = f"Wallet funded via Kora Pay - ₦{amount_ngn:,.2f}"
            pending_transaction.save()
            
            logger.info(f"Successfully credited ₦{amount_ngn} to user {pending_transaction.user.id} (Balance: ₦{profile.balance})")
        
        logger.info(f"Successfully credited ₦{amount_ngn} to user {pending_transaction.user.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing payment {tx_ref}: {str(e)}")
        return False
