import os, base64, json, subprocess, re, time, uuid, pdfkit, urllib3, hashlib, openpyxl, logging, string, requests, random, secrets, imaplib, smtplib
from .forms import *
from .models import *
from SpcbApp.models import *
from django.views import View
from RvsfApp.urls import *
from RvsfApp.views import *
from CpcbApp.models import *
from Transfer_Certificate.models import *
from django.db import transaction

from django.conf import settings
from sendgrid.helpers.mail import Mail, Email, To

from django.db import IntegrityError

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, FileResponse, Http404, HttpResponseServerError, HttpResponseBadRequest
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model

from django.core.mail import send_mail
from datetime import timedelta, datetime, timezone
from django.utils import timezone

from django.contrib.auth.hashers import check_password, make_password
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
# from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from pytz import timezone
User = get_user_model()
from django.db.models import Count, Q, Sum, Max
from collections import defaultdict
logger = logging.getLogger('sanskar')

from jose.exceptions import JWTError
from jose import jwt
import django.utils.timezone as dj_timezone
from django.contrib.auth.hashers import check_password as django_check_password
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse

from .session_utils import set_active_session
# EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'
# MOBILE_REGEX = r'^[0-9]\d{9}$'  
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
MOBILE_REGEX = r'^[6-9]\d{9}$'
MAX_OTP_REQUESTS = 5      # Max OTP requests per period
OTP_REQUEST_PERIOD = 3600 # 1 hour in seconds
MAX_OTP_ATTEMPTS = 5      # Max verification attempts per OTP
OTP_EXPIRY = 900

from django.contrib.auth.decorators import login_required
from .session_utils import set_active_session, mask_email, mask_phone
from cryptography.fernet import Fernet

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

# import redis

from django.core.cache import cache
from django.utils.crypto import get_random_string
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timezone

aware_now = datetime.now(timezone.utc)
from datetime import datetime
from zoneinfo import ZoneInfo
from django_ratelimit.decorators import ratelimit
from .validators import validate_uploaded_file, secure_filename
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

import os
import ssl
import urllib3
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import certifi

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64

from django.core import signing

from django.http import JsonResponse
from ELV.whatsapp_api import WhatsAppService

from utils.email_services import *

# @login_required
# def protected_file(request, path):
#     file_path = os.path.join(settings.MEDIA_ROOT, path)
    
#     if not os.path.exists(file_path):
#         raise Http404("File not found")

#     # Optional: Add per-user or per-object permission checks here
#     return FileResponse(open(file_path, 'rb'), as_attachment=False)

# def protected_file(request, path):
#     user_id = request.session.get('admin_user_id')
#     if not request.user.is_authenticated and not user_id:
#         return redirect('custom_admin_login')  # or user login if preferred

#     file_path = os.path.join(settings.MEDIA_ROOT, path)
#     if not os.path.exists(file_path):
#         raise Http404("File not found")

#     return FileResponse(open(file_path, 'rb'), as_attachment=False)

def protected_file(request, path):
    logger.info("Entering protected_file function")
    logger.info(f"Requested file path: {path}")
    
    # Check for either admin or producer login
    logger.info("Retrieving session information")
    admin_id = request.session.get('admin_user_id')
    producer_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    logger.info(f"admin_id: {admin_id}, producer_id: {producer_id}, user_role: {user_role}")
    
    # if neither producer nor admin logged in
    logger.info("Checking if user is authenticated")
    if not admin_id and not producer_id:
        logger.info("Neither admin nor producer is logged in")
        # Redirect based on role (default to producer login)
        logger.info(f"Checking user_role for redirect: {user_role}")
        if user_role == 'producer':
            logger.info("User role is producer - redirecting to producer_login")
            return redirect('producer_login')  # use your producer login view name
        else:
            logger.info("User role is not producer - redirecting to custom_admin_login")
            # return redirect('custom_admin_login')
    logger.info("User is authenticated")

    # File access
    logger.info(f"Constructing full file path from MEDIA_ROOT: {settings.MEDIA_ROOT}")
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    logger.info(f"Full file path: {file_path}")
    
    logger.info("Checking if file exists")
    if not os.path.exists(file_path):
        logger.info(f"File not found at path: {file_path}")
        raise Http404("File not found")
    logger.info("File exists")

    logger.info("Opening file and returning FileResponse")
    return FileResponse(open(file_path, 'rb'), as_attachment=False)

# def protected_file(request, path):
#     # Check for either admin or producer login
#     admin_id = request.session.get('admin_user_id')
#     producer_id = request.session.get('user_id')
#     user_role = request.session.get('user_role')
    
#     # if neither producer nor admin logged in
#     if not admin_id and not producer_id:
#         # Redirect based on role (default to producer login)
#         if user_role == 'producer':
#             return redirect('producer_login')  # use your producer login view name
#         else:
#             return redirect('custom_admin_login')

#     # File access
#     file_path = os.path.join(settings.MEDIA_ROOT, path)
#     if not os.path.exists(file_path):
#         raise Http404("File not found")

#     return FileResponse(open(file_path, 'rb'), as_attachment=False)


def decrypt_aes(encrypted_text):
    key = b"16charSecretKey!"  # same as client
    iv = b"16charSecretIV!!"   # same as client
    encrypted_bytes = base64.b64decode(encrypted_text)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
    # remove PKCS7 padding
    pad_len = decrypted_padded[-1]
    return decrypted_padded[:-pad_len].decode('utf-8')


def save_cookie_consent(request):
    if request.method == "POST" and request.user.is_authenticated:
        data = json.loads(request.body)
        consent = data.get("consent", False)
        # Save consent to user's profile or a model
        # Example: request.user.profile.cookies_accepted = consent
        # request.user.profile.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)


#----------------------------------------------------- Common Functions --------------------------------------------------------#

# def custom_404_view(request, exception=None):
#     # messages.warning(request, "Page not found.")
#     return render(request,"404.html")

def custom_404_view(request, exception=None):
    home_url = reverse("home")  # default
    # print(request.session.get("user_id"))
    # print("asdasda")
    # print(request.session.get("user_role"))
    # print("sadasd")
    
    if request.session.get("user_id"):   # user is logged in
        role = request.session.get("user_role")
        
        if role == "producer":
            home_url = reverse("producer_dashboard")
        elif role == "rvsf":
            home_url = reverse("rvsf_dashboard")
        elif role == "consumer":
            home_url = reverse("consumer_dashboard")
    
    return render(request, "404.html", {"home_url": home_url}, status=404)

def custom_500_view(request):
    # messages.warning(request, "Page not found.")
    return redirect('home')   # redirect for 500

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # Fallback to default if None or empty
    if not ip:
        ip = '10.24.84.232'
    
    return ip

# def get_client_ip(request):
#     return request.META.get('REMOTE_ADDR', '127.0.0.1')
#     # return request.META.get('REMOTE_ADDR', '10.24.84.232')

def load_districts(request):
    state_id = request.GET.get('state_id')
    districts = District.objects.filter(state_id=state_id).values('city_id', 'city_name')
    return JsonResponse(list(districts), safe=False)  # Send data as JSON

def generate_password():
    length = 10  # You can adjust the default length here
    if length < 8:
        raise ValueError("Password length must be at least 8 characters")

    # Required characters
    upper = random.choice(string.ascii_uppercase)
    digit = random.choice(string.digits)
    special = random.choice('!@#$%^&*()_+-=')
    others = ''.join(random.choices(string.ascii_letters + string.digits, k=length - 3))

    # Combine and shuffle
    password_list = list(upper + digit + special + others)
    random.shuffle(password_list)
    return ''.join(password_list)

