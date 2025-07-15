"""
Email utilities for sending various types of emails
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

def send_html_email(subject, template_name, context, recipient_email, from_email=None):
    """
    Send an HTML email using a template
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        # Render the HTML template
        html_message = render_to_string(template_name, context)
        
        # Create plain text version by stripping HTML tags
        plain_message = strip_tags(html_message)
        
        # Send the email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email sent successfully to {recipient_email}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False

def send_welcome_email(user):
    """
    Send welcome email to new user
    """
    subject = "Welcome to Young PG Virtual - Your Account is Ready!"
    template_name = 'emails/welcome_email.html'
    
    context = {
        'user': user,
    }
    
    return send_html_email(
        subject=subject,
        template_name=template_name,
        context=context,
        recipient_email=user.email
    )

def send_password_reset_email(user, reset_token):
    """
    Send password reset email to user
    """
    subject = "Reset Your Password - Young PG Virtual"
    template_name = 'emails/password_reset_email.html'
    
    # Construct the reset URL
    # You'll need to replace 'your-domain.com' with your actual domain
    reset_url = f"https://your-domain.com/reset-password/{reset_token.token}/"
    
    context = {
        'user': user,
        'reset_url': reset_url,
        'token': reset_token.token,
    }
    
    return send_html_email(
        subject=subject,
        template_name=template_name,
        context=context,
        recipient_email=user.email
    )

def send_password_changed_notification(user):
    """
    Send notification email when password is successfully changed
    """
    subject = "Password Changed Successfully - Young PG Virtual"
    
    # Simple HTML content for password change notification
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #17a2b8;">Password Changed Successfully</h2>
        <p>Hi {user.first_name or user.username},</p>
        <p>Your password for Young PG Virtual has been successfully changed.</p>
        <p>If you didn't make this change, please contact our support team immediately.</p>
        <p>Best regards,<br>The Young PG Virtual Team</p>
    </div>
    """
    
    plain_content = f"""
    Password Changed Successfully
    
    Hi {user.first_name or user.username},
    
    Your password for Young PG Virtual has been successfully changed.
    
    If you didn't make this change, please contact our support team immediately.
    
    Best regards,
    The Young PG Virtual Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Password change notification sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password change notification to {user.email}: {str(e)}")
        return False
