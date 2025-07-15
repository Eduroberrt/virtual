"""
Authentication views for password reset functionality
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import PasswordResetToken
from .email_utils import send_password_reset_email, send_password_changed_notification
import logging

logger = logging.getLogger(__name__)

def forgot_password(request):
    """
    Handle forgot password requests
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'forgot_password.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Create password reset token
            reset_token = PasswordResetToken.create_token(user)
            
            # Send password reset email
            if send_password_reset_email(user, reset_token):
                messages.success(
                    request, 
                    'Password reset instructions have been sent to your email address. '
                    'Please check your inbox and spam folder.'
                )
                logger.info(f"Password reset email sent to {email}")
            else:
                messages.error(
                    request, 
                    'There was an error sending the password reset email. '
                    'Please try again later or contact support.'
                )
                logger.error(f"Failed to send password reset email to {email}")
            
        except User.DoesNotExist:
            # For security reasons, we don't reveal if an email exists or not
            messages.success(
                request, 
                'If an account with that email address exists, '
                'password reset instructions have been sent.'
            )
            logger.info(f"Password reset requested for non-existent email: {email}")
        
        except Exception as e:
            messages.error(
                request, 
                'An error occurred while processing your request. Please try again later.'
            )
            logger.error(f"Error in forgot_password view: {str(e)}")
    
    return render(request, 'forgot_password.html')

def password_reset_confirm(request, token):
    """
    Handle password reset confirmation with token
    """
    # Get the token object
    try:
        reset_token = get_object_or_404(PasswordResetToken, token=token)
        
        # Check if token is valid
        if not reset_token.is_valid():
            messages.error(
                request, 
                'This password reset link has expired or is invalid. '
                'Please request a new password reset.'
            )
            return redirect('forgot_password')
        
        if request.method == 'POST':
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password_confirm', '')
            
            # Validate passwords
            if not password or not password_confirm:
                messages.error(request, 'Please fill in both password fields.')
                return render(request, 'password_reset_confirm.html', {'token': token})
            
            if password != password_confirm:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'password_reset_confirm.html', {'token': token})
            
            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'password_reset_confirm.html', {'token': token})
            
            try:
                # Update user password
                user = reset_token.user
                user.set_password(password)
                user.save()
                
                # Mark token as used
                reset_token.mark_as_used()
                
                # Send confirmation email
                send_password_changed_notification(user)
                
                # Log the user in
                login(request, user)
                
                messages.success(
                    request, 
                    'Your password has been successfully updated! You are now logged in.'
                )
                
                logger.info(f"Password successfully reset for user: {user.username}")
                
                return redirect('password_reset_success')
                
            except Exception as e:
                messages.error(
                    request, 
                    'An error occurred while updating your password. Please try again.'
                )
                logger.error(f"Error updating password: {str(e)}")
                return render(request, 'password_reset_confirm.html', {'token': token})
        
        return render(request, 'password_reset_confirm.html', {'token': token})
        
    except Exception as e:
        messages.error(
            request, 
            'Invalid or expired password reset link. Please request a new password reset.'
        )
        logger.error(f"Error in password_reset_confirm view: {str(e)}")
        return redirect('forgot_password')

def password_reset_success(request):
    """
    Display password reset success page
    """
    return render(request, 'password_reset_success.html')
