"""
Security settings for PRODUCTION (strict, HTTPS required).
Use when DEBUG=False and running behind HTTPS (nginx/gunicorn).
"""

# ----------------------------------------------------------------------
# 🔒 Enforce HTTPS
# ----------------------------------------------------------------------
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

# ----------------------------------------------------------------------
# 🔒 HSTS (forces HTTPS in browsers)
# ----------------------------------------------------------------------
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ----------------------------------------------------------------------
# 🔒 Cookies
# ----------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1800  # 30 minutes
CSRF_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_SAMESITE = "Strict"

CSRF_USE_SESSIONS = True
CSRF_COOKIE_AGE = 3600

# ----------------------------------------------------------------------
# 🔒 Security Headers
# ----------------------------------------------------------------------
X_FRAME_OPTIONS = "DENY"  # prevents clickjacking
SECURE_CONTENT_TYPE_NOSNIFF = True  # prevent MIME sniffing
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ----------------------------------------------------------------------
# 🔒 Content Security Policy (CSP)
# ----------------------------------------------------------------------
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ("'self'",),
        "script-src": (
            "'self'",
            "https://cdn.jsdelivr.net",
            "https://code.jquery.com",
        ),
        "style-src": ("'self'", "https://cdn.jsdelivr.net"),
        "img-src": ("'self'", "data:"),
        "font-src": ("'self'", "https://cdn.jsdelivr.net"),
        "frame-ancestors": ("'none'",),
        "object-src": ("'none'",),  # disable Flash/Java/etc
        "base-uri": ("'self'",),  # prevent base tag injection
        "form-action": ("'self'",),  # restrict form submits
    }
}

# ----------------------------------------------------------------------
# 🔒 Additional Security Headers (via middleware)
# ----------------------------------------------------------------------
class AdditionalSecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        
        response["Cross-Origin-Opener-Policy"] = "same-origin"
        response["Cross-Origin-Embedder-Policy"] = "require-corp"
        response["Cross-Origin-Resource-Policy"] = "same-origin"

        
        response["Permissions-Policy"] = (
            "geolocation=(self), microphone=(), camera=(), payment=(), usb=(), "
            "accelerometer=(), autoplay=(), fullscreen=(), magnetometer=(), "
            "midi=(), gyroscope=(), sync-xhr=()"
        )

        
        response["X-Permitted-Cross-Domain-Policies"] = "none"
        response["X-DNS-Prefetch-Control"] = "off"

        
        response["X-XSS-Protection"] = "1; mode=block"
        response["X-Content-Type-Options"] = "nosniff"
        response["Referrer-Policy"] = "same-origin"

        return response