def convert_defaultdict_to_dict(d):
    if isinstance(d, defaultdict):
        return {k: convert_defaultdict_to_dict(v) for k, v in d.items()}
    elif isinstance(d, dict):
        return {k: convert_defaultdict_to_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [convert_defaultdict_to_dict(i) for i in d]
    else:
        return d
    

def send_dh_application(mobile_no):
    whatsapp = WhatsAppService()

    response = whatsapp.send_template(
        number=mobile_no,
        template_name="dh_new_application",
        components=[]
    )

    return JsonResponse(response)


def send_sms_otp_direct(number, otp):
    """
    Send OTP via the updated SMS API
    """
    print("Send OTP via the updated SMS API")
    # API credentials & configuration
    username = "CPCB_IT"
    password = "Smscpcb#2026"
    senderid = "CPCBEL"
    dept_secure_key = "106a9ed9-00c4-442d-a857-3447d308c9d9"
    templateid = "1307175188767634262"
    entity_id = "1301158798803147760"

    # OTP message
    message = (
        f"Dear User, Your OTP for signing up on the ELV EPR Portal is {otp}. Please enter this code to proceed with the signup process. Do not share this OTP with anyone. Regards, CPCB."
    )

    # Encrypt password
    encrypted_password = hashlib.sha1(password.strip().encode()).hexdigest()

    # Generate key for request
    key_string = f"{username.strip()}{senderid.strip()}{message.strip()}{dept_secure_key.strip()}"
    key = hashlib.sha512(key_string.encode()).hexdigest()

    # API payload
    payload = {
        "username": username.strip(),
        "password": encrypted_password,
        "senderid": senderid.strip(),
        "content": message.strip(),
        "smsservicetype": "singlemsg",
        "mobileno": number.strip(),
        "key": key,
        "templateid": templateid.strip(),
        "entityid": entity_id.strip(),
    }

    try:
        # ✅ Send request to NEW API endpoint
        test_url = "https://msdgweb.mgov.gov.in/esms/sendsmsrequestDLT"
        response = requests.post(test_url, data=payload, timeout=10)

        print("API Raw Response (repr):", repr(response.text))
        print("Status code:", response.status_code)
        print("Request Payload Sent:", payload)
        print("API Response Code:", response.status_code)
        print("API Response Text:", response.text)

        return response.text

    except requests.RequestException as e:
        print("Failed to send OTP:", str(e))
        return f"API call failed: {str(e)}"

def send_signup_sms(number):
    
    print("Send Signup Successfully message via the updated SMS API")
    # API credentials & configuration
    username = "CPCB_IT"
    password = "Smscpcb#2026"
    senderid = "CPCBEL"
    dept_secure_key = "106a9ed9-00c4-442d-a857-3447d308c9d9"
    templateid = "1307175188769642964"
    entity_id = "1301158798803147760"

    # Signup Successfully message
    message = (
        f"Dear User, You have successfully signed up on the ELV EPR Portal. Please check your registered company email id for login credentials. Regards, CPCB."
    )

    # Encrypt password
    encrypted_password = hashlib.sha1(password.strip().encode()).hexdigest()

    # Generate key for request
    key_string = f"{username.strip()}{senderid.strip()}{message.strip()}{dept_secure_key.strip()}"
    key = hashlib.sha512(key_string.encode()).hexdigest()

    # API payload
    payload = {
        "username": username.strip(),
        "password": encrypted_password,
        "senderid": senderid.strip(),
        "content": message.strip(),
        "smsservicetype": "singlemsg",
        "mobileno": number.strip(),
        "key": key,
        "templateid": templateid.strip(),
        "entityid": entity_id.strip(),
    }

    try:
        # ✅ Send request to NEW API endpoint
        test_url = "https://msdgweb.mgov.gov.in/esms/sendsmsrequestDLT"
        response = requests.post(test_url, data=payload, timeout=10)

        print("API Raw Response (repr):", repr(response.text))
        print("Status code:", response.status_code)
        print("Request Payload Sent:", payload)
        print("API Response Code:", response.status_code)
        print("API Response Text:", response.text)

        return response.text

    except requests.RequestException as e:
        print("Failed to send OTP:", str(e))
        return f"API call failed: {str(e)}"

def send_login_otp_sms(number, otp):
    """
    Send OTP via the updated SMS API
    """
    print("Send OTP via the updated SMS API")
    # API credentials & configuration
    username = "CPCB_IT"
    password = "Smscpcb#2026"
    senderid = "CPCBEL"
    dept_secure_key = "106a9ed9-00c4-442d-a857-3447d308c9d9"
    templateid = "1307175188771815034"
    entity_id = "1301158798803147760"

    # OTP message
    message = (
        f"Dear User, Your OTP for logging into the ELV EPR Portal is {otp}. Please enter this code to complete the login process. Do not share this OTP with anyone. Regards, CPCB."
    )

    # Encrypt password
    encrypted_password = hashlib.sha1(password.strip().encode()).hexdigest()

    # Generate key for request
    key_string = f"{username.strip()}{senderid.strip()}{message.strip()}{dept_secure_key.strip()}"
    key = hashlib.sha512(key_string.encode()).hexdigest()

    # API payload
    payload = {
        "username": username.strip(),
        "password": encrypted_password,
        "senderid": senderid.strip(),
        "content": message.strip(),
        "smsservicetype": "singlemsg",
        "mobileno": number.strip(),
        "key": key,
        "templateid": templateid.strip(),
        "entityid": entity_id.strip(),
    }

    try:
        # ✅ Send request to NEW API endpoint
        test_url = "https://msdgweb.mgov.gov.in/esms/sendsmsrequestDLT"
        response = requests.post(test_url, data=payload, timeout=10)

        print("API Raw Response (repr):", repr(response.text))
        print("Status code:", response.status_code)
        print("Request Payload Sent:", payload)
        print("API Response Code:", response.status_code)
        print("API Response Text:", response.text)

        return response.text

    except requests.RequestException as e:
        print("Failed to send OTP:", str(e))
        return f"API call failed: {str(e)}"

def send_registered_sms(number):
    
    print("Send Registered Successfully message via the updated SMS API")
    # API credentials & configuration
    username = "CPCB_IT"
    password = "Smscpcb#2026"
    senderid = "CPCBEL"
    dept_secure_key = "106a9ed9-00c4-442d-a857-3447d308c9d9"
    templateid = "1307175188773441600"
    entity_id = "1301158798803147760"

    # Registered Successfully message
    message = (
        f"Dear User, You have successfully submitted the application for Registration on ELV EPR Portal. Your application is currently under review at CPCB. Regards, CPCB."
    )

    # Encrypt password
    encrypted_password = hashlib.sha1(password.strip().encode()).hexdigest()

    # Generate key for request
    key_string = f"{username.strip()}{senderid.strip()}{message.strip()}{dept_secure_key.strip()}"
    key = hashlib.sha512(key_string.encode()).hexdigest()

    # API payload
    payload = {
        "username": username.strip(),
        "password": encrypted_password,
        "senderid": senderid.strip(),
        "content": message.strip(),
        "smsservicetype": "singlemsg",
        "mobileno": number.strip(),
        "key": key,
        "templateid": templateid.strip(),
        "entityid": entity_id.strip(),
    }

    try:
        # ✅ Send request to NEW API endpoint
        test_url = "https://msdgweb.mgov.gov.in/esms/sendsmsrequestDLT"
        response = requests.post(test_url, data=payload, timeout=10)

        print("API Raw Response (repr):", repr(response.text))
        print("Status code:", response.status_code)
        print("Request Payload Sent:", payload)
        print("API Response Code:", response.status_code)
        print("API Response Text:", response.text)

        return response.text

    except requests.RequestException as e:
        print("Failed to send OTP:", str(e))
        return f"API call failed: {str(e)}"

def send_query_sms(number):
    
    print("Send Query message via the updated SMS API")
    # API credentials & configuration
    username = "CPCB_IT"
    password = "Smscpcb#2026"
    senderid = "CPCBEL"
    dept_secure_key = "106a9ed9-00c4-442d-a857-3447d308c9d9"
    templateid = "1307175188774978199"
    entity_id = "1301158798803147760"

    # Query message
    message = (
        f"Dear User, Your application has been reviewed. Please check the ELV EPR Portal and provide the requisite information. Regards, CPCB."
    )

    # Encrypt password
    encrypted_password = hashlib.sha1(password.strip().encode()).hexdigest()

    # Generate key for request
    key_string = f"{username.strip()}{senderid.strip()}{message.strip()}{dept_secure_key.strip()}"
    key = hashlib.sha512(key_string.encode()).hexdigest()

    # API payload
    payload = {
        "username": username.strip(),
        "password": encrypted_password,
        "senderid": senderid.strip(),
        "content": message.strip(),
        "smsservicetype": "singlemsg",
        "mobileno": number.strip(),
        "key": key,
        "templateid": templateid.strip(),
        "entityid": entity_id.strip(),
    }

    try:
        # ✅ Send request to NEW API endpoint
        test_url = "https://msdgweb.mgov.gov.in/esms/sendsmsrequestDLT"
        response = requests.post(test_url, data=payload, timeout=10)

        print("API Raw Response (repr):", repr(response.text))
        print("Status code:", response.status_code)
        print("Request Payload Sent:", payload)
        print("API Response Code:", response.status_code)
        print("API Response Text:", response.text)

        return response.text

    except requests.RequestException as e:
        print("Failed to send OTP:", str(e))
        return f"API call failed: {str(e)}"


# class GenerateOTPView(View):
#     def post(self, request):
#         data = json.loads(request.body)
#         otp_type = data.get('otp_type')
#         authorization = data.get('authorization')

#         if not authorization:
#             return JsonResponse({'success': False, 'message': 'Please provide authorization (email or mobile).'})

        
#         # Validate email or mobile
#         if re.match(EMAIL_REGEX, authorization):
#             try:
#                 validate_email(authorization)
#             except ValidationError:
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'Invalid email format. Please enter a valid email.'
#                 })
#             contact_type = 'email'
#         elif re.match(MOBILE_REGEX, authorization):
#             contact_type = 'mobile'
#         else:
#             return JsonResponse({'success': False, 'message': 'Invalid email or mobile.'})
        
        
#         if contact_type == 'email':
#             try:
#                 validate_email(authorization)  # raises ValidationError if invalid
#             except ValidationError:
#                 messages.error(request, "Invalid email format.")
#                 return redirect('signup')

#         # Fetch or create OTP record
#         # otp_record, created = OTP.objects.get_or_create(type=otp_type, authorization=authorization)

#         # Generate and save OTP
#         # otp_record.generate_otp()
#         otp = str(random.randint(100000, 999999))
#         # otp="123456"
#         cache.set(f"otp_{otp_type}", otp, timeout=300)
#         from_email = settings.DEFAULT_FROM_EMAIL

#         try:
#             if contact_type == 'email':
#                 # pass
#                 # send_mail(
#                 #     subject=f'Your OTP for {otp_type.replace("_", " ")}',
#                 #     message=f'Your OTP is: {otp_record.otp} (Valid for 15 minutes)',
#                 #     from_email=from_email,
#                 #     recipient_list=[authorization],
#                 #     fail_silently=False,
#                 # )
#                 sendtitanemail('', authorization, otp)
#             elif contact_type == 'mobile':
#                 # send_sms_otp_direct(authorization, otp_record.otp)
#                 # send_sms_otp_direct(authorization, "123456")
#                 send_sms_otp_direct(authorization, otp)
#                 # pass
                

#             return JsonResponse({'success': True, 'message': 'OTP sent successfully.'})
#         except Exception as e:
#             return JsonResponse({'success': False, 'message': f'Error sending OTP: {str(e)}'})

# class VerifyOTPView(View):
#     def post(self, request):
#         data = json.loads(request.body)
#         otp_type = data.get('otp_type')
#         authorization = data.get('authorization')
#         entered_otp = data.get('otp')
        
#         stored_otp = cache.get(f"otp_{otp_type}")

#         if not authorization or not entered_otp:
#             return JsonResponse({'success': False, 'message': 'Please provide authorization and OTP'})

#         # otp_record = get_object_or_404(OTP, type=otp_type, authorization=authorization)

#         # Check if OTP has expired
#         # if dj_timezone.now() > otp_record.otp_expires_at:
#         #     otp_record.delete()  # Delete expired OTP
#         #     return JsonResponse({'success': False, 'message': 'OTP has expired'})

#         # Verify OTP
#         # if entered_otp == otp_record.otp:
#         #     otp_record.delete()  # Delete OTP after successful verification

#         if stored_otp == entered_otp:
#             cache.delete(f"otp_{otp_type}")
#             return JsonResponse({'success': True, 'message': 'OTP verified successfully'})
#         elif stored_otp is None:
#             messages.error(request, 'OTP expired or not found')
#             return redirect('signup')
#         else:
#             return JsonResponse({'success': False, 'message': 'Invalid OTP'})

# ---------------------------New OTP generation ------------------------------------------------------#
# class GenerateOTPView(View):
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#         except json.JSONDecodeError:
#             return JsonResponse({'success': False, 'message': 'Invalid JSON.'})

#         otp_type = data.get('otp_type')
#         authorization = data.get('authorization', '').strip().lower()

#         if not authorization:
#             return JsonResponse({'success': False, 'message': 'Please provide authorization (email or mobile).'})

#         # Determine contact type and validate
#         contact_type = None
#         if re.match(EMAIL_REGEX, authorization):
#             try:
#                 validate_email(authorization)
#                 contact_type = 'email'
#             except ValidationError:
#                 return JsonResponse({'success': False, 'message': 'Invalid email format.'})
#         elif re.match(MOBILE_REGEX, authorization):
#             contact_type = 'mobile'
#         else:
#             return JsonResponse({'success': False, 'message': 'Invalid email or mobile number.'})

#         # Rate limiting OTP requests
#         cache_key_requests = f"otp_requests_{authorization}"
#         request_count = cache.get(cache_key_requests, 0)
#         if request_count >= MAX_OTP_REQUESTS:
#             return JsonResponse({'success': False, 'message': 'You have requested OTP too many times. Please try again after 1 hour.'})
#         cache.set(cache_key_requests, request_count + 1, timeout=OTP_REQUEST_PERIOD)

#         # Generate OTP and store in cache
#         otp = str(random.randint(100000, 999999))
#         cache_key_otp = f"otp_{otp_type}_{authorization}"
#         cache.set(cache_key_otp, otp, timeout=OTP_EXPIRY)  # OTP valid for 5 minutes

#         # Reset verification attempts
#         cache_key_attempts = f"otp_attempts_{authorization}_{otp_type}"
#         cache.set(cache_key_attempts, 0, timeout=OTP_EXPIRY)

#         # Send OTP via email or mobile
#         try:
#             if contact_type == 'email':
#                 sendtitanemail('', authorization, otp)  # replace with your email function
#             elif contact_type == 'mobile':
#                 send_sms_otp_direct(authorization, otp)  # replace with your SMS function

#             return JsonResponse({'success': True, 'message': f'OTP sent successfully to your {contact_type}.'})
#         except Exception as e:
#             return JsonResponse({'success': False, 'message': f'Error sending OTP: {str(e)}'})

# ------------------ Verify OTP ------------------ #
# class VerifyOTPView(View):
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#         except json.JSONDecodeError:
#             return JsonResponse({'success': False, 'message': 'Invalid JSON.'})

#         otp_type = data.get('otp_type')
#         authorization = data.get('authorization', '').strip().lower()
#         entered_otp = data.get('otp', '').strip()

#         # Validate input format
#         if not authorization or not entered_otp:
#             return JsonResponse({'success': False, 'message': 'Please provide both authorization and OTP.'})
#         if not entered_otp.isdigit() or len(entered_otp) != 6:
#             return JsonResponse({'success': False, 'message': 'Invalid OTP format.'})

#         cache_key_otp = f"otp_{otp_type}_{authorization}"
#         cache_key_attempts = f"otp_attempts_{authorization}_{otp_type}"

#         stored_otp = cache.get(cache_key_otp)
#         attempts = cache.get(cache_key_attempts, 0)

#         # Check if OTP has expired
#         if stored_otp is None:
#             return JsonResponse({'success': False, 'message': 'OTP expired or not found. Please request a new OTP.'})

#         # Check max verification attempts
#         if attempts >= MAX_OTP_ATTEMPTS:
#             cache.delete(cache_key_otp)
#             cache.delete(cache_key_attempts)
#             return JsonResponse({'success': False, 'message': 'Maximum verification attempts reached. Please request a new OTP.'})

#         # Increment attempt count
#         cache.set(cache_key_attempts, attempts + 1, timeout=OTP_EXPIRY)

#         # Strong verification: exact match and valid authorization
#         if entered_otp == stored_otp:
#             # Delete OTP and attempts immediately
#             cache.delete(cache_key_otp)
#             cache.delete(cache_key_attempts)
#             return JsonResponse({'success': True, 'message': 'OTP verified successfully.'})
#         else:
#             return JsonResponse({'success': False, 'message': 'Invalid OTP. Please try again.'})

# -----------------------------------------------------------------------------------------------------------#
# class GenerateOTPView(View):
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#         except json.JSONDecodeError:
#             return JsonResponse({'success': False, 'message': 'Invalid JSON.'})

#         otp_type = data.get('otp_type')
#         authorization = data.get('authorization', '').strip().lower()

#         if not authorization:
#             return JsonResponse({'success': False, 'message': 'Please provide authorization (email or mobile).'})

#         # Validate email or mobile
#         contact_type = None
#         if re.match(EMAIL_REGEX, authorization):
#             try:
#                 validate_email(authorization)
#                 contact_type = 'email'
#             except ValidationError:
#                 return JsonResponse({'success': False, 'message': 'Invalid email format.'})
#         elif re.match(MOBILE_REGEX, authorization):
#             contact_type = 'mobile'
#         else:
#             return JsonResponse({'success': False, 'message': 'Invalid email or mobile number.'})

#         # Rate limiting OTP requests
#         cache_key_requests = f"otp_requests_{authorization}"
#         request_count = cache.get(cache_key_requests, 0)
#         if request_count >= MAX_OTP_REQUESTS:
#             return JsonResponse({'success': False, 'message': 'You have requested OTP too many times. Please try again after 1 hour.'})
#         cache.set(cache_key_requests, request_count + 1, timeout=OTP_REQUEST_PERIOD)

#         # Generate OTP
#         # otp = str(random.randint(100000, 999999))
#         otp="123456"

#         # Hash OTP with authorization and type
#         hash_input = f"{otp_type}|{authorization}|{otp}"
#         otp_hash = hashlib.sha256(hash_input.encode()).hexdigest()

#         # Store OTP hash in cache
#         cache_key_otp = f"otp_{otp_type}_{authorization}"
#         cache.set(cache_key_otp, otp_hash, timeout=OTP_EXPIRY)

#         # Reset verification attempts
#         cache_key_attempts = f"otp_attempts_{authorization}_{otp_type}"
#         cache.set(cache_key_attempts, 0, timeout=OTP_EXPIRY)

#         # Send OTP
#         try:
#             if contact_type == 'email':
#                 sendtitanemail('','', authorization, otp)
#             elif contact_type == 'mobile':
#                 send_sms_otp_direct(authorization, otp)

#             return JsonResponse({'success': True, 'message': f'OTP sent successfully to your {contact_type}.'})
#         except Exception as e:
#             return JsonResponse({'success': False, 'message': f'Error sending OTP: {str(e)}'})
        
# class VerifyOTPView(View):
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#         except json.JSONDecodeError:
#             return JsonResponse({'success': False, 'message': 'Invalid JSON.'})

#         otp_type = data.get('otp_type')
#         authorization = data.get('authorization', '').strip().lower()
#         entered_otp = data.get('otp', '').strip()

#         if not authorization or not entered_otp:
#             return JsonResponse({'success': False, 'message': 'Please provide both authorization and OTP.'})
#         if not entered_otp.isdigit() or len(entered_otp) != 6:
#             return JsonResponse({'success': False, 'message': 'Invalid OTP format.'})

#         cache_key_otp = f"otp_{otp_type}_{authorization}"
#         cache_key_attempts = f"otp_attempts_{authorization}_{otp_type}"

#         stored_hash = cache.get(cache_key_otp)
#         attempts = cache.get(cache_key_attempts, 0)

#         # Check if OTP has expired
#         if stored_hash is None:
#             return JsonResponse({'success': False, 'message': 'OTP expired or not found. Please request a new OTP.'})

#         # Check max verification attempts
#         if attempts >= MAX_OTP_ATTEMPTS:
#             cache.delete(cache_key_otp)
#             cache.delete(cache_key_attempts)
#             return JsonResponse({'success': False, 'message': 'Maximum verification attempts reached. Please request a new OTP.'})

#         # Increment attempt count
#         cache.set(cache_key_attempts, attempts + 1, timeout=OTP_EXPIRY)

#         # Hash entered OTP with authorization and type
#         entered_hash = hashlib.sha256(f"{otp_type}|{authorization}|{entered_otp}".encode()).hexdigest()

#         if entered_hash == stored_hash:
#             # Success: delete OTP and attempts
#             cache.delete(cache_key_otp)
#             cache.delete(cache_key_attempts)
            
#             # Mark verified in session securely
#             verified_key = f"{otp_type}_verified"
#             request.session[verified_key] = True
#             request.session.modified = True
            
            
#             return JsonResponse({'success': True, 'message': 'OTP verified successfully.'})
#         else:
#             return JsonResponse({'success': False, 'message': 'Invalid OTP. Please try again.'})

class GenerateOTPView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.'})

        # otp_type = data.get('otp_type')
        # authorization = data.get('authorization', '').strip().lower()
        
        otp_type = (data.get('otp_type') or '').strip().lower()
        authorization = (data.get('authorization') or '').strip().lower()

        if not authorization:
            return JsonResponse({'success': False, 'message': 'Authorization required.'})

        # Validate email or mobile
        contact_type = None
        if re.match(EMAIL_REGEX, authorization):
            try:
                validate_email(authorization)
                contact_type = 'email'
            except ValidationError:
                return JsonResponse({'success': False, 'message': 'Invalid email format.'})
        elif re.match(MOBILE_REGEX, authorization):
            contact_type = 'mobile'
        else:
            return JsonResponse({'success': False, 'message': 'Invalid email or mobile.'})
        
        # 🔹 Check if email or mobile already exists in Registration table
        if otp_type == 'company_email':
            if Registration.objects.filter(company_email__iexact=authorization).exists():
                return JsonResponse({'success': False, 'message': 'Company email already registered. Please use another email.'})
        elif otp_type == 'authorized_person_email':
            if Registration.objects.filter(authorized_person_email__iexact=authorization).exists():
                return JsonResponse({'success': False, 'message': 'Authorized person email already registered. Please use another email.'})
        elif otp_type == 'authorized_person_mobile':
            if Registration.objects.filter(authorized_person_mobile__iexact=authorization).exists():
                return JsonResponse({'success': False, 'message': 'Authorized person mobile already registered. Please use another mobile number.'})
        
        
        # 🔹 NEW: Block disposable emails before sending OTP
        if contact_type == 'email' and is_disposable_email(authorization):
            return JsonResponse({
                'success': False,
                'message': 'Fake emails are not allowed. Please use a valid email.'
            })

        # Rate limiting OTP requests
        cache_key_requests = f"otp_requests_{authorization}"
        request_count = cache.get(cache_key_requests, 0)
        if request_count >= MAX_OTP_REQUESTS:
            return JsonResponse({'success': False, 'message': 'OTP request limit exceeded. Try again in 1 hour.'})
        cache.set(cache_key_requests, request_count + 1, timeout=OTP_REQUEST_PERIOD)

        # Generate OTP
        otp = str(random.randint(100000, 999999))  # remove hardcoded 123456
        # otp="123456"
        otp_hash = hashlib.sha256(f"{otp_type}|{authorization}|{otp}".encode()).hexdigest()

        # Store OTP hash securely in cache
        cache.set(f"otp_{otp_type}_{authorization}", otp_hash, timeout=OTP_EXPIRY)
        cache.set(f"otp_attempts_{otp_type}_{authorization}", 0, timeout=OTP_EXPIRY)

        # Send OTP
        try:
            if contact_type == 'email':
                # sendtitanemail('', '', authorization, otp)
                sendOtpEmail('', '', authorization, otp)
            else:
                send_sms_otp_direct(authorization, otp)

            return JsonResponse({'success': True, 'message': f'OTP sent to your {contact_type}.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error sending OTP: {str(e)}'})

class VerifyOTPView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.'})

        # otp_type = data.get('otp_type')
        # authorization = data.get('authorization', '').strip().lower()
        otp_type = (data.get('otp_type') or '').strip().lower()
        authorization = (data.get('authorization') or '').strip().lower()
        entered_otp = data.get('otp', '').strip()

        if not authorization or not entered_otp:
            return JsonResponse({'success': False, 'message': 'Authorization and OTP required.'})
        if not entered_otp.isdigit() or len(entered_otp) != 6:
            return JsonResponse({'success': False, 'message': 'Invalid OTP format.'})

        cache_key_otp = f"otp_{otp_type}_{authorization}"
        cache_key_attempts = f"otp_attempts_{otp_type}_{authorization}"

        stored_hash = cache.get(cache_key_otp)
        attempts = cache.get(cache_key_attempts, 0)

        if stored_hash is None:
            return JsonResponse({'success': False, 'message': 'OTP expired or not found.'})

        if attempts >= MAX_OTP_ATTEMPTS:
            cache.delete(cache_key_otp)
            cache.delete(cache_key_attempts)
            return JsonResponse({'success': False, 'message': 'Maximum OTP attempts reached.'})

        entered_hash = hashlib.sha256(f"{otp_type}|{authorization}|{entered_otp}".encode()).hexdigest()

        if entered_hash == stored_hash:
            # Mark verified securely
            cache.set(f"otp_verified_{otp_type}_{authorization}", True, timeout=OTP_EXPIRY)
            cache.delete(cache_key_otp)
            cache.delete(cache_key_attempts)
            return JsonResponse({'success': True, 'message': 'OTP verified successfully.'})
        else:
            cache.set(cache_key_attempts, attempts + 1, timeout=OTP_EXPIRY)
            return JsonResponse({'success': False, 'message': 'Invalid OTP. Try again.'})


Send_Grid_Api_Key="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"

def sendtitanemail(name, username, email_id, otp):
    # Disable SSL warnings for development (not recommended for production)
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Prepare the email
    message = Mail(
        from_email='kumar.ashish.cpcb@gmail.com',  # Your verified sender email in SendGrid
        to_emails=email_id,
        subject='One Time Password for End of Life Vehicle',
        # plain_text_content=f'Dear {username}, Your OTP for verification on the ELV EPR Portal is {otp}. Please enter this code to proceed with the verification process. Do not share this OTP with anyone. Regards, CPCB.',
        html_content=f"""
                <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <p>Dear <strong>{username}</strong>,</p>

                    <p>Your One-Time Password (OTP) for verification on the <strong>ELV EPR Portal</strong> is:</p>

                    <p style="font-size: 20px; font-weight: bold; color: #2a7ae2; margin: 10px 0;">
                        {otp}
                    </p>

                    <p>Please enter this code to proceed with the verification process.<br>
                    <b>Do not share this OTP with anyone.</b></p>

                    <p>Regards,<br>
                    Central Pollution Control Board (CPCB)</p>
                </div>
                """
    )

    # Send the email
    try:
        sg = SendGridAPIClient(api_key=Send_Grid_Api_Key)
        response = sg.send(message)
        print(f"Email sent successfully. Status Code: {response.status_code}")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return HttpResponse(f"Error sending email: {e}")

def sendNewPasswordemail(name, username,auth_email,password):
    # Disable SSL warnings for development (not recommended for production)
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Prepare the email
    message = Mail(
        from_email='kumar.ashish.cpcb@gmail.com',  # Your verified sender email in SendGrid
        to_emails=auth_email,
        subject='Password Changed Successfully EPR End of Life Vehicle',
        html_content=f"""
            <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <p>Dear <strong>{name}</strong>,</p>

                <p>Your password has been successfully changed for the 
                <strong>EPR End of Life Vehicle</strong> portal.</p>

                <div style="background-color: #f5f7fa; border: 1px solid #ddd; border-radius: 6px; padding: 12px; margin: 15px 0;">
                    <p style="margin: 4px 0;"><strong>Username:</strong> {username}</p>
                    <p style="margin: 4px 0;"><strong>Password:</strong> {password}</p>
                </div>

                <p>Please keep these details safe and do not share them with anyone.</p>

                <p>Regards,<br>
                Central Pollution Control Board (CPCB)</p>
            </div>
            """
    )

    # Send the email
    try:
        sg = SendGridAPIClient(api_key=Send_Grid_Api_Key)
        response = sg.send(message)
        print(f"Email sent successfully. Status Code: {response.status_code}")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return HttpResponse(f"Error sending email: {e}")

def sendforgetpwdemail(username, company_email):
    # Disable SSL warnings for development (not recommended for production)
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    user = Registration.objects.filter(username=username, company_email=company_email).first()

    if user:
        # generate new password
        new_password = get_random_string(
            length=8,
            allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        )

        # save hashed password
        user.password = make_password(new_password)
        user.first_login = 0
        
        
        message = Mail(
            from_email='kumar.ashish.cpcb@gmail.com',  # Your verified sender email in SendGrid
            to_emails=company_email,
            subject='Welcome to EPR End of Life Vehicle',
            html_content=f"""
                <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <p>Dear User,</p>

                    <p>Welcome to the <strong>EPR End of Life Vehicle</strong> portal.</p>

                    <p>Your login credentials are as follows:</p>

                    <div style="background-color: #f5f7fa; border: 1px solid #ddd; border-radius: 6px; padding: 12px; margin: 15px 0;">
                        <p style="margin: 4px 0;"><strong>Username:</strong> {username}</p>
                        <p style="margin: 4px 0;"><strong>New Password:</strong> {new_password}</p>
                    </div>

                    <p>Please keep these details safe and do not share them with anyone.</p>

                    <p>Regards,<br>
                    Central Pollution Control Board (CPCB)</p>
                </div>
                """
        )
        
        # Send the email
        try:
            sg = SendGridAPIClient(api_key=Send_Grid_Api_Key)
            response = sg.send(message)
            print(f"Email sent successfully. Status Code: {response.status_code}")
            user.save()
            return True, "New password has been sent to your registered Company email."

        except Exception as e:
            print(f"Error sending email: {e}")
            return HttpResponse(f"Error sending email: {e}")
        
    else:
        return False, "Invalid Username or Email."

def sendsigupemail(name,username,auth_email,password):
    # Disable SSL warnings for development (not recommended for production)
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Prepare the email
    message = Mail(
        from_email='kumar.ashish.cpcb@gmail.com',  # Your verified sender email in SendGrid
        to_emails=auth_email,
        subject='Signup Successfully Completed EPR End of Life Vehicle',
        html_content=f"""
            <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <p>Dear {name},</p>

                <p>Your signup has been successfully completed for the <strong>EPR End of Life Vehicle</strong> portal.</p>

                <p>Your login credentials are as follows:</p>

                <div style="background-color: #f5f7fa; border: 1px solid #ddd; border-radius: 6px; padding: 12px; margin: 15px 0;">
                    <p style="margin: 4px 0;"><strong>Username:</strong> {username}</p>
                    <p style="margin: 4px 0;"><strong>Password:</strong> {password}</p>
                </div>

                <p>Please keep these details safe and do not share them with anyone.</p>

                <p>Regards,<br>
                Central Pollution Control Board (CPCB)</p>
            </div>
            """
    )

    # Send the email
    try:
        sg = SendGridAPIClient(api_key=Send_Grid_Api_Key)
        response = sg.send(message)
        print(f"Email sent successfully. Status Code: {response.status_code}")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return HttpResponse(f"Error sending email: {e}")



# def sendNewPasswordemail(username,auth_email,password):
#     email = auth_email
#     userid = username
#     sender_email = 'cpcbepr@cpcbauditempanelment.co.in'
#     sender_password = 'airtel@123'
#     recipient_email = email
#     subject = 'Password Changed Successfully EPR End of Life Vehicle'
#     body = f"""
#     Dear {username},

#     Your Password has been successfully changed for EPR End of Life Vehicle.

#     Username: {username}
#     Password: {password}

#     Please keep these details safe.
#     """

#     smtp_server = 'smtp.titan.email'
#     smtp_port = 587
#     imap_server = 'imap.titan.email'
#     imap_port = 993

#     return send_email(sender_email, sender_password, recipient_email, subject, body, smtp_port, smtp_server, imap_server, imap_port)


# def sendforgetpwdemail(username, company_email):
#     user = Registration.objects.filter(username=username, company_email=company_email).first()

#     if user:
#         # generate new password
#         new_password = get_random_string(
#             length=8,
#             allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
#         )

#         # save hashed password
#         user.password = make_password(new_password)
#         user.first_login = 0
#         user.save()

#         # send mail
#         subject = "Welcome to EPR End of Life Vehicle"
#         body = f"""
#             Dear User,

#             Your Username and Password for EPR End of Life Vehicle.

#             Username: {username}
#             Password: {new_password}

#             Please keep these details safe.
#             """
#         try:
#             send_mail(
#                 subject,
#                 body,
#                 settings.EMAIL_HOST_USER,
#                 [company_email],
#                 fail_silently=False,
#             )
#             return True, "New password has been sent to your registered email."
#         except Exception as e:
#             return False, f"Error sending email: {str(e)}"

#     else:
#         return False, "Invalid Username or Email."

def sendResetLink(username, company_email, request = None):
    
    # Generate reset token
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = custom_token_generator.make_token(user)

    domain = get_current_site(request).domain if request else "localhost:8000"
    reset_link = f"http://{domain}/custom_reset_password/{uid}/{token}/"
    
    
    email = company_email
    userid = username
    sender_email = 'cpcbepr@cpcbauditempanelment.co.in'
    sender_password = 'airtel@123'
    recipient_email = email
    subject = 'Reset Link for EPR End of Life Vehicle'
    body = f"""
    Dear {username},

    Click on below Link to Reset your password for EPR End of Life Vehicle.

    Username: {username}
    Password: {reset_link}

    Please keep these details safe.
    """

    smtp_server = 'smtp.titan.email'
    smtp_port = 587
    imap_server = 'imap.titan.email'
    imap_port = 993

    return send_email(sender_email, sender_password, recipient_email, subject, body, smtp_port, smtp_server, imap_server, imap_port)

# def sendsigupemail(name,username,auth_email,password):
#     email = auth_email
#     userid = username
#     sender_email = 'cpcbepr@cpcbauditempanelment.co.in'
#     sender_password = 'airtel@123'
#     recipient_email = email
#     subject = 'Signup Successfully Completed EPR End of Life Vehicle'
#     body = f"""
#     Dear {name},

#     Your Signup has been successfully completed for EPR End of Life Vehicle.

#     Username: {username}
#     Password: {password}

#     Please keep these details safe.
#     """

#     smtp_server = 'smtp.titan.email'
#     smtp_port = 587
#     imap_server = 'imap.titan.email'
#     imap_port = 993

#     return send_email(sender_email, sender_password, recipient_email, subject, body, smtp_port, smtp_server, imap_server, imap_port)

# def sendtitanemail(name, username, email_id, otp):
#     email = email_id
#     userid = username
#     sender_email = 'cpcbepr@cpcbauditempanelment.co.in'
#     sender_password = 'airtel@123'
#     recipient_email = email
#     subject = 'One Time Password for End of Life Vehicle'
#     body = 'Dear ' + name +' , Your OTP for verification on the ELV EPR Portal is ' + str(otp) + '. Please enter this code to proceed with the verification process. Do not share this OTP with anyone. Regards, CPCB.'
    
#     # body = 'Your One Time Password for login is '+ str(otp)

#     smtp_server = 'smtp.titan.email'
#     smtp_port = 587
#     imap_server = 'imap.titan.email'
#     imap_port = 993

#     return send_email(sender_email, sender_password, recipient_email, subject, body, smtp_port, smtp_server, imap_server, imap_port)

# def send_email(sender_email, sender_password, recipient_email, subject, body, smtp_port, smtp_server, imap_server, imap_port):
#     message = MIMEText(body, 'plain', 'utf-8')
#     message['From'] = sender_email
#     message['To'] = recipient_email
#     message['Subject'] = Header(subject, 'utf-8')

#     try:
#         smtp_obj = smtplib.SMTP(smtp_server, smtp_port)
#         smtp_obj.starttls()
#         smtp_obj.login(sender_email, sender_password)
#         smtp_obj.sendmail(sender_email, recipient_email, message.as_string())
#         smtp_obj.quit()
#         print('Email sent successfully.')

#         imap_obj = imaplib.IMAP4_SSL(imap_server, imap_port)
#         imap_obj.login(sender_email, sender_password)
#         imap_obj.append('Sent', '',  imaplib.Time2Internaldate(aware_now), message.as_bytes())
#         imap_obj.logout()
#         print('Email appended to "Sent" folder.')

#         return True

#     except smtplib.SMTPException as e:
#         print('Error sending email:', str(e))
#         return False

#     except imaplib.IMAP4.error as e:
#         print('Error appending email to "Sent" folder:', str(e))
#         return False




def check_redis_connection():
    try:
        cache.set("ping_test", "pong", timeout=5)
        value = cache.get("ping_test")
        if value == "pong":
            return True
        else:
            return False, "⚠️ Redis cache not working properly"
    except Exception as e:
        return False



def refresh_captcha(request):
    # Create a new form instance to regenerate the captcha
    form = LoginForm()
    
    # Render the new captcha field HTML and send it as a response
    captcha_html = form['captcha'].as_widget()  # Renders just the captcha widget
    
    return JsonResponse({'captcha_html': captcha_html})

def safe_int(value):
    try:
        return int(value) if value else 0 
    except ValueError:
        return 0
    
def safe_float(value):
    try:
        return float(value) if value else 0.0
    except ValueError:
        return 0.0

@csrf_exempt 
def resend_otp(request):
    if request.method == "POST":
        # Logic to resend OTP here
        print("OTP resend triggered")
        user_id = request.session.get('user_id')
        admin_user_id = request.session.get('admin_user_id')

        if user_id:
            try:
                user = Registration.objects.get(id=user_id)
                # Save to session
                request.session['user_id'] = user.id
                request.session['username'] = user.username

                get_otp = request.session.get('otp')
                created_at_str = request.session.get('otp_created_at')

                if get_otp and created_at_str:
                    created_at = datetime.fromisoformat(created_at_str)
                    if datetime.now() - created_at > timedelta(seconds=60):
                        # Expired
                        del request.session['otp']
                        del request.session['otp_created_at']
                    
                # Generate OTP
                # otp = str(random.randint(100000, 999999))
                otp="123456"
                request.session['otp'] = otp
                print("resend-otp", otp)
                send_sms_otp_direct(user.authorized_person_mobile, otp)


                return render(request, 'auth/otp_verify.html', {'form': ProducerOTPForm()})
                
            except Registration.DoesNotExist:
                messages.error(request, "Invalid username or password.")
        
        elif admin_user_id:
            try:
                admin_user = User.objects.get(id=admin_user_id)
                # Save to session
                request.session['admin_user_id'] = admin_user.id

                get_admin_otp = request.session.get('admin_otp')
                created_at_str = request.session.get('otp_created_at')

                if get_admin_otp and created_at_str:
                    created_at = datetime.fromisoformat(created_at_str)
                    if datetime.now() - created_at > timedelta(seconds=60):
                        # Expired
                        del request.session['admin_otp']
                        del request.session['admin_otp_created_at']
                    
                # Generate OTP
                # otp = str(random.randint(100000, 999999))
                otp="123456"
                request.session['admin_otp'] = otp
                print("admin-resend-otp", otp)
                #send_sms_otp_direct(user.mobile_no, otp)

                return render(request, 'admin/admin_otp_verify.html', {'form': ProducerOTPForm()})
                
            except Registration.DoesNotExist:
                messages.error(request, "Invalid username or password.")

        else:
            messages.error(request, "Invalid captcha.")
    else:
        form = LoginForm()
    return render(request, 'admin/admin_login.html', {'form': form})


# ---------------------------------------------------- Header & Footer Functions ----------------------------------------------------------#

# def national_dashboard(request):
#     # role = request.GET.get('role')
#     role="Producer"
#     # print(role)

#     if not role:
#         raw_bytes = request.body
#         role = None

#         if raw_bytes and raw_bytes.strip():
#             try:
#                 data = json.loads(raw_bytes.decode('utf-8'))
#                 role = data.get('role')
#                 print("Parsed Role:", role)
#             except json.JSONDecodeError as e:
#                 print("Invalid JSON:", e)
#         else:
#             print("No data received")
    
#     if role == "Producer":

#         producer_counts = Registration.objects.aggregate(
#             total_registered=Count('id', filter=Q(status__gte=0)),
#             total_active = Count('id', filter=Q(status__gt=0)),
#             # new_application=Count('id', filter=Q(status=1)),
#             # under_review=Count('id', filter=Q(status=2)),
#             under_review = Count('id', filter=Q(status__in=[1, 2, 4, 5, 8])),
#             incomplete_application=Count('id', filter=Q(status=3)),
#             # for_approval=Count('id', filter=Q(status=4)),
#             # approved_application=Count('id', filter=Q(status=5)),
#             granted_application=Count('id', filter=Q(status=6)),
#             rejected_application=Count('id', filter=Q(status=7)),
#         )
#         # print("producer_counts", producer_counts)

#         return render(request, 'dashboard/national_dashboard.html', {'all_data': producer_counts})

def national_dashboard(request):
    # role = request.GET.get('role')
    role="Producer"
    # print(role)

    if not role:
        raw_bytes = request.body
        role = None

        if raw_bytes and raw_bytes.strip():
            try:
                data = json.loads(raw_bytes.decode('utf-8'))
                role = data.get('role')
                print("Parsed Role:", role)
            except json.JSONDecodeError as e:
                print("Invalid JSON:", e)
        else:
            print("No data received")
    
    if role == "Producer":

        producer_counts = Registration.objects.aggregate(
            total_registered=Count('id', filter=Q(status__gte=0)),
            total_active = Count('id', filter=Q(status__gt=0)),
            # new_application=Count('id', filter=Q(status=1)),
            # under_review=Count('id', filter=Q(status=2)),
            under_review = Count('id', filter=Q(status__in=[1, 2, 4, 5, 8])),
            incomplete_application=Count('id', filter=Q(status=3)),
            # for_approval=Count('id', filter=Q(status=4)),
            # approved_application=Count('id', filter=Q(status=5)),
            granted_application=Count('id', filter=Q(status=6)),
            rejected_application=Count('id', filter=Q(status=7)),
        )
        rvsf_counts=ConfirmApplication.objects.aggregate(
            total_registered=Count('id'),
            total_active = Count('id', filter=Q(appstatus__gt=0)),
            # new_application=Count('id', filter=Q(status=1)),
            # under_review=Count('id', filter=Q(status=2)),
            under_review = Count('id', filter=Q(appstatus__in=[ 1,2,3, 4, 5,6, 8]),incomplete=0),
            incomplete_application=Count('id', filter=Q(incomplete=1)),
            # for_approval=Count('id', filter=Q(status=4)),
            # approved_application=Count('id', filter=Q(status=5)),
            # granted_application=Count('id', filter=Q(appstatus=9)),
            granted_application=Count('id', filter=Q(appstatus=9,certificateattested=1)),
            rejected_application=Count('id', filter=Q(appstatus=7)),
        )
        # print("producer_counts", producer_counts)

        return render(request, 'dashboard/national_dashboard.html', {'all_data': producer_counts,'rvsfdata': rvsf_counts})

def aboutus(request):
    return render(request, 'auth/aboutus.html')


def contact_us(request):
    if request.method == 'POST':
        form = CaptchaForm(request.POST)
        name = request.POST.get('name', '').strip()
        user_email = request.POST.get('email', '').strip()
        designation = request.POST.get('designation', '').strip()
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        phone = request.POST.get('phone', '').strip()

        # Step 1: Validate CAPTCHA
        if not form.is_valid():
            return JsonResponse({'status': 'error', 'message': 'Invalid captcha. Please try again.'})

        # Step 2: Regex validation
        import re, ssl, urllib3
        text_regex = re.compile(r'^[A-Za-z0-9 .,]+$')
        phone_regex = re.compile(r'^\d{10}$')
        email_regex = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')

        # Step 3: Field checks
        if not all([name, user_email, designation, subject, description, phone]):
            return JsonResponse({'status': 'error', 'message': 'All fields are required.'})

        if not email_regex.match(user_email):
            return JsonResponse({'status': 'error', 'message': 'Invalid email format.'})

        if not phone_regex.match(phone):
            return JsonResponse({'status': 'error', 'message': 'Phone number must be 10 digits.'})

        for value, field in [(name, "Name"), (designation, "Designation"), (subject, "Subject"), (description, "Description")]:
            if not text_regex.match(value):
                return JsonResponse({'status': 'error', 'message': f'{field} contains invalid characters.'})

        # Step 4: Send email
        try:
            admin_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <meta charset="UTF-8">
                <title>New Contact Message</title>
                </head>
                <body style="margin:0;padding:0;background:#eef1f5;font-family:Arial,Helvetica,sans-serif;">
                <table width="100%" cellpadding="0" cellspacing="0" style="padding:24px 0;">
                <tr>
                <td align="center">

                <table width="620" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #dfe3eb;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.05);">

                <tr>
                <td style="padding:16px 20px;background:#0b5cff;color:#ffffff;font-size:18px;font-weight:bold;border-radius:8px 8px 0 0;">
                Contact Us – New Submission
                </td>
                </tr>

                <tr>
                <td style="padding:20px;font-size:14px;color:#333333;">

                <table width="100%" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
                <tr>
                <td width="30%" style="font-weight:bold;background:#f5f7fb;border:1px solid #e3e6ec;">Name</td>
                <td style="border:1px solid #e3e6ec;">{name}</td>
                </tr>
                <tr>
                <td style="font-weight:bold;background:#f5f7fb;border:1px solid #e3e6ec;">Email</td>
                <td style="border:1px solid #e3e6ec;">{user_email}</td>
                </tr>
                <tr>
                <td style="font-weight:bold;background:#f5f7fb;border:1px solid #e3e6ec;">Designation</td>
                <td style="border:1px solid #e3e6ec;">{designation}</td>
                </tr>
                <tr>
                <td style="font-weight:bold;background:#f5f7fb;border:1px solid #e3e6ec;">Subject</td>
                <td style="border:1px solid #e3e6ec;">{subject}</td>
                </tr>
                <tr>
                <td style="font-weight:bold;background:#f5f7fb;border:1px solid #e3e6ec;">Phone</td>
                <td style="border:1px solid #e3e6ec;">{phone}</td>
                </tr>
                <tr>
                <td style="font-weight:bold;background:#f5f7fb;border:1px solid #e3e6ec;vertical-align:top;">Message</td>
                <td style="border:1px solid #e3e6ec;">{description}</td>
                </tr>
                </table>

                </td>
                </tr>

                <tr>
                <td style="padding:12px 20px;background:#fafbfc;border-top:1px solid #e3e6ec;font-size:12px;color:#777777;">
                System generated email – Contact Us Form
                </td>
                </tr>

                </table>

                </td>
                </tr>
                </table>
                </body>
                </html>
            """


            user_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <meta charset="UTF-8">
                <title>Message Received</title>
                </head>
                <body style="margin:0;padding:0;background:#eef1f5;font-family:Arial,Helvetica,sans-serif;">
                <table width="100%" cellpadding="0" cellspacing="0" style="padding:24px 0;">
                <tr>
                <td align="center">

                <table width="620" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #dfe3eb;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.05);">

                <tr>
                <td style="padding:16px 20px;background:#0b5cff;color:#ffffff;font-size:18px;font-weight:bold;border-radius:8px 8px 0 0;">
                Thank You for Contacting Us
                </td>
                </tr>

                <tr>
                <td style="padding:22px;font-size:14px;color:#333333;line-height:1.7;">

                <p style="margin:0 0 12px;">Dear <strong>{name}</strong>,</p>

                <p style="margin:0 0 14px;">
                We acknowledge receipt of your message submitted through the Contact Us form.
                </p>

                <table width="100%" cellpadding="10" cellspacing="0" style="background:#f5f7fb;border:1px solid #e3e6ec;border-radius:6px;">
                <tr>
                <td style="font-size:13px;">
                Our team will review your query and respond at the earliest.
                </td>
                </tr>
                </table>

                <p style="margin:18px 0 0;">
                Regards,<br>
                <strong>Central Pollution Control Board</strong>
                </p>

                </td>
                </tr>

                <tr>
                <td style="padding:12px 20px;background:#fafbfc;border-top:1px solid #e3e6ec;font-size:12px;color:#777777;">
                This is an automated confirmation email. Please do not reply.
                </td>
                </tr>

                </table>

                </td>
                </tr>
                </table>
                </body>
                </html>
            """


            # send to admin
            sendContactEmail(
                subject=f"New Contact Us Message: {subject}",
                to_email="eprelv.cpcb@gov.in",
                html_content=admin_html,
            )

            # send confirmation to user
            sendContactEmail(
                subject="Confirmation: Your message has been received",
                to_email=user_email,
                html_content=user_html,
            )

            return JsonResponse({'status': 'success', 'message': 'Your message has been sent successfully!'})

        except Exception as e:
            print("Email Error:", e)
            return JsonResponse({'status': 'error', 'message': 'Error sending email. Please try again later.'})
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

    #     try:
    #         ssl._create_default_https_context = ssl._create_unverified_context
    #         urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    #         sg = SendGridAPIClient(api_key=Send_Grid_Api_Key)

    #         html_content_to_admin = f"""
    #             <div>
    #                 <p><strong>Name:</strong> {name}</p>
    #                 <p><strong>Email:</strong> {user_email}</p>
    #                 <p><strong>Designation:</strong> {designation}</p>
    #                 <p><strong>Subject:</strong> {subject}</p>
    #                 <p><strong>Description:</strong> {description}</p>
    #                 <p><strong>Phone:</strong> {phone}</p>
    #             </div>
    #         """

    #         message_to_admin = Mail(
    #             from_email=Email('kumar.ashish.cpcb@gmail.com'),
    #             to_emails=To('sanskar.cpcb@gmail.com'),
    #             subject=f"New Contact Us Message: {subject}",
    #             html_content=html_content_to_admin
    #         )
    #         message_to_admin.reply_to = Email(user_email)
    #         response = sg.send(message_to_admin)

    #         if response.status_code not in [200, 202]:
    #             return JsonResponse({'status': 'error', 'message': 'Failed to send message. Try again later.'})

    #         # Confirmation mail to user
    #         confirmation_html = f"""
    #             <div>
    #                 <p>Dear {name},</p>
    #                 <p>Thank you for contacting us! We have received your message and will get back to you shortly.</p>
    #                 <p>Regards,<br>CPCB Team</p>
    #             </div>
    #         """
    #         confirmation_email = Mail(
    #             from_email=Email('kumar.ashish.cpcb@gmail.com'),
    #             to_emails=To(user_email),
    #             subject="Confirmation: Your message has been received",
    #             html_content=confirmation_html
    #         )
    #         sg.send(confirmation_email)

    #         return JsonResponse({'status': 'success', 'message': 'Your message has been sent successfully!'})

    #     except Exception as e:
    #         print("Email Error:", e)
    #         return JsonResponse({'status': 'error', 'message': 'Error sending email. Please try again later.'})

    # return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})



def termsAndCondition(request):
    return render(request, 'footer/termsAndCondition.html')

def refundPolicy(request):
    return render(request, 'footer/refundPolicy.html')

def privacyPolicy(request):
    return render(request, 'footer/privacyPolicy.html')



# ---------------------------------------------------------- GST Function -----------------------------------------------------#

def fetch_gst_details(request):
    gst_no = request.GET.get("gst_no", "").strip()
    # print(gst_no)

    if not gst_no or len(gst_no) != 15:
        return JsonResponse({"error": "Please enter a valid 15-digit GST Number"}, status=400)
    
    if Registration.objects.filter(gst_no=gst_no).exists():
        return JsonResponse({"error": "GST Number already registered."}, status=400)
            # errors.append("GST Number is already registered.")

    api_url = "https://apiservices.cpcb.gov.in/gst/details"
    payload = {"gstNo": gst_no}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=20,
            verify=False  # Use certifi.where() if cert issue gets resolved
        )

        if response.status_code == 200:
            try:
                result = response.json()
            except ValueError:
                return JsonResponse({"error": "Invalid JSON response from server"}, status=500)

            if not result.get("status") or "data" not in result:
                return JsonResponse({"error": "GST Number not found or inactive"}, status=404)

            gst_data = result["data"]
            # print(gst_data)

            return JsonResponse({
                "success": True,
                "company_name": gst_data.get("tradeNam", ""),
                "legal_name": gst_data.get("lgnm", ""),
                "business_category": gst_data.get("ctb", ""),
                "gst_no": gst_data.get("gstin", ""),
            })

        return JsonResponse({"error": "Failed to fetch GST details. Please try again later."}, status=500)

    except requests.exceptions.Timeout:
        return JsonResponse({"error": "GST API request timed out"}, status=504)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Error connecting to GST API: {str(e)}"}, status=500)





