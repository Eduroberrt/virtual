"""
MTelSMS API Integration
Handles all communication with MTelSMS API for SMS verification services
"""

import requests
import time
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class MTelSMSException(Exception):
    """Custom exception for MTelSMS API errors"""
    pass

class MTelSMSClient:
    """
    MTelSMS API Client for handling all SMS verification service operations
    """
    
    BASE_URL = "https://mtelsms.com/stubs/handler_api.php"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WDN-Virtual-SMS/2.0'
        })
    
    def _make_request(self, action: str, params: Dict = None) -> Dict:
        """
        Make API request to MTelSMS with logging and error handling
        
        Returns:
            Dict: JSON response from API
        """
        if params is None:
            params = {}
        
        params.update({
            'api_key': self.api_key,
            'action': action
        })
        
        start_time = time.time()
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            execution_time = time.time() - start_time
            
            # Log request details
            logger.info(f"MTelSMS Request URL: {response.url}")
            logger.info(f"MTelSMS Request params: {params}")
            logger.info(f"MTelSMS Response status: {response.status_code}")
            logger.info(f"MTelSMS Response text: {response.text}")
            logger.info(f"MTelSMS Execution time: {execution_time:.2f}s")
            
            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
            except ValueError:
                raise MTelSMSException(f"Invalid JSON response: {response.text}")
            
            # Check for API-level errors
            if data.get('status') == 'error':
                error_message = data.get('message', 'Unknown error')
                
                # Log the raw error for debugging
                logger.error(f"MTelSMS API Error - Action: {action}, Raw Response: {data}")
                
                # Translate common errors to user-friendly messages
                if 'Authorization failed' in error_message or 'API key' in error_message:
                    raise MTelSMSException("Service authentication failed. Please contact support.")
                elif 'balance' in error_message.lower() or 'insufficient' in error_message.lower():
                    raise MTelSMSException("Insufficient service provider balance. Please contact support.")
                elif 'maximum request' in error_message.lower() or 'rate limit' in error_message.lower():
                    raise MTelSMSException("Too many requests. Please wait a moment and try again.")
                else:
                    # Pass through the actual error message from MTelSMS
                    raise MTelSMSException(f"Service Error: {error_message}")
            
            logger.info(f"MTelSMS API call successful: {action}")
            return data
            
        except requests.RequestException as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            # Convert technical errors to user-friendly messages
            if "SSLError" in error_msg or "SSL" in error_msg:
                error_msg = "Connection security issue with SMS service. Please try again in a few minutes."
            elif "ConnectionError" in error_msg or "Connection refused" in error_msg:
                error_msg = "Unable to connect to SMS service. Please check your internet connection and try again."
            elif "Timeout" in error_msg or "timeout" in error_msg:
                error_msg = "SMS service is taking too long to respond. Please try again."
            elif "Max retries exceeded" in error_msg:
                error_msg = "SMS service is currently unavailable. Please try again in a few minutes."
            else:
                error_msg = "Connection problem with SMS service. Please try again."
            
            logger.error(f"MTelSMS API request failed: {action} - {error_msg}")
            raise MTelSMSException(error_msg)
        
        except MTelSMSException as e:
            logger.warning(f"MTelSMS API error: {action} - {str(e)}")
            raise
    
    def get_balance(self) -> Decimal:
        """
        Get account balance from MTelSMS
        Returns: Decimal balance amount in USD
        """
        response = self._make_request('getBalance')
        
        if response.get('status') == 'success':
            balance_str = response.get('balance', '0.00')
            return Decimal(balance_str)
        
        raise MTelSMSException("Failed to retrieve balance")
    
    def get_number(self, service_id: str, max_price: Optional[Decimal] = None, 
                   wholesale: bool = False) -> Tuple[str, str, Decimal, int]:
        """
        Rent a phone number for SMS verification
        
        Args:
            service_id: MTelSMS service ID
            max_price: Maximum price in USD
            wholesale: Use wholesale pricing
            
        Returns:
            Tuple[rental_id, phone_number, actual_price_usd, time_remaining_seconds]
        """
        params = {
            'service_id': service_id,
            'wholesale_status': 'true' if wholesale else 'false'
        }
        
        if max_price:
            params['max_price'] = str(round(float(max_price), 2))
        
        response = self._make_request('getNumber', params)
        
        if response.get('status') == 'success':
            data = response.get('data', {})
            
            rental_id = data.get('id')
            phone_number = data.get('number', 'waiting')
            
            # Use wholesale_price if available, otherwise use service_price
            price_key = 'wholesale_price' if wholesale else 'service_price'
            actual_price = Decimal(data.get(price_key, data.get('service_price', '0.00')))
            
            time_remaining = int(data.get('time_remaining', 1800))
            
            if not rental_id:
                raise MTelSMSException("No rental ID received from service")
            
            return rental_id, phone_number, actual_price, time_remaining
        
        raise MTelSMSException("Failed to rent number")
    
    def get_code(self, rental_id: str) -> Tuple[str, Optional[str], str, int]:
        """
        Get SMS verification code and status
        
        According to MTelSMS API docs, this is the ONLY way to check status.
        There is no separate getStatus endpoint.
        
        Returns:
            Tuple[status, code, phone_number, time_remaining]
            status: 'WAITING' or 'RECEIVED'
            code: SMS code or None if waiting
        """
        params = {'id': rental_id}
        response = self._make_request('getCode', params)
        
        if response.get('status') == 'success':
            data = response.get('data', {})
            
            code = data.get('code', 'waiting')
            phone_number = data.get('number', '')
            time_remaining = int(data.get('time_remaining', 0))
            
            if code == 'waiting':
                return 'WAITING', None, phone_number, time_remaining
            else:
                return 'RECEIVED', code, phone_number, time_remaining
        
        raise MTelSMSException("Failed to get code")
    
    def cancel_rental(self, rental_id: str) -> bool:
        """
        Cancel rental and get refund
        
        Returns:
            bool: True if successfully cancelled
        """
        params = {'id': rental_id}
        response = self._make_request('cancelNumber', params)
        
        if response.get('status') == 'success':
            message = response.get('message', '')
            logger.info(f"Rental cancelled: {rental_id} - {message}")
            return True
        
        return False
    
    def get_all_services(self) -> List[Dict]:
        """
        Get all available services with pricing
        
        Returns:
            List of service dictionaries with id, name, price, wholesale_price, validity_time
        """
        response = self._make_request('allService')
        
        if response.get('status') == 'success':
            services = response.get('data', [])
            return services
        
        raise MTelSMSException("Failed to retrieve services")
    
    def get_service_price(self, service_id: str) -> Dict:
        """
        Get price details for a specific service
        
        Returns:
            Dict with service_id, name, price, wholesale_price, validity_time
        """
        params = {'service_id': service_id}
        response = self._make_request('getPrice', params)
        
        if response.get('status') == 'success':
            return response.get('data', {})
        
        raise MTelSMSException("Failed to retrieve service price")
    
    def get_prices_verification(self) -> Dict:
        """
        Get all services in a format compatible with DaisySMS sync
        Returns services organized by service code for easy lookup
        """
        services = self.get_all_services()
        
        # Transform to format expected by sync_services
        # Key: service name (lowercase, no spaces) -> Value: service data
        result = {}
        
        for service in services:
            # Create a service code from the name (lowercase, no spaces)
            service_code = service.get('name', '').lower().replace(' ', '').replace('-', '')
            
            if service_code:
                result[service_code] = {
                    'service_id': service.get('service_id'),
                    'name': service.get('name'),
                    'cost': service.get('price', '0.00'),  # Use retail price
                    'wholesale_cost': service.get('wholesale_price', '0.00'),
                    'validity_time': service.get('validity_time', '1800'),
                    'count': 100,  # MTelSMS doesn't provide stock info, assume available
                    'multi': False  # MTelSMS doesn't specify, assume single SMS
                }
        
        return result
    
    def sync_services(self) -> int:
        """
        Sync services from MTelSMS API to local database
        Returns: Number of services updated
        """
        try:
            from .models import Service
            from decimal import Decimal
            
            services_data = self.get_all_services()
            updated_count = 0
            
            for service_data in services_data:
                service_id = service_data.get('service_id')
                service_name = service_data.get('name', '')
                
                # Create service code from name
                service_code = service_name.lower().replace(' ', '').replace('-', '')
                
                if not service_code:
                    continue
                
                # Use retail price (not wholesale)
                price_usd = Decimal(service_data.get('price', '0.00'))
                
                service, created = Service.objects.get_or_create(
                    code=service_code,
                    defaults={
                        'name': service_name,
                        'price': price_usd,
                        'available_numbers': 100,  # Assume available
                        'supports_multiple_sms': False,
                        'profit_margin': Decimal('800.00'),  # Fixed ₦800 margin
                    }
                )
                
                if not created:
                    # Update existing service
                    service.name = service_name
                    service.price = price_usd
                    service.available_numbers = 100
                    service.save()
                
                updated_count += 1
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to sync services: {str(e)}")
            raise MTelSMSException(f"Failed to sync services: {str(e)}")


def get_mtelsms_client() -> MTelSMSClient:
    """
    Get MTelSMS client instance using system API key
    """
    system_api_key = getattr(settings, 'MTELSMS_API_KEY', None)
    if system_api_key:
        return MTelSMSClient(system_api_key)
    
    raise MTelSMSException("No system API key configured")
