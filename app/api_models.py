"""
Models for Reseller API System
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid


class APIKey(models.Model):
    """
    API Keys for reseller partners
    Each user can have multiple API keys for different applications
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100, help_text="Friendly name for this API key (e.g., 'Production Site', 'Testing')")
    key_hash = models.CharField(max_length=64, unique=True, db_index=True)  # SHA-256 hash of actual key
    key_prefix = models.CharField(max_length=20, help_text="First 8 chars for identification")
    
    # Permissions
    can_purchase = models.BooleanField(default=True, help_text="Can purchase phone numbers")
    can_check_balance = models.BooleanField(default=True, help_text="Can check account balance")
    can_get_prices = models.BooleanField(default=True, help_text="Can get pricing information")
    can_cancel = models.BooleanField(default=True, help_text="Can cancel orders")
    
    # Rate limiting
    rate_limit_per_minute = models.IntegerField(default=60, help_text="Max API calls per minute")
    
    # Pricing markup (for resellers)
    markup_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Markup percentage added to base price (e.g., 10.00 for 10%)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Usage tracking
    total_requests = models.IntegerField(default=0)
    total_purchases = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiration date")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
    
    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.key_prefix}...)"
    
    def record_usage(self):
        """Record API usage"""
        self.last_used_at = timezone.now()
        self.total_requests += 1
        self.save(update_fields=['last_used_at', 'total_requests'])
    
    def is_rate_limited(self):
        """Check if rate limit is exceeded"""
        if self.rate_limit_per_minute <= 0:
            return False  # No limit
        
        # Count requests in the last minute
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        recent_requests = APIRequest.objects.filter(
            api_key=self,
            created_at__gte=one_minute_ago
        ).count()
        
        return recent_requests >= self.rate_limit_per_minute
    
    def is_expired(self):
        """Check if API key has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def get_masked_key(self):
        """Return masked version of API key for display"""
        return f"{self.key_prefix}...{self.key_hash[-8:]}"


class APIRequest(models.Model):
    """
    Log of all API requests for analytics and rate limiting
    """
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='requests')
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    
    # Request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Response
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField(help_text="Response time in milliseconds")
    
    # For purchase requests
    order_id = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "API Request"
        verbose_name_plural = "API Requests"
        indexes = [
            models.Index(fields=['api_key', '-created_at']),
            models.Index(fields=['endpoint', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.api_key.user.username} - {self.method} {self.endpoint} - {self.status_code}"


class APIWebhook(models.Model):
    """
    Webhook endpoints for API users to receive order status updates
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_webhooks')
    url = models.URLField(help_text="Your webhook endpoint URL")
    secret = models.CharField(max_length=64, help_text="Webhook secret for signature verification")
    
    # Events to listen for
    on_sms_received = models.BooleanField(default=True)
    on_order_expired = models.BooleanField(default=True)
    on_order_cancelled = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    
    # Reliability tracking
    total_sent = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "API Webhook"
        verbose_name_plural = "API Webhooks"
    
    def __str__(self):
        return f"{self.user.username} - {self.url}"


class APIOrderMapping(models.Model):
    """
    Maps internal rentals to API user's orders
    Tracks which API key created which order
    """
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='orders')
    
    # Link to internal rental (MTelSMS)
    rental = models.ForeignKey('Rental', on_delete=models.CASCADE, null=True, blank=True)
    
    # API response data
    api_order_id = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Pricing for this API user (with markup)
    api_price = models.DecimalField(max_digits=12, decimal_places=2)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    markup_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Status
    status = models.CharField(max_length=20, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "API Order"
        verbose_name_plural = "API Orders"
    
    def __str__(self):
        return f"API Order {self.api_order_id} by {self.api_key.user.username}"
