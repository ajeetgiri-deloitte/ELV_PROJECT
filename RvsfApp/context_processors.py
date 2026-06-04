# context_processors.py
from .models import RvsfRegistration

def certificate_access(request):
    userid = request.session.get("user_id")

    context = {
        'show_certificate_section': False,
        'application_status': None,
        'certificate_issued_date': None,
        'certificate_number': None,
    }

    if userid:
        has_value = RvsfRegistration.objects.filter(
            id=userid,
            attested_certificate__isnull=False
        ).exclude(attested_certificate="").exists()

        context['show_certificate_section'] = has_value

    return context
