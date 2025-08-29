from django.contrib import admin
from django.core.cache import cache
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from .models import (
    UserProfile, Service, Rental, SMSMessage, Transaction,
    SMSService, FiveSimOrder, FiveSimSMS
)

# Import models to unregister them from admin (but don't use them)
from .models import APILog, PasswordResetToken, SMSServiceCategory, SMSOperator, FiveSimAPIKey

# Unregister unwanted models from admin
try:
    admin.site.unregister(APILog)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(PasswordResetToken)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(SMSServiceCategory)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(SMSOperator)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(FiveSimAPIKey)
except admin.sites.NotRegistered:
    pass

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'display_usd_price', 'profit_margin', 'display_naira_price', 'available_numbers', 'is_active', 'is_special_service']
    list_filter = ['is_active', 'supports_multiple_sms']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at', 'display_naira_price', 'display_profit_margin_naira']
    list_editable = ['is_active', 'profit_margin']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'icon_url', 'is_active', 'supports_multiple_sms')
        }),
        ('Pricing', {
            'fields': ('price', 'profit_margin'),
            'description': 'Base price in USD (from DaisySMS API) and profit margin in Naira. Example: price = 0.50 (USD), profit_margin = 100.00 (NGN) = Final price ₦925.00'
        }),
        ('Pricing (Calculated)', {
            'fields': ('display_naira_price', 'display_profit_margin_naira'),
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
    
    def display_usd_price(self, obj):
        """Display real-time USD price from DaisySMS API"""
        try:
            from .daisysms import get_daisysms_client
            
            # Use cached prices to avoid too many API calls (cache for 5 minutes)
            cache_key = 'daisysms_realtime_prices'
            prices_data = cache.get(cache_key)
            
            if prices_data is None:
                # Get real-time price from DaisySMS
                client = get_daisysms_client()
                prices_data = client.get_prices_verification()
                cache.set(cache_key, prices_data, 300)  # Cache for 5 minutes
            
            # Look for this service in the pricing data
            if obj.code in prices_data:
                countries = prices_data[obj.code]
                if '187' in countries:  # USA country code
                    cost = countries['187'].get('cost', 0)
                    return f"${cost}"
                        
            # Service not found in real-time data, show stored price with indicator
            return f"${obj.price:.2f} (stored)"
            
        except Exception as e:
            # Fallback to stored price on error
            return f"${obj.price:.2f} (error)"
    display_usd_price.short_description = 'Real-time Price (USD)'
    
    def display_profit_margin_naira(self, obj):
        return f"₦{obj.profit_margin:,.2f}"
    display_profit_margin_naira.short_description = 'Profit Margin (NGN)'
    
    def update_prices_from_daisysms(self, request, queryset):
        """Update selected services' prices from DaisySMS real-time prices"""
        try:
            from .daisysms import get_daisysms_client
            from django.contrib import messages
            from decimal import Decimal
            
            client = get_daisysms_client()
            prices_data = client.get_prices_verification()
            
            updated_count = 0
            for service in queryset:
                if service.code in prices_data:
                    countries = prices_data[service.code]
                    if '187' in countries:  # USA country code
                        new_price = Decimal(str(countries['187'].get('cost', 0)))
                        old_price = service.price
                        
                        if new_price != old_price:
                            service.price = new_price
                            service.save()
                            updated_count += 1
            
            if updated_count > 0:
                messages.success(request, f"Updated {updated_count} service(s) with real-time prices from DaisySMS.")
            else:
                messages.info(request, "No price updates needed - all prices are current.")
                
        except Exception as e:
            messages.error(request, f"Error updating prices: {str(e)}")
    
    update_prices_from_daisysms.short_description = "Update prices from DaisySMS real-time data"
    
    actions = ['update_prices_from_daisysms']
    
    def is_special_service(self, obj):
        return obj.code == 'service_not_listed'
    is_special_service.boolean = True
    is_special_service.short_description = 'Service Not Listed'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Put "Service Not Listed" at the top if it exists
        return qs.extra(
            select={'is_service_not_listed': "code = 'service_not_listed'"},
            order_by=['-is_service_not_listed', 'name']
        )
    
    def changelist_view(self, request, extra_context=None):
        # Check if Service Not Listed exists, if not, show a message
        if not Service.objects.filter(code='service_not_listed').exists():
            from django.contrib import messages
            messages.warning(
                request,
                'Service Not Listed is not set up. You can create it by running: python manage.py add_service_not_listed'
            )
        
        return super().changelist_view(request, extra_context)

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'phone_number', 'status', 'price', 'created_at']
    list_filter = ['status', 'created_at']
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

# SMS Service Management Admin Classes

@admin.register(SMSService)
class SMSServiceAdmin(admin.ModelAdmin):
    list_display = [
        'service_name', 'service_code', 'category', 'display_wholesale_price', 
        'profit_margin_naira', 'display_final_price', 'operator_count', 
        'is_active', 'last_price_update'
    ]
    list_filter = ['category', 'is_active', 'is_featured', 'last_price_update']
    search_fields = ['service_name', 'service_code', 'description']
    readonly_fields = [
        'last_price_update', 'price_update_count', 'created_at', 'updated_at',
        'display_wholesale_price', 'display_final_price', 'base_price_usd'
    ]
    list_editable = ['profit_margin_naira', 'is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('service_name', 'service_code', 'category', 'description', 'is_active', 'is_featured')
        }),
        ('Pricing Configuration', {
            'fields': ('base_price_usd', 'base_price_naira', 'profit_margin_naira'),
            'description': 'Base prices are auto-updated from 5sim API. Adjust profit margin in Naira to set final customer price.'
        }),
        ('Price Display (Calculated)', {
            'fields': ('display_wholesale_price', 'display_final_price'),
            'classes': ('collapse',)
        }),
        ('Auto-Update Tracking', {
            'fields': ('last_price_update', 'price_update_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['sync_prices_with_5sim', 'enable_auto_sync', 'disable_auto_sync']
    
    def display_wholesale_price(self, obj):
        return f"₦{obj.get_wholesale_price_ngn():,.2f}"
    display_wholesale_price.short_description = 'Wholesale Price (NGN)'
    
    def display_final_price(self, obj):
        return f"₦{obj.get_final_price_ngn():,.2f}"
    display_final_price.short_description = 'Customer Price (NGN)'
    
    def display_profit_margin(self, obj):
        return f"₦{obj.profit_margin_naira:,.2f}"
    display_profit_margin.short_description = 'Profit Margin (NGN)'
    
    def operator_count(self, obj):
        return obj.operators.filter(is_active=True).count()
    operator_count.short_description = 'Active Operators'
    
    def sync_prices_with_5sim(self, request, queryset):
        """Admin action to sync prices with 5sim API"""
        from django.core.management import call_command
        from django.contrib import messages
        import io
        import sys
        
        try:
            # Capture command output
            old_stdout = sys.stdout
            sys.stdout = output = io.StringIO()
            
            # Run the price update command
            call_command('update_fivesim_prices', 
                        services=[service.service_code for service in queryset])
            
            # Restore stdout
            sys.stdout = old_stdout
            
            # Show success message
            messages.success(request, f"Price sync completed for {queryset.count()} services. Check logs for details.")
            
        except Exception as e:
            messages.error(request, f"Failed to sync prices: {str(e)}")
    
    sync_prices_with_5sim.short_description = "🔄 Sync prices with 5sim API"
    
    def enable_auto_sync(self, request, queryset):
        """Enable services for auto-sync"""
        queryset.update(is_active=True)
        messages.success(request, f"Enabled auto-sync for {queryset.count()} services")
    
    enable_auto_sync.short_description = "✅ Enable auto-sync"
    
    def disable_auto_sync(self, request, queryset):
        """Disable services from auto-sync"""
        queryset.update(is_active=False)
        messages.success(request, f"Disabled auto-sync for {queryset.count()} services")
    
    disable_auto_sync.short_description = "❌ Disable auto-sync"


# 5sim Purchase System Admin Classes

@admin.register(FiveSimOrder)
class FiveSimOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_id', 'user', 'phone_number', 'product', 'order_type', 
        'status', 'display_price_naira', 'created_at', 'expires_at'
    ]
    list_filter = ['order_type', 'status', 'created_at', 'country', 'product']
    search_fields = ['order_id', 'phone_number', 'user__username', 'product']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user', 'order_type', 'status', 'product')
        }),
        ('Phone Details', {
            'fields': ('phone_number', 'country', 'operator')
        }),
        ('Pricing', {
            'fields': ('price', 'price_naira')
        }),
        ('Options', {
            'fields': ('forwarding', 'forwarding_number', 'reuse_enabled', 'voice_enabled', 'max_price', 'referral_key')
        }),
        ('Timing', {
            'fields': ('created_at', 'updated_at', 'expires_at')
        }),
    )
    
    def display_price_naira(self, obj):
        return f"₦{obj.price_naira:,.2f}"
    display_price_naira.short_description = 'Price (NGN)'

@admin.register(FiveSimSMS)
class FiveSimSMSAdmin(admin.ModelAdmin):
    list_display = ['order', 'sender', 'text_preview', 'code', 'date']
    list_filter = ['date', 'order__product']
    search_fields = ['sender', 'text', 'code', 'order__phone_number']
    readonly_fields = ['sms_id', 'date']
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Message Preview'

# Ensure SMS models are registered (backup registration)
try:
    from .models import SMSService, SMSServiceCategory, SMSOperator
    
    # Simple registration if the complex ones failed
    if SMSService not in admin.site._registry:
        @admin.register(SMSService)
        class SMSServiceSimpleAdmin(admin.ModelAdmin):
            list_display = ['service_name', 'service_code', 'base_price_naira', 'profit_margin_naira', 'is_active']
            list_filter = ['is_active', 'category']
            search_fields = ['service_name', 'service_code']
            list_editable = ['profit_margin_naira', 'is_active']
    
    # Removed: SMSServiceCategory and SMSOperator backup registrations
    # These models are now hidden from admin as requested

except Exception as e:
    print(f"Admin registration error: {e}")
