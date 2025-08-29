"""
User Balance API View
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import UserProfile

@login_required
@require_http_methods(["GET"])
def get_user_balance(request):
    """Get user's current balance"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        balance = user_profile.get_naira_balance()
        
        # Format balance the same way as in template
        balance_formatted = f"₦{balance:,.2f}"
        
        return JsonResponse({
            'success': True,
            'balance': balance_formatted,
            'balance_raw': float(balance)
        })
        
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User profile not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