# ------------------------------------------------------- Registration Section ------------------------------------------------#

def generate_username(gst_number):
    # Get full 4-digit year
    year_str = datetime.now().strftime('%Y')  # e.g., '2025'

    # Get last 2 characters of the GST number
    gst_suffix = gst_number[-2:] if gst_number and len(gst_number) >= 2 else '00'

    # File to store serial number
    sequence_file = 'sequence.txt'

    # Read last sequence from file
    if os.path.exists(sequence_file):
        with open(sequence_file, 'r') as f:
            last_seq = int(f.read().strip())
    else:
        last_seq = 0

    # Increment and store new sequence
    new_seq = last_seq + 1
    with open(sequence_file, 'w') as f:
        f.write(str(new_seq))

    # Pad serial number to 4 digits
    serial_str = str(new_seq).zfill(4)  # e.g., '0003'
    
    # print(f'{year_str}{gst_suffix}{serial_str}')

    # Combine to create username
    return f'P{year_str}{gst_suffix}{serial_str}'



# -------------------------
# Disposable Email Validator
# -------------------------
DISPOSABLE_DOMAINS_FILE = os.path.join(
    os.path.dirname(__file__), 'disposable_domains.txt'
)

def is_disposable_email(email):
    """Check if email's domain is disposable (in blocklist)."""
    if '@' not in email:
        return False

    domain = email.split('@')[-1].strip().lower()

    # Cache list in memory for performance
    if not hasattr(is_disposable_email, "_cache"):
        if not os.path.exists(DISPOSABLE_DOMAINS_FILE):
            # If file missing, skip check safely
            is_disposable_email._cache = set()
        else:
            with open(DISPOSABLE_DOMAINS_FILE, 'r') as f:
                is_disposable_email._cache = {
                    line.strip().lower() for line in f if line.strip()
                }

    return domain in is_disposable_email._cache


# -------------------------
# Registration View
# -------------------------
class RegistrationView(View):

    def get(self, request):
        states = State.objects.all()
        form = CaptchaForm()
        return render(request, 'auth/registration.html', {'states': states, 'form': form})

    def post(self, request):
        states = State.objects.all()
        post_data = request.POST
        form = CaptchaForm(request.POST)
        errors = []
        
        # ------------------ Collect Data ------------------
        entity_list = post_data.getlist('entity[]') or [post_data.get('entity')]
        gst_no = post_data.get("gst_no", "").strip().upper()
        gst_verified_no = post_data.get("gst_verified_no", "").strip().upper()
        company_email = post_data.get('company_email')
        email = post_data.get('authorized_person_email')
        authorized_person_name = post_data.get('authorized_person_name')
        company_name = post_data.get('company_name', '').strip()
        business_category = post_data.get('business_category', '').strip()
        state = post_data.get('state')
        district = post_data.get('district')
        company_pan = post_data.get('pan_no')
        auth_pan = post_data.get('authorized_person_pan')
        authorized_person_mobile = post_data.get('authorized_person_mobile')
        registered_address = post_data.get('registered_address', '').strip()
        
        is_company_email_verified = cache.get(f"otp_verified_company_email_{company_email}", False)
        is_auth_email_verified = cache.get(f"otp_verified_authorized_person_email_{email}", False)
        is_mobile_verified = cache.get(f"otp_verified_authorized_person_mobile_{authorized_person_mobile}", False)

        # ------------------ CAPTCHA ------------------
        if not form.is_valid():
            errors.append("Invalid Captcha. Please try again.")
            for error in errors:
                messages.error(request, error)
            return render(request, 'auth/registration.html', {
                'states': states,
                'form': CaptchaForm(),
                'form_data': post_data,
                'errors': errors,
                'is_company_email_verified': is_company_email_verified,
                'is_auth_email_verified': is_auth_email_verified,
                'is_mobile_verified': is_mobile_verified,
            })


        # ------------------ GST Verification ------------------
        api_url = "https://apiservices.cpcb.gov.in/gst/details"
        payload = {"gstNo": gst_no}
        headers = {"Content-Type": "application/json"}
        
        # Store GST API data for re-rendering
        gst_api_data = {
            'company_name': company_name,
            'legal_name': post_data.get('legal_name', ''),
            'business_category': business_category,
            'gst_verified_no': gst_verified_no
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=20, verify=False)
            if response.status_code == 200:
                result = response.json()
                if not result.get("status") or "data" not in result:
                    errors.append("GST Number not found or inactive.")
                else:
                    gst_data = result["data"]
                    api_gstin = gst_data.get("gstin", "").upper()
                    
                    # If gst_verified_no is empty (form re-render), use the current GST number
                    if not gst_verified_no:
                        gst_verified_no = api_gstin
                    
                    # Check if GST numbers match
                    if gst_no != api_gstin:
                        errors.append("GST Number mismatch. Please fetch GST details again.")
                    elif gst_verified_no and gst_verified_no != api_gstin:
                        errors.append("GST Number mismatch. Please fetch GST details again.")
                    else:
                        # Update the GST verified number to ensure it matches
                        gst_verified_no = api_gstin

                    company_name = gst_data.get("tradeNam", company_name)
                    legal_name = gst_data.get("lgnm", "")
                    business_category = gst_data.get("ctb", business_category)
                    
                    # Update GST API data
                    gst_api_data.update({
                        'company_name': company_name,
                        'legal_name': legal_name,
                        'business_category': business_category,
                        'gst_verified_no': gst_verified_no
                    })
            else:
                errors.append("Failed to fetch GST details from CPCB. Try again later.")
        except requests.exceptions.RequestException as e:
            errors.append(f"Error connecting to GST API: {str(e)}")

        # ------------------ Email Validation ------------------
        context = {'states': states, 'form_data': post_data}

        try:
            validate_email(company_email)
        except ValidationError:
            errors.append("Invalid Company Email format.")

        try:
            validate_email(email)
        except ValidationError:
            errors.append("Invalid Authorized Person Email format.")

        # 🔹 NEW: Check disposable emails
        if is_disposable_email(company_email):
            errors.append("Company Email uses a Fake emails. Please use a valid business email.")
        if is_disposable_email(email):
            errors.append("Authorized Person Email uses a fake emails. Please use a valid email.")

        # ------------------ OTP Verification ------------------

        if company_email and email and company_email.lower() == email.lower():
            errors.append("Company Email and Authorized Person Email should not be same.")

        if not is_company_email_verified:
            errors.append("Company Email OTP not verified.")
        if not is_auth_email_verified:
            errors.append("Authorized Person Email OTP not verified.")
        if not is_mobile_verified:
            errors.append("Mobile OTP not verified.")

        # ------------------ Duplicate Checks ------------------
        if Registration.objects.filter(gst_no=gst_no).exists():
            errors.append("GST Number is already registered.")
        elif not company_name or not business_category:
            errors.append("GST Number not found or inactive.")

        if Registration.objects.filter(company_email=company_email).exists():
            errors.append("Company email already exists.")
        if Registration.objects.filter(authorized_person_email=email).exists():
            errors.append("Authorized person email already exists.")
        if Registration.objects.filter(authorized_person_mobile=authorized_person_mobile).exists():
            errors.append("Authorized person contact already exists.")

        if not state or not district:
            errors.append("State and District are required.")

        # ------------------ Handle Errors ------------------
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'auth/registration.html', {
                'states': states,
                'form': CaptchaForm(),
                'form_data': post_data,
                'entity_selected': entity_list,
                'errors': errors,
                'is_company_email_verified': is_company_email_verified,
                'is_auth_email_verified': is_auth_email_verified,
                'is_mobile_verified': is_mobile_verified,
            })

        # ------------------ Create User ------------------
        username = generate_username(gst_no)
        password = generate_password()
        password_hashed = make_password(password)

        registration = Registration.objects.create(
            company_email=company_email,
            authorized_person_email=email,
            authorized_person_mobile=authorized_person_mobile,
            entity_types=','.join(entity_list),
            gst_no=gst_no,
            company_name=company_name,
            legal_name=post_data.get('legal_name'),
            business_category=business_category,
            registered_address=registered_address,
            state=state,
            district=district,
            pin_code=post_data.get('pin_code'),
            website=post_data.get('website'),
            pan_no=company_pan,
            tin=post_data.get('tin'),
            cin=post_data.get('cin'),
            authorized_person_name=authorized_person_name,
            authorized_person_designation=post_data.get('authorized_person_designation'),
            authorized_person_pan=auth_pan,
            username=username,
            password=password_hashed,
        )

        registration.save()

        # ------------------ Send Credentials ------------------
        try:
            # sendsigupemail(company_name, username, company_email, password)
            # sendsigupemail(authorized_person_name, username, email, password)
            sendSignupEmail(company_name, username, company_email, password)
            sendSignupEmail(authorized_person_name, username, email, password)
            send_signup_sms(authorized_person_mobile)

            # Clear OTP cache
            cache.delete(f"otp_verified_company_email_{company_email}")
            cache.delete(f"otp_verified_authorized_email_{email}")
            cache.delete(f"otp_verified_mobile_{authorized_person_mobile}")

            return render(request, 'auth/registration.html', {'registration_success': True})

        except Exception as e:
            messages.warning(request, f"Registration saved, but failed to send credentials: {e}")
            return redirect('home')



def check_redis_connection():
    try:
        cache.set("ping_test", "pong", timeout=5)
        value = cache.get("ping_test")
        if value == "pong":
            return True
        else:
            return False, "⚠️ Redis cache not working properly"
    except Exception as e:
        return False


def otpviewpage1(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid captcha.")
            return redirect('home')

        # Decrypt username & password
        enc_username = request.POST.get('username')
        enc_password = request.POST.get('password')

        try:
            username = decrypt_aes(enc_username)
            password = decrypt_aes(enc_password)
        except Exception:
            messages.error(request, "Invalid Credentials.")
            return redirect('home')

        # ✅ Fetch user
        user = Registration.objects.filter(username=username).first()
        if not user:
            messages.error(request, "User not found.")
            return redirect('home')

        # ✅ Check password
        if not check_password(password, user.password):
            messages.error(request, "Invalid username or password.")
            return redirect('home')

        # OTP logic (same as your code)
        conn = check_redis_connection()
        if conn == False:
            return HttpResponse('Please try again — Redis not connected.')
        
        stored_otp = cache.get(f"otp_{username}")
        if stored_otp:
            messages.error(request, 'OTP already sent, please wait.')
            return redirect('home')
        
        otp = str(random.randint(100000, 999999))
        cache.set(f"otp_{username}", otp, timeout=120)

        # sendtitanemail(user.company_name, username, user.company_email, otp)
        sendOtpEmail(user.company_name, username, user.company_email, otp)
        send_login_otp_sms(user.authorized_person_mobile, otp)

        return render(request, 'auth/otpverify.html', {
            'username': username,
            'otp': otp,
            'form': LoginForm(),
        })

    return render(request, 'auth/home.html', {'form': LoginForm()})



def verify_otp1(request):
    if request.method == 'POST':
        form = CaptchaForm(request.POST)
        username = request.POST.get('username')
        # raw_pwd = request.POST.get('password')

        # ✅ Decrypt the OTP sent from client
        enc_otp = request.POST.get('enc_otp')
        try:
            entered_otp = decrypt_aes(enc_otp)
        except Exception as e:
            messages.error(request, "OTP decryption failed.")
            return render(request, 'auth/otpverify.html', {
                'username': username,
                # 'password': raw_pwd,
                'form': form,
            })

        # Step 1: Validate captcha
        if not form.is_valid():
            messages.error(request, "Invalid captcha. Please try again.")
            return render(request, 'auth/otpverify.html', {
                'username': username,
                # 'password': raw_pwd,
                'form': form,
            })

        # Step 2: Validate OTP
        stored_otp = cache.get(f"otp_{username}")
        if stored_otp is None:
            messages.error(request, 'OTP expired or not found. Please request a new one.')
            return render(request, 'auth/otpverify.html', {
                'username': username,
                # 'password': raw_pwd,
                'form': form,
            })

        if stored_otp != entered_otp:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, 'auth/otpverify.html', {
                'username': username,
                # 'password': raw_pwd,
                'form': form,
            })

        # Step 3: OTP correct → proceed
        cache.delete(f"otp_{username}")
        try:
            user = Registration.objects.get(username=username)
        except Registration.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('home')
        
        # ✅ Ensure there's a linked Django User
        # django_user, _ = User.objects.get_or_create(
        #     username=user.username,
        #     defaults={
        #         "email": user.company_email,
        #         "first_name": user.authorized_person_name or "",
        #     }
        # )
        
        # try:
        #     django_user, _ = User.objects.update_or_create(
        #         username=user.username,
        #         defaults={
        #             "email": user.company_email,
        #             "first_name": user.authorized_person_name or "",
        #         }
        #     )
        # except IntegrityError:
        #     django_user = User.objects.get(email=user.company_email)
        

        # print(django_user)
        # login(request, django_user, backend='django.contrib.auth.backends.ModelBackend')

        request.session['user_id'] = user.id
        request.session['user_role'] = "producer"
        set_active_session("user", user.id, request)

        if user.first_login == 0:
            return redirect('change_password_first')
        else:
            return redirect('producer_dashboard')

    return redirect('home')



