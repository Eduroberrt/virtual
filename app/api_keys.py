"""
API Key Management System
Handles API key generation, validation, and authentication for reseller API
"""
import secrets
import hashlib
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import APIKey
import logging

logger = logging.getLogger(__name__)


def generate_api_key():
    """
    Generate a secure API key
    Format: 32 random characters
    """
    return secrets.token_urlsafe(24)


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for secure storage
    Uses SHA-256 for one-way hashing
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_user_from_api_key(api_key: str):
    """
    Validate API key and return associated user
    Returns: (user, api_key_obj) or (None, None)
    """
    if not api_key:
        return None, None
    
    try:
        # Hash the provided key
        key_hash = hash_api_key(api_key)
        
        # Find matching API key
        api_key_obj = APIKey.objects.select_related('user').get(
            key_hash=key_hash,
            is_active=True
        )
        
        # Check if user is active
        if not api_key_obj.user.is_active:
            return None, None
        
        # Update last used timestamp
        api_key_obj.record_usage()
        
        return api_key_obj.user, api_key_obj
        
    except APIKey.DoesNotExist:
        return None, None
    except Exception as e:
        logger.error(f"Error validating API key: {str(e)}")
        return None, None


def require_api_key(f):
    """
    Decorator to require API key authentication
    Usage: @require_api_key
    """
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        # Get API key from header or query parameter
        api_key = request.META.get('HTTP_X_API_KEY') or request.GET.get('api_key')
        
        if not api_key:
            return JsonResponse({
                'success': False,
                'error': 'API key is required. Include it in X-API-Key header or api_key parameter.'
            }, status=401)
        
        # Validate API key
        user, api_key_obj = get_user_from_api_key(api_key)
        
        if not user:
            return JsonResponse({
                'success': False,
                'error': 'Invalid or inactive API key.'
            }, status=401)
        
        # Check rate limit
        if api_key_obj.is_rate_limited():
            return JsonResponse({
                'success': False,
                'error': 'Rate limit exceeded. Please try again later.',
                'rate_limit': {
                    'max_requests_per_minute': api_key_obj.rate_limit_per_minute,
                    'retry_after': 60  # seconds
                }
            }, status=429)
        
        # Attach user and api_key to request
        request.api_user = user
        request.api_key_obj = api_key_obj
        
        return f(request, *args, **kwargs)
    
    return decorated_function


def check_api_permission(permission: str):
    """
    Decorator to check specific API permissions
    Usage: @check_api_permission('purchase')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(request, *args, **kwargs):
            if not hasattr(request, 'api_key_obj'):
                return JsonResponse({
                    'success': False,
                    'error': 'API authentication required.'
                }, status=401)
            
            api_key_obj = request.api_key_obj
            
            # Check if permission is enabled
            if permission == 'purchase' and not api_key_obj.can_purchase:
                return JsonResponse({
                    'success': False,
                    'error': 'This API key does not have purchase permission.'
                }, status=403)
            elif permission == 'balance' and not api_key_obj.can_check_balance:
                return JsonResponse({
                    'success': False,
                    'error': 'This API key does not have balance check permission.'
                }, status=403)
            elif permission == 'prices' and not api_key_obj.can_get_prices:
                return JsonResponse({
                    'success': False,
                    'error': 'This API key does not have price query permission.'
                }, status=403)
            
            return f(request, *args, **kwargs)
        
        return decorated_function
    return decorator
