from django.contrib.sessions.models import Session
from .models import ActiveSession

def ensure_session_key(request):
    """
    Make sure the current request has a session key.
    Django only creates one after the session is saved.
    """
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key

def set_active_session(user_type: str, user_id: int, request) -> None:
    """
    Stores the current session as the only allowed one for this user.
    If a previous session exists, it is deleted immediately.
    """
    current_key = ensure_session_key(request)

    prev = ActiveSession.objects.filter(user_type=user_type, user_id=user_id).first()
    if prev and prev.session_key != current_key:
        # Kill the previous session so the old browser is logged out immediately
        Session.objects.filter(session_key=prev.session_key).delete()

    ActiveSession.objects.update_or_create(
        user_type=user_type,
        user_id=user_id,
        defaults={"session_key": current_key},
    )
    
def mask_email(email):
    if not email or "@" not in email:
        return email
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        masked_name = name[0] + "*" * (len(name) - 1)
    else:
        masked_name = name[:2] + "*" * (len(name) - 2)
    return f"{masked_name}@{domain}"

def mask_phone(phone):
    if not phone or len(phone) < 4:
        return phone
    return "*" * (len(phone) - 2) + phone[-2:]