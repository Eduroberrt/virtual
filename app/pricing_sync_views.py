"""
Real-time pricing views with automatic sync
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import SMSService
from .fivesim import FiveSimAPI
import json

@require_http_methods(["GET"])
def get_service_prices_with_auto_sync(request):
    """
    Get service prices with automatic price checking
    If prices are stale, update them from 5sim API
    """
    try:
        # Check if we need to update prices
        stale_threshold = timezone.now() - timedelta(hours=1)  # 1 hour
        stale_services = SMSService.objects.filter(
            is_active=True,
            last_price_update__lt=stale_threshold
        ).count()
        
        # If more than 10% of services are stale, trigger update
        total_services = SMSService.objects.filter(is_active=True).count()
        if total_services > 0 and (stale_services / total_services) > 0.1:
            # Trigger background price update
            from django.core.management import call_command
            import threading
            
            def update_prices():
                try:
                    call_command('update_fivesim_prices', '--batch-size', '20')
                except Exception:
                    pass
            
            # Run in background thread
            thread = threading.Thread(target=update_prices)
            thread.daemon = True
            thread.start()
        
        # Get current prices
        services = SMSService.objects.filter(is_active=True).select_related('category')
        
        price_data = []
        for service in services:
            price_data.append({
                'service_code': service.service_code,
                'service_name': service.service_name,
                'category': service.category.name,
                'wholesale_price_ngn': service.get_wholesale_price_ngn(),
                'final_price_ngn': service.get_final_price_ngn(),
                'profit_margin_ngn': service.get_profit_amount_ngn(),
                'last_updated': service.last_price_update.isoformat() if service.last_price_update else None
            })
        
        return JsonResponse({
            'status': 'success',
            'data': price_data,
            'meta': {
                'total_services': total_services,
                'stale_services': stale_services,
                'auto_sync_enabled': getattr(settings, 'FIVESIM_AUTO_SYNC_ENABLED', False)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def trigger_price_sync(request):
    """
    Manually trigger price sync (for admin use)
    """
    try:
        data = json.loads(request.body)
        sync_type = data.get('type', 'prices')  # 'prices' or 'full'
        
        from django.core.management import call_command
        import threading
        
        def run_sync():
            try:
                if sync_type == 'full':
                    call_command('sync_fivesim_services', '--force')
                else:
                    call_command('update_fivesim_prices')
            except Exception as e:
                pass
        
        # Run in background
        thread = threading.Thread(target=run_sync)
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'status': 'success',
            'message': f'{sync_type.title()} sync triggered successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def pricing_health_check(request):
    """
    Check the health of pricing data
    """
    try:
        now = timezone.now()
        
        # Check how many services have recent updates
        recent_threshold = now - timedelta(hours=2)
        stale_threshold = now - timedelta(hours=24)
        
        total_services = SMSService.objects.filter(is_active=True).count()
        recent_updates = SMSService.objects.filter(
            is_active=True,
            last_price_update__gte=recent_threshold
        ).count()
        stale_services = SMSService.objects.filter(
            is_active=True,
            last_price_update__lt=stale_threshold
        ).count()
        
        # Calculate health score
        if total_services == 0:
            health_score = 0
        else:
            health_score = ((total_services - stale_services) / total_services) * 100
        
        # Determine status
        if health_score >= 90:
            status = 'healthy'
        elif health_score >= 70:
            status = 'warning'
        else:
            status = 'critical'
        
        return JsonResponse({
            'status': status,
            'health_score': round(health_score, 2),
            'total_services': total_services,
            'recent_updates': recent_updates,
            'stale_services': stale_services,
            'last_check': now.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
