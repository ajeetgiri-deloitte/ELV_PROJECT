from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

class MultiUserAuthBackend(ModelBackend):
    """
    Authenticate against both auth_user (for superadmin) and registration.User tables
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # First: Try auth_user table (for superadmin accessing /admin)
        try:
            from django.contrib.auth.models import User as AuthUser
            user = AuthUser.objects.filter(
                Q(username=username) | Q(email=username)
            ).first()
            
            if user and user.check_password(password):
                return user
        except Exception:
            pass
        
        # Second: Try registration.User table (for regular users)
        try:
            from .models import User as RegistrationUser
            user = RegistrationUser.objects.filter(
                Q(username=username) | Q(email=username)
            ).first()
            
            if user and user.check_password(password):
                return user
        except Exception:
            pass
        
        return None
    
    def get_user(self, user_id):
        """
        Get user from either table by ID
        """
        # Try auth_user table first (for superadmin)
        try:
            from django.contrib.auth.models import User as AuthUser
            user = AuthUser.objects.filter(pk=user_id).first()
            if user:
                return user
        except Exception:
            pass
        
        # Try registration.User table
        try:
            from .models import User as RegistrationUser
            user = RegistrationUser.objects.filter(pk=user_id).first()
            if user:
                return user
        except Exception:
            pass
        
        return None