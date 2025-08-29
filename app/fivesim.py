"""
5sim.net API Integration
Handles all communication with 5sim.net API for SMS verification services
"""

import requests
import logging
from typing import Dict, List, Optional, Union
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class FiveSimAPI:
    """
    5sim.net API client for SMS verification services
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://5sim.net/v1"
        self.api_key = api_key or getattr(settings, 'FIVESIM_API_KEY', None)
        self.headers = {
            'Accept': 'application/json',
        }
        
        # Add authorization header if API key is available
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to 5sim API
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            Exception: If API request fails
        """
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    # Handle non-JSON responses
                    response_text = response.text.strip()
                    raise Exception(f"Response: {response_text}")
            elif response.status_code == 400:
                logger.error(f"5sim API error: {response.text}")
                response_text = response.text.strip()
                raise Exception(f"Response: {response_text}")
            else:
                logger.error(f"5sim API error {response.status_code}: {response.text}")
                response_text = response.text.strip()
                raise Exception(f"Response: {response_text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"5sim API request failed: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
    
    def get_products(self, country: str = "any", operator: str = "any") -> Dict:
        """
        Get available products for a specific country and operator
        
        Args:
            country: Country name or "any" for all countries
            operator: Operator name or "any" for all operators
            
        Returns:
            Dictionary of products with their details
        """
        cache_key = f"5sim_products_{country}_{operator}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        endpoint = f"/guest/products/{country}/{operator}"
        data = self._make_request(endpoint)
        
        # Cache for 5 minutes
        cache.set(cache_key, data, 300)
        return data
    
    def get_all_prices(self) -> Dict:
        """
        Get all product prices across all countries and operators
        
        Returns:
            Complete pricing data
        """
        cache_key = "5sim_all_prices"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        endpoint = "/guest/prices"
        data = self._make_request(endpoint)
        
        # Cache for 10 minutes
        cache.set(cache_key, data, 600)
        return data
    
    def get_prices_by_country(self, country: str) -> Dict:
        """
        Get product prices for a specific country
        
        Args:
            country: Country name
            
        Returns:
            Pricing data for the specified country
        """
        cache_key = f"5sim_prices_country_{country}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        endpoint = "/guest/prices"
        params = {"country": country}
        data = self._make_request(endpoint, params)
        
        # Cache for 10 minutes
        cache.set(cache_key, data, 600)
        return data
    
    def get_prices_by_product(self, product: str) -> Dict:
        """
        Get prices for a specific product across all countries
        
        Args:
            product: Product name (e.g., 'facebook', 'whatsapp')
            
        Returns:
            Pricing data for the specified product
        """
        cache_key = f"5sim_prices_product_{product}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        endpoint = "/guest/prices"
        params = {"product": product}
        data = self._make_request(endpoint, params)
        
        # Cache for 10 minutes
        cache.set(cache_key, data, 600)
        return data
    
    def get_prices_by_country_and_product(self, country: str, product: str) -> Dict:
        """
        Get prices for a specific product in a specific country
        
        Args:
            country: Country name
            product: Product name
            
        Returns:
            Pricing data for the specified country and product
        """
        cache_key = f"5sim_prices_{country}_{product}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        endpoint = "/guest/prices"
        params = {"country": country, "product": product}
        data = self._make_request(endpoint, params)
        
        # Cache for 10 minutes
        cache.set(cache_key, data, 600)
        return data
    
    def get_available_countries(self) -> List[str]:
        """
        Get list of available countries from pricing data
        
        Returns:
            List of country names
        """
        try:
            prices = self.get_all_prices()
            return list(prices.keys())
        except Exception as e:
            logger.error(f"Failed to get countries: {str(e)}")
            return []
    
    def get_available_products(self) -> List[str]:
        """
        Get list of available products from pricing data
        
        Returns:
            List of product names
        """
        try:
            prices = self.get_all_prices()
            products = set()
            
            for country_data in prices.values():
                if isinstance(country_data, dict):
                    products.update(country_data.keys())
            
            return list(products)
        except Exception as e:
            logger.error(f"Failed to get products: {str(e)}")
            return []
    
    def get_available_operators(self, country: str = None, product: str = None) -> List[str]:
        """
        Get list of available operators
        
        Args:
            country: Optional country filter
            product: Optional product filter
            
        Returns:
            List of operator names
        """
        try:
            if country and product:
                data = self.get_prices_by_country_and_product(country, product)
                if country in data and product in data[country]:
                    return list(data[country][product].keys())
            elif country:
                data = self.get_prices_by_country(country)
                operators = set()
                for product_data in data.get(country, {}).values():
                    if isinstance(product_data, dict):
                        operators.update(product_data.keys())
                return list(operators)
            else:
                # Get all operators from all countries
                prices = self.get_all_prices()
                operators = set()
                
                for country_data in prices.values():
                    if isinstance(country_data, dict):
                        for product_data in country_data.values():
                            if isinstance(product_data, dict):
                                operators.update(product_data.keys())
                
                return list(operators)
        except Exception as e:
            logger.error(f"Failed to get operators: {str(e)}")
            return []


    # Purchase methods (require authentication)
    
    def buy_activation_number(self, country: str, operator: str, product: str, 
                            forwarding: bool = False, number: Optional[str] = None,
                            reuse: bool = False, voice: bool = False, 
                            ref: Optional[str] = None, max_price: Optional[float] = None) -> Dict:
        """
        Buy an activation number
        
        Args:
            country: Country name or "any"
            operator: Operator name or "any"
            product: Product name
            forwarding: Enable call forwarding
            number: Forwarding number (11 digits without +)
            reuse: Buy with reuse ability
            voice: Buy with voice call ability
            ref: Referral key
            max_price: Maximum price limit
            
        Returns:
            Order details dictionary
            
        Raises:
            Exception: If purchase fails or authentication required
        """
        if not self.api_key:
            raise Exception("API key required for purchases")
            
        endpoint = f"/user/buy/activation/{country}/{operator}/{product}"
        
        params = {}
        if forwarding:
            params['forwarding'] = '1'
        if number:
            params['number'] = number
        if reuse:
            params['reuse'] = '1'
        if voice:
            params['voice'] = '1'
        if ref:
            params['ref'] = ref
        if max_price:
            params['maxPrice'] = str(max_price)
            
        return self._make_request(endpoint, params)
    
    def buy_hosting_number(self, country: str, operator: str, product: str) -> Dict:
        """
        Buy a hosting number
        
        Args:
            country: Country name or "any"
            operator: Operator name or "any"
            product: Product name (e.g., '3hours', 'facebook')
            
        Returns:
            Order details dictionary
            
        Raises:
            Exception: If purchase fails or authentication required
        """
        if not self.api_key:
            raise Exception("API key required for purchases")
            
        endpoint = f"/user/buy/hosting/{country}/{operator}/{product}"
        return self._make_request(endpoint)
    
    def reuse_number(self, product: str, number: str) -> Dict:
        """
        Re-buy/reuse a previously used number
        
        Args:
            product: Product name
            number: Phone number (4-15 digits without +)
            
        Returns:
            Order details dictionary
            
        Raises:
            Exception: If reuse fails or authentication required
        """
        if not self.api_key:
            raise Exception("API key required for purchases")
            
        endpoint = f"/user/reuse/{product}/{number}"
        return self._make_request(endpoint)
    
    def check_order(self, order_id: int) -> Dict:
        """
        Check order status and get SMS messages
        
        Args:
            order_id: 5sim order ID
            
        Returns:
            Order details with SMS messages
            
        Raises:
            Exception: If check fails or authentication required
        """
        if not self.api_key:
            raise Exception("API key required for order operations")
            
        endpoint = f"/user/check/{order_id}"
        return self._make_request(endpoint)
    
    def finish_order(self, order_id: int) -> Dict:
        """
        Mark order as finished
        
        Args:
            order_id: 5sim order ID
            
        Returns:
            Updated order details
            
        Raises:
            Exception: If operation fails or authentication required
        """
        if not self.api_key:
            raise Exception("API key required for order operations")
            
        endpoint = f"/user/finish/{order_id}"
        return self._make_request(endpoint)
    
    def cancel_order(self, order_id: int) -> Dict:
        """
        Cancel an order
        
        Args:
            order_id: 5sim order ID
            
        Returns:
            Updated order details
            
        Raises:
            Exception: If operation fails or authentication required
        """
        if not self.api_key:
            raise Exception("API key required for order operations")
            
        endpoint = f"/user/cancel/{order_id}"
        return self._make_request(endpoint)
    
    def ban_order(self, order_id: int) -> Dict:
        """
        Ban/report a number
        
        Args:
            order_id: 5sim order ID
            
        Returns:
            Updated order details
            
        Raises:
            Exception: If operation fails or authentication required
        """
        if not self.api_key:
            raise Exception("API key required for order operations")
            
        endpoint = f"/user/ban/{order_id}"
        return self._make_request(endpoint)
    
    def get_user_profile(self) -> Dict:
        """
        Get user profile information including balance and rating
        
        Returns:
            User profile data
            
        Raises:
            Exception: If request fails or authentication required
        """
        if not self.api_key:
            raise Exception("API key required for user operations")
            
        endpoint = "/user/profile"
        return self._make_request(endpoint)
    
    def get_sms_inbox(self, order_id: int) -> Dict:
        """
        Get SMS inbox for hosting orders
        
        Args:
            order_id: 5sim order ID
            
        Returns:
            SMS inbox data
            
        Raises:
            Exception: If request fails or authentication required
        """
        if not self.api_key:
            raise Exception("API key required for SMS operations")
            
        endpoint = f"/user/sms/inbox/{order_id}"
        return self._make_request(endpoint)


# Create a global instance
fivesim_api = FiveSimAPI()
