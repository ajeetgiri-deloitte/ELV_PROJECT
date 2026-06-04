import datetime
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.sessions.models import Session
from .models import ActiveSession

from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from registration.metadata_cleaner import sanitize_file
from io import BytesIO
from django.utils.deprecation import MiddlewareMixin

class AutoLogout(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return

        # Timeout value in seconds
        timeout = getattr(settings, 'SESSION_IDLE_TIMEOUT', 1800)

        last_activity = request.session.get('last_activity')

        now = datetime.datetime.now().timestamp()

        if last_activity and (now - last_activity > timeout):
            from django.contrib.auth import logout
            logout(request)
            request.session.flush()
        else:
            request.session['last_activity'] = now

class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

class RemoveServerHeadersMiddleware:
    """
    Middleware to remove server/software identifying headers from HTTP responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Headers that may leak server info
        headers_to_remove = [
            'Server',
            'X-Powered-By',
            'X-AspNet-Version',
            'X-AspNetMvc-Version'
        ]

        for header in headers_to_remove:
            if header in response:
                del response[header]

        return response
    
class OneSessionPerUserMiddleware:
    """
    Enforces one active session per user for:
      - Admin users (django.contrib.auth.User)  -> user_type='admin'
      - Registration users (tracked via request.session['user_id']) -> user_type='reg'
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_key = request.session.session_key

        # 1) Admin users (Django auth)
        # if request.user.is_authenticated:
        #     active = ActiveSession.objects.filter(
        #         user_type="admin", user_id=request.user.id
        #     ).first()
        #     if active and current_key and active.session_key != current_key:
        #         # This is not the allowed session -> log out & redirect to admin login
        #         logout(request)
        #         return redirect("custom_admin_login")

        # 2) Registration users (your custom users)
        reg_user_id = request.session.get("user_id")
        if reg_user_id:
            active = ActiveSession.objects.filter(
                user_type="reg", user_id=reg_user_id
            ).first()
            if active and current_key and active.session_key != current_key:
                # Flush entire session store for safety and force re-login
                request.session.flush()
                return redirect("home")  # your normal users' login page

        return self.get_response(request)
    
class RestrictAdminToSuperuserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/") and request.user.is_authenticated:
            if not request.user.is_superuser:
                return redirect('/cpcb/')
        return self.get_response(request)
    
    
class MetadataStripMiddleware(MiddlewareMixin):
    """
    Intercepts all file uploads and removes metadata
    before the file reaches views or storage.
    """

    def process_request(self, request):
        if not request.FILES:
            return None

        for key, file in list(request.FILES.items()):
            try:
                sanitized = sanitize_file(file)
                mem = BytesIO(sanitized.read())
                clean_file = InMemoryUploadedFile(
                    mem,
                    field_name=getattr(file, 'field_name', key),
                    name=file.name,
                    content_type=file.content_type,
                    size=mem.getbuffer().nbytes,
                    charset=None
                )
                request.FILES[key] = clean_file
            except Exception as e:
                print(f"[WARN] Failed to clean file {file.name}: {e}")
        return None