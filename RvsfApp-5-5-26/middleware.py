import datetime
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class AutoLogout(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return

        # Timeout value in seconds
        timeout = getattr(settings, 'SESSION_IDLE_TIMEOUT', 10)

        last_activity = request.session.get('last_activity')

        now = datetime.datetime.now().timestamp()

        if last_activity and (now - last_activity > timeout):
            from django.contrib.auth import logout
            logout(request)
            request.session.flush()
        else:
            request.session['last_activity'] = now
