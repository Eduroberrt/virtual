"""
URL configuration for virtual project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app.views import *
from app.api_views import *
from app.fivesim_views import *
from app.fivesim_purchase_views import *
from app.pricing_sync_views import *
from app.balance_views import get_user_balance as get_user_balance_new
from app.debug_views import debug_callback
from app.unified_korapay import unified_korapay_handler

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('privacy/', privacy, name='privacy'),
    path('terms/', terms, name='terms'),
    path('faq/', faq, name='faq'),
    path('how-to-buy/', how_to_buy, name='how_to_buy'),
    path('simple-dropdown-test/', simple_dropdown_test, name='simple_dropdown_test'),
    path('signup/', signup, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('password-reset-email-sent/', password_reset_email_sent, name='password_reset_email_sent'),
    path('reset-password/<str:token>/', password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-success/', password_reset_success, name='password_reset_success'),
    path('change-password/', change_password, name='change_password'),
    path('dashboard/', dashboard_selector, name='dashboard'),
    path('dashboard-1/', dashboard_1, name='dashboard_1'),
    path('dashboard-2/', dashboard_2, name='dashboard_2'),
    path('countries/', countries_list, name='countries_list'),
    path('products/', products_list, name='products_list'),
    path('5sim-test/', fivesim_test, name='fivesim_test'),
    path('stats/', stats, name='stats'),
    path('wallet/', wallet, name='wallet'),
    path('rentals/', rentals, name='rentals'),
    path('service/', service, name='service'),
    path('news/', news, name='news'),
    path('payment/', payment, name='payment'),
    path('history/', history, name='history'),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap_xml, name="sitemap_xml"),
    
    # API Endpoints
    path('api/balance/', get_user_balance, name='api_balance'),
    path('api/services/', get_services, name='api_services'),
    path('api/create-service-not-listed/', create_service_not_listed, name='api_create_service_not_listed'),
    path('api/realtime-prices/', get_realtime_prices, name='api_realtime_prices'),
    path('api/rent/', rent_number, name='api_rent'),
    path('api/cancel/', cancel_rental, name='api_cancel'),
    path('api/rentals/', get_rentals, name='api_rentals'),
    path('api/sms/<str:rental_id>/', check_sms, name='api_check_sms'),
    path('api/transactions/', get_transactions, name='api_transactions'),
    path('api/rental-history/', get_rental_history, name='api_rental_history'),
    path('api/sync-services/', sync_services, name='api_sync_services'),
    
    # 5sim API Endpoints
    path('api/5sim/products/', get_products, name='api_5sim_products'),
    path('api/5sim/products/<str:country>/<str:operator>/', get_products, name='api_5sim_products_filtered'),
    path('api/5sim/prices/', get_all_prices, name='api_5sim_all_prices'),
    path('api/5sim/prices/country/<str:country>/', get_prices_by_country, name='api_5sim_prices_country'),
    path('api/5sim/prices/product/<str:product>/', get_prices_by_product, name='api_5sim_prices_product'),
    path('api/5sim/prices/<str:country>/<str:product>/', get_prices_by_country_and_product, name='api_5sim_prices_country_product'),
    path('api/5sim/countries/', get_countries, name='api_5sim_countries'),
    path('api/5sim/products-list/', get_products_list, name='api_5sim_products_list'),
    path('api/5sim/operators/', get_operators, name='api_5sim_operators'),
    
    # Pricing Auto-Sync Endpoints
    path('api/5sim/prices/auto-sync/', get_service_prices_with_auto_sync, name='api_prices_auto_sync'),
    path('api/5sim/sync/trigger/', trigger_price_sync, name='api_trigger_sync'),
    path('api/5sim/sync/health/', pricing_health_check, name='api_pricing_health'),
    
    # 5sim Purchase System - Backend API only
    path('api/5sim/buy-activation/', buy_activation_number, name='api_buy_activation'),
    path('api/5sim/orders/', get_user_orders, name='api_5sim_orders'),
    path('api/5sim/order/<str:order_id>/status/', check_order_status, name='api_order_status'),
    path('api/5sim/order/<str:order_id>/finish/', finish_order, name='api_finish_order'),
    path('api/5sim/order/<str:order_id>/cancel/', cancel_order, name='api_cancel_order'),
    
    # User Balance API
    path('api/user/balance/', get_user_balance_new, name='api_user_balance'),
    
    # Kora Pay Payment Endpoints
    path('api/korapay/initiate/', initiate_korapay_payment, name='api_korapay_initiate'),
    path('api/korapay/callback/', korapay_callback, name='api_korapay_callback'),
    path('api/korapay/webhook/', korapay_webhook, name='api_korapay_webhook'),
    path('api/korapay/unified/', unified_korapay_handler, name='api_korapay_unified'),
    path('api/debug/callback/', debug_callback, name='api_debug_callback'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
