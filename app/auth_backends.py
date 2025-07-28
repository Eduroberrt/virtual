"""
Custom authentication backend that allows users to login with either username or email
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password


class EmailOrUsernameModelBackend(BaseBackend):
    """
    Custom authentication backend that allows login with either username or email
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with either username or email
        """
        if username is None or password is None:
            return None
        
        # Try to find user by username first
        user = None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # If username doesn't exist, try to find by email (normalize to lowercase)
            try:
                # Normalize email to lowercase for comparison
                normalized_email = username.lower().strip()
                user = User.objects.get(email=normalized_email)
            except User.DoesNotExist:
                # Neither username nor email found
                return None
        
        # Check if the password is correct
        if user and user.check_password(password):
            return user
        
        return None
    
    def get_user(self, user_id):
        """
        Get user by ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