def resend_otp1(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Step 1: Validate user
        try:
            user = Registration.objects.get(username=username)
        except Registration.DoesNotExist:
            return JsonResponse({"status": "error", "message": "User not found."})

        # Step 2: Check if OTP already exists in cache (prevent spam)
        stored_otp = cache.get(f"otp_{username}")
        if stored_otp:
            return JsonResponse({
                "status": "error",
                "message": "OTP already sent. Please wait before requesting again."
            })

        # Step 3: Generate new OTP and store in cache
        otp = str(random.randint(100000, 999999))
        # otp="123456"
        cache.set(f"otp_{username}", otp, timeout=120)  # valid for 2 minutes

        # Step 4: Send OTP via email
        # sendtitanemail(user.company_name, username, user.company_email, otp)
        sendOtpEmail(user.company_name, username, user.company_email, otp)
        send_login_otp_sms(user.authorized_person_mobile, otp)

        return JsonResponse({
            "status": "success",
            "message": "OTP resent successfully."
        })

    return JsonResponse({"status": "error", "message": "Invalid request method."})




# def home(request):
#     if request.method == 'POST':
#         form = LoginForm(request.POST)  

#         if form.is_valid():  
#             username = form.cleaned_data.get('username')
#             input_password = form.cleaned_data.get('password')
            
#             user = Registration.objects.filter(username=username).first()
            
#             if user is not None:  # check if user exists
#                 if check_password(input_password, user.password):
#                     request.session['user_id'] = user.id
#                     request.session['user_role'] = "producer"
#                     set_active_session("user", user.id, request)
                    
#                     if user.first_login == 0:
#                         return redirect('change_password_first')
#                     else:
#                         return redirect('producer_dashboard')
#                 else:
#                     messages.error(request, "Invalid username or password.")
#                     return redirect('home')
#             else:
#                 messages.error(request, "User Not Found.")
#                 return redirect('home')

#         else:
#             messages.error(request, "Invalid captcha.")
#             return render(request, 'auth/home.html', {'form': form})
#     else:
#         form = LoginForm()
#     return render(request, 'auth/home.html', {'form': form})


def home(request):
    form = LoginForm()
    return render(request, 'auth/home.html', {'form': form})

class ChangePasswordFirst(View):

    def get(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Session expired. Please login again.")
            return redirect('login')

        user = Registration.objects.filter(id=user_id).first()
        if not user:
            messages.error(request, "User not found.")
            return redirect('login')

        fresh_count = producerGeneralDetails.objects.filter(application_type=0, forwarded_to=user_id).count()
        resubmit_count = producerGeneralDetails.objects.filter(application_type=1, forwarded_to=user_id).count()
        entitytype_list = user.entity_types.split(',') if user.entity_types else []

        return render(request, 'auth/change_password.html', {
            'url': 'login/change-password',
            'entity_types': [e.strip() for e in entitytype_list],
            'fresh_count': fresh_count,
            'resubmit_count': resubmit_count,
            'form': ProducerOTPForm(),
        })

    def post(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Session expired. Please login again.")
            return redirect('login')
        
        form = CaptchaForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid captcha. Please try again.")
            return redirect('change_password_first')
        
        old_password = new_password = confirm_password = None
        
        enc_oldPassword = request.POST.get('old_password')
        enc_newPassword = request.POST.get('new_password')
        enc_confirmPassword = request.POST.get('confirm_password')
        
        print(enc_oldPassword)
        print(enc_newPassword)
        print(enc_confirmPassword)
        

        try:
            old_password = decrypt_aes(enc_oldPassword)
            new_password = decrypt_aes(enc_newPassword)
            confirm_password = decrypt_aes(enc_confirmPassword)
            
        except Exception:
            messages.error(request, "Passwords not match")
            return redirect('change_password_first')

        # old_password = request.POST.get('old_password')
        # new_password = request.POST.get('new_password')
        # confirm_password = request.POST.get('confirm_password')

        try:
            user = Registration.objects.get(id=user_id)
        except Registration.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('change_password_first')

        if not check_password(old_password, user.password):
            messages.error(request, "Old password is incorrect.")
            return redirect('change_password_first')

        if new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('change_password_first')

        if not self.is_strong_password(new_password):
            messages.error(request, "Password must be at least 8 characters long and include uppercase, lowercase, digit, and special character.")
            return redirect('change_password_first')

        # Check against last 3 passwords
        password_history = json.loads(user.password_history or '[]')
        recent_passwords = [user.password] + password_history[:2]  # current + last 2

        for old_hashed in recent_passwords:
            if check_password(new_password, old_hashed):
                messages.error(request, "New password must not match any of the last 3 passwords.")
                return redirect('change_password_first')

        # Update password
        new_hashed = make_password(new_password)
        updated_history = [user.password] + password_history
        user.password_history = json.dumps(updated_history[:3])
        user.password = new_hashed
        user.first_login=1
        user.save()
        
        # sendNewPasswordemail(user.company_name, user.username, user.company_email, new_password)
        sendNewPasswordEmail(user.company_name, user.username, user.company_email, new_password)
        
        
        request.session['user_id'] = user.id
        request.session['user_role'] = "producer"
        set_active_session("user", user.id, request)

        messages.success(request, "Password changed successfully.")
        return redirect('producer_dashboard')

    def is_strong_password(self, password):
        return (
            len(password) >= 8 and
            re.search(r'[A-Z]', password) and
            re.search(r'[a-z]', password) and
            re.search(r'\d', password) and
            re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
        )


def forget_password(request):
    form = CaptchaForm()  # load captcha for GET
    return render(request, 'auth/forget_password.html', {'form': form})


def reset_password(request):
    """Handle password reset requests with full validation and rate limiting."""
    form = CaptchaForm(request.POST or None)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        company_email = request.POST.get('company_email', '').strip()
        user_ip = get_client_ip(request)

        # === 1️⃣ Validate inputs ===
        if not username or not company_email:
            messages.error(request, "Both username and company email are required.")
            return render(request, 'auth/forget_password.html', {'form': form})

        # === 2️⃣ Validate CAPTCHA ===
        if not form.is_valid():
            messages.error(request, "Invalid CAPTCHA. Please try again.")
            return render(request, 'auth/forget_password.html', {'form': CaptchaForm()})

        # === 3️⃣ Rate Limiting ===
        rate_key_user = f"reset_attempts_user_{username}"
        rate_key_ip = f"reset_attempts_ip_{user_ip}"

        max_attempts = 3
        block_time = 10  # in minutes

        if is_rate_limited(rate_key_user, max_attempts, block_time) or \
           is_rate_limited(rate_key_ip, max_attempts, block_time):
            messages.error(request, "Too many attempts. Please try again later.")
            return render(request, 'auth/forget_password.html', {'form': CaptchaForm()})

        # === 4️⃣ Verify username and email ===
        user = Registration.objects.filter(username=username, company_email=company_email).first()
        if not user:
            messages.error(request, "Invalid username or email address.")
            return render(request, 'auth/forget_password.html', {'form': CaptchaForm()})

        # === 5️⃣ Send password reset email ===
        # success, msg = sendforgetpwdemail(username, company_email)
        success, msg = sendForgetPwdEmail(username, company_email)
        if success:
            messages.success(request, msg)
            return redirect('home')
        else:
            messages.error(request, msg)
            return render(request, 'auth/forget_password.html', {'form': CaptchaForm()})

    # GET → show form
    return render(request, 'auth/forget_password.html', {'form': form})


# ==============================
# 🧠 Helper Functions
# ==============================

def get_client_ip(request):
    """Extract IP address safely from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or "0.0.0.0"


def is_rate_limited(key, max_attempts, block_time):
    """
    Increment rate-limit counter and return True if blocked.
    Uses Django cache (works with Redis or Memcached).
    """
    attempts = cache.get(key, 0)
    if attempts >= max_attempts:
        return True
    else:
        cache.set(key, attempts + 1, timeout=block_time * 60)
        return False

# ------------------------- New Forget Password Logic ---------------------------------------------------------
def forgot_password(request):
    return render(request,"forgot_password/forgot_password.html", {'form': LoginForm()})


# def resetpassword(request):
#     if request.method == 'POST':
#         form = PasswordResetFormCustom(data=request.POST)

#         if form.is_valid():
#             email = form.cleaned_data["email"]
#             # Check if the email exists in the User model
#             users = UserDetails.objects.filter(email=email, is_active=True)  

#             if users.exists():  # If users exist, proceed
#                 for user in users:
#                     # Generate UID and token for secure password reset
#                     uid = urlsafe_base64_encode(force_bytes(user.pk))
#                     token = default_token_generator.make_token(user)

#                     # Build absolute reset link
#                     domain = get_current_site(request).domain
#                     reset_link = f"http://{domain}/custom_reset_password/{uid}/{token}/"
#                     # reset_link = f"http://rempfence_portal/reset_password/{uid}/{token}/"
                    

#                     # Email subject and message
#                     subject = "🔐 Password Reset Request"
#                     message = f"""
#                     Hello {user.first_name} {user.last_name} ({user.username}),

#                     You are requested a password reset for your account. 
#                     Click the link below to reset your password:

#                     {reset_link}

#                     If you did not request this, please ignore this email.

#                     Regards,
#                     REMPFENCE Team
#                     """

#                     # Send email
#                     # send_mail(
#                     #     subject,
#                     #     message,
#                     #     'help.cpcb@gmail.com', 
#                     #     # settings.DEFAULT_FROM_EMAIL,
#                     #     [email],
#                     #     fail_silently=False,
#                     # )

#                 messages.success(request, "Reset link sent successfully to your email!")
#                 return redirect('home')
#             else:
#                 messages.warning(request, "No user found with this email!")
#                 return redirect('forgot_password')

#         messages.warning(request, "Invalid email or captcha!")
#         return redirect('forgot_password')
#         # return render(request, "accounts/auth/forgot_password.html", {'form': form})

#     return redirect('forgot_password')


def resetPassword(request):
    if request.method == 'POST':
        username = request.POST.get("username", "").strip()
        company_email = request.POST.get("company_email", "").strip().lower()

        # === Basic validation ===
        if not username or not company_email:
            messages.error(request, "Both Username and Email are required!")
            return redirect("resetPassword")

        try:
            # Look for matching active user
            user = Registration.objects.get(username=username, company_email=company_email)
        except Registration.DoesNotExist:
            messages.error(request, "No active account found with the given Username and Email!")
            return redirect("resetPassword")

        try:
            sendResetLink(username, company_email, request)
            messages.success(request, "✅ Reset link sent successfully to your email!")
        except Exception as e:
            messages.error(request, f"⚠️ Failed to send reset email: {str(e)}")

        return redirect("resetPassword")

    # If GET request → render the form
    return render(request, "forgot_password/forgot_password.html")

def custom_reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = UserDetails.objects.get(pk=uid)
    except (UserDetails.DoesNotExist, ValueError, TypeError):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password = request.POST["password"]
            confirm_password = request.POST["confirm_password"]
            
            if new_password == confirm_password:
                user.password = make_password(new_password)
                user.save()
                messages.success(request, "Password reset successfully! You can now log in.")
                return redirect("home")
            else:
                messages.error(request, "Passwords do not match!")

        return render(request, "forgot_password/custom_reset_password.html", {"uidb64": uidb64, "token": token, 'form': LoginForm()})
    
    messages.error(request, "Invalid or expired reset link!")
    return redirect("forgot_password")







def producer_logout(request):
    request.session.flush()  # Clears all session data
    return redirect('home')



# ---------------------------------------------------------------- Dashboard ------------------------------------------------ #

def producer_profile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('home')

    userdata = Registration.objects.filter(id=user_id).first()
    
    # Fetch state and district names
    state_name = ''
    district_name = ''

    if userdata:
        if userdata.state:
            state_obj = State.objects.filter(state_id=userdata.state).first()
            if state_obj:
                state_name = state_obj.state_name

        if userdata.district:
            district_obj = District.objects.filter(city_id=userdata.district).first()
            if district_obj:
                district_name = district_obj.city_name
    
    return render(request,"dashboard/profile.html",{'user': userdata, 'statename': state_name, 'districtname': district_name})




def producer_dashboard(request):
    user_id = request.session.get('user_id')
    # print(user_id)
    if not user_id:
        return redirect('home')

    users = Registration.objects.filter(id=user_id)

    userdata = Registration.objects.filter(id=user_id).first()
    if not userdata:
        return redirect('home')
    
    # inside producer_dashboard
    # userdata.company_email = mask_email(userdata.company_email)
    # userdata.authorized_person_mobile = mask_phone(userdata.authorized_person_mobile)
    # userdata.authorized_person_email = mask_email(userdata.authorized_person_email)
    
    producers = producerGeneralDetails.objects.filter(gst_no=userdata.gst_no).first()
    entitytype_list = userdata.entity_types.split(',') if userdata and userdata.entity_types else []
    if producers is not None:
        sales_data_raw = list(
            ProducerSalesSummary.objects
            .filter(producer_id=producers.id)
            .values('financial_year', 'category')
            .annotate(total_epr_target=Sum('total_epr_target'))
        )
    else:
        sales_data_raw = []

    # Grouped by final financial_year_display
    grouped_sales = defaultdict(lambda: {'total_epr_target': 0, 'base_year': 0})

    for item in sales_data_raw:
        year_str = item['financial_year']  # e.g., '2019-20'
        try:
            base_year = int(year_str.split('-')[0])  # extract 2019
        except (ValueError, IndexError):
            base_year = 0

        if item['category'] == 'transport':
            start_year = base_year + 15
        else:
            start_year = base_year + 20

        end_year_suffix = str(start_year + 1)[-2:]
        display_year = f"{start_year}-{end_year_suffix}"

        grouped_sales[display_year]['total_epr_target'] += item['total_epr_target']
        grouped_sales[display_year]['base_year'] = start_year
        grouped_sales[display_year]['financial_year_display'] = display_year

    # Convert to list and sort by base_year
    sales_data = sorted(grouped_sales.values(), key=lambda x: x['base_year'])
    
    submission_date = "-"
    if producers:
        submission_date = Transaction.objects.filter(owner_id=producers.id).filter(status="success").first()
    
    producers_with_status = []
    for producer in users:
        status_name = None
        if producer.status>=0:
            status = ProgressStatus.objects.filter(id=producer.status).first()
            if status:
                status_name = status.name
        if '3' in producer.entity_types:
            entity_type = "Producer"
            
        producers_with_status.append({
            'producer_id': producers.id if producers else None,
            'producer': producer,
            'status_name': status_name,
            'entity_type' : entity_type,
            'submission_date' : submission_date,
            
        })
        
    

    return render(request, 'dashboard/dashboard.html', {
        'user': userdata,
        'entity_types': [e.strip() for e in entitytype_list],
        'producers': producers_with_status,
        'user_type': "Producer",
        'sales_data': sales_data,
    })
    
from django.utils import timezone
import pytz
def get_last_comment(request, user_id):
    userdata = Registration.objects.filter(id=user_id).first()
    producer = producerGeneralDetails.objects.filter(gst_no=userdata.gst_no).first()
    last_note = Noting.objects.filter(producer_id=producer.id).order_by('-id').first()

    formatted_date = None
    if last_note and last_note.forwarded_at:
        # Convert to IST
        ist = pytz.timezone("Asia/Kolkata")
        forwarded_at_ist = timezone.localtime(last_note.forwarded_at, ist)
        formatted_date = forwarded_at_ist.strftime("%d %b %Y, %I:%M %p")
        # Example output: "19 Sep 2025, 02:45 PM"

    return JsonResponse({
        'comment': last_note.comment if last_note else None,
        'date': formatted_date
    })


def get_trail(request, user_id):

    # Find Producer by user
    userdata = Registration.objects.filter(id=user_id).first()
    producer = producerGeneralDetails.objects.filter(gst_no=userdata.gst_no).first()

    # Get messages exchanged between officer and user only
    noting_list = Noting.objects.filter(
        producer_id=producer.id
    ).filter(
        Q(forwarded_from=0) | Q(forwarded_to=0)
    ).order_by('-id')

    trail = []
    ist = pytz.timezone("Asia/Kolkata")

    for note in noting_list:
        forwarded_at = timezone.localtime(note.forwarded_at, ist) if note.forwarded_at else None

        trail.append({
            "from": note.forwarded_from,
            "to": note.forwarded_to,
            "comment": note.comment,
            "date": forwarded_at.strftime("%d %b %Y, %I:%M %p") if forwarded_at else "-",
        })

    return JsonResponse({"trail": trail})


def reg_application(request):
    user_id = request.session.get('user_id')
    # print(user_id)
    if not user_id:
        return redirect('home')

    users = Registration.objects.filter(id=user_id)

    userdata = Registration.objects.filter(id=user_id).first()
    if not userdata:
        return redirect('home')
    
    producers = producerGeneralDetails.objects.filter(gst_no=userdata.gst_no).first()
    entitytype_list = userdata.entity_types.split(',') if userdata and userdata.entity_types else []
    # sales_data = (
    #     ProducerSalesSummary.objects
    #     .filter(producer_id=producers.id)
    #     .values('financial_year')
    #     .annotate(total_epr_target=Sum('total_epr_target'))
    #     .order_by('financial_year')
    # )
    
    submission_date = "-"
    if producers:
        submission_date = Transaction.objects.filter(owner_id=producers.id).filter(status="success").first()
        
    producers_with_status = []
    for producer in users:
        status_name = None
        if producer.status>=0:
            status = ProgressStatus.objects.filter(id=producer.status).first()
            if status:
                status_name = status.name
        if '3' in producer.entity_types:
            entity_type = "Producer"
            
        producers_with_status.append({
            'producer': producer,
            'status_name': status_name,
            'entity_type' : entity_type,
            'submission_date' : submission_date,
        })


    return render(request, 'auth/reg_application.html', {
        'user': userdata,
        'entity_types': [e.strip() for e in entitytype_list],
        'producers': producers_with_status,
        'user_type': "Producer",
        # 'sales_data': sales_data,
    })  

def consumer_dashboard(request):
    user_id = request.session.get('user_id')
    # print(user_id)
    if not user_id:
        return redirect('home')

    users = Registration.objects.filter(id=user_id)

    userdata = Registration.objects.filter(id=user_id).first()
    if not userdata:
        return redirect('home')
    
    producers = producerGeneralDetails.objects.filter(gst_no=userdata.gst_no)
    entitytype_list = userdata.entity_types.split(',') if userdata and userdata.entity_types else []
    
    producers_with_status = []
    for producer in users:
        status_name = None
        if producer.status>=0:
            status = ProgressStatus.objects.filter(id=producer.status).first()
            if status:
                status_name = status.name
        if '2' in producer.entity_types:
            entity_type = "Bulk Consumer"
            
        producers_with_status.append({
            'producer': producer,
            'status_name': status_name,
            'entity_type' : entity_type,
        })
        
    # producers_with_status = []
    # for producer in producers:
    #     status_name = None
    #     if producer.status>=0:
    #         status = ProgressStatus.objects.filter(id=producer.status).first()
    #         if status:
    #             status_name = status.name
    #     producers_with_status.append({
    #         'producer': producer,
    #         'status_name': status_name
    #     })

    return render(request, 'dashboard/dashboard.html', {
        'user': userdata,
        'entity_types': [e.strip() for e in entitytype_list],
        'producers': producers_with_status,
        'user_type': "Consumer",
    })

def reg_bulk_consumer_application(request):
    user_id = request.session.get('user_id')
    # print(user_id)
    if not user_id:
        return redirect('home')

    users = Registration.objects.filter(id=user_id)

    userdata = Registration.objects.filter(id=user_id).first()
    if not userdata:
        return redirect('home')
    
    producers = producerGeneralDetails.objects.filter(gst_no=userdata.gst_no).first()
    entitytype_list = userdata.entity_types.split(',') if userdata and userdata.entity_types else []
    # sales_data = (
    #     ProducerSalesSummary.objects
    #     .filter(producer_id=producers.id)
    #     .values('financial_year')
    #     .annotate(total_epr_target=Sum('total_epr_target'))
    #     .order_by('financial_year')
    # )
    
    
    
    producers_with_status = []
    for producer in users:
        status_name = None
        if producer.status>=0:
            status = ProgressStatus.objects.filter(id=producer.status).first()
            if status:
                status_name = status.name
    
        if '2' in producer.entity_types:
            entity_type = "Bulk Consumer"
        
        producers_with_status.append({
            'producer': producer,
            'status_name': status_name,
            'entity_type' : entity_type,
        })

    return render(request, 'auth/reg_application.html', {
        'user': userdata,
        'entity_types': [e.strip() for e in entitytype_list],
        'producers': producers_with_status,
        'user_type': "Consumer",
        # 'sales_data': sales_data,
    })

def rvsf_dashboard(request):
    user_id = request.session.get('user_id')
    # print(user_id)
    if not user_id:
        return redirect('home')

    users = Registration.objects.filter(id=user_id)

    userdata = Registration.objects.filter(id=user_id).first()
    if not userdata:
        return redirect('home')
    
    producers = producerGeneralDetails.objects.filter(gst_no=userdata.gst_no)
    entitytype_list = userdata.entity_types.split(',') if userdata and userdata.entity_types else []
    
    producers_with_status = []
    for producer in users:
        status_name = None
        if producer.status>=0:
            status = ProgressStatus.objects.filter(id=producer.status).first()
            if status:
                status_name = status.name
        if '1' in producer.entity_types:
            entity_type = "RVSFs"
            
        producers_with_status.append({
            'producer': producer,
            'status_name': status_name,
            'entity_type' : entity_type,
        })

    return render(request, 'dashboard/dashboard.html', {
        'user': userdata,
        'entity_types': [e.strip() for e in entitytype_list],
        'producers': producers_with_status,
        'user_type': "Rvsf",
    })

def reg_rvsf_application(request):
    user_id = request.session.get('user_id')
    # print(user_id)
    if not user_id:
        return redirect('home')

    users = Registration.objects.filter(id=user_id)

    userdata = Registration.objects.filter(id=user_id).first()
    if not userdata:
        return redirect('home')
    
    producers = producerGeneralDetails.objects.filter(gst_no=userdata.gst_no).first()
    entitytype_list = userdata.entity_types.split(',') if userdata and userdata.entity_types else []
    # sales_data = (
    #     ProducerSalesSummary.objects
    #     .filter(producer_id=producers.id)
    #     .values('financial_year')
    #     .annotate(total_epr_target=Sum('total_epr_target'))
    #     .order_by('financial_year')
    # )
    
    producers_with_status = []
    for producer in users:
        status_name = None
        if producer.status>=0:
            status = ProgressStatus.objects.filter(id=producer.status).first()
            if status:
                status_name = status.name
    
        if '1' in producer.entity_types:
            entity_type = "RVSFs"
        
        producers_with_status.append({
            'producer': producer,
            'status_name': status_name,
            'entity_type' : entity_type,
        })

    return render(request, 'auth/reg_application.html', {
        'user': userdata,
        'entity_types': [e.strip() for e in entitytype_list],
        'producers': producers_with_status,
        'user_type': "Rvsf",
        # 'sales_data': sales_data,
    })



# ------------------------------------------------------------------ Producer General Details -----------------------------------#
def producer(request):
    user_id = request.session.get('user_id')
    states = State.objects.all()
    enabled_years = request.session.get('enabled_years', {})
    turnover_23_24 = 0
    turnover_24_25 = 0
    total_turnover = 0
    average_turnover = 0
    registration_fee = 0
    
    if not user_id:
        return redirect('home')  # Redirect to login if not authenticated
    
    userdata = Registration.objects.filter(id=user_id).first()
    
    producer_fees = ProducerRegistrationFee.objects.all()
    rvsf_fees = RVSFRegistrationFee.objects.all()
    
    
    entitytype_list = userdata.entity_types.split(',') if userdata and userdata.entity_types else []
    
    # Fetch state and district names
    state_name = ''
    district_name = ''

    if userdata:
        if userdata.state not in (None, '', ' '):
            state_obj = State.objects.filter(state_id=userdata.state).first()
            if state_obj:
                state_name = state_obj.state_name

        if userdata.district:
            district_obj = District.objects.filter(city_id=userdata.district).first()
            if district_obj:
                district_name = district_obj.city_name
    
    vehicle_data = {}
    fy_data = {}
    grouped_data = {}
    metadata = {}
    manufacturing_details = None
    nature_selected = []
    facilities = []
    vehicle_records = None
    declaration = None
    turnover_23_24 = 0
    turnover_24_25 = 0
    total_turnover = 0
    registration_fee = 0
    
    
    try:
        general = producerGeneralDetails.objects.get(gst_no=userdata.gst_no)
    except producerGeneralDetails.DoesNotExist:
        general = None

    if general:
        try:
            manufacturing_details = ManufacturingDetails.objects.get(producer_id=general.id)
            nature_selected = (
                manufacturing_details.nature_of_business.split(",")
                if manufacturing_details and manufacturing_details.nature_of_business
                else []
            )
        except ManufacturingDetails.DoesNotExist:
            manufacturing_details = None
            nature_selected = []

        if manufacturing_details:
            facilities = ManufacturingFacilityDetails.objects.filter(manufacturer_id=manufacturing_details.id)
            for facility in facilities:
                value = (facility.state or '').strip()

                if value.isdigit():
                    state = State.objects.filter(state_id=int(value)).first()
                    facility.state_name = state.state_name if state else ''
                else:
                    facility.state_name = ''
        else:
            facilities = []
            
        
        try:
            vehicle_records = ProducerSalesData.objects.filter(producer_id=general.id)
            vehicle_data = {}
            for record in vehicle_records:
                year = str(record.financial_year)
                category = record.category  # 'transport' or 'non_transport'
                vehicle_type = record.vehicle_type
                
                vehicle_data.setdefault(year, {}).setdefault(category, {})[vehicle_type] = {
                    'manufactured': record.no_of_vehicles_manufactured,
                    'imported': record.no_of_vehicles_imported,
                    'procurred': record.no_of_vehicles_procurred_domestically,
                    'open_market_vehicles': record.open_market_vehicles,
                    'open_market_vehicle_weight': record.open_market_vehicle_weight,
                    'open_market_steel_weight': record.open_market_steel_weight,
                    'open_market_brand_name': record.open_market_brand_name,
                    'producer_vehicles': record.producer_vehicles,
                    'producer_vehicle_weight': record.producer_vehicle_weight,
                    'producer_steel_weight': record.producer_steel_weight,
                    'producer_sale_file': record.producer_sale_file,
                    'cobranded_vehicles': record.cobranded_vehicles,
                    'cobranded_vehicle_weight': record.cobranded_vehicle_weight,
                    'cobranded_steel_weight': record.cobranded_steel_weight,
                    'cobranded_brand_name': record.cobranded_brand_name,
                    'cobranded_partner_file': record.cobranded_partner_file,
                    'selfuse_vehicles': record.selfuse_vehicles,
                    'selfuse_vehicle_weight': record.selfuse_vehicle_weight,
                    'selfuse_steel_weight': record.selfuse_steel_weight,
                    'export_vehicles': record.export_vehicles,
                    'vehicle_number_qty': record.vehicle_number_qty,
                    'vehicle_weight_qty': record.vehicle_weight_qty,
                    'epr_qty': record.epr_qty,
                    'epr_target': record.epr_target
                }
        except:
            vehicle_records = None
            vehicle_data = {}
            
        if vehicle_records:
            producer_ids = vehicle_records.values_list('producer_id', flat=True)
            fy_records = ProducerSalesSummary.objects.filter(producer_id__in=producer_ids)
            fy_data = {}
            for record in fy_records:
                year = str(record.financial_year)
                category = record.category  # 'transport' or 'non_transport'

                # Safely get the nested dictionary
                category_dict = fy_data.setdefault(year, {}).setdefault(category, {})

                # Now update it with values
                category_dict['ca_certificate'] = record.ca_certificate
                category_dict['total_epr_target'] = record.total_epr_target

        else:
            fy_records = None
            fy_data = {}


        try:
            vehicle_sales_data = ProducerSalesData.objects.filter(producer_id=general.id)
            vehicle_fy_data = ProducerSalesSummary.objects.filter(producer_id=general.id)

            grouped_data = {
                'non_transport': defaultdict(lambda: defaultdict(list)),
                'transport': defaultdict(lambda: defaultdict(list)),
            }
            
            # Store extra metadata like epr_target and ca_certificate
            metadata = {
                'non_transport': defaultdict(dict),
                'transport': defaultdict(dict),
            }

            for fy_item in vehicle_fy_data:
                
                categories = fy_item.category.split(',') if isinstance(fy_item.category, str) else fy_item.category
                year = fy_item.financial_year  # assuming field is named financial_year
                epr_target = fy_item.total_epr_target
                ca_certificate = fy_item.ca_certificate
                
                for cat in categories:
                    cat = cat.strip()
                    if cat in grouped_data:
                        # Save epr_target and ca_certificate once per category + year
                        metadata[cat][year] = {
                            'epr_target': epr_target,
                            'ca_certificate': ca_certificate
                        }
                        # Filter vehicle_data by matching category and financial year
                        matching_vehicles = vehicle_sales_data.filter(category=cat, financial_year=year.split('-')[0].strip())

                        for vehicle in matching_vehicles:
                            vehicle_type = vehicle.vehicle_type
                            grouped_data[cat][year][vehicle_type].append({
                                # 'vehicle_type': vehicle.vehicle_type,
                                'no_of_vehicles_manufactured': vehicle.no_of_vehicles_manufactured,
                                'no_of_vehicles_imported': vehicle.no_of_vehicles_imported,
                                'no_of_vehicles_procurred_domestically': vehicle.no_of_vehicles_procurred_domestically,
                                'open_market_vehicles': vehicle.open_market_vehicles,
                                'open_market_vehicle_weight': "{:.3f}".format(vehicle.open_market_vehicle_weight or 0),
                                'open_market_steel_weight': "{:.3f}".format(vehicle.open_market_steel_weight or 0),
                                'open_market_brand_name': vehicle.open_market_brand_name,
                                'producer_vehicles': vehicle.producer_vehicles,
                                'producer_vehicle_weight': "{:.3f}".format(vehicle.producer_vehicle_weight or 0),
                                'producer_steel_weight': "{:.3f}".format(vehicle.producer_steel_weight or 0),
                                'producer_sale_file': vehicle.producer_sale_file,
                                'cobranded_vehicles': vehicle.cobranded_vehicles,
                                'cobranded_vehicle_weight': "{:.3f}".format(vehicle.cobranded_vehicle_weight or 0),
                                'cobranded_steel_weight': "{:.3f}".format(vehicle.cobranded_steel_weight or 0),
                                'cobranded_brand_name': vehicle.cobranded_brand_name,
                                'cobranded_partner_file': vehicle.cobranded_partner_file,
                                'selfuse_vehicles': vehicle.selfuse_vehicles,
                                'selfuse_vehicle_weight': "{:.3f}".format(vehicle.selfuse_vehicle_weight or 0),
                                'selfuse_steel_weight': "{:.3f}".format(vehicle.selfuse_steel_weight or 0),
                                'export_vehicles': vehicle.export_vehicles,
                                'vehicle_number_qty': vehicle.vehicle_number_qty,
                                'vehicle_weight_qty': "{:.3f}".format(vehicle.vehicle_weight_qty or 0),
                                'epr_qty': "{:.3f}".format(vehicle.epr_qty or 0),
                                'epr_target': vehicle.epr_target,
                                # 'category': vehicle.category,
                                # 'financial_year': vehicle.financial_year,
                                # 'producer_id': vehicle.producer_id,
                            })
            
            grouped_data['non_transport'] = convert_defaultdict_to_dict(grouped_data['non_transport'])
            grouped_data['transport'] = convert_defaultdict_to_dict(grouped_data['transport'])
            metadata['non_transport'] = convert_defaultdict_to_dict(metadata['non_transport'])
            metadata['transport'] = convert_defaultdict_to_dict(metadata['transport'])
            
        except: 
            grouped_data = {}
        
        try:
            declaration = ProducerDeclaration.objects.filter(producer_id=general.id).first()
            registration_fee = 0

            if declaration:
                turnover_23_24 = declaration.turnover_23_24 if declaration and declaration.turnover_23_24 else 0
                turnover_24_25 = declaration.turnover_24_25 if declaration and declaration.turnover_24_25 else 0
                total_turnover = turnover_23_24 + turnover_24_25
                average_turnover = total_turnover / 2

                # Find the matching fee slab
                fee_record = ProducerRegistrationFee.objects.filter(
                    models.Q(min_turnover__lte=average_turnover) | models.Q(min_turnover__isnull=True)
                    
                ).filter(
                    models.Q(max_turnover__gte=average_turnover) | models.Q(max_turnover__isnull=True)
                ).first()

                # print(fee_record)
                if fee_record:
                    registration_fee = fee_record.registration_fee
            
        except ProducerDeclaration.DoesNotExist:
            declaration = None
            
    else:
        userdata = Registration.objects.filter(id=user_id).first()

    document_exists = bool(general and general.doc)   
    # print(document_exists)
    # Get nature_of_business IDs
    # nature_list = userdata.nature_of_business.split(',') if userdata and userdata.nature_of_business else []
    # selected_nature_ids = [int(nid.strip()) for nid in nature_list if nid.strip().isdigit()]
    
    
    # print(json.dumps(vehicle_data, default=str))
    # print(json.dumps(fy_data, default=str))
    
    
    checklist = None
    if general:
        try:
            checklist = Checklist.objects.get(producer_id=general.id)
        except Checklist.DoesNotExist:
            pass
    
    transaction=None
    additional_registration_fee=None
    total_paid_amount=0
    all_transactions=[]
    
    if general:
        try: 
            all_transactions = Transaction.objects.filter(
                owner_id=general.id, 
                status="success"
            ).order_by('-ru_date')
            
            if all_transactions.exists():
                # Get the latest transaction
                transaction = all_transactions.first()
                
                # Calculate total paid from all transactions
                total_paid_amount = sum(t.amount_initiated for t in all_transactions)
            
            # transaction=Transaction.objects.filter(status="success").get(owner_id=general.id)
            additional_registration_fee = registration_fee - total_paid_amount
            
        except Transaction.DoesNotExist:
            pass
    
    
    payload = {
        "fee": registration_fee,
        "user_id": user_id,
        "additional_registration_fee": additional_registration_fee,
    }

    # Convert to JSON and encrypt
    f = Fernet(settings.CRYPTOGRAPHY_ENCRYPTION_KEY)
    encrypted_fee = f.encrypt(json.dumps(payload).encode()).decode()
    
    # additional_registration_fee=0
    
    # print(additional_registration_fee)
    
    return render(request, 'dashboard/producer.html', {
        'user': userdata,
        'user_id': user_id,
        'states': states,
        'url': 'producer',
        'entity_types': [e.strip() for e in entitytype_list],
        'state_name': state_name,
        'district_name': district_name,
        'general': general,
        'nature_selected': nature_selected,
        'documet_exists' : document_exists,
        # 'producer': producer, 
        'manufacturing_details' : manufacturing_details,
        'facilities': facilities,
        # 'nature_choices': Registration.NATURE_OF_BUSINESS,
        # 'selected_nature_ids': selected_nature_ids,
        'declaration': declaration,
        'vehicle_data_json': json.dumps(vehicle_data, default=str),
        'fy_data' : json.dumps(fy_data, default=str),
        'enabled_years_json': json.dumps(enabled_years),
        'grouped_data': grouped_data,
        'metadata': metadata,
        'checklist': checklist,
        'turnover_23_24': turnover_23_24,
        'turnover_24_25': turnover_24_25,
        'total_turnover': total_turnover,
        'average_turnover' : average_turnover,
        'registration_fee': registration_fee,
        'producer_fees': producer_fees,
        'rvsf_fees': rvsf_fees,
        'completed_step': userdata.completed_step,
        'additional_registration_fee': additional_registration_fee,
        'transaction': transaction,
        "encrypted_fee": encrypted_fee,
        "total_paid_amount": total_paid_amount,
        "all_transactions": all_transactions,
        
    })

def producergeneral(request):
    logger.debug("Entered producergeneral view")

    user_id = request.session.get('user_id')
    logger.debug("Fetched user_id from session: %s", user_id)

    if not user_id:
        logger.warning("No user_id in session, redirecting to home")
        return redirect('home')

    logger.debug("Fetching Registration object for user_id=%s", user_id)
    userdata = Registration.objects.filter(id=user_id).first()
    logger.debug("Userdata fetched: %s", userdata)

    if request.method == 'POST':
        logger.debug("Request method is POST")

        try:
            incorporation_date_str = request.POST.get('incorporation_date')
            logger.debug("Received incorporation_date (raw): %s", incorporation_date_str)

            incorporation_date = int(incorporation_date_str) if incorporation_date_str else None
            logger.debug("Parsed incorporation_date: %s", incorporation_date)

            iec = request.POST.get('iec')
            tin = request.POST.get('tin')
            cin = request.POST.get('cin')
            logger.debug("IEC: %s, TIN: %s, CIN: %s", iec, tin, cin)

            logger.debug("Attempting to fetch existing producerGeneralDetails by gst_no=%s", userdata.gst_no)
            try:
                general1 = producerGeneralDetails.objects.get(gst_no=userdata.gst_no)
                logger.debug("Existing general details found: %s", general1)
            except producerGeneralDetails.DoesNotExist:
                general1 = None
                logger.debug("No existing general details found")

            # ---------------- FILE INPUTS ----------------
            logger.debug("Processing file inputs depending on existing record")

            if general1:
                auth_pan_document = request.FILES.get('doc1')
                gst_document = request.FILES.get('gst_doc1')
                pan_document = request.FILES.get('pan_doc1')
                tin_document = request.FILES.get('tin_doc1')
                cin_document = request.FILES.get('cin_doc1')

                logger.debug("Received updated file uploads for existing record")

                if general1.iec_doc:
                    iec_document = request.FILES.get('iec_doc1')
                else:
                    iec_document = request.FILES.get('iec_doc')

            else:
                auth_pan_document = request.FILES.get('doc')
                gst_document = request.FILES.get('gst_doc')
                pan_document = request.FILES.get('pan_doc')
                tin_document = request.FILES.get('tin_doc')
                cin_document = request.FILES.get('cin_doc')
                iec_document = request.FILES.get('iec_doc')

                logger.debug("Received file uploads for new record")

            # ---------------- VALIDATE FILES ----------------
            logger.debug("Validating uploaded files")

            try:
                if auth_pan_document:
                    logger.debug("Validating auth_pan_document: %s", auth_pan_document)
                    auth_pan_document = validate_uploaded_file(auth_pan_document)
                    auth_pan_document.name = secure_filename(auth_pan_document.name)

                if gst_document:
                    logger.debug("Validating gst_document")
                    gst_document = validate_uploaded_file(gst_document)
                    gst_document.name = secure_filename(gst_document.name)

                if pan_document:
                    logger.debug("Validating pan_document")
                    pan_document = validate_uploaded_file(pan_document)
                    pan_document.name = secure_filename(pan_document.name)

                if tin_document:
                    logger.debug("Validating tin_document")
                    tin_document = validate_uploaded_file(tin_document)
                    tin_document.name = secure_filename(tin_document.name)

                if cin_document:
                    logger.debug("Validating cin_document")
                    cin_document = validate_uploaded_file(cin_document)
                    cin_document.name = secure_filename(cin_document.name)

                if iec_document:
                    logger.debug("Validating iec_document")
                    iec_document = validate_uploaded_file(iec_document)
                    iec_document.name = secure_filename(iec_document.name)

            except ValidationError as e:
                logger.error("Validation error occurred during file upload: %s", str(e))
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

            # ---------------- INCORPORATION CHANGE LOGIC ----------------
            old_incorp = general1.incorporation_date if general1 else None
            logger.debug("Old incorporation date: %s", old_incorp)

            if general1 and incorporation_date and old_incorp and incorporation_date != old_incorp:
                logger.info("Incorporation date changed. Deleting related data")

                producer = general1

                related_sales_data = ProducerSalesData.objects.filter(producer=producer)
                related_declaration_data = ProducerDeclaration.objects.filter(producer=producer)

                logger.debug("Deleting dependent Excel and summary data")

                OtherProducerExcelData.objects.filter(
                    sales_data_id__in=related_sales_data.values_list('id', flat=True)
                ).delete()

                CobrandedExcelData.objects.filter(
                    sales_data_id__in=related_sales_data.values_list('id', flat=True)
                ).delete()

                related_sales_data.delete()

                if userdata.status == 0:
                    logger.debug("User status 0, deleting declaration data also")
                    related_declaration_data.delete()

                ProducerSalesSummary.objects.filter(producer=producer).delete()

            # ---------------- PRESERVE OLD DOCUMENTS ----------------
            if general1:
                logger.debug("Checking whether to reuse old documents")

                if general1.gst_doc and not gst_document:
                    gst_document = general1.gst_doc
                if general1.pan_doc and not pan_document:
                    pan_document = general1.pan_doc
                if general1.tin_doc and not tin_document:
                    tin_document = general1.tin_doc
                if general1.cin_doc and not cin_document:
                    cin_document = general1.cin_doc
                if general1.iec_doc and not iec_document:
                    iec_document = general1.iec_doc
                if general1.doc and not auth_pan_document:
                    auth_pan_document = general1.doc

            gst_no = request.POST.get('gst_no', '').strip()
            email = request.POST.get('company_email', '').strip()

            logger.debug("GST No: %s, Company Email: %s", gst_no, email)

            # ---------------- VALIDATIONS ----------------
            logger.debug("Running form validations")

            if not incorporation_date:
                logger.error("Missing incorporation_date")
                return JsonResponse({'status': 'error', 'message': 'Please fill all required fields and upload the document.'}, status=400)

            if not auth_pan_document or not gst_document or not pan_document:
                logger.error("Required documents missing")
                return JsonResponse({'status': 'error', 'message': 'Please upload required documents.'}, status=400)

            if tin and not tin_document:
                logger.error("TIN provided but no document uploaded")
                return JsonResponse({'status': 'error', 'message': 'Please upload the tin document.'}, status=400)

            if cin and not cin_document:
                logger.error("CIN provided but no document uploaded")
                return JsonResponse({'status': 'error', 'message': 'Please upload the cin document.'}, status=400)

            if iec and not iec_document:
                logger.error("IEC provided but no document uploaded")
                return JsonResponse({'status': 'error', 'message': 'Please upload the iec document.'}, status=400)

            # ---------------- SAVE / UPDATE ----------------
            logger.debug("Creating or updating producerGeneralDetails object")

            general, created = producerGeneralDetails.objects.update_or_create(
                gst_no=gst_no,
                defaults={
                    'company_email': email,
                    'authorized_person_email': request.POST.get('authorized_person_email'),
                    'authorized_person_mobile': request.POST.get('authorized_person_mobile'),
                    'company_name': request.POST.get('company_name'),
                    'legal_name': request.POST.get('legal_name'),
                    'incorporation_date': incorporation_date,
                    'business_category': request.POST.get('business_category'),
                    'registered_address': request.POST.get('registered_address'),
                    'state': request.POST.get('state'),
                    'district': request.POST.get('district'),
                    'pin_code': request.POST.get('pin_code'),
                    'website': request.POST.get('website'),
                    'pan_no': request.POST.get('pan_no'),
                    'tin': tin,
                    'cin': cin,
                    'iec': iec,
                    'authorized_person_name': request.POST.get('authorized_person_name'),
                    'authorized_person_designation': request.POST.get('authorized_person_designation'),
                    'authorized_person_pan': request.POST.get('authorized_pan'),
                    'doc': auth_pan_document,
                    'gst_doc': gst_document,
                    'pan_doc': pan_document,
                    'tin_doc': tin_document,
                    'cin_doc': cin_document,
                    'iec_doc': iec_document,
                    'user_type': 'Producer',
                }
            )

            logger.info("Producer general details saved. Created=%s, Object=%s", created, general)

            if incorporation_date != old_incorp:
                logger.debug("Incorporation date changed; updating completed_step to 'general'")
                userdata.completed_step = 'general'
                userdata.save()

            logger.info("Returning success JSON response")
            return JsonResponse({'status': 'success', 'message': 'Details saved successfully.'})

        except Exception as e:
            logger.exception("Unexpected error in producergeneral")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    logger.debug("Non-POST request; redirecting to home")
    return redirect('home')

# ------------------------------------------------------------------ Producer Manufacturing Details ----------------------------------#

# Allow alphanumeric, spaces, comma, dot, dash, slash, parentheses, ampersand, and colon.
SAFE_TEXT_PATTERN = re.compile(r'^[a-zA-Z0-9\s,.\-()/&:]+$')

def validate_safe_text(value, field_name="Field"):
    """
    Strictly validate and sanitize text input.
    - Blocks HTML/script injection
    - Restricts special characters
    - Allows basic punctuation and safe symbols
    """
    if value is None:
        return ""

    # Convert to string and trim spaces
    value = str(value).strip()

    # Remove any HTML tags if accidentally submitted
    sanitized = strip_tags(value)
    if sanitized != value:
        raise ValidationError(f"{field_name} contains disallowed HTML content.")

    # Check character pattern
    if not SAFE_TEXT_PATTERN.fullmatch(sanitized):
        raise ValidationError(f"{field_name} contains invalid characters.")

    # Optional: limit max length to avoid buffer or DB overflow
    if len(sanitized) > 255:
        raise ValidationError(f"{field_name} exceeds maximum length of 255 characters.")

    return sanitized



# def save_manufacturing_status(request):
#     user_id = request.session.get('user_id')
#     userdata = Registration.objects.filter(id=user_id).first()

#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)

#             nature_ids = data.get('nature_of_business', [])
#             has_facility = data.get('has_facility')
#             facilities = data.get('facilities', [])
            
#             # print(data)
            
#             if not nature_ids:
#                 return JsonResponse({'status': 'error', 'message': 'Nature of Business is required.'}, status=400)
            
#             # Update has_facility flag
#             producer = producerGeneralDetails.objects.get(gst_no=userdata.gst_no)
#             # producer.has_facility = has_facility
#             # producer.save()
#             manufacturer, _ = ManufacturingDetails.objects.update_or_create(
#                 producer=producer,
#                 defaults={
#                     'nature_of_business': ','.join(nature_ids),
#                     'has_facility': has_facility,
#                 }
#             )
            
#             if has_facility == 'No':
#                 ManufacturingFacilityDetails.objects.filter(producer=producer).delete()

#             elif facilities:
#                 # Save each facility
#                 for f in facilities:
#                     try:
#                         name = validate_safe_text(f.get('name', ''), 'Facility Name')
#                         address = validate_safe_text(f.get('address', ''), 'Address')
#                         gstin = validate_safe_text(f.get('gstin', ''), 'GSTIN')
#                     except ValidationError as ve:
#                         return JsonResponse({'status': 'error', 'message': str(ve)}, status=400)
                    
#                     ManufacturingFacilityDetails.objects.create(
#                         producer=producer,
#                         manufacturer=manufacturer,
#                         name=name,
#                         address=address,
#                         state=f.get('state_id', ''),
#                         gstin=gstin,
#                         year_of_establishment=f.get('year_of_establishment'),
#                         manufacturing_capacity=f.get('manufacturing_capacity') or '',
#                         assembly_capacity=f.get('assembly_capacity') or '',
#                         activity_types=f.get('activity_types', [])
#                     )
                    
#                     # ManufacturingFacilityDetails.objects.create(
#                     #     producer=producer,
#                     #     manufacturer=manufacturer,
#                     #     name=f.get('name'),
#                     #     address=f.get('address'),
#                     #     state=f.get('state_id', ''),
#                     #     gstin=f.get('gstin'),
#                     #     year_of_establishment=f.get('year_of_establishment'),
#                     #     manufacturing_capacity=f.get('manufacturing_capacity') or '',
#                     #     assembly_capacity=f.get('assembly_capacity') or '',
#                     #     activity_types=f.get('activity_types', [])
#                     # )

#             if userdata.status == 3 and userdata.completed_step!='general':
#                 pass
#             else:
#                 userdata.completed_step = 'manufacturer'
#                 userdata.save()
            
#             return JsonResponse({'status': 'success'})

#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

#     return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)

def save_manufacturing_status(request):
    user_id = request.session.get('user_id')
    userdata = Registration.objects.filter(id=user_id).first()

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)

    try:
        data = json.loads(request.body)

        nature_ids = data.get('nature_of_business', [])
        has_facility = data.get('has_facility')
        facilities = data.get('facilities', [])

        if not nature_ids:
            return JsonResponse({'status': 'error', 'message': 'Nature of Business is required.'}, status=400)

        # Fetch producer
        producer = producerGeneralDetails.objects.get(gst_no=userdata.gst_no)

        # Create or update manufacturer details
        manufacturer, _ = ManufacturingDetails.objects.update_or_create(
            producer=producer,
            defaults={
                'nature_of_business': ','.join(nature_ids),
                'has_facility': has_facility,
            }
        )

        # If 'No' -> clear facilities
        if has_facility == 'No':
            ManufacturingFacilityDetails.objects.filter(producer=producer).delete()

        # If facilities exist -> validate and save
        elif facilities:
            # Remove old records before inserting updated list
            # ManufacturingFacilityDetails.objects.filter(producer=producer).delete()

            for f in facilities:
                try:
                    # Validate required text fields
                    name = validate_safe_text(f.get('name', ''), 'Facility Name')
                    address = validate_safe_text(f.get('address', ''), 'Address')
                    gstin = validate_safe_text(f.get('gstin', ''), 'GSTIN')

                    # Validate optional fields
                    state = validate_safe_text(f.get('state_id', ''), 'State') if f.get('state_id') else ''
                    year_of_establishment = validate_safe_text(str(f.get('year_of_establishment', '')), 'Year of Establishment') if f.get('year_of_establishment') else ''
                    manufacturing_capacity = validate_safe_text(str(f.get('manufacturing_capacity', '')), 'Manufacturing Capacity') if f.get('manufacturing_capacity') else ''
                    assembly_capacity = validate_safe_text(str(f.get('assembly_capacity', '')), 'Assembly Capacity') if f.get('assembly_capacity') else ''

                    # Validate and sanitize activity_types
                    activity_types = f.get('activity_types', [])
                    if not isinstance(activity_types, (list, str)):
                        raise ValidationError("Invalid format for Activity Types.")
                    if isinstance(activity_types, list):
                        activity_types = [validate_safe_text(str(a), 'Activity Type') for a in activity_types]
                    else:
                        activity_types = [validate_safe_text(activity_types, 'Activity Type')]

                except ValidationError as ve:
                    return JsonResponse({'status': 'error', 'message': str(ve)}, status=400)
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': f"Validation failed: {str(e)}"}, status=400)

                # Save validated record
                ManufacturingFacilityDetails.objects.create(
                    producer=producer,
                    manufacturer=manufacturer,
                    name=name,
                    address=address,
                    state=state,
                    gstin=gstin,
                    year_of_establishment=year_of_establishment,
                    manufacturing_capacity=manufacturing_capacity,
                    assembly_capacity=assembly_capacity,
                    activity_types=activity_types
                )

        # Step tracking logic
        # if userdata.status != 3 or userdata.completed_step != 'general':
        #     userdata.completed_step = 'manufacturer'
        #     userdata.save()
        
        if userdata.completed_step == 'general':
            userdata.completed_step = 'manufacturer'
            userdata.save()

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def get_facility(request, facility_id):
    try:
        facility = ManufacturingFacilityDetails.objects.get(id=facility_id)
        
        facility_data = {
            'id': facility.id,
            'name': facility.name,
            'address': facility.address,
            'state': facility.state,
            'gstin': facility.gstin,
            'year_of_establishment': facility.year_of_establishment,
            'activity_types': facility.activity_types,
            'manufacturing_capacity': facility.manufacturing_capacity,
            'assembly_capacity': facility.assembly_capacity,
        }
        print(facility_data)
        return JsonResponse({'success': True, 'facility': facility_data})
    except ManufacturingFacilityDetails.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Facility not found.'})


def update_facility(request):
    try:
        data = json.loads(request.body)

        facility_id = data.get('id')
        if not facility_id:
            return JsonResponse({'success': False, 'message': 'Facility ID missing.'}, status=400)

        # Fetch facility
        try:
            facility = ManufacturingFacilityDetails.objects.get(id=facility_id)
        except ManufacturingFacilityDetails.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Facility not found.'}, status=404)

        try:
            # ✅ Validate text fields
            name = validate_safe_text(data.get('name', facility.name), 'Facility Name')
            address = validate_safe_text(data.get('address', facility.address), 'Address')
            gstin = validate_safe_text(data.get('gstin', facility.gstin), 'GSTIN')

            # Optional text fields
            state = validate_safe_text(data.get('state', facility.state), 'State') if data.get('state') else facility.state
            year_of_establishment = validate_safe_text(
                str(data.get('year_of_establishment', facility.year_of_establishment)), 
                'Year of Establishment'
            ) if data.get('year_of_establishment') else facility.year_of_establishment

            # Capacity fields (validate safe characters only)
            manufacturing_capacity = validate_safe_text(
                str(data.get('manufacturing_capacity', facility.manufacturing_capacity)), 
                'Manufacturing Capacity'
            ) if data.get('manufacturing_capacity') else "NA"

            assembly_capacity = validate_safe_text(
                str(data.get('assembly_capacity', facility.assembly_capacity)), 
                'Assembly Capacity'
            ) if data.get('assembly_capacity') else "NA"

            # ✅ Validate activity types
            activity_types = data.get('activity_types', [])
            if not isinstance(activity_types, (list, str)):
                raise ValidationError("Invalid format for Activity Types.")

            if isinstance(activity_types, list):
                activity_types = [validate_safe_text(str(a), 'Activity Type') for a in activity_types]
            else:
                activity_types = [validate_safe_text(activity_types, 'Activity Type')]

        except ValidationError as ve:
            return JsonResponse({'success': False, 'message': str(ve)}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f"Validation failed: {str(e)}"}, status=400)

        # ✅ Save validated fields
        facility.name = name
        facility.address = address
        facility.gstin = gstin
        facility.state = state
        facility.year_of_establishment = year_of_establishment
        facility.manufacturing_capacity = manufacturing_capacity
        facility.assembly_capacity = assembly_capacity

        # Handle activity_types (JSONField or comma-separated string)
        if hasattr(facility, 'activity_types'):
            if isinstance(facility.activity_types, list):
                facility.activity_types = activity_types
            else:
                facility.activity_types = ','.join(activity_types)

        facility.save()

        return JsonResponse({'success': True, 'updated_facility': model_to_dict(facility)}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# def update_facility(request):
#     try:
#         data = json.loads(request.body)

#         facility_id = data.get('id')
#         if not facility_id:
#             return JsonResponse({'success': False, 'message': 'Facility ID missing.'})

#         # Fetch the facility object
#         try:
#             facility = ManufacturingFacilityDetails.objects.get(id=facility_id)
#         except ManufacturingFacilityDetails.DoesNotExist:
#             return JsonResponse({'success': False, 'message': 'Facility not found.'})
        
#         try:
#             name = validate_safe_text(data.get('name', facility.name), 'Facility Name')
#             address = validate_safe_text(data.get('address', facility.address), 'Address')
#             gstin = validate_safe_text(data.get('gstin', facility.gstin), 'GSTIN')
#         except ValidationError as ve:
#             return JsonResponse({'success': False, 'message': str(ve)}, status=400)

#         # Update basic fields
#         facility.name = name
#         facility.address = address
#         facility.gstin = gstin
#         # facility.name = data.get('name', facility.name)
#         # facility.address = data.get('address', facility.address)
#         facility.state = data.get('state', facility.state)
#         # facility.gstin = data.get('gstin', facility.gstin)
#         facility.year_of_establishment = data.get('year_of_establishment', facility.year_of_establishment)

#         # Handle activity_types - assume stored as list in JSONField or as comma-separated string
#         activity_types = data.get('activity_types', [])
#         if isinstance(activity_types, list):
#             # if JSONField, assign directly
#             # facility.activity_types = activity_types

#             # if CharField storing comma separated, join to string:
#             facility.activity_types = ','.join(activity_types)
#         else:
#             # fallback, store empty string or leave unchanged
#             facility.activity_types = ''

#         # Update capacities
#         facility.manufacturing_capacity = data.get('manufacturing_capacity', facility.manufacturing_capacity)
#         facility.assembly_capacity = data.get('assembly_capacity', facility.assembly_capacity)

#         # Save updated facility
#         facility.save()

#         return JsonResponse({'success': True, 'updated_facility': model_to_dict(facility)})

#     except json.JSONDecodeError:
#         return JsonResponse({'success': False, 'message': 'Invalid JSON.'})

#     except Exception as e:
#         return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
def delete_facility_row(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            row_id = data.get('row_id')
            if row_id:
                ManufacturingFacilityDetails.objects.filter(id=row_id).delete()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Row ID missing'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)


# --------------------------------------------------------------- Producer Sales Data ---------------------------------------------#

def validate_producer_excel_file(uploaded_file, expected_vehicle_no, expected_vehicle_weight, expected_steel_weight):
    expected_vehicle_no = float(expected_vehicle_no)
    expected_vehicle_weight = float(expected_vehicle_weight)
    expected_steel_weight = float(expected_steel_weight)

    if uploaded_file:
        wb = openpyxl.load_workbook(uploaded_file)
        sheet = wb.active

        total_vehicle_no = 0
        total_weight = 0
        total_steel = 0
        data_to_insert = []
        
        try:

            count = 0
            for cell in sheet[1]:
                if cell.value is not None:
                    count += 1
                    
            print(count)

            if count != 12:
                error_msg = "Excel format mismatched in Other Producer. Download the correct format before uploading."
                return False, JsonResponse({'message': error_msg}, status=400)

            for i, row in enumerate(sheet.iter_rows(values_only=True, min_row=2), start=2):
                try:
                    (
                        s_no,
                        producer_name,
                        address,
                        gst,
                        mobile_no,
                        email_id,
                        vehicle_category,
                        vehicle_type,
                        other_vehicle_type,
                        # hsn_code,
                        no_of_vehicle_sold,
                        total_weight_vehicles,
                        total_weight_steel_used
                    ) = row

                    total_vehicle_no += float(no_of_vehicle_sold or 0)
                    total_weight += float(total_weight_vehicles or 0)
                    total_steel += float(total_weight_steel_used or 0)

                    data_to_insert.append(OtherProducerExcelData(
                        producer_name=producer_name,
                        address=address,
                        gst=gst,
                        mobile_no=mobile_no,
                        email_id=email_id,
                        vehicle_category=vehicle_category,
                        vehicle_type=vehicle_type,
                        other_vehicle_type=other_vehicle_type,
                        # hsn_code=hsn_code,
                        no_of_vehicle_sold=no_of_vehicle_sold,
                        total_weight_vehicles=total_weight_vehicles,
                        total_weight_steel_used=total_weight_steel_used,
                    ))

                except Exception as e:
                    return False, JsonResponse({'message': f'Error in row {i}: {str(e)}'}, status=400)
                
        except Exception as e:
            return False, JsonResponse({'message': f"Error while reading Excel: {str(e)}"}, status=400)

        field_errors = {}

        if total_vehicle_no != expected_vehicle_no:
            field_errors['producer_vehicles'] = f"Vehicle count mismatch: Excel={total_vehicle_no}, Entered={expected_vehicle_no}"
        if total_weight != expected_vehicle_weight:
            field_errors['producer_vehicle_weight'] = f"Weight mismatch: Excel={total_weight}, Entered={expected_vehicle_weight}"
        if total_steel != expected_steel_weight:
            field_errors['producer_steel_weight'] = f"Steel mismatch: Excel={total_steel}, Entered={expected_steel_weight}"

        if field_errors:
            return False, JsonResponse({'field_errors': field_errors}, status=400)

        return True, data_to_insert


def validate_cobranded_excel_file(uploaded_file, expected_vehicle_no, expected_vehicle_weight, expected_steel_weight):
    expected_vehicle_no = float(expected_vehicle_no)
    expected_vehicle_weight = float(expected_vehicle_weight)
    expected_steel_weight = float(expected_steel_weight)

    if uploaded_file:
        wb = openpyxl.load_workbook(uploaded_file)
        sheet = wb.active

        total_vehicle_no = 0
        total_weight = 0
        total_steel = 0
        data_to_insert = []
        
        try:
            # Count headers in the first row
            count = 0
            for cell in sheet[1]:
                if cell.value is not None:
                    count += 1
            
            if count != 14:
                error_msg = "Excel format mismatched in Co-Branded Partner. Download the correct format before uploading."
                return False, JsonResponse({'message': error_msg}, status=400)

            # Iterate rows, starting at row 2 (skip header)
            for i, row in enumerate(sheet.iter_rows(values_only=True, min_row=2), start=2):
                try:
                    (
                        s_no,
                        cobrand_partners_name,
                        address,
                        gst,
                        mobile_no,
                        email_id,
                        cobrand_share_percentage,
                        manufactured_facility,
                        vehicle_category,
                        vehicle_type,
                        other_vehicle_type,
                        # hsn_code,
                        no_of_vehicle_sold,
                        total_weight_vehicles,
                        total_weight_steel_used
                    ) = row

                    total_vehicle_no += float(no_of_vehicle_sold or 0)
                    total_weight += float(total_weight_vehicles or 0)
                    total_steel += float(total_weight_steel_used or 0)

                    data_to_insert.append(CobrandedExcelData(
                        cobrand_partners_name=cobrand_partners_name,
                        address=address,
                        gst=gst,
                        mobile_no=mobile_no,
                        email_id=email_id,
                        cobrand_share_percentage=cobrand_share_percentage,
                        manufactured_facility=manufactured_facility,
                        vehicle_category=vehicle_category,
                        vehicle_type=vehicle_type,
                        other_vehicle_type=other_vehicle_type,
                        # hsn_code=hsn_code,
                        no_of_vehicle_sold=no_of_vehicle_sold,
                        total_weight_vehicles=total_weight_vehicles,
                        total_weight_steel_used=total_weight_steel_used,
                    ))

                except Exception as e:
                    return False, JsonResponse({'message': f'Error in row {i}: {str(e)}'}, status=400)

        except Exception as e:
            return False, JsonResponse({'message': f"Error while reading Excel: {str(e)}"}, status=400)

        field_errors = {}

        if total_vehicle_no != expected_vehicle_no:
            field_errors['cobranded_vehicles'] = f"Vehicle count mismatch: Excel={total_vehicle_no}, Entered={expected_vehicle_no}"
        if total_weight != expected_vehicle_weight:
            field_errors['cobranded_vehicle_weight'] = f"Weight mismatch: Excel={total_weight}, Entered={expected_vehicle_weight}"
        if total_steel != expected_steel_weight:
            field_errors['cobranded_steel_weight'] = f"Steel mismatch: Excel={total_steel}, Entered={expected_steel_weight}"

        if field_errors:
            return False, JsonResponse({'field_errors': field_errors}, status=400)

        return True, data_to_insert

def save_vehicle_data(request):
    user_id = request.session.get('user_id')
    userdata = Registration.objects.filter(id=user_id).first()
    # producer = producerGeneralDetails.objects.get(gst_no=userdata.gst_no)
    if request.method == 'POST':
        producer = get_object_or_404(producerGeneralDetails, gst_no=userdata.gst_no)

        year = request.POST.get('year')
        vehicle_type = request.POST.get('vehicle_type')
        category = request.POST.get('category')
        
        # Build field names dynamically
        manufactured = safe_int(request.POST.get(f'manufactured_{year}_{category}_{vehicle_type}', '0'))
        imported = safe_int(request.POST.get(f'imported_{year}_{category}_{vehicle_type}', '0'))
        procured = safe_int(request.POST.get(f'procurred_{year}_{category}_{vehicle_type}', '0'))

        open_market_vehicles = safe_int(request.POST.get(f'open_market_vehicles_{year}_{category}_{vehicle_type}', '0'))
        open_market_vehicle_weight = safe_float(request.POST.get(f'open_market_vehicle_weight_{year}_{category}_{vehicle_type}', '0.0'))
        open_market_steel_weight = safe_float(request.POST.get(f'open_market_steel_weight_{year}_{category}_{vehicle_type}', '0.0'))
        open_market_brand_name = request.POST.get(f'brand_market_{year}_{category}_{vehicle_type}', '')

        producer_vehicles = safe_int(request.POST.get(f'producer_vehicles_{year}_{category}_{vehicle_type}', '0'))
        producer_vehicle_weight = safe_float(request.POST.get(f'producer_vehicle_weight_{year}_{category}_{vehicle_type}', '0.0'))
        producer_steel_weight = safe_float(request.POST.get(f'producer_steel_weight_{year}_{category}_{vehicle_type}', '0.0'))
        # producer_sale_file = request.FILES.get(f'file_producer_{year}_{category}_{vehicle_type}')
        producer_sale_file_uploaded = request.FILES.get(f'file_producer_{year}_{category}_{vehicle_type}')

        cobranded_vehicles = safe_int(request.POST.get(f'cobranded_vehicles_{year}_{category}_{vehicle_type}', '0'))
        cobranded_vehicle_weight = safe_float(request.POST.get(f'cobranded_vehicle_weight_{year}_{category}_{vehicle_type}', '0.0'))
        cobranded_steel_weight = safe_float(request.POST.get(f'cobranded_steel_weight_{year}_{category}_{vehicle_type}', '0.0'))
        cobranded_brand_name = request.POST.get(f'brand_cobranded_{year}_{category}_{vehicle_type}', '')
        # cobranded_partner_file = request.FILES.get(f'file_cobranded_{year}_{category}_{vehicle_type}')
        cobranded_partner_file_uploaded = request.FILES.get(f'file_cobranded_{year}_{category}_{vehicle_type}')

        selfuse_vehicles = safe_int(request.POST.get(f'selfuse_vehicles_{year}_{category}_{vehicle_type}', '0'))
        selfuse_vehicle_weight = safe_float(request.POST.get(f'selfuse_vehicle_weight_{year}_{category}_{vehicle_type}', '0.0'))
        selfuse_steel_weight = safe_float(request.POST.get(f'selfuse_steel_weight_{year}_{category}_{vehicle_type}', '0.0'))

        export_vehicles = safe_int(request.POST.get(f'exports_vehicles_{year}_{category}_{vehicle_type}', '0'))
        
        vehicle_number_qty = safe_float(request.POST.get(f'vehicle_number_qty_{year}_{category}_{vehicle_type}', '0.0'))
        vehicle_weight_qty = safe_float(request.POST.get(f'vehicle_weight_qty_{year}_{category}_{vehicle_type}', '0.0'))

        epr_qty = safe_float(request.POST.get(f'epr_qty_{year}_{category}_{vehicle_type}', '0.0'))
        epr_target = safe_float(request.POST.get(f'epr_target_{year}_{category}_{vehicle_type}', '0.0'))
        
        existing_data = ProducerSalesData.objects.filter(
            producer=producer,
            financial_year=year,
            vehicle_type=vehicle_type,
            category=category
        ).first()
        
        producer_sale_file = (
            producer_sale_file_uploaded 
            if producer_sale_file_uploaded 
            else (existing_data.producer_sale_file if existing_data else None)
        )

        cobranded_partner_file = (
            cobranded_partner_file_uploaded 
            if cobranded_partner_file_uploaded 
            else (existing_data.cobranded_partner_file if existing_data else None)
        )
        
        # === Validation: File required if any related producer field has value ===
        if (producer_vehicles > 0 or producer_vehicle_weight > 0 or producer_steel_weight > 0) and not producer_sale_file:
            if not producer_sale_file and (not existing_data or not existing_data.producer_sale_file):
                return JsonResponse({
                    'field_errors': {
                        f'file_producer': 'Producer sales file is required '
                    }
                }, status=400)
            
        if (cobranded_vehicles > 0 or cobranded_vehicle_weight > 0 or cobranded_steel_weight > 0) and not cobranded_partner_file:
            if not cobranded_partner_file and (not existing_data or not existing_data.cobranded_partner_file):
                return JsonResponse({
                    'field_errors': {
                        f'file_cobranded': 'Co-branded Partners file is required '
                    }
                }, status=400)

        # If file is uploaded, validate format
        file_response_or_data_list = []
        if producer_sale_file:
            success, file_response_or_data_list = validate_producer_excel_file(
                producer_sale_file,
                producer_vehicles,
                producer_vehicle_weight,
                producer_steel_weight
            )
            if not success:
                return file_response_or_data_list  # Return validation error directly
            
        # If file is uploaded, validate format
        file_cobranded_response_or_data_list = []
        if cobranded_partner_file:
            success, file_cobranded_response_or_data_list = validate_cobranded_excel_file(
                cobranded_partner_file,
                cobranded_vehicles,
                cobranded_vehicle_weight,
                cobranded_steel_weight
            )
            if not success:
                return file_cobranded_response_or_data_list  # Return validation error directly
            
        defaults = {
            'no_of_vehicles_manufactured': manufactured,
            'no_of_vehicles_imported': imported,
            'no_of_vehicles_procurred_domestically': procured,

            'open_market_vehicles': open_market_vehicles,
            'open_market_vehicle_weight': open_market_vehicle_weight,
            'open_market_steel_weight': open_market_steel_weight,
            'open_market_brand_name': open_market_brand_name,

            'producer_vehicles': producer_vehicles,
            'producer_vehicle_weight': producer_vehicle_weight,
            'producer_steel_weight': producer_steel_weight,

            'cobranded_vehicles': cobranded_vehicles,
            'cobranded_vehicle_weight': cobranded_vehicle_weight,
            'cobranded_steel_weight': cobranded_steel_weight,
            'cobranded_brand_name': cobranded_brand_name,

            'selfuse_vehicles': selfuse_vehicles,
            'selfuse_vehicle_weight': selfuse_vehicle_weight,
            'selfuse_steel_weight': selfuse_steel_weight,

            'export_vehicles': export_vehicles,

            'vehicle_number_qty': vehicle_number_qty,
            'vehicle_weight_qty': vehicle_weight_qty,
            'epr_qty': epr_qty,
            'epr_target': epr_target,
        }

        if producer_sale_file_uploaded:
            defaults['producer_sale_file'] = producer_sale_file_uploaded

        if cobranded_partner_file_uploaded:
            defaults['cobranded_partner_file'] = cobranded_partner_file_uploaded


        sales_data, created = ProducerSalesData.objects.update_or_create(
            producer=producer,
            financial_year=year,
            vehicle_type=vehicle_type,
            category=category,
            defaults=defaults
        )

        # print(sales_data)
        
        if producer_sale_file_uploaded and existing_data and existing_data.producer_sale_file:
            # Delete old Excel data and file
            OtherProducerExcelData.objects.filter(sales_data_id=existing_data.id).delete()
            existing_data.producer_sale_file.delete(save=False)

        if cobranded_partner_file_uploaded and existing_data and existing_data.cobranded_partner_file:
            # Delete old Excel data and file
            CobrandedExcelData.objects.filter(sales_data_id=existing_data.id).delete()
            existing_data.cobranded_partner_file.delete(save=False)
        
        for item in file_response_or_data_list:
            item.sales_data_id = sales_data.id  # Associate with sales data ID
            item.producer_id = producer.id

        OtherProducerExcelData.objects.bulk_create(file_response_or_data_list, ignore_conflicts=True)
        
        for item in file_cobranded_response_or_data_list:
            item.sales_data_id = sales_data.id  # Associate with sales data ID
            item.producer_id = producer.id

        CobrandedExcelData.objects.bulk_create(file_cobranded_response_or_data_list, ignore_conflicts=True)
        
        return JsonResponse({
            'message': 'Vehicle data {} successfully!'.format('created' if created else 'updated')
        })
        # return redirect('producer_dashboard')  # Adjust your redirect URL

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

# def submit_sales_summary(request):
#     user_id = request.session.get('user_id')
#     userdata = Registration.objects.filter(id=user_id).first()

#     if request.method == 'POST' and userdata:
        
#         category = request.POST.get('category')
#         financial_year = request.POST.get('financial_year')
#         base_year = financial_year.split('-')[0]
#         total_epr_target = request.POST.get(f'total_epr_qty_{category}_{base_year}')
#         file_field_name = f"ca_cert_{category}_{base_year}"
#         ca_certificate = request.FILES.get(file_field_name)

#         producer = get_object_or_404(producerGeneralDetails, gst_no=userdata.gst_no)
        
#         try:
#             if ca_certificate:
#                 ca_certificate = validate_uploaded_file(ca_certificate)
#                 ca_certificate.name = secure_filename(ca_certificate.name)
#         except ValidationError as e:
#             return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

#         # Try to get existing entry
#         existing_entry = ProducerSalesSummary.objects.filter(
#             producer=producer,
#             category=category,
#             financial_year=financial_year
#         ).first()
        

#         # Prepare POST and FILES dicts
#         post_data = request.POST.copy()
#         file_data = request.FILES.copy()
        
#         post_data['total_epr_target'] = total_epr_target

        
#         if ca_certificate:
#             file_data['ca_certificate'] = ca_certificate

#         if existing_entry:
#             # Update existing entry
#             form = ProducerSalesSummaryForm(post_data, file_data, instance=existing_entry, producer=producer)
            
#         else:
#             # Create new entry
#             form = ProducerSalesSummaryForm(post_data, file_data, producer=producer)
            

#         if form.is_valid():
#             form.instance.producer = producer
#             form.save()
            
#             # Enable next year in session
#             current_year_str = f"{int(base_year)}-{str(int(base_year) + 1)[-2:]}"
#             next_base_year = int(base_year) + 1
#             next_year_str = f"{next_base_year}-{str(next_base_year + 1)[-2:]}"
            
#             # Get or initialize enabled_years dict from session
#             enabled_years = request.session.get('enabled_years', {})
            
#             # Ensure list exists for the current category
#             if category not in enabled_years:
#                 enabled_years[category] = []
            
#             # Include current year if not already present
#             if current_year_str not in enabled_years[category]:
#                 enabled_years[category].append(current_year_str)
            
#             # Include next year if not already present
#             if next_year_str not in enabled_years[category]:
#                 enabled_years[category].append(next_year_str)
            
#             # Update the session
#             request.session['enabled_years'] = enabled_years

#             # userdata.completed_step = 'sales'
#             # userdata.save()
#             return JsonResponse({'status': 'success', 'message': 'Data saved successfully!'})
#         else:
#             return JsonResponse({'status': 'error', 'errors': form.errors})

#     return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@csrf_exempt
# @require_POST
def delete_vehicle_type_data(request):
    # print("hhhhhhhhhhh")
    try:
        data = json.loads(request.body)
        vehicle_type = data.get('vehicle_type')
        user_id = request.session.get('user_id')
        userdata = Registration.objects.filter(id=user_id).first()

       
        # Get the current user
        # user = request.user
        producer = get_object_or_404(producerGeneralDetails, gst_no=userdata.gst_no)
        # print(producer.id)

       
        # Delete all sales data for this vehicle type and user
        # Replace with your actual model and query
        ProducerSalesSummary.objects.filter(producer=producer.id, category=vehicle_type).delete()
       
        # Also delete any related FY data
        ProducerSalesData.objects.filter(producer=producer.id, category=vehicle_type).delete()
        userdata = Registration.objects.filter(id=user_id).first()
        if userdata:
            userdata.completed_step = "manufacturer"
            userdata.save()
       
        return JsonResponse({'status': 'success', 'message': f'{vehicle_type} data deleted successfully'})
       
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
def submit_sales_summary(request):
    try:
        user_id = request.session.get('user_id')
        userdata = Registration.objects.filter(id=user_id).first()

        if request.method != 'POST' or not userdata:
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

        category = request.POST.get('category')
        financial_year = request.POST.get('financial_year')
        base_year = financial_year.split('-')[0]
        total_epr_target = request.POST.get(f'total_epr_qty_{category}_{base_year}')
        file_field_name = f"ca_cert_{category}_{base_year}"
        ca_certificate = request.FILES.get(file_field_name)

        producer = get_object_or_404(producerGeneralDetails, gst_no=userdata.gst_no)

        if ca_certificate:
            try:
                ca_certificate = validate_uploaded_file(ca_certificate)
                ca_certificate.name = secure_filename(ca_certificate.name)
            except ValidationError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f"File validation failed: {e.message if hasattr(e, 'message') else str(e)}"
                }, status=400)

        existing_entry = ProducerSalesSummary.objects.filter(
            producer=producer,
            category=category,
            financial_year=financial_year
        ).first()

        post_data = request.POST.copy()
        file_data = request.FILES.copy()
        post_data['total_epr_target'] = total_epr_target
        if ca_certificate:
            file_data['ca_certificate'] = ca_certificate

        if existing_entry:
            form = ProducerSalesSummaryForm(post_data, file_data, instance=existing_entry, producer=producer)
        else:
            form = ProducerSalesSummaryForm(post_data, file_data, producer=producer)

        if form.is_valid():
            try:
                form.instance.producer = producer
                form.save()
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'File save failed: {e}'}, status=500)

            # ... your session enabled_years logic here ...
            current_year_str = f"{int(base_year)}-{str(int(base_year) + 1)[-2:]}"
            next_base_year = int(base_year) + 1
            next_year_str = f"{next_base_year}-{str(next_base_year + 1)[-2:]}"
            
            # Get or initialize enabled_years dict from session
            enabled_years = request.session.get('enabled_years', {})
            
            # Ensure list exists for the current category
            if category not in enabled_years:
                enabled_years[category] = []
            
            # Include current year if not already present
            if current_year_str not in enabled_years[category]:
                enabled_years[category].append(current_year_str)
            
            # Include next year if not already present
            if next_year_str not in enabled_years[category]:
                enabled_years[category].append(next_year_str)
            
            # Update the session
            request.session['enabled_years'] = enabled_years

            return JsonResponse({'status': 'success', 'message': 'Data saved successfully!'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt   # ⚠️ only if you don’t pass CSRF in fetch
def submit_sales_data(request):
    if request.method == "POST":
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"status": "error", "message": "User not logged in"})

        userdata = Registration.objects.filter(id=user_id).first()
        print(userdata)
        if userdata:
            userdata.completed_step = "sales"
            userdata.save()
            return JsonResponse({"status": "success", "message": "Sales data saved"})
        
        return JsonResponse({"status": "error", "message": "User not found"})
    
    return JsonResponse({"status": "error", "message": "Invalid request"})

# --------------------------------------------------------- Producer Declaration -------------------------------------------------- #
# @csrf_exempt
# def producerdeclaration(request):
#     if request.method == 'POST':
#         user_id = request.session.get('user_id')
#         userdata = Registration.objects.filter(id=user_id).first()
#         producer = producerGeneralDetails.objects.get(gst_no=userdata.gst_no)

#         turnover_23_24 = float(request.POST.get('turnover_23_24', 0))
#         turnover_24_25 = float(request.POST.get('turnover_24_25', 0))
#         declaration = request.POST.get('declarationCheckbox')
#         undertaking_file = request.FILES.get('undertaking_file')
#         undertaking_file1 = request.FILES.get('undertaking_file1')
#         ca_certificate_23_24 = request.FILES.get('ca_certificate_23_24')
#         ca_certificate1_23_24 = request.FILES.get('ca_certificate1_23_24')
#         ca_certificate_24_25 = request.FILES.get('ca_certificate_24_25')
#         ca_certificate1_24_25 = request.FILES.get('ca_certificate1_24_25')
        
#         # print(turnover_23_24)
#         # print(turnover_24_25)

#         declaration1 = ProducerDeclaration.objects.filter(producer_id=producer.id).first()

#         # if declaration1:
#         #     if undertaking_file1 is None:
#         #         undertaking_file = declaration1.undertaking_file
#         #     else:
#         #         undertaking_file = undertaking_file1
                
