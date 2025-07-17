from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import PasswordResetToken
from django.core.mail import send_mail
from django.conf import settings
import logging

# Configure logging to show more details
logging.basicConfig(level=logging.DEBUG)

class Command(BaseCommand):
    help = 'Test password reset email sending'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to test with')

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(f"🧪 Testing password reset email for: {email}")
        
        # Show email configuration
        self.stdout.write(f"📧 EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"🌐 EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"👤 EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"📤 DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        try:
            # Test basic email first
            self.stdout.write("\n🔍 Testing basic email...")
            send_mail(
                'Test Email - Basic',
                'This is a basic test email to verify configuration.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("✅ Basic email sent successfully!"))
            
            # Create or get user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0] + '_test',
                    'first_name': 'Test',
                    'last_name': 'User'
                }
            )
            
            if created:
                self.stdout.write(f"👤 Created new user: {user.username}")
            else:
                self.stdout.write(f"👤 Using existing user: {user.username}")
            
            # Create password reset token
            reset_token = PasswordResetToken.create_token(user)
            self.stdout.write(f"🔑 Created reset token: {reset_token.token}")
            
            # Test password reset email
            self.stdout.write("\n🔍 Testing password reset email...")
            
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
                self.stdout.write(self.style.ERROR(f"❌ Error sending email: {str(e)}"))
                result = False
            
            if result:
                self.stdout.write(self.style.SUCCESS("✅ Password reset email sent successfully!"))
                self.stdout.write(f"🔗 Reset URL: {reset_url}")
            else:
                self.stdout.write(self.style.ERROR("❌ Password reset email failed!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())
