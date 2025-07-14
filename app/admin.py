from django.contrib import admin
from .models import UserProfile, Service, Rental, SMSMessage, Transaction, APILog

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'api_key', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'price', 'daily_price', 'profit_margin', 'display_naira_price', 'available_numbers', 'is_active']
    list_filter = ['is_active', 'supports_multiple_sms']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at', 'display_naira_price', 'display_naira_daily_price']
    list_editable = ['is_active', 'price', 'daily_price', 'profit_margin']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'icon_url', 'is_active', 'supports_multiple_sms')
        }),
        ('Pricing (USD)', {
            'fields': ('price', 'daily_price', 'profit_margin')
        }),
        ('Pricing (Naira - Calculated)', {
            'fields': ('display_naira_price', 'display_naira_daily_price'),
            'classes': ('collapse',)
        }),
        ('Availability', {
            'fields': ('available_numbers',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_naira_price(self, obj):
        return f"₦{obj.get_naira_price():,.2f}"
    display_naira_price.short_description = 'Price (NGN)'
    
    def display_naira_daily_price(self, obj):
        return f"₦{obj.get_naira_daily_price():,.2f}"
    display_naira_daily_price.short_description = 'Daily Price (NGN)'

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'phone_number', 'status', 'price', 'is_ltr', 'created_at']
    list_filter = ['status', 'is_ltr', 'auto_renew', 'created_at']
    search_fields = ['user__username', 'phone_number', 'rental_id']
    readonly_fields = ['rental_id', 'created_at', 'updated_at']

@admin.register(SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    list_display = ['rental', 'code', 'received_at']
    list_filter = ['received_at']
    search_fields = ['rental__phone_number', 'code', 'full_text']
    readonly_fields = ['received_at']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'transaction_id', 'description']
    readonly_fields = ['transaction_id', 'created_at']

@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    list_display = ['endpoint', 'user', 'status_code', 'execution_time', 'created_at']
    list_filter = ['endpoint', 'status_code', 'created_at']
    search_fields = ['endpoint', 'user__username', 'error_message']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
