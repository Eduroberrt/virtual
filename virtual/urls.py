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
from app.views import *
from app.api_views import *
from app.auth_views import forgot_password, password_reset_confirm, password_reset_success

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('privacy/', privacy, name='privacy'),
    path('terms/', terms, name='terms'),
    path('faq/', faq, name='faq'),
    path('signup/', signup, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-success/', password_reset_success, name='password_reset_success'),
    path('change-password/', change_password, name='change_password'),
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/', profile, name='profile'),
    path('stats/', stats, name='stats'),
    path('wallet/', wallet, name='wallet'),
    path('rentals/', rentals, name='rentals'),
    path('service/', service, name='service'),
    path('news/', news, name='news'),
    path('payment/', payment, name='payment'),
    path('history/', history, name='history'),
    
    # API Endpoints
    path('api/balance/', get_user_balance, name='api_balance'),
    path('api/services/', get_services, name='api_services'),
    path('api/create-service-not-listed/', create_service_not_listed, name='api_create_service_not_listed'),
    path('api/realtime-prices/', get_realtime_prices, name='api_realtime_prices'),
    path('api/sync-services/', sync_services, name='api_sync_services'),
    path('api/rent/', rent_number, name='api_rent'),
    path('api/sms/<str:rental_id>/', check_sms, name='api_check_sms'),
    path('api/cancel/', cancel_rental, name='api_cancel'),
    path('api/expire/', expire_rental, name='api_expire'),
    path('api/auto-renew/', set_auto_renew, name='api_auto_renew'),
    path('api/rentals/', get_rentals, name='api_rentals'),
    path('api/transactions/', get_transactions, name='api_transactions'),
    path('api/rental-history/', get_rental_history, name='api_rental_history'),
]