#         #     if ca_certificate1_23_24 is None:
#         #         ca_certificate_23_24 = declaration1.ca_certificate_23_24
#         #     else:
#         #         ca_certificate_23_24 = ca_certificate1_23_24
            
#         #     if ca_certificate1_24_25 is None:
#         #         ca_certificate_24_25 = declaration1.ca_certificate_24_25
#         #     else:
#         #         ca_certificate_24_25 = ca_certificate1_24_25
        
#         if declaration1:
#             undertaking_file = undertaking_file1 or declaration1.undertaking_file
#             ca_certificate_23_24 = ca_certificate1_23_24 or declaration1.ca_certificate_23_24
#             ca_certificate_24_25 = ca_certificate1_24_25 or declaration1.ca_certificate_24_25

#         # ---- File Validation ----
#         try:
#             if undertaking_file:
#                 undertaking_file = validate_uploaded_file(undertaking_file)
#                 undertaking_file.name = secure_filename(undertaking_file.name)

#             if ca_certificate_23_24:
#                 ca_certificate_23_24 = validate_uploaded_file(ca_certificate_23_24)
#                 ca_certificate_23_24.name = secure_filename(ca_certificate_23_24.name)

#             if ca_certificate_24_25:
#                 ca_certificate_24_25 = validate_uploaded_file(ca_certificate_24_25)
#                 ca_certificate_24_25.name = secure_filename(ca_certificate_24_25.name)

#         except ValidationError as e:
#             return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

#         if not all([undertaking_file, declaration]):
#             return JsonResponse({'status': 'error', 'message': 'All fields are required.'})

#         try:
#             ProducerDeclaration.objects.update_or_create(
#                 producer_id=producer.id,
#                 defaults={
#                     'turnover_23_24': turnover_23_24,
#                     'turnover_24_25': turnover_24_25,
#                     'undertaking_file': undertaking_file,
#                     'ca_certificate_23_24': ca_certificate_23_24,
#                     'ca_certificate_24_25': ca_certificate_24_25,
#                     'declaration': True
#                 }
#             )

#             total_turnover = turnover_23_24 + turnover_24_25
#             average_turnover = total_turnover/2

#             # Fetch registration fee based on total_turnover
#             fee_record = ProducerRegistrationFee.objects.filter(
#                 Q(min_turnover__lte=average_turnover) | Q(min_turnover__isnull=True)
#             ).filter(
#                 Q(max_turnover__gte=average_turnover) | Q(max_turnover__isnull=True)
#             ).first()

#             registration_fee = fee_record.registration_fee if fee_record else 0  
            
            
            
#             try: 
#                 transaction=Transaction.objects.filter(status="success").get(owner_id=userdata.id)
#                 additional_registration_fee = registration_fee - transaction.amount_initiated
                
#             except Transaction.DoesNotExist:
#                 transaction=None
#                 additional_registration_fee=None

#             userdata.completed_step = 'declaration'
#             userdata.save()
#             return JsonResponse({
#                 'status': 'success',
#                 'message': 'Details saved successfully.',
#                 'turnover_23_24': turnover_23_24,
#                 'turnover_24_25': turnover_24_25,
#                 'total_turnover': total_turnover,
#                 'average_turnover': average_turnover,
#                 'registration_fee': registration_fee,
#                 'additional_registration_fee': additional_registration_fee
#             })
        
#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': f'Error saving data: {str(e)}'})

#     return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


@csrf_exempt
def producerdeclaration(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        userdata = Registration.objects.filter(id=user_id).first()
        producer = producerGeneralDetails.objects.get(gst_no=userdata.gst_no)

        turnover_23_24 = float(request.POST.get('turnover_23_24', 0))
        turnover_24_25 = float(request.POST.get('turnover_24_25', 0))
        declaration = request.POST.get('declarationCheckbox')
        
        undertaking_file = request.FILES.get('undertaking_file')
        undertaking_file1 = request.FILES.get('undertaking_file1')
        ca_certificate_23_24 = request.FILES.get('ca_certificate_23_24')
        ca_certificate1_23_24 = request.FILES.get('ca_certificate1_23_24')
        ca_certificate_24_25 = request.FILES.get('ca_certificate_24_25')
        ca_certificate1_24_25 = request.FILES.get('ca_certificate1_24_25')

        declaration1 = ProducerDeclaration.objects.filter(producer_id=producer.id).first()

        # --- Use existing files if available and no new files uploaded ---
        if declaration1:
            undertaking_file = undertaking_file1 or declaration1.undertaking_file
            ca_certificate_23_24 = ca_certificate1_23_24 or declaration1.ca_certificate_23_24
            ca_certificate_24_25 = ca_certificate1_24_25 or declaration1.ca_certificate_24_25
        else:
            # No existing record yet, so use only new uploads
            undertaking_file = undertaking_file1 or undertaking_file
            ca_certificate_23_24 = ca_certificate1_23_24 or ca_certificate_23_24
            ca_certificate_24_25 = ca_certificate1_24_25 or ca_certificate_24_25

        # ---- File Validation (only validate newly uploaded files) ----
        try:
            if undertaking_file1 or (not declaration1 and undertaking_file):
                undertaking_file = validate_uploaded_file(undertaking_file)
                undertaking_file.name = secure_filename(undertaking_file.name)

            if ca_certificate1_23_24 or (not declaration1 and ca_certificate_23_24):
                ca_certificate_23_24 = validate_uploaded_file(ca_certificate_23_24)
                ca_certificate_23_24.name = secure_filename(ca_certificate_23_24.name)

            if ca_certificate1_24_25 or (not declaration1 and ca_certificate_24_25):
                ca_certificate_24_25 = validate_uploaded_file(ca_certificate_24_25)
                ca_certificate_24_25.name = secure_filename(ca_certificate_24_25.name)

        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

        # ---- Required Fields ----
        if not all([undertaking_file, declaration]):
            return JsonResponse({'status': 'error', 'message': 'All fields are required.'})

        # ---- Save or Update Data ----
        try:
            ProducerDeclaration.objects.update_or_create(
                producer_id=producer.id,
                defaults={
                    'turnover_23_24': turnover_23_24,
                    'turnover_24_25': turnover_24_25,
                    'undertaking_file': undertaking_file,
                    'ca_certificate_23_24': ca_certificate_23_24,
                    'ca_certificate_24_25': ca_certificate_24_25,
                    'declaration': True
                }
            )

            total_turnover = turnover_23_24 + turnover_24_25
            average_turnover = total_turnover / 2

            fee_record = ProducerRegistrationFee.objects.filter(
                Q(min_turnover__lte=average_turnover) | Q(min_turnover__isnull=True)
            ).filter(
                Q(max_turnover__gte=average_turnover) | Q(max_turnover__isnull=True)
            ).first()

            registration_fee = fee_record.registration_fee if fee_record else 0

            try:
                transaction = Transaction.objects.filter(status="success").get(owner_id=userdata.id)
                additional_registration_fee = registration_fee - transaction.amount_initiated
            except Transaction.DoesNotExist:
                transaction = None
                additional_registration_fee = None

            userdata.completed_step = 'declaration'
            userdata.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Details saved successfully.',
                'turnover_23_24': turnover_23_24,
                'turnover_24_25': turnover_24_25,
                'total_turnover': total_turnover,
                'average_turnover': average_turnover,
                'registration_fee': registration_fee,
                'additional_registration_fee': additional_registration_fee
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error saving data: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})



# -------------------------------------------------------------- Some Other Functions ---------------------------------------------- #

# def applications_list(request):
#     app_type = request.GET.get('type')

#     if app_type == 'registered':
#         applications = Registration.objects.all()
#     elif app_type == 'received':
#         applications = Registration.objects.filter(status__gt=0)
#     elif app_type == 'inprocess':
#         applications = Registration.objects.filter(status__in=[1, 2, 4, 5, 8])
#     elif app_type == 'incomplete':
#         applications = Registration.objects.filter(status=3)
#     elif app_type == 'granted':
#         applications = Registration.objects.filter(status=6)
#     elif app_type == 'rejected':
#         applications = Registration.objects.filter(status=7)
#     else:
#         applications = Registration.objects.none()

#     # Attach submission_date to each application
#     application_data = []
#     for app in applications:
#         txn = Transaction.objects.filter(owner_id=app.id, status='success').first()
#         application_data.append({
#             'app': app,
#             'submission_date': app.application_submitted
#         })
#     print(application_data)

#     return render(request, 'dashboard/application_list.html', {
#         'application_data': application_data
#     })


def applications_list(request):
    app_type = request.GET.get('type')
    role = request.GET.get('role', 'producer')

    application_data = []

    # ==================================================
    # RVSF FLOW
    # ==================================================
    if role == 'rvsf':

        qs = ConfirmApplication.objects.all()

        # ---------- STATUS FILTERING ----------
        if app_type == 'registered':
            applications = qs
        elif app_type == 'received':
            applications = qs.filter(appstatus__gt=0)
        elif app_type == 'inprocess':
            applications = qs.filter(appstatus__in=[1,2, 3, 4, 5, 6,8],incomplete=0)
        elif app_type == 'incomplete':
            applications = qs.filter(incomplete=1)
        elif app_type == 'granted':
            # applications = qs.filter(appstatus=9)   # Approved
            applications = qs.filter(appstatus=9,certificateattested=1)
        elif app_type == 'rejected':
            applications = qs.filter(appstatus=7)
        else:
            applications = qs.none()

        # ---------- FETCH RVSF REGISTRATIONS ----------
        user_ids = applications.values_list('userid', flat=True)
        rvsf_map = {
            r.id: r
            for r in RvsfRegistration.objects.filter(id__in=user_ids)
        }

        # ---------- BUILD RESPONSE ----------
        for app in applications:
            r = rvsf_map.get(app.userid)
            if not r:
                continue

            # address = f"{r.registered_address}, {r.district}, {r.state} - {r.pin_code}"
            address = f"{r.registered_address}"
            state_name = ""
            if r.state:
                state_obj = State.objects.filter(state_id=r.state).first()
                if state_obj:
                    state_name = state_obj.state_name
            print(state_name)
            application_data.append({
                'company_name': r.company_name,
                'address': address,
                'state': state_name,
                'submission_date': app.created_at
            })

    # ==================================================
    # PRODUCER FLOW
    # ==================================================
    else:
        qs = Registration.objects.all()

        if app_type == 'registered':
            applications = qs
        elif app_type == 'received':
            applications = qs.filter(status__gt=0)
        elif app_type == 'inprocess':
            applications = qs.filter(status__in=[1, 2, 4, 5, 8])
        elif app_type == 'incomplete':
            applications = qs.filter(status=3)
        elif app_type == 'granted':
            applications = qs.filter(status=6)
        elif app_type == 'rejected':
            applications = qs.filter(status=7)
        else:
            applications = qs.none()

        for app in applications:
            state_name = ""
            if app.state:
                state_obj = State.objects.filter(state_id=app.state).first()
                if state_obj:
                    state_name = state_obj.state_name
            print(state_name)
            application_data.append({
                'company_name': app.company_name,
                'state': state_name,
                'address': app.registered_address,
                'submission_date': app.application_submitted
            })

    return render(request, 'dashboard/application_list.html', {
        'application_data': application_data,
        'role': role
    })

def get_user_progress(request):
    # print("sanskar")
    user_id = request.session.get('user_id')
    # print(user_id)
    if user_id:
        progress, _ = Registration.objects.get_or_create(id=user_id)
        print(progress.completed_step)
        return JsonResponse({'current_step': progress.completed_step}) 
    return JsonResponse({'error': 'Not authenticated'}, status=403)


def update_user_progress(request):
    if request.method == 'POST':
        print(f"=== UPDATE PROGRESS REQUEST ===")
        print(f"POST data: {dict(request.POST)}")
        print(f"Session user_id: {request.session.get('user_id')}")
        
        step = request.POST.get('step')
        print(f"Received step: '{step}'")
        
        
        # Check if step is provided
        if not step:
            print("ERROR: No step provided in request")
            return JsonResponse({'status': 'error', 'message': 'Step parameter is required'}, status=400)
        
        # Check if step is valid
        valid_steps = ['general', 'manufacturer', 'sales', 'declaration', 'payment']
        if step not in valid_steps:
            print(f"ERROR: Invalid step '{step}'. Valid steps are: {valid_steps}")
            return JsonResponse({'status': 'error', 'message': f'Invalid step: {step}'}, status=400)
        
        # Check user authentication
        user_id = request.session.get('user_id')
        if not user_id:
            print("ERROR: User not authenticated")
            return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)
            
        try:
            userdata = Registration.objects.get(id=user_id)
            print(f"Updating user {user_id} progress from '{userdata.completed_step}' to '{step}'")
            
            userdata.completed_step = step
            userdata.save()
            
            print(f"SUCCESS: Progress updated to '{step}'")
            return JsonResponse({
                'status': 'success', 
                'message': f'Progress updated to {step}',
                'new_step': step
            })
            
        except Registration.DoesNotExist:
            print(f"ERROR: User with id {user_id} not found")
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
        except Exception as e:
            print(f"ERROR: Exception updating progress: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    print("ERROR: Invalid method - only POST allowed")
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)

# def update_user_progress(request):
#     print(request.user)
#     if request.method == 'POST' and request.user.is_authenticated:
#         new_step = request.POST.get('step')
#         progress, _ = Registration.objects.get_or_create(user=request.user)
#         progress.completed_step = new_step
#         progress.save()
#         return JsonResponse({'status': 'success'})
#     return JsonResponse({'status': 'failed'}, status=400)

def get_applications(request, user_id):
    
    applications = producerGeneralDetails.objects.filter(forwarded_to=user_id)
    roles = RoleType.objects.all()
    users = CpcbUser.objects.all()
    # Sort by division field, assuming division is an integer or string
    users = sorted(users, key=lambda officer: officer.division)
    # Build a dictionary: {id: role_name}
    role_dict = {role.id: role.name for role in roles}

    all_notings = Noting.objects.select_related('producer').order_by('-forwarded_at')
    noting_dict = defaultdict(list)
    for note in all_notings:
        # noting_dict[note.producer_id].append(note)
        noting_dict[str(note.producer_id)].append(note)
    
    user_dict = {}
    for u in users:
        try:
            division_id = int(u.division)
        except (TypeError, ValueError):
            division_id = None

        role_name = role_dict.get(division_id, "User")

        # user_dict[u.id] = {
        #     'name': u.get_full_name() or u.username,
        #     'division': u.division,
        #     'role_name': role_name,
        # }
        
        name = f"{(u.first_name or '').strip()} {(u.last_name or '').strip()}".strip()
        if not name:
            name = u.username

        user_dict[u.id] = {
            'name': name,
            'division': u.division,
            'role_name': role_name,
        }

    data = []
    for app in applications:
        # Find fee info and noting info
        # fee = Transaction.objects.filter(owner_id=app.id).first()
        fee = Transaction.objects.filter(owner_id=app.id, was_success=True).first()
        noting = noting_dict.get(str(app.id), [])
        latest_note = noting[0] if noting else None
        
        encrypted_id = signing.dumps(app.id)

        data.append({
            'id': app.id,
            'encrypted_id': encrypted_id,
            'company_name': app.company_name,
            'state': app.state,
            'txn_date': timezone.localtime(fee.txn_date).strftime('%d %b %Y, %H:%M') if fee else '-',
            'forwarded_to_name': user_dict.get(latest_note.forwarded_to, {}).get('name') if latest_note and latest_note.forwarded_to else '-',
            'forwarded_to_role': user_dict.get(latest_note.forwarded_to, {}).get('role_name') if latest_note and latest_note.forwarded_to else '',
            'forwarded_at': timezone.localtime(latest_note.forwarded_at).strftime('%d %b %Y, %H:%M') if latest_note else '-',
        })

    return JsonResponse({'applications': data})

