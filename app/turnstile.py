import requests
from django.conf import settings

def verify_turnstile(token, ip_address=None):
    """
    Verify Cloudflare Turnstile token
    
    Args:
        token: The Turnstile token from the form
        ip_address: The user's IP address (optional)
    
    Returns:
        dict: Response from Turnstile API with success status
    """
    if not token:
        return {'success': False, 'error': 'No token provided'}
    
    # Prepare the verification request
    data = {
        'secret': settings.TURNSTILE_SECRET_KEY,
        'response': token,
    }
    
    if ip_address:
        data['remoteip'] = ip_address
    
    try:
        # Make request to Turnstile verification endpoint
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            return {
                'success': False, 
                'error': f'HTTP {response.status_code}: {response.text}'
            }
            
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Request failed: {str(e)}'
        }

def get_client_ip(request):
    """
    Get the client's IP address from the request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
