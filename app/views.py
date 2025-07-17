from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import UserProfile, Service, Rental, PasswordResetToken
from .turnstile import verify_turnstile, get_client_ip
import logging

logger = logging.getLogger(__name__)

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
        turnstile_token = request.POST.get('cf-turnstile-response')
        
        # Verify Turnstile CAPTCHA
        client_ip = get_client_ip(request)
        turnstile_result = verify_turnstile(turnstile_token, client_ip)
        
        if not turnstile_result.get('success'):
            messages.error(request, '❌ CAPTCHA verification failed. Please try again.')
            return render(request, 'signup.html')
        
        # Basic validation
        if not all([username, email, password, password_confirm]):
            messages.error(request, '❌ All fields are required. Please fill in all the information.')
            return render(request, 'signup.html')
        
        if password != password_confirm:
            messages.error(request, '❌ Passwords do not match. Please make sure both password fields are identical.')
            return render(request, 'signup.html')
        
        if len(password) < 8:
            messages.error(request, '❌ Password must be at least 8 characters long. Please choose a stronger password.')
            return render(request, 'signup.html')
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, '❌ This username is already taken. Please choose a different username.')
            return render(request, 'signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, '❌ An account with this email already exists. Please use a different email or try logging in.')
            return render(request, 'signup.html')
        
        # Create user and redirect to dashboard
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create user profile
        UserProfile.objects.get_or_create(user=user)
        
        # Send welcome email using HTML template
        try:
            # Render the HTML template with request context for proper URLs
            html_message = render_to_string('emails/welcome_email.html', {
                'user': user,
                'request': request,
            })
            
            # Create plain text version by stripping HTML tags
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject="Welcome to Young PG Virtual - Your Account is Ready!",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=True,
            )
            logger.info(f"Welcome email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {str(e)}")
        
        # Log the user in with explicit backend and redirect to dashboard
        user.backend = 'app.auth_backends.EmailOrUsernameModelBackend'
        login(request, user)
        return redirect('dashboard')
    
    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, '❌ Both username/email and password are required.')
            return render(request, 'login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Create user profile if it doesn't exist
            UserProfile.objects.get_or_create(user=user)
            
            messages.success(request, '✅ Logged in successfully!')
            
            # Redirect to next page or dashboard
            next_page = request.GET.get('next', 'dashboard')
            return redirect(next_page)
        else:
            messages.error(request, '❌ Invalid username/email or password.')
    
    return render(request, 'login.html')

def forgot_password(request):
    """Simple forgot password view"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()  # Don't convert to lowercase
        
        if not email:
            messages.error(request, '❌ Please enter your email address.')
            return render(request, 'forgot_password.html')
        
        # Use case-insensitive email lookup
        try:
            user = User.objects.get(email__iexact=email)
            logger.info(f"Found user: {user.username} with email: '{user.email}'")
        except User.DoesNotExist:
            messages.error(request, f'❌ No account found with email: {email}')
            logger.info(f"No user found with email: '{email}'")
            return render(request, 'forgot_password.html')
        
        try:
            # Create reset token
            reset_token = PasswordResetToken.create_token(user)
            
            # Send simple reset email
            reset_url = f"{request.scheme}://{request.get_host()}/reset-password/{reset_token.token}/"
            
            send_mail(
                subject="Reset Your Password - Young PG Virtual",
                message=f"""
Hi {user.first_name or user.username},

You requested to reset your password for Young PG Virtual.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours for security reasons.

If you didn't request this, please ignore this email.

Best regards,
Young PG Virtual Team
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],  # Use the actual email from database
                fail_silently=False,
            )
            logger.info(f"Password reset email sent to {user.email}")
            messages.success(request, f'✅ Password reset email sent to {user.email}')
            return redirect('password_reset_email_sent')
            
        except Exception as e:
            logger.error(f"Error sending reset email: {str(e)}")
            messages.error(request, f'❌ Failed to send email: {str(e)}')
            return render(request, 'forgot_password.html')
    
    return render(request, 'forgot_password.html')

def password_reset_email_sent(request):
    """Display email sent confirmation page"""
    return render(request, 'password_reset_email_sent.html')

def password_reset_confirm(request, token):
    """Handle password reset with token"""
    try:
        reset_token = get_object_or_404(PasswordResetToken, token=token)
        
        if not reset_token.is_valid():
            messages.error(request, '❌ This reset link has expired. Please request a new one.')
            return redirect('forgot_password')
        
        if request.method == 'POST':
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password_confirm', '')
            
            if not password or not password_confirm:
                messages.error(request, '❌ Please fill in both password fields.')
                return render(request, 'password_reset_confirm.html', {'token': token})
            
            if password != password_confirm:
                messages.error(request, '❌ Passwords do not match.')
                return render(request, 'password_reset_confirm.html', {'token': token})
            
            if len(password) < 8:
                messages.error(request, '❌ Password must be at least 8 characters long.')
                return render(request, 'password_reset_confirm.html', {'token': token})
            
            # Update password
            user = reset_token.user
            user.set_password(password)
            user.save()
            
            # Mark token as used
            reset_token.mark_as_used()
            
            # Send confirmation email
            try:
                send_mail(
                    subject="Password Changed - Young PG Virtual",
                    message=f"""
Hi {user.first_name or user.username},

Your password has been successfully changed.

If you didn't make this change, please contact support immediately.

Best regards,
Young PG Virtual Team
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Failed to send password change notification: {str(e)}")
            
            # Log user in and redirect
            login(request, user)
            messages.success(request, '🎉 Password updated successfully! You are now logged in.')
            return redirect('password_reset_success')
        
        return render(request, 'password_reset_confirm.html', {'token': token})
        
    except Exception as e:
        logger.error(f"Error in password reset: {str(e)}")
        messages.error(request, '❌ Invalid reset link.')
        return redirect('forgot_password')

def password_reset_success(request):
    """Display success page"""
    return render(request, 'password_reset_success.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, '✅ Logged out successfully! Come back soon!')
    return redirect('login')

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
            error = '❌ All fields are required.'
        elif not request.user.check_password(current_password):
            error = '❌ Current password is incorrect. Please enter your correct current password.'
        elif new_password != confirm_password:
            error = '❌ New passwords do not match. Please make sure both new password fields are identical.'
        elif len(new_password) < 8:
            error = '❌ Password must be at least 8 characters long. Please choose a stronger password.'
        else:
            # Change password
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keep user logged in
            success = '✅ Your password was successfully updated!'
    
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