def finalsubmit(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            # Handle missing session
            return redirect('login')  # or an error page
        
        final_comment = request.POST.get('final_comments', '').strip()
        if not final_comment:
            messages.error(request, "Comment is required for final submission.")
            return redirect('producer_dashboard')
        
        userdata = get_object_or_404(Registration, id=user_id)
        producer = get_object_or_404(producerGeneralDetails, gst_no=userdata.gst_no)
        dh_user = CpcbUser.objects.filter(division='2').first()  # Assuming one DH per division

        

        checklist, created = Checklist.objects.get_or_create(producer_id=producer.id)

        Noting.objects.create(
            comment=final_comment,
            forwarded_to=dh_user.id,
            forwarded_from=0,
            last_updated_by=0,
            producer_id=producer.id,
            checklist_id=checklist.id
        )

        userdata.status = 8
        userdata.save()

        producer.status = 2
        producer.forwarded_to = dh_user.id
        producer.application_type = 1
        producer.save()

        # messages.success(request, "Submitted successfully with your comment.")
        return redirect('producer_dashboard')

def verify_consent(request):
    states = State.objects.all() 
    return render(request,'dashboard/verifyconsent.html',{'states': states})


# -------------------------------------------------------- Payment Section ------------------------------------------------------#
def initiate_payment(request):
    logger.info("Initiate payment called")

    user_id = request.session.get('user_id')
    logger.debug(f"Session user_id: {user_id}")

    if not user_id:
        logger.warning("No user_id found in session during initiate_payment")
        return redirect('home')

    user = Registration.objects.filter(id=user_id).first()
    producer = producerGeneralDetails.objects.filter(gst_no=user.gst_no).first()

    logger.debug(f"User object: {user}")
    logger.debug(f"Producer object: {producer}")

    email = user.authorized_person_email if user else ""

    if user.status == 3:
        plain_fee = request.POST.get("additional_registration_fee")
        encrypted_fee = request.POST.get("encrypted_fee")
        logger.debug("User status=3, using additional registration fee")
    else:
        plain_fee = request.POST.get("registration_fee")
        encrypted_fee = request.POST.get("encrypted_fee")
        logger.debug("User status!=3, using regular registration fee")

    # --- Decrypt payload ---
    try:
        logger.info("Decrypting payment payload")
        f = Fernet(settings.CRYPTOGRAPHY_ENCRYPTION_KEY)

        decrypted_payload = f.decrypt(encrypted_fee.encode()).decode()
        payload = json.loads(decrypted_payload)

        decrypted_user_id = str(payload.get("user_id"))
        decrypted_fee = str(payload.get("fee"))
        decrypted_additional_fee = str(payload.get("additional_registration_fee"))

        logger.debug(f"Decrypted payload: {payload}")

    except Exception as e:
        logger.error("Payload decryption failed", exc_info=True)
        return HttpResponseForbidden("Invalid or tampered encrypted data")

    # --- Validation checks ---
    if str(user_id) != decrypted_user_id:
        logger.error("User mismatch detected in decrypted payload")
        return HttpResponseForbidden("User mismatch detected!")

    if user.status == 3:
        if str(plain_fee) != decrypted_additional_fee:
            logger.error("Additional fee tampering detected")
            return HttpResponseForbidden("Fee tampering detected!")
        amount = decrypted_additional_fee
        logger.info(f"Validated additional amount: {amount}")
    else:
        if str(plain_fee) != decrypted_fee:
            logger.error("Regular fee tampering detected")
            return HttpResponseForbidden("Fee tampering detected!")
        amount = decrypted_fee
        logger.info(f"Validated fee amount: {amount}")

    if request.method == 'POST':
        order_id = uuid.uuid4().hex[:35]
        logger.info(f"Generated Order ID: {order_id}")

        redirect_url = request.build_absolute_uri('/payment/response/')
        logger.debug(f"BillDesk redirect URL for response: {redirect_url}")

        india_time = datetime.now(ZoneInfo("Asia/Kolkata")).replace(microsecond=0)
        order_date = india_time.isoformat()

        payload = {
            "mercid": settings.BILLDESK_MERCHANT_ID,
            "orderid": order_id,
           "amount": amount,
            # "amount": 1,
            "order_date": order_date,
            "currency": "356",
            "ru": redirect_url,
            "itemcode": "DIRECT",
            "device": {
                "init_channel": "internet",
                "ip": get_client_ip(request),
                "user_agent": request.META.get('HTTP_USER_AGENT', 'DjangoTestAgent'),
            },
            "additional_info": {
                "additional_info1": "NA",
                "additional_info2": "NA",
                "additional_info3": "NA",
                "additional_info4": "NA",
            },
        }

        logger.debug(f"Final BillDesk order payload: {payload}")

        trace_id = uuid.uuid4().hex[:32]
        timestamp = str(int(time.time()))

        jws_header = {
            "alg": "HS256",
            "clientid": settings.BILLDESK_CLIENT_ID,
        }

        http_headers = {
            "Content-Type": "application/jose",
            "Accept": "application/jose",
            "BD-Traceid": trace_id,
            "BD-Timestamp": timestamp,
            "ClientId": settings.BILLDESK_CLIENT_ID,
        }

        logger.debug(f"BillDesk HTTP headers: {http_headers}")

        jws_token = jwt.encode(
            claims=payload,
            key=settings.BILLDESK_KEY_ID,
            algorithm="HS256",
            headers=jws_header,
        )

        logger.info("Calling BillDesk Create Order API")
        logger.debug(f"BillDesk endpoint: {settings.BILLDESK_API_ENDPOINT}")

        try:
            response = requests.post(
                settings.BILLDESK_API_ENDPOINT,
                headers=http_headers,
                data=jws_token,
            )

            logger.info(f"BillDesk response status: {response.status_code}")
            logger.debug(f"BillDesk raw response: {response.text}")

            if response.status_code != 200:
                logger.error(f"BillDesk returned non-200: {response.text}")
                return HttpResponse(f"BillDesk error: {response.text}", status=500)

            decoded = jwt.decode(
                token=response.text,
                key=settings.BILLDESK_KEY_ID,
                algorithms=["HS256"],
            )

            logger.debug(f"Decoded BillDesk response: {decoded}")

            redirect_link = None
            for link in decoded.get('links', []):
                if link.get('rel') == 'redirect':
                    redirect_link = link
                    break

            if not redirect_link:
                logger.error("Redirect link missing in BillDesk response")
                return HttpResponse(
                    f"Redirect link not found in BillDesk response. Full response: {decoded}",
                    status=500,
                )

            redirect_url = redirect_link.get('href')
            authorization_token = redirect_link.get('headers', {}).get('authorization')

            logger.info(f"Redirecting user to BillDesk hosted page")
            logger.debug(f"BillDesk hosted URL: {redirect_url}")

            Transaction.objects.create(
                owner_id=producer.id,
                order_id=order_id,
                amount_initiated=amount,
                status='initiated',
            )

            return render(
                request,
                'auth/redirect_to_billdesk.html',
                {
                    'bd_order_id': decoded.get('bdorderid'),
                    'auth_token': authorization_token,
                    'merchant_id': settings.BILLDESK_MERCHANT_ID,
                    'return_url': request.build_absolute_uri('/payment/response/'),
                },
            )

        except Exception as e:
            logger.error("BillDesk communication failure", exc_info=True)
            return HttpResponse("Error during BillDesk communication: " + str(e), status=500)

    logger.info("Initiate payment ended — redirecting to producer dashboard")
    return redirect('producer')

@csrf_exempt
def payment_response(request):
    logger.debug("Entered payment_response view")

    if request.method != 'POST':
        logger.warning("Invalid HTTP method used: %s", request.method)
        return HttpResponse("Invalid method", status=405)

    logger.debug("Request method is POST")

    encoded_response = request.POST.get('transaction_response')
    logger.debug("Encoded response received: %s", encoded_response)

    if not encoded_response:
        logger.error("No transaction_response found in POST data")
        return HttpResponse("No response received", status=400)

    try:
        logger.debug("Attempting to decode JWT")
        decoded_data = jwt.decode(
            token=encoded_response,
            key=settings.BILLDESK_KEY_ID,
            algorithms=["HS256"]
        )
        logger.debug("JWT decoded successfully: %s", decoded_data)

        order_id = decoded_data.get("orderid")
        logger.debug("Order ID extracted: %s", order_id)

        txn_id = decoded_data.get("transactionid")
        logger.debug("Transaction ID extracted: %s", txn_id)

        status = decoded_data.get("transaction_error_type", "").lower()
        logger.debug("Transaction status extracted: %s", status)

        amount = decoded_data.get("amount", "0.00")
        logger.debug("Amount extracted: %s", amount)

        ru_time_raw = decoded_data.get("transaction_date")
        logger.debug("Raw transaction date extracted: %s", ru_time_raw)

        try:
            parsed_datetime = datetime.fromisoformat(ru_time_raw)
            logger.debug("Parsed transaction date successfully: %s", parsed_datetime)
        except ValueError:
            logger.exception("Invalid date format in transaction response")
            return HttpResponse("Invalid date format in transaction response.", status=400)

        ru_time = parsed_datetime
        logger.debug("Final ru_time set: %s", ru_time)

        if not order_id:
            logger.error("Missing order ID in decoded JWT data")
            return HttpResponse("Missing order ID in payment response.", status=400)

        logger.debug("Fetching Transaction object for order_id=%s", order_id)
        transaction = Transaction.objects.filter(order_id=order_id).first()
        logger.debug("Transaction object fetched: %s", transaction)

        if transaction:
            logger.debug("Transaction exists, fetching related user and producer objects")

            user_id = transaction.owner_id
            logger.debug("User ID from transaction: %s", user_id)

            producer = producerGeneralDetails.objects.filter(id=user_id).first()
            logger.debug("Producer fetched: %s", producer)

            user = Registration.objects.filter(gst_no=producer.gst_no).first()
            logger.debug("User fetched: %s", user)

            declaration = ProducerDeclaration.objects.filter(producer_id=producer.id).first()
            logger.debug("Producer declaration fetched: %s", declaration)

            total_turnover = declaration.turnover_23_24 + declaration.turnover_24_25
            logger.debug("Total turnover calculated: %s", total_turnover)

            average_turnover = total_turnover / 2
            logger.debug("Average turnover calculated: %s", average_turnover)

            email = user.authorized_person_email
            logger.debug("User email extracted: %s", email)

            registration_fee = 0
            additional_registration_fee = 0
            logger.debug("Initialized registration fees to zero")

            if user.status == 3:
                additional_registration_fee = int(float(amount))
                logger.debug("User status == 3, additional registration fee set: %s", additional_registration_fee)
            else:
                registration_fee = int(float(amount))
                logger.debug("Initial registration fee set: %s", registration_fee)

            logger.debug("Updating or creating Transaction record in DB")
            Transaction.objects.update_or_create(
                order_id=order_id,
                defaults={
                    "owner_id": user_id,
                    "txn_id": txn_id,
                    "email": email,
                    "amount_initiated": int(float(amount)),
                    "was_success": status == "success",
                    "status": status,
                    "log": json.dumps(decoded_data, indent=2),
                    "ru_date": ru_time,
                    "txn_date": ru_time,
                    "turnover_23_24": declaration.turnover_23_24,
                    "turnover_24_25": declaration.turnover_24_25,
                    "total_turnover": total_turnover,
                    "average_turnover": average_turnover,
                    "registration_fee": registration_fee,
                    "additional_registration_fee": additional_registration_fee
                }
            )
            logger.debug("Transaction record updated/created successfully")

            if status == "success":
                logger.info("Payment status is success")

                if user.status != 3:
                    logger.debug("Creating Noting entry for initial submission")
                    Noting.objects.create(
                        comment="Initial Submission",
                        forwarded_to=2,
                        forwarded_from=0,
                        last_updated_by=0,
                        producer_id=producer.id,
                        checklist_id=None
                    )

                    logger.debug("Updating user and producer status to submitted")
                    user.status = 1
                    user.application_submitted = ru_time
                    producer.status = 1
                    producer.forwarded_to = 2
                    producer.application_submitted = ru_time
                    user.save()
                    producer.save()
                    logger.debug("User and producer saved successfully")

                    dh_cpcb = CpcbUser.objects.filter(division='2', is_active=1).first()
                    logger.debug("Fetched CPCB user: %s", dh_cpcb)

                    logger.debug("Sending registered SMS")
                    send_registered_sms(producer.authorized_person_mobile)

            redirect_url = reverse("payment_result") + f"?status={status}&order_id={order_id}"
            logger.debug("Redirecting to result page: %s", redirect_url)

            return redirect(redirect_url)

    except JWTError as e:
        logger.exception("JWT decoding failed")
        return HttpResponse("JWT decoding failed: " + str(e), status=400)
    except Exception as e:
        logger.exception("Unexpected error occurred in payment_response")
        return HttpResponse("Unexpected error: " + str(e), status=500)

@csrf_exempt
def payment_result(request):
    status = request.GET.get("status")
    order_id = request.GET.get("order_id")

    transaction = Transaction.objects.filter(order_id=order_id).first()
    if not transaction:
        return HttpResponse("Transaction not found", status=404)
    
    producer = producerGeneralDetails.objects.filter(id=transaction.owner_id).first()
    user = Registration.objects.filter(gst_no=producer.gst_no).first()
    # declaration = ProducerDeclaration.objects.filter(producer_id=producer.id).first()
    # total_turnover = declaration.turnover_23_24 + declaration.turnover_24_25
    # average_turnover = total_turnover / 2

    if status == "success":
        if user and user.status == 3:
            template_name = "auth/additional_payment_receipt.html"
        else:
            template_name = "auth/payment_receipt.html"
    else:
        template_name = "auth/payment_failed.html"
    
    return render(request, template_name, {
        "status": status,
        "order_id": order_id,
        "transaction_id": transaction.txn_id,
        "transaction_date": transaction.ru_date,
        "amount": transaction.amount_initiated,
        "turnover_23_24": transaction.turnover_23_24,
        "turnover_24_25": transaction.turnover_24_25,
        "total_turnover": transaction.total_turnover,
        "average_turnover": transaction.average_turnover,
        "registration_fee": transaction.registration_fee,
        "additional_registration_fee": transaction.additional_registration_fee,
        "total_paid_amount": transaction.additional_registration_fee - transaction.registration_fee,
        "producer": transaction.owner,  # This is the producer via foreign key
        "payment_success": status == "success"
    })

    # return render(request, template_name, {
    #     "status": status,
    #     "order_id": order_id,
    #     "transaction_id": transaction.txn_id,
    #     "transaction_date": transaction.txn_date,
    #     "amount": transaction.amount_initiated,
    #     "producer": producer,
    #     "declaration": declaration,
    #     "total_turnover": total_turnover,
    #     "average_turnover": average_turnover,
    #     "payment_success": status == "success"
    # })


def payment_receipt(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        # print(user_id)
        if not user_id:
            return redirect('home')
        
        user = Registration.objects.filter(id=user_id).first()
        
        producer = producerGeneralDetails.objects.filter(gst_no=user.gst_no).first()
        if not producer:
            return redirect('home')
        
        # Get specific transaction by order_id from form or latest transaction
        order_id = request.POST.get('order_id')
        if order_id:
            # Get specific transaction by order_id
            transaction = Transaction.objects.filter(
                order_id=order_id, 
                owner_id=producer.id
            ).first()
        else:
            # Get the latest transaction
            transaction = Transaction.objects.filter(
                owner_id=producer.id
            ).order_by('-ru_date').first()
        
        
        # transaction = Transaction.objects.filter(owner_id=producer.id).order_by('-ru_date').first()
        
        if transaction:
            return render(request, 'auth/payment_receipt.html', {
                'status': transaction.status,
                'order_id': transaction.order_id,
                'transaction_id': transaction.txn_id,
                'transaction_date': transaction.ru_date,
                "amount": transaction.amount_initiated,
                "turnover_23_24": transaction.turnover_23_24,
                "turnover_24_25": transaction.turnover_24_25,
                "total_turnover": transaction.total_turnover,
                "average_turnover": transaction.average_turnover,
                "registration_fee": transaction.registration_fee,
                "additional_registration_fee": transaction.additional_registration_fee,
                "producer": producer,
                # "payment_success": transaction.status == "success"
            })
        
        return redirect('producer_dashboard')
    
    return redirect('home')
        
        # if transaction:
        #     user_id = transaction.owner_id
        #     status = transaction.status
        #     order_id=transaction.order_id
        #     transaction_id =transaction.txn_id
        #     transaction_date=transaction.ru_date
        #     amount=transaction.amount_initiated
        #     declaration = ProducerDeclaration.objects.filter(producer_id=producer.id).first()
        #     total_turnover = declaration.turnover_23_24 + declaration.turnover_24_25
        #     average_turnover = total_turnover/2
        #     email = user.authorized_person_email


        #     return render(request, 'auth/payment_receipt.html', {
        #         'status': status,
        #         'order_id': order_id,
        #         'transaction_id': transaction_id,
        #         'transaction_date': transaction_date,
        #         "amount": amount,
        #         "producer": producer,
        #         "declaration": declaration,
        #         "total_turnover": total_turnover,
        #         "average_turnover": average_turnover
        #     })
        
        # return redirect('producer_dashboard') 




# ----------------------------------------------------- Producer Registration Certificate --------------------------------------- #

def generate_reg_no(gst_number):
    # 1. Fixed prefix
    prefix = "CB"

    # 2. Year - Full 4-digit year
    year = datetime.now().strftime("%Y")

    # 3. Last 2 characters of GST number
    gst_suffix = gst_number[-2:] if gst_number else "XX"

    # 4. Build base for filtering existing records
    base_code = f"{prefix}{year}{gst_suffix}"

    # 5. Fetch latest registration with same prefix-year-GST pattern
    latest = CertificateRegistry.objects.filter(
        registration_no__startswith=base_code
    ).aggregate(
        Max('registration_no')
    )['registration_no__max']

    # 6. Get last sequence number or start with 0001
    if latest:
        last_seq = int(latest[-4:])
        new_seq = f"{last_seq + 1:04d}"
    else:
        new_seq = "0001"

    # 7. Final registration number
    return f"{base_code}{new_seq}"

def create_pdf(request):
    # producer_id = request.POST.get("producer_id")
    encrypted_id = request.POST.get("producer_id")
    # print(encrypted_id)

    try:
        producer_id = signing.loads(encrypted_id)
    except signing.BadSignature:
        return HttpResponseBadRequest("Invalid or tampered producer ID")
    
    # print(producer_id)
    from datetime import datetime
    try:
        # Fetch producer and user data
        producer = producerGeneralDetails.objects.get(id=producer_id)
        user = Registration.objects.get(gst_no=producer.gst_no)
        nature_qs = ManufacturingDetails.objects.filter(producer_id=producer.id)

        sales_data = ProducerSalesData.objects.filter(producer_id=producer.id)

        vehicle_summary = defaultdict(lambda: defaultdict(int))

        for entry in sales_data:
            vehicle_summary[entry.category][entry.vehicle_type] += 1

        # Convert to regular nested dict
        vehicle_summary = {
            category: dict(types)
            for category, types in vehicle_summary.items()
        }

        total_business_rows = sum(len(row.get_nature_of_business_names()) for row in nature_qs)



        # Count overall total entries
        # overall_total = sum(
        #     count for category_data in vehicle_summary.values() for count in category_data.values()
        # )

        # print(dict(vehicle_summary))
        # print(overall_total)

        # Generate a registration number
        registration_no = generate_reg_no(producer.gst_no)

        context = {
            "application_number": user.username,
            "application_date": producer.application_submitted,
            "issue_date": datetime.now().strftime("%d-%m-%Y"),
            "registration_number": registration_no,
            "company_name": producer.company_name,
            "registered_address": producer.registered_address,
            "issue_place": "New Delhi",
            "nature_of_business": nature_qs,
            "vehicle_summary": dict(vehicle_summary),
            "total_business_rows": total_business_rows

        }
        return render_to_string('admin/producer_certificate.html', context)
        # return render(request, 'admin/producer_certificate.html', context)

    except (producerGeneralDetails.DoesNotExist, Registration.DoesNotExist):
        # return 404 if data is not found
        raise Http404("Producer or User not found.")
    except Exception as e:
        # For any unexpected failure, return 500 error
        return HttpResponseServerError("Internal Server Error occurred while generating certificate.")
    

# -------------------------------------------------------- EmSigner ---------------------------------------------------------------- #

def view_certificate(request):
    encrypted_id = request.GET.get("producer_id") or request.POST.get("producer_id")

    try:
        producer_id = signing.loads(encrypted_id)
    except signing.BadSignature:
        return HttpResponseBadRequest("Invalid or tampered producer ID")

    print(producer_id)
    reference = f"CERT_{producer_id}"
    signed_dir = os.path.join(settings.BASE_DIR, "certificates", "signed_files")
    signed_pdf_path = os.path.join(signed_dir, f"{reference}.pdf")

    if not os.path.exists(signed_pdf_path):
        return HttpResponse("Certificate not found", status=404)

    # ✅ If ?download=true is in the URL → force download
    if request.GET.get("download") == "true":
        return FileResponse(
            open(signed_pdf_path, "rb"),
            as_attachment=True,
            filename=f"{reference}.pdf",
            content_type="application/pdf"
        )

    # ✅ Otherwise → view inline in the browser
    response = FileResponse(open(signed_pdf_path, "rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{reference}.pdf"'
    return response

def important_communications(request):

    return render(request, "dashboard/important_communications.html")


def decrypt_aes_cert(encrypted_text):
    key = b"16charSecretKey!"  # same as client
    iv = b"16charSecretIV!!"   # same as client
    encrypted_bytes = base64.b64decode(encrypted_text)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
    # remove PKCS7 padding
    pad_len = decrypted_padded[-1]
    return decrypted_padded[:-pad_len].decode('utf-8')

def receive_certificates(request):
    producer_id = request.session.get("user_id")
    user_role = request.session.get("user_role")

    if not producer_id or user_role != "producer":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    if not producer_id:
        return redirect("home")

    transactions = (
        CertificateTransaction.objects
        .filter(producer_id=producer_id)
        .select_related()  # safe
        .prefetch_related("transfers__denomination_detail")
        .order_by("-created_at")
    )

    pending_data = []
    accepted_data = []
    rejected_data = []
    accepted_total_kg = 0
    accepted_total_mt = 0

    for txn in transactions:

        # 🔹 Get RVSF company name
        try:
            rvsf_company = RvsfRegistration.objects.get(
                id=txn.rvsf_id
            ).company_name
        except RvsfRegistration.DoesNotExist:
            rvsf_company = "Unknown"

        transfers = txn.transfers.all()

        # 🔹 Determine status based on transfer rows
        transfer_statuses = list(transfers.values_list("status", flat=True))

        if not transfer_statuses:
            continue

        if all(status == "pending" for status in transfer_statuses):
            category = "pending"

        elif all(status == "accepted" for status in transfer_statuses):
            category = "accepted"

        elif all(status in ["rejected", "reverted"] for status in transfer_statuses):
            category = "rejected"

        else:
            category = txn.status  # fallback safety

        # 🔹 Build certificate list
        certificates = []
        
        total_kg = 0

        for transfer in transfers:
            denom = transfer.denomination_detail
            total_kg += denom.denomination_kg * denom.quantity
            
            certificates.append({ "unique_id": denom.unique_id, "transfer_status": transfer.status })

        total_mt = total_kg / 1000

        txn_data = {
            "transaction_db_id": txn.id,
            "transaction_uuid": txn.transaction_id,
            "rvsf_company_name": rvsf_company,
            "created_at": txn.created_at,
            "certificates": certificates,
            "total_value_kg": total_kg,
            "total_value_mt": total_mt,
            "transaction_status": txn.status,
        }

        # 🔹 Categorize into correct list
        if category == "pending":
            pending_data.append(txn_data)

        elif category == "accepted":
            accepted_total_kg += total_kg
            accepted_total_mt += total_mt   
            accepted_data.append(txn_data)

        else:
            rejected_data.append(txn_data)

    context = {
        "pending_transactions": pending_data,
        "accepted_transactions": accepted_data,
        "rejected_transactions": rejected_data,
        "accepted_total_kg": accepted_total_kg,
        "accepted_total_mt": accepted_total_mt,
        "user_type": "Producer"
    }
    print(context, 11111111111111111111)
    return render(
        request,
        "transfer_certificate/receive_certificates.html",
        context
    )

def mark_certificate_transferred(txn_id, producer_id, action, reason=""):
    txn = CertificateTransaction.objects.filter(
        transaction_id=txn_id,
        producer_id=producer_id,
        status="pending"
    ).first()

    if not txn:
        return {"error": "Transaction not found or already processed"}

    if action not in ["accepted", "rejected"]:
        return {"error": "Invalid action"}

    with transaction.atomic():

        # Update transaction
        txn.status = action
        txn.save(update_fields=["status"])

        # Update transfers
        CertificateTransfer.objects.filter(
            transaction=txn
        ).update(status=action)

        # Update certificates
        if action == "accepted":
            DenominationDetail.objects.filter(
                transfers__transaction=txn
            ).update(status="transferred")
        else:
            DenominationDetail.objects.filter(
                transfers__transaction=txn
            ).update(status="generated")

    return {"success": True}

def send_sms_otp_for_transfer_certificate(request):
    if request.method == "POST":
        # producer_id = 4
        producer_id = request.session.get('user_id')
        user_number = Registration.objects.filter(id=producer_id).first()
        transfer_id = request.POST.get('transaction_uuid')
        status = request.POST.get('status')
        try:
            transfer_id = decrypt_aes_cert(transfer_id)
            status = decrypt_aes_cert(status)
        except Exception as e:
            print(f"❌ OTP decryption failed: {e}")
            messages.error(request, "Transfer ID or Status decryption failed.")
            # return  redirect('receive_certificates')
            return JsonResponse({
                "status": "error",
                "message": f"Transfer ID or Status decryption failed."
            })
        otp = str(random.randint(100000, 999999))
        # otp = "123456"
        cache.set(f"otp_{user_number.username}", otp, timeout=120)
    # API credentials & configuration
    username = "CPCB_IT"
    password = "Smscpcb#2026"
    senderid = "CPCBEL"
    dept_secure_key = "106a9ed9-00c4-442d-a857-3447d308c9d9"
    # templateid = "1307175188771815034"
    entity_id = "1301158798803147760"
    
    if status.lower() == "rejected":
        templateid = "1707177305336266182"
        message = (
            f"Dear Producer, Your OTP for rejecting the ELV Certificate transfer on the ELV EPR Portal is {otp}. Please enter this code to confirm rejection of the certificate. Do not share this OTP with anyone. Regards, CPCB."
        )
    elif status.lower() == "accepted":
        templateid = "1707177305334303349"
        message = (
            f"Dear Producer, Your OTP for accepting the ELV Certificate transfer on the ELV EPR Portal is {otp}. Please enter this code to confirm acceptance of the certificate. Do not share this OTP with anyone. Regards, CPCB."
        )
    else:
        return JsonResponse({
            "status": "error",
            "message": "Invalid status provided."
        })

    # OTP message
    

    # Encrypt password
    encrypted_password = hashlib.sha1(password.strip().encode()).hexdigest()

    # Generate key for request
    key_string = f"{username.strip()}{senderid.strip()}{message.strip()}{dept_secure_key.strip()}"
    key = hashlib.sha512(key_string.encode()).hexdigest()

    # API payload
    payload = {
        "username": username.strip(),
        "password": encrypted_password,
        "senderid": senderid.strip(),
        "content": message.strip(),
        "smsservicetype": "singlemsg",
        "mobileno": user_number.authorized_person_mobile.strip(),
        "key": key,
        "templateid": templateid.strip(),
        "entityid": entity_id.strip(),
    }

    try:
        # ✅ Send request to NEW API endpoint
        test_url = "https://msdgweb.mgov.gov.in/esms/sendsmsrequestDLT"
        response = requests.post(test_url, data=payload, timeout=10)

        return JsonResponse({"status": "success", "message": "OTP sent successfully"})

    except requests.RequestException as e:
        print("Failed to send OTP:", str(e))
        return JsonResponse({"status": "error"}, status=400)

def verify_otp_certificate(request):
    userid = request.session.get('user_id')
    print("🔹 Entered verify_otp view")

    if request.method == 'POST':
        print("✅ Request method is POST")

        

        # ✅ Decrypt the OTP sent from client
        enc_otp = request.POST.get('enc_otp')
        print(enc_otp)
        print(f"Encrypted OTP received: {enc_otp}")
        # 26-2-26
        transfer_id = request.POST.get('transaction_uuid') 
        print("ttt9999993",transfer_id)
        status = request.POST.get('status')
        remark = request.POST.get('reason')
        

        try:
            entered_otp = decrypt_aes_cert(enc_otp)
            print(f"🔓 Decrypted OTP: {entered_otp}")
        except Exception as e:
            print(f"❌ OTP decryption failed: {e}")
            messages.error(request, "OTP decryption failed.")
            # return  redirect('receive_certificates')
            return JsonResponse({
                "status": "error",
                "message": f"OTP decryption failed."
            })

       
        # Step 2: Validate OTP
        user_number=Registration.objects.filter(id=userid).first()
        print("🧩 Fetching stored OTP from cache...")
        stored_otp = cache.get(f"otp_{user_number.username}")
        print(enc_otp,stored_otp,'tops')
        print(f"📦 Stored OTP in cache: {stored_otp}")

        if stored_otp is None:
            print("⚠️ No OTP found or expired in cache")
            messages.error(request, 'OTP expired or not found. Please request a new one.')
            # return  redirect('receive_certificates')
            return JsonResponse({
                "status": "error",
                "message": f"OTP expired or not found. Please request a new one."
            })

        if stored_otp != entered_otp:
            return JsonResponse({"status": "error", "message": "Invalid OTP"})

        cache.delete(f"otp_{user_number.username}")

        result = mark_certificate_transferred(transfer_id, userid, status, remark)

        if "error" in result:
            return JsonResponse(result, status=400)

        if status == "accepted":
            message = "Certificate accepted successfully"
        elif status == "rejected":
            message = "Certificate rejected successfully"
        else:
            message = "Certificate updated successfully"

        return JsonResponse({
            "status": "success",
            "message": message
        })
        
    return redirect("receive_certificates")

