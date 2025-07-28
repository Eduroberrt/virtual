from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid
import secrets
from datetime import timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Now stores NGN balance
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USD_TO_NGN_RATE = Decimal('1650.00')  # Used for DaisySMS API conversions only

    def __str__(self):
        return f"{self.user.username} - ₦{self.balance}"
    
    def get_naira_balance(self):
        """Get balance in Naira - handles both USD and NGN stored balances"""
        from decimal import Decimal
        
        # Detect if balance is stored in USD (< 100) or NGN (>= 100)
        if self.balance < 100 and self.balance > 0:
            # Balance is stored in USD - convert to NGN
            return Decimal(str(self.balance)) * self.USD_TO_NGN_RATE
        else:
            # Balance is already stored in NGN or is zero
            return Decimal(str(self.balance))
    
    def get_usd_balance(self):
        """Get balance in USD for DaisySMS API calls"""
        from decimal import Decimal
        
        # If balance is already in USD format, return as-is
        if self.balance < 100 and self.balance > 0:
            return Decimal(str(self.balance))
        else:
            # Balance is in NGN - convert to USD
            return Decimal(str(self.balance)) / self.USD_TO_NGN_RATE

class Service(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    icon_url = models.URLField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Now stores NGN price
    daily_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Now stores NGN price
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
        """Get price in Naira with profit margin - handles both USD and NGN stored prices"""
        from decimal import Decimal
        
        # Detect if price is stored in USD (< 100) or NGN (>= 100)
        if self.price < 100:
            # Price is stored in USD - convert to NGN first
            base_price_naira = Decimal(str(self.price)) * self.USD_TO_NGN_RATE
        else:
            # Price is already stored in NGN
            base_price_naira = Decimal(str(self.price))
        
        # Apply absolute profit margin in Naira (not percentage)
        absolute_margin = Decimal(str(self.profit_margin))
        return base_price_naira + absolute_margin
    
    def get_naira_daily_price(self):
        """Get daily price in Naira with profit margin - handles both USD and NGN stored prices"""
        from decimal import Decimal
        
        # Detect if daily_price is stored in USD (< 100) or NGN (>= 100)
        if self.daily_price < 100:
            # Daily price is stored in USD - convert to NGN first
            base_daily_price_naira = Decimal(str(self.daily_price)) * self.USD_TO_NGN_RATE
        else:
            # Daily price is already stored in NGN
            base_daily_price_naira = Decimal(str(self.daily_price))
        
        # Apply absolute profit margin in Naira (not percentage)
        absolute_margin = Decimal(str(self.profit_margin))
        return base_daily_price_naira + absolute_margin
    
    def get_usd_price(self):
        """Convert NGN price to USD for DaisySMS API calls"""
        return self.get_naira_price() / self.USD_TO_NGN_RATE

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
    price = models.DecimalField(max_digits=12, decimal_places=2)  # Now stores NGN price
    is_ltr = models.BooleanField(default=False)  # Long-term rental
    auto_renew = models.BooleanField(default=False)
    paid_until = models.DateTimeField(blank=True, null=True)  # For LTR
    area_codes = models.CharField(max_length=255, blank=True, null=True)
    carriers = models.CharField(max_length=255, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # NGN
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.service.name} - {self.phone_number}"

    @property
    def is_expired(self):
        if self.is_ltr and self.paid_until:
            return timezone.now() > self.paid_until
        return False
    
    def get_naira_price(self):
        """Get rental price in Naira - handles both USD and NGN stored prices"""
        from decimal import Decimal
        
        # Detect if price is stored in USD (< 100) or NGN (>= 100)
        if self.price < 100:
            # Price is stored in USD - convert to NGN
            return Decimal(str(self.price)) * UserProfile.USD_TO_NGN_RATE
        else:
            # Price is already stored in NGN
            return Decimal(str(self.price))
    
    def get_usd_price(self):
        """Get rental price in USD for DaisySMS API calls"""
        from decimal import Decimal
        
        # If price is already in USD format, return as-is
        if self.price < 100:
            return Decimal(str(self.price))
        else:
            # Price is in NGN - convert to USD
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
        ('LTR_RENEWAL', 'LTR Renewal'),
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
