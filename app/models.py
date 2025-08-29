from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid
import secrets
from datetime import timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Stores NGN balance
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USD_TO_NGN_RATE = Decimal('1650.00')  # Used for DaisySMS API conversions only

    def __str__(self):
        return f"{self.user.username} - ₦{self.balance}"
    
    def get_naira_balance(self):
        """Get balance in Naira (all balances are stored in NGN)"""
        from decimal import Decimal
        return Decimal(str(self.balance))
    
    def get_usd_balance(self):
        """Convert NGN balance to USD for DaisySMS API calls"""
        from decimal import Decimal
        return Decimal(str(self.balance)) / self.USD_TO_NGN_RATE

class Service(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    icon_url = models.URLField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Stores USD price from DaisySMS API
    profit_margin = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Profit margin in Naira (e.g., 100.00 for ₦100)")
    available_numbers = models.IntegerField(default=0)
    supports_multiple_sms = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USD_TO_NGN_RATE = Decimal('1650.00')  # Used for DaisySMS API conversions only

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_naira_price(self):
        """Get price in Naira: USD base price converted to NGN + profit margin"""
        from decimal import Decimal
        
        # Convert USD base price to NGN
        base_price_usd = Decimal(str(self.price))
        base_price_naira = base_price_usd * self.USD_TO_NGN_RATE
        
        # Apply absolute profit margin in Naira
        absolute_margin = Decimal(str(self.profit_margin))
        return base_price_naira + absolute_margin
    
    def get_usd_price(self):
        """Get USD base price (for DaisySMS API calls)"""
        from decimal import Decimal
        return Decimal(str(self.price))

class Rental(models.Model):
    STATUS_CHOICES = [
        ('WAITING', 'Waiting for SMS'),
        ('RECEIVED', 'SMS Received'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
        ('DONE', 'Marked as Done'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rental_id = models.CharField(max_length=100, unique=True)  # DaisySMS ID
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WAITING')
    price = models.DecimalField(max_digits=12, decimal_places=2)  # Stores NGN price
    area_codes = models.CharField(max_length=255, blank=True, null=True)
    carriers = models.CharField(max_length=255, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # NGN
    refunded = models.BooleanField(default=False)  # Prevent double refunds
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.service.name} - {self.phone_number}"

    @property
    def is_expired(self):
        """Check if rental has expired - now syncs with DaisySMS status instead of time-based"""
        # This property is deprecated - expiration is now managed by DaisySMS API status
        # Use the status field instead: 'EXPIRED' status indicates DaisySMS has expired the rental
        return self.status == 'EXPIRED'
    
    def get_naira_price(self):
        """Get rental price in Naira (all prices are stored in NGN)"""
        from decimal import Decimal
        return Decimal(str(self.price))
    
    def get_usd_price(self):
        """Convert NGN price to USD for DaisySMS API calls"""
        from decimal import Decimal
        return Decimal(str(self.price)) / UserProfile.USD_TO_NGN_RATE

class SMSMessage(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='messages')
    code = models.CharField(max_length=20, blank=True, null=True)
    full_text = models.TextField(blank=True, null=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_at']

    def __str__(self):
        return f"{self.rental.phone_number} - {self.code or 'No code'}"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('RENTAL', 'Rental Payment'),
        ('REFUND', 'Refund'),
        ('PENALTY', 'Penalty'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Now stores NGN amounts
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True, null=True)
    rental = models.ForeignKey(Rental, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - ₦{self.amount}"

class APILog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    request_data = models.JSONField(blank=True, null=True)
    response_data = models.JSONField(blank=True, null=True)
    status_code = models.IntegerField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    execution_time = models.FloatField(blank=True, null=True)  # In seconds
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.endpoint} - {self.status_code} - {self.created_at}"

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Password reset token for {self.user.username}"
    
    def is_valid(self):
        """Check if token is still valid (not expired and not used)"""
        if self.used:
            return False
        
        # Token expires after 1 hour
        expiry_time = self.created_at + timedelta(hours=1)
        return timezone.now() < expiry_time
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.save()
    
    @classmethod
    def create_token(cls, user):
        """Create a new password reset token for user"""
        # Delete any existing unused tokens for this user
        cls.objects.filter(user=user, used=False).delete()
        
        # Generate a secure random token
        token = secrets.token_urlsafe(48)
        
        return cls.objects.create(user=user, token=token)

# SMS Service Configuration Models (for admin management)
class SMSServiceCategory(models.Model):
    """Categories for SMS services (e.g. Social Media, Messaging, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "SMS Service Category"
        verbose_name_plural = "SMS Service Categories"
    
    def __str__(self):
        return self.name

class SMSService(models.Model):
    """Individual SMS services with pricing configuration"""
    service_code = models.CharField(max_length=50, unique=True)  # e.g. 'whatsapp', 'telegram'
    service_name = models.CharField(max_length=100)  # Display name
    category = models.ForeignKey(SMSServiceCategory, on_delete=models.CASCADE, related_name='services')
    
    # Pricing
    base_price_usd = models.DecimalField(max_digits=10, decimal_places=4, default=0)  # Legacy USD field
    base_price_rub = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Wholesale from 5sim (RUB)
    base_price_naira = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Base price in Naira
    profit_margin_naira = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Profit margin in Naira
    
    # Configuration
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    
    # Auto-update tracking
    last_price_update = models.DateTimeField(null=True, blank=True)
    price_update_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['service_name']
        verbose_name = "SMS Service"
        verbose_name_plural = "SMS Services"
    
    def __str__(self):
        return f"{self.service_name} ({self.service_code})"
    
    def get_wholesale_price_ngn(self):
        """Get wholesale price in NGN"""
        if self.base_price_naira > 0:
            return float(self.base_price_naira)
        elif self.base_price_rub > 0:
            # Convert RUB to NGN (5sim uses RUB)
            from django.conf import settings
            return float(self.base_price_rub * settings.EXCHANGE_RATE_RUB_TO_NGN)
        else:
            # Fallback to USD conversion if neither Naira nor RUB price is set
            from django.conf import settings
            return float(self.base_price_usd * settings.EXCHANGE_RATE_USD_TO_NGN)
    
    def get_final_price_ngn(self):
        """Get final price including profit margin in NGN"""
        wholesale_ngn = self.get_wholesale_price_ngn()
        return round(wholesale_ngn + float(self.profit_margin_naira), 2)
    
    def get_profit_amount_ngn(self):
        """Get profit amount in NGN"""
        return float(self.profit_margin_naira)
    
    def save(self, *args, **kwargs):
        """Auto-calculate base price in Naira when saving"""
        if self.base_price_usd and not self.base_price_naira:
            from django.conf import settings
            self.base_price_naira = self.base_price_usd * settings.EXCHANGE_RATE_USD_TO_NGN
        
        # Set default profit margin if not set
        if not self.profit_margin_naira:
            from django.conf import settings
            wholesale_naira = self.get_wholesale_price_ngn()
            self.profit_margin_naira = round(wholesale_naira * settings.DEFAULT_PROFIT_MARGIN_PERCENT / 100, 2)
        
        super().save(*args, **kwargs)
    
    def update_base_price(self, new_price_usd):
        """Update base price and track the update"""
        if self.base_price_usd != new_price_usd:
            self.base_price_usd = new_price_usd
            self.last_price_update = timezone.now()
            self.price_update_count += 1
            self.save()

class SMSOperator(models.Model):
    """SMS operators for different countries/services"""
    country_code = models.CharField(max_length=10)  # e.g. 'nigeria', 'usa'
    country_name = models.CharField(max_length=100)
    operator_code = models.CharField(max_length=50)  # e.g. 'mtn', 'airtel'
    operator_name = models.CharField(max_length=100)
    service = models.ForeignKey(SMSService, on_delete=models.CASCADE, related_name='operators')
    
    # Operator-specific pricing (if different from service default)
    base_price_usd = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    base_price_naira = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    profit_margin_naira = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Availability
    is_active = models.BooleanField(default=True)
    available_count = models.IntegerField(default=0)  # Available numbers
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=95.0)
    
    # Auto-update tracking
    last_update = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['country_code', 'operator_code', 'service']
        ordering = ['country_name', 'operator_name']
        verbose_name = "SMS Operator"
        verbose_name_plural = "SMS Operators"
    
    def __str__(self):
        return f"{self.country_name} - {self.operator_name} - {self.service.service_name}"
    
    def get_effective_price_usd(self):
        """Get effective price (operator-specific or service default)"""
        return self.base_price_usd or self.service.base_price_usd
    
    def get_effective_price_naira(self):
        """Get effective base price in Naira"""
        if self.base_price_naira:
            return float(self.base_price_naira)
        elif self.service.base_price_naira:
            return float(self.service.base_price_naira)
        else:
            # Fallback to USD conversion
            from django.conf import settings
            return float(self.get_effective_price_usd() * settings.EXCHANGE_RATE_USD_TO_NGN)
    
    def get_effective_profit_margin_naira(self):
        """Get effective profit margin in Naira"""
        return float(self.profit_margin_naira or self.service.profit_margin_naira)
    
    def get_final_price_ngn(self):
        """Get final price for this operator"""
        wholesale_ngn = self.get_effective_price_naira()
        profit_ngn = self.get_effective_profit_margin_naira()
        return round(wholesale_ngn + profit_ngn, 2)

# 5sim.net Purchase Models
class FiveSimOrder(models.Model):
    ORDER_TYPES = [
        ('ACTIVATION', 'Activation'),
        ('HOSTING', 'Hosting'),
        ('REUSE', 'Reuse'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RECEIVED', 'SMS Received'),
        ('CANCELED', 'Canceled'),
        ('TIMEOUT', 'Timeout'),
        ('FINISHED', 'Finished'),
        ('BANNED', 'Number Banned'),
        ('EXPIRED', 'Expired'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.BigIntegerField(unique=True)  # 5sim order ID
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='ACTIVATION')
    phone_number = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    operator = models.CharField(max_length=100)
    product = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2)  # Original price from 5sim (in RUB/USD)
    price_naira = models.DecimalField(max_digits=12, decimal_places=2)  # Price charged to user in NGN
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    expires_at = models.DateTimeField()
    forwarding = models.BooleanField(default=False)
    forwarding_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Purchase options
    reuse_enabled = models.BooleanField(default=False)
    voice_enabled = models.BooleanField(default=False)
    max_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    referral_key = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product} - {self.phone_number} - {self.status}"

    @property
    def is_expired(self):
        """Check if order has expired"""
        return timezone.now() > self.expires_at
    
    def get_time_left(self):
        """Get time left until expiration in a human readable format"""
        if self.is_expired:
            return "Expired"
        
        delta = self.expires_at - timezone.now()
        total_seconds = int(delta.total_seconds())
        
        if total_seconds >= 3600:  # More than an hour
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        elif total_seconds >= 60:  # More than a minute
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            return f"{total_seconds}s"
    
    def get_time_left_minutes(self):
        """Get time left until expiration in minutes"""
        if self.is_expired:
            return 0
        delta = self.expires_at - timezone.now()
        return max(0, int(delta.total_seconds() / 60))

class FiveSimSMS(models.Model):
    order = models.ForeignKey(FiveSimOrder, on_delete=models.CASCADE, related_name='sms_messages')
    sms_id = models.BigIntegerField(blank=True, null=True)  # 5sim SMS ID if available
    sender = models.CharField(max_length=100, blank=True, null=True)
    text = models.TextField()
    code = models.CharField(max_length=20, blank=True, null=True)  # Extracted verification code
    date = models.DateTimeField()  # When SMS was actually received
    created_at = models.DateTimeField(auto_now_add=True)  # When we retrieved it

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.order.phone_number} - {self.sender} - {self.code or 'No code'}"

class FiveSimAPIKey(models.Model):
    """Store user's 5sim API keys"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=500, help_text="JWT token from 5sim.net")
    is_active = models.BooleanField(default=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="5sim account balance")
    rating = models.IntegerField(default=96, help_text="5sim account rating")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_balance_check = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - 5sim API Key"

    def mask_api_key(self):
        """Return masked API key for display"""
        if len(self.api_key) > 10:
            return f"{self.api_key[:10]}...{self.api_key[-4:]}"
        return "***"
