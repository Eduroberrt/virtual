"""
Custom email backend with fallback and retry logic
"""
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)

class FallbackEmailBackend(SMTPEmailBackend):
    """
    Email backend that falls back to console output if SMTP fails
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console_backend = ConsoleEmailBackend(*args, **kwargs)
    
    def send_messages(self, email_messages):
        """
        Send email messages with retry logic and fallback
        """
        if not email_messages:
            return 0
        
        # Try SMTP first with retry
        for attempt in range(3):  # 3 attempts
            try:
                logger.info(f"Attempting to send {len(email_messages)} email(s) via SMTP (attempt {attempt + 1})")
                sent_count = super().send_messages(email_messages)
                logger.info(f"Successfully sent {sent_count} email(s) via SMTP")
                return sent_count
            except Exception as e:
                logger.warning(f"SMTP attempt {attempt + 1} failed: {str(e)}")
                if attempt < 2:  # Don't sleep on the last attempt
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        # If SMTP fails, fall back to console output (for development)
        if settings.DEBUG:
            logger.warning("SMTP failed, falling back to console output for debugging")
            return self.console_backend.send_messages(email_messages)
        else:
            logger.error("SMTP failed and not in debug mode, emails not sent")
            return 0
