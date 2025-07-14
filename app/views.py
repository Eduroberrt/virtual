from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import UserProfile, Service, Rental

# Create your views here.

def index(request):
    return render(request, 'index.html')

def privacy(request):
    return render(request, 'privacy.html')

def terms(request):
    return render(request, 'terms.html')

def faq(request):
    return render(request, 'faq.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Basic validation
        if not all([username, email, password, password_confirm]):
            messages.error(request, 'All fields are required.')
            return render(request, 'signup.html')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html')
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'signup.html')
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'signup.html')
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Log the user in
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, 'Error creating account. Please try again.')
            return render(request, 'signup.html')
    
    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Create user profile if it doesn't exist
            UserProfile.objects.get_or_create(user=user)
            
            messages.success(request, 'Logged in successfully!')
            
            # Redirect to next page or dashboard
            next_page = request.GET.get('next', 'dashboard')
            return redirect(next_page)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('index')

@login_required
def change_password(request):
    error = None
    success = None
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate inputs
        if not all([current_password, new_password, confirm_password]):
            error = 'All fields are required.'
        elif not request.user.check_password(current_password):
            error = 'Current password is incorrect.'
        elif new_password != confirm_password:
            error = 'New passwords do not match.'
        elif len(new_password) < 8:
            error = 'Password must be at least 8 characters long.'
        else:
            # Change password
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keep user logged in
            success = 'Your password was successfully updated!'
    
    return render(request, 'change_password.html', {
        'error': error,
        'success': success
    })

@login_required
def dashboard(request):
    # Get user's recent rentals and all active services for dashboard
    recent_rentals = Rental.objects.filter(user=request.user).select_related('service')[:5]
    services = Service.objects.filter(is_active=True).order_by('name')
    
    context = {
        'recent_rentals': recent_rentals,
        'services': services,
    }
    return render(request, 'dashboard.html', context)

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        api_key = request.POST.get('api_key', '').strip()
        profile.api_key = api_key if api_key else None
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    context = {
        'profile': profile,
    }
    return render(request, 'profile.html', context)

@login_required
def stats(request):
    from django.db.models import Count, Sum
    from django.utils import timezone
    from datetime import timedelta
    import pytz
    import json
    
    # Get the last 30 days of data
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get user's rentals from the last 30 days
    user_rentals = Rental.objects.filter(
        user=request.user,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('service')
    
    # Group by date and service to calculate statistics
    la_tz = pytz.timezone('America/Los_Angeles')
    stats_data = []
    
    # Create a dictionary to group rentals by date and service
    grouped_data = {}
    
    for rental in user_rentals:
        # Convert to LA timezone
        rental_date_la = rental.created_at.astimezone(la_tz).date()
        service_name = rental.service.name
        
        key = (rental_date_la, service_name)
        
        if key not in grouped_data:
            grouped_data[key] = {
                'date': rental_date_la.strftime('%Y-%m-%d'),
                'service': service_name,
                'count': 0,
                'total_naira': 0.0,
                'rentals': []
            }
        
        grouped_data[key]['count'] += 1
        grouped_data[key]['total_naira'] += float(rental.get_naira_price())
        grouped_data[key]['rentals'].append(rental)
    
    # Convert to list and calculate averages
    for key, data in grouped_data.items():
        data['average_naira'] = data['total_naira'] / data['count'] if data['count'] > 0 else 0
        # Remove rentals list as it's not needed for frontend
        del data['rentals']
        stats_data.append(data)
    
    # Sort by date (newest first) then by service name
    stats_data.sort(key=lambda x: (x['date'], x['service']), reverse=True)
    
    context = {
        'stats_data_json': json.dumps(stats_data),
        'has_data': len(stats_data) > 0,
    }
    return render(request, 'stats.html', context)

@login_required
def wallet(request):
    return render(request, 'wallet.html')

@login_required
def rentals(request):
    # Get all user rentals with pagination
    rentals_list = Rental.objects.filter(user=request.user).select_related('service')
    
    # Filter by phone number if provided
    phone_filter = request.GET.get('phone', '').strip()
    if phone_filter:
        rentals_list = rentals_list.filter(phone_number__icontains=phone_filter)
    
    # Pagination
    paginator = Paginator(rentals_list, 20)
    page_number = request.GET.get('page')
    rentals_page = paginator.get_page(page_number)
    
    context = {
        'rentals': rentals_page,
        'phone_filter': phone_filter,
    }
    return render(request, 'rentals.html', context)

@login_required
def service(request):
    # Get all active services with prices
    services = Service.objects.filter(is_active=True).order_by('name')
    
    context = {
        'services': services,
    }
    return render(request, 'service_new.html', context)

@login_required
def news(request):
    return render(request, 'news.html')

@login_required
def payment(request):
    return render(request, 'payments.html')

@login_required
def history(request):
    from .models import Service
    
    # Get all services for the filter dropdown
    services = Service.objects.filter(is_active=True).order_by('name')
    
    context = {
        'services': services,
    }
    return render(request, 'history.html', context)
