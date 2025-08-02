from django.contrib import admin
from django.core.cache import cache
from .models import UserProfile, Service, Rental, SMSMessage, Transaction, APILog, PasswordResetToken

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

@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    list_display = ['endpoint', 'user', 'status_code', 'execution_time', 'created_at']
    list_filter = ['endpoint', 'status_code', 'created_at']
    search_fields = ['endpoint', 'user__username', 'error_message']
    readonly_fields = ['created_at']

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'used', 'is_valid_status']
    list_filter = ['used', 'created_at']
    search_fields = ['user__username', 'user__email', 'token']
    readonly_fields = ['token', 'created_at']
    
    def is_valid_status(self, obj):
        return obj.is_valid()
    is_valid_status.boolean = True
    is_valid_status.short_description = 'Valid'
