from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.mail import send_mail
from app.models import PasswordResetToken
from django.conf import settings

class Command(BaseCommand):
    help = 'Send a test password reset email to yourself'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Your email address')
        parser.add_argument('--console', action='store_true', help='Use console backend for testing')

    def handle(self, *args, **options):
        email = options['email']
        use_console = options['console']
        
        if use_console:
            # Temporarily switch to console backend
            original_backend = settings.EMAIL_BACKEND
            settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
            self.stdout.write(self.style.WARNING('📧 Using console backend - email will appear below'))
        
        try:
            # Create or get user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': 'Test',
                    'last_name': 'User'
                }
            )
            
            # Create reset token
            reset_token = PasswordResetToken.create_token(user)
            
            # Send password reset email (simple version)
            reset_url = f"http://127.0.0.1:8000/reset-password/{reset_token.token}/"
            
            try:
                result = send_mail(
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
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                
                result = result > 0  # Convert to boolean
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error sending email: {str(e)}'))
                result = False
            
            if result:
                self.stdout.write(self.style.SUCCESS(f'✅ Password reset email sent to {email}'))
                if not use_console:
                    self.stdout.write('📬 Check your email inbox (and spam folder)')
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to send password reset email to {email}'))
                self.stdout.write('💡 Try using --console flag to test email content')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
        finally:
            if use_console:
                # Restore original backend
                settings.EMAIL_BACKEND = original_backend
