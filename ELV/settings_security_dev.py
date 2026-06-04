"""
Security settings for local development (no HTTPS).
Use when DEBUG=False but you are running on localhost/127.0.0.1.
"""

# Cookies (not HTTPS-only since dev server is HTTP)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Do not redirect HTTP to HTTPS
SECURE_SSL_REDIRECT = False

# HSTS disabled (only makes sense with HTTPS)
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Safe defaults (keep enabled)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1800  # 30 minutes

CSRF_USE_SESSIONS = True
CSRF_COOKIE_AGE = 3600

# CSRF & Session protection
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# Security headers
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"


ADDITIONAL_SECURITY_HEADERS = {
    "Permissions-Policy": "geolocation=(self), microphone=(), camera=()",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
    "Expect-CT": "enforce, max-age=86400",
    "X-Permitted-Cross-Domain-Policies": "none",
    "X-DNS-Prefetch-Control": "off",
    "X-XSS-Protection": "1; mode=block",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
}
SECURE_BROWSER_XSS_FILTER = True

class AdditionalSecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        for header, value in ADDITIONAL_SECURITY_HEADERS.items():
            response[header] = value
        return response

CSP_DIRECTIVES = {
    "default-src": ("'self'",),
    "script-src": ("'self'", "https://cdn.jsdelivr.net", "https://code.jquery.com"),
    "style-src": ("'self'", "https://cdn.jsdelivr.net"),
    "img-src": ("'self'", "data:"),
    "font-src": ("'self'", "https://cdn.jsdelivr.net"),
    "frame-ancestors": ("'none'",),
}
