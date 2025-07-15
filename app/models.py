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
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USD_TO_NGN_RATE = Decimal('1650.00') 

    def __str__(self):
        return f"{self.user.username} - ${self.balance}"
    
    def get_naira_balance(self):
        """Convert USD balance to Naira"""
        return self.balance * self.USD_TO_NGN_RATE

class Service(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    icon_url = models.URLField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    daily_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Profit margin percentage (e.g., 15.00 for 15%)")
    available_numbers = models.IntegerField(default=0)
    supports_multiple_sms = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USD_TO_NGN_RATE = Decimal('1650.00')  

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_naira_price(self):
        """Calculate price in Naira with profit margin"""
        base_price_naira = self.price * self.USD_TO_NGN_RATE
        margin_amount = base_price_naira * (self.profit_margin / 100)
        return base_price_naira + margin_amount
    
    def get_naira_daily_price(self):
        """Calculate daily price in Naira with profit margin"""
        base_daily_price_naira = self.daily_price * self.USD_TO_NGN_RATE
        margin_amount = base_daily_price_naira * (self.profit_margin / 100)
        return base_daily_price_naira + margin_amount

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
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_ltr = models.BooleanField(default=False)  # Long-term rental
    auto_renew = models.BooleanField(default=False)
    paid_until = models.DateTimeField(blank=True, null=True)  # For LTR
    area_codes = models.CharField(max_length=255, blank=True, null=True)
    carriers = models.CharField(max_length=255, blank=True, null=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
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
        """Convert rental price to Naira"""
        return self.price * UserProfile.USD_TO_NGN_RATE

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
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True, null=True)
    rental = models.ForeignKey(Rental, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - ${self.amount}"

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
