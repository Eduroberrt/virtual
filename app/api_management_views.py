"""
User-facing views for managing API keys
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count
from decimal import Decimal

from .api_models import APIKey, APIRequest, APIOrderMapping
from .api_keys import generate_api_key, hash_api_key


@login_required
def api_keys_dashboard(request):
    """
    Combined API key management and documentation page
    """
    # Get or create API key for user
    api_key_obj = APIKey.objects.filter(user=request.user, is_active=True).first()
    
    # Always show the key prefix (first 8 chars) - user can see it
    # For security, we can't retrieve the full key from hash, but show what we have
    display_key = api_key_obj.key_prefix if api_key_obj else None
    
    # Check if we just generated a new key (stored in session)
    session_key = f'api_key_{api_key_obj.id if api_key_obj else "new"}'
    full_api_key = request.session.get(session_key)
    
    # If no active key exists, create one automatically
    if not api_key_obj:
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        key_prefix = api_key[:8]  # Store first 8 chars
        
        api_key_obj = APIKey.objects.create(
            user=request.user,
            name='API Key',
            key_hash=key_hash,
            key_prefix=key_prefix,
            markup_percentage=Decimal('0.00')
        )
        full_api_key = api_key
        # Store in session
        request.session[f'api_key_{api_key_obj.id}'] = api_key
    
    context = {
        'api_key_obj': api_key_obj,
        'full_api_key': full_api_key,
        'show_full_key': full_api_key is not None,
    }
    
    return render(request, 'api_keys/dashboard.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_api_key(request):
    """
    Create/regenerate API key for user
    """
    try:
        # Deactivate all existing keys
        old_keys = APIKey.objects.filter(user=request.user, is_active=True)
        old_key_ids = list(old_keys.values_list('id', flat=True))
        old_keys.update(is_active=False)
        
        # Clear old keys from session
        for key_id in old_key_ids:
            session_key = f'api_key_{key_id}'
            if session_key in request.session:
                del request.session[session_key]
        
        # Generate new API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        key_prefix = api_key[:8]  # Store first 8 chars
        
        # Create new API key record
        api_key_obj = APIKey.objects.create(
            user=request.user,
            name='API Key',
            key_hash=key_hash,
            key_prefix=key_prefix,
            markup_percentage=Decimal('0.00')
        )
        
        # Store full key in session
        request.session[f'api_key_{api_key_obj.id}'] = api_key
        
        return JsonResponse({
            'success': True,
            'api_key': api_key,
            'message': 'New API key generated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
