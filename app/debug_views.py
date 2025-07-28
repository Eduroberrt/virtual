from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def debug_callback(request):
    """Debug callback to see what KoraPay is sending"""
    try:
        logger.info("=== DEBUG CALLBACK RECEIVED ===")
        logger.info(f"Method: {request.method}")
        logger.info(f"Headers: {dict(request.META)}")
        logger.info(f"Full URL: {request.build_absolute_uri()}")
        
        if request.method == 'GET':
            logger.info(f"GET Parameters: {dict(request.GET)}")
            data = dict(request.GET)
        else:
            body = request.body.decode('utf-8')
            logger.info(f"POST Body: {body}")
            try:
                data = json.loads(body)
            except:
                data = {"raw_body": body}
        
        logger.info(f"Processed Data: {data}")
        logger.info("=== END DEBUG CALLBACK ===")
        
        # Always return success for debugging
        return JsonResponse({
            "status": "received",
            "method": request.method,
            "data": data
        })
        
    except Exception as e:
        logger.error(f"Debug callback error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
