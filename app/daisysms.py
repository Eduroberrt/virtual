import requests
import time
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from .models import APILog, Service, Rental, SMSMessage

logger = logging.getLogger(__name__)

class DaisySMSException(Exception):
    """Custom exception for DaisySMS API errors"""
    pass

class DaisySMSClient:
    """
    DaisySMS API Client for handling all SMS verification service operations
    """
    
    BASE_URL = "https://daisysms.com/stubs/handler_api.php"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WDN-Virtual-SMS/1.0'
        })
    
    def _make_request(self, action: str, params: Dict = None, user=None) -> Tuple[str, Dict]:
        """
        Make API request to DaisySMS with logging and error handling
        """
        if params is None:
            params = {}
        
        params.update({
            'api_key': self.api_key,
            'action': action
        })
        
        start_time = time.time()
        log_entry = None
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            execution_time = time.time() - start_time
            
            # DETAILED DEBUGGING - Log exact request details
            logger.info(f"DaisySMS Request URL: {response.url}")
            logger.info(f"DaisySMS Request params: {params}")
            logger.info(f"DaisySMS Response status: {response.status_code}")
            logger.info(f"DaisySMS Response text: {response.text}")
            
            # Log the API call
            log_entry = APILog.objects.create(
                user=user,
                endpoint=f"{action}",
                method='GET',
                request_data=params,
                response_data={'body': response.text, 'headers': dict(response.headers)},
                status_code=response.status_code,
                execution_time=execution_time
            )
            
            # Parse response first before checking HTTP status
            response_text = response.text.strip()
            headers = dict(response.headers)
            
            # Check for API errors (DaisySMS returns these even with 400 status codes)
            if response_text.startswith('BAD_KEY'):
                raise DaisySMSException("Invalid API key")
            elif response_text.startswith('NO_MONEY'):
                raise DaisySMSException("Insufficient balance")
            elif response_text.startswith('MAX_PRICE_EXCEEDED'):
                raise DaisySMSException("Maximum price exceeded")
            elif response_text.startswith('NO_NUMBERS'):
                # Check if this is due to specific filters
                areas = params.get('areas', '')
                carriers = params.get('carriers', '')
                phone = params.get('number', '')
                
                if phone:
                    raise DaisySMSException(f"The specific phone number ({phone}) is not available. It may be already rented or not exist in our pool.")
                elif areas and carriers:
                    raise DaisySMSException(f"No numbers available for area codes ({areas}) and carriers ({carriers}). Try different combinations or remove filters.")
                elif areas:
                    raise DaisySMSException(f"No numbers available for area codes ({areas}). Try different area codes or remove the filter.")
                elif carriers:
                    raise DaisySMSException(f"No numbers available for carriers ({carriers}). Try different carriers or remove the filter.")
                else:
                    raise DaisySMSException("No numbers available for this service")
            elif response_text.startswith('TOO_MANY_ACTIVE_RENTALS'):
                raise DaisySMSException("Too many active rentals (max 20)")
            elif response_text.startswith('NO_ACTIVATION'):
                raise DaisySMSException("Rental not found")
            elif response_text.startswith('BAD_ID'):
                raise DaisySMSException("Invalid rental ID")
            elif response_text.startswith('BAD_NUMBER'):
                phone = params.get('number', '')
                if phone:
                    raise DaisySMSException(f"Phone number ({phone}) format is not accepted by the service. Try a different number or remove the phone filter.")
                else:
                    raise DaisySMSException("Invalid phone number format")
            elif response_text.startswith('NUMBER_NOT_AVAILABLE'):
                phone = params.get('number', '')
                if phone:
                    raise DaisySMSException(f"Phone number ({phone}) is currently unavailable or already rented.")
                else:
                    raise DaisySMSException("Requested number is not available")
            
            # Only check HTTP status after handling DaisySMS API errors
            response.raise_for_status()
            
            logger.info(f"DaisySMS API call successful: {action} - {response_text[:100]}")
            return response_text, headers
            
        except requests.RequestException as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            # Handle specific HTTP errors that might indicate area code/carrier/phone issues
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 400:
                    # Bad Request - likely due to invalid parameters
                    areas = params.get('areas', '')
                    carriers = params.get('carriers', '')
                    phone = params.get('number', '')
                    
                    if phone:
                        error_msg = f"Invalid phone number format ({phone}). Please enter a 10-digit US phone number (e.g., 5551234567)."
                    elif areas and carriers:
                        error_msg = f"Invalid area codes ({areas}) or carriers ({carriers}). Please check your settings and try again."
                    elif areas:
                        error_msg = f"Invalid area codes ({areas}). Please enter valid US area codes (e.g., 503, 202, 404)."
                    elif carriers:
                        error_msg = f"Invalid carriers ({carriers}). Please use: tmo (T-Mobile), vz (Verizon), or att (AT&T)."
                    else:
                        error_msg = "Invalid request parameters. Please check your settings."
                elif e.response.status_code == 404:
                    error_msg = "Service temporarily unavailable. Please try again later."
                elif e.response.status_code >= 500:
                    error_msg = "SMS service is experiencing issues. Please try again in a few minutes."
            
            if log_entry:
                log_entry.error_message = error_msg
                log_entry.save()
            else:
                APILog.objects.create(
                    user=user,
                    endpoint=f"{action}",
                    method='GET',
                    request_data=params,
                    error_message=error_msg,
                    execution_time=execution_time
                )
            
            logger.error(f"DaisySMS API request failed: {action} - {error_msg}")
            raise DaisySMSException(error_msg)
        
        except DaisySMSException as e:
            if log_entry:
                log_entry.error_message = str(e)
                log_entry.save()
            logger.warning(f"DaisySMS API error: {action} - {str(e)}")
            raise
    
    def get_balance(self, user=None) -> Decimal:
        """
        Get user balance from DaisySMS
        Returns: Decimal balance amount
        """
        response_text, _ = self._make_request('getBalance', user=user)
        
        if response_text.startswith('ACCESS_BALANCE:'):
            balance_str = response_text.split(':')[1]
            return Decimal(balance_str)
        
        raise DaisySMSException(f"Unexpected balance response: {response_text}")
    
    def get_number(self, service_code: str, user=None, max_price: Optional[Decimal] = None, 
                   area_codes: Optional[List[str]] = None,
                   carriers: Optional[List[str]] = None,
                   specific_number: Optional[str] = None) -> Tuple[str, str, Decimal]:
        """
        Rent a phone number for SMS verification
        Returns: (rental_id, phone_number, actual_price)
        """
        # Note: Using WhatsApp ('wa') as fallback for unlisted services since it's widely supported
        # When user requests unlisted service, we use WhatsApp numbers which work for most services
        if service_code == 'service_not_listed':
            service_code = 'wa'  # WhatsApp is reliable and widely supported
            logger.info(f"Converting 'service_not_listed' to 'wa' (WhatsApp) for DaisySMS API")
        
        params = {'service': service_code}
        
        if max_price:
            # Round max_price to 2 decimal places to avoid precision issues with DaisySMS API
            rounded_price = round(float(max_price), 2)
            params['max_price'] = str(rounded_price)
        
        if area_codes:
            params['areas'] = ','.join(area_codes)
        
        if carriers:
            params['carriers'] = ','.join(carriers)
        
        if specific_number:
            params['number'] = specific_number
        
        response_text, headers = self._make_request('getNumber', params, user=user)
        
        if response_text.startswith('ACCESS_NUMBER:'):
            parts = response_text.split(':')
            rental_id = parts[1]
            phone_number = parts[2]
            
            # Get actual price from headers
            actual_price = Decimal('0.00')
            if 'X-Price' in headers:
                actual_price = Decimal(headers['X-Price'])
            
            return rental_id, phone_number, actual_price
        
        raise DaisySMSException(f"Unexpected rent response: {response_text}")
    
    def get_status(self, rental_id: str, user=None, get_full_text: bool = False) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Get SMS status for a rental
        Returns: (status, code, full_text)
        """
        # Regular DaisySMS API call for all services (including 'other')
        params = {'id': rental_id}
        if get_full_text:
            params['text'] = '1'
        
        try:
            response_text, headers = self._make_request('getStatus', params, user=user)
            
            if response_text.startswith('STATUS_OK:'):
                code = response_text.split(':')[1]
                full_text = headers.get('X-Text', None) if get_full_text else None
                return 'RECEIVED', code, full_text
            elif response_text == 'STATUS_WAIT_CODE':
                return 'WAITING', None, None
            elif response_text == 'STATUS_CANCEL':
                return 'CANCELLED', None, None
            
            raise DaisySMSException(f"Unexpected status response: {response_text}")
            
        except DaisySMSException as e:
            # If we get NO_ACTIVATION, it likely means the rental has expired or been removed by DaisySMS
            if "Rental not found" in str(e):
                return 'EXPIRED', None, None
            raise
    
    def set_status_done(self, rental_id: str, user=None) -> bool:
        """
        Mark rental as done (status 6)
        """
        params = {'id': rental_id, 'status': '6'}
        response_text, _ = self._make_request('setStatus', params, user=user)
        
        return response_text == 'ACCESS_ACTIVATION'
    
    def cancel_rental(self, rental_id: str, user=None) -> bool:
        """
        Cancel rental and get refund (status 8)
        """
        # Regular DaisySMS API call for all services (including 'other')
        params = {'id': rental_id, 'status': '8'}
        response_text, _ = self._make_request('setStatus', params, user=user)
        
        return response_text == 'ACCESS_CANCEL'
    
    def keep_number(self, rental_id: str, user=None) -> bool:
        """
        Keep number without receiving message (pay as if received)
        """
        params = {'id': rental_id}
        response_text, _ = self._make_request('keep', params, user=user)
        
        return response_text == 'OK'
    
    def get_extra_activation(self, previous_activation_id: str, user=None) -> str:
        """
        Get additional message on same number
        """
        params = {'activationId': previous_activation_id}
        response_text, _ = self._make_request('getExtraActivation', params, user=user)
        
        # Implementation depends on specific response format
        return response_text
    
    def get_prices_verification(self, user=None) -> Dict:
        """
        Get services with prices (service => country => data format)
        """
        response_text, _ = self._make_request('getPricesVerification', user=user)
        
        # Parse JSON response
        import json
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            raise DaisySMSException(f"Invalid JSON response: {response_text}")
    
    def get_prices(self, user=None) -> Dict:
        """
        Get services with prices (country => service => data format)
        """
        response_text, _ = self._make_request('getPrices', user=user)
        
        # Parse JSON response
        import json
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            raise DaisySMSException(f"Invalid JSON response: {response_text}")
    
    def sync_services(self, user=None) -> int:
        """
        Sync services from DaisySMS API to local database
        Returns: Number of services updated
        """
        try:
            prices_data = self.get_prices_verification(user=user)
            updated_count = 0
            
            for service_code, countries in prices_data.items():
                if '187' in countries:  # USA country code
                    service_data = countries['187']
                    
                    service, created = Service.objects.get_or_create(
                        code=service_code,
                        defaults={
                            'name': service_data.get('name', service_code),
                            'price': Decimal(str(service_data.get('cost', 0))),
                            'available_numbers': min(int(service_data.get('count', 0)), 100),
                            'supports_multiple_sms': service_data.get('multi', False),
                        }
                    )
                    
                    if not created:
                        # Don't overwrite pricing for special services like "Service Not Listed"
                        if service_code != 'service_not_listed':
                            # Update existing service with API prices
                            service.price = Decimal(str(service_data.get('cost', 0)))
                            service.available_numbers = min(int(service_data.get('count', 0)), 100)
                            service.supports_multiple_sms = service_data.get('multi', False)
                            service.save()
                        else:
                            # For "Service Not Listed", only update availability and multi-SMS support
                            service.available_numbers = min(int(service_data.get('count', 0)), 100)
                            service.supports_multiple_sms = service_data.get('multi', False)
                            service.save()
                    
                    updated_count += 1
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to sync services: {str(e)}")
            raise DaisySMSException(f"Failed to sync services: {str(e)}")


def get_daisysms_client(user=None) -> DaisySMSClient:
    """
    Get DaisySMS client instance using system API key
    """
    # Use system API key (individual user API keys have been removed)
    system_api_key = getattr(settings, 'DAISYSMS_API_KEY', None)
    if system_api_key:
        return DaisySMSClient(system_api_key)
    
    raise DaisySMSException("No system API key configured")
