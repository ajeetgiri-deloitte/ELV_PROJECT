from django.http import FileResponse, Http404
from django.conf import settings
from django.contrib.auth.decorators import login_required
import os

def secure_media_serve(request, path):
    """
    Secure media serving with conditional authentication
    """
    # Add this temporarily to your view for debugging
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"User: {request.user}")
    print(f"Session: {dict(request.session)}")
    # Normalize path
    relative_path = path.strip('/')
    
    print(f"🔐 Secure media serve called for: {relative_path}")
    print(f"👤 User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    
    # 1. Basic security - prevent directory traversal
    if '..' in relative_path or relative_path.startswith('/'):
        raise Http404("Invalid path")
    
    # 2. Check if this path requires authentication
    requires_auth = should_require_authentication(relative_path)
    user_id = request.session.get('user_id')
    if requires_auth and not user_id:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.path)
    
    # 3. Check file type
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
    file_ext = os.path.splitext(relative_path)[1].lower()
    if file_ext not in allowed_extensions:
        raise Http404("File type not allowed")
    
    # 4. Construct absolute path
    absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    
    # 5. Check if file exists
    if not os.path.exists(absolute_path) or not os.path.isfile(absolute_path):
        raise Http404("File not found")
    
    # 6. Serve the file
    print(f"✅ Serving file: {absolute_path}")
    response = FileResponse(open(absolute_path, 'rb'))
    
    # Optional: Add security headers
    response['X-Content-Type-Options'] = 'nosniff'
    
    return response

def should_require_authentication(relative_path):
    """
    Define which paths require authentication
    """
    # These paths require authentication
    auth_required_patterns = [
        'documents/auth_person_pan/',
        'private/',
        'user_uploads/',
    ]
    
    # These paths are public (no auth required)
    public_patterns = [
        'documents/public/',
        'images/avatars/',
        'uploads/temp/',
    ]
    
    # Check if path matches any auth-required pattern
    requires_auth = any(relative_path.startswith(pattern) for pattern in auth_required_patterns)
    
    # If it's explicitly public, override
    is_public = any(relative_path.startswith(pattern) for pattern in public_patterns)
    
    return requires_auth and not is_public