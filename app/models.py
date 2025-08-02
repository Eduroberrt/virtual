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
        """Check if rental has expired (5 minutes)"""
        from datetime import timedelta
        expiry_time = self.created_at + timedelta(minutes=5)
        return timezone.now() > expiry_time
    
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
