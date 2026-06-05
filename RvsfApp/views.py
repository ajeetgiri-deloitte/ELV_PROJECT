import time
from datetime import date,datetime, time, timedelta, timezone
from django.utils.timezone import now
from django.utils.html import strip_tags
from django.utils.dateparse import parse_date
from django.db import transaction
from Transfer_Certificate.models import *
from decimal import Decimal
from .common_utils import *
import traceback
# import base64
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_v1_5
from Cryptodome.Random import get_random_bytes
from PyPDF2 import PdfReader
from functools import wraps
from utils.email_utils import is_blocked_domain
import imaplib
import ssl
# from django.db.models import Sum,Q  # Add this import
from django.db.models import Sum,Q, F, ExpressionWrapper, DecimalField, OuterRef, Subquery
from django.urls import reverse
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
MOBILE_REGEX = r'^[6-9]\d{9}$'
MAX_OTP_REQUESTS = 5      # Max OTP requests per period
OTP_REQUEST_PERIOD = 3600 # 1 hour in seconds
MAX_OTP_ATTEMPTS = 5      # Max verification attempts per OTP
OTP_EXPIRY = 900
from django.db import IntegrityError
from .session_utils import set_active_session
import urllib3
from sendgrid.helpers.mail import Mail
from .forms import *
from sendgrid import SendGridAPIClient
# import redis
import smtplib
from django.core.cache import cache
from django.views.decorators.http import require_POST,require_http_methods
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views import View
import hashlib
import json
import uuid
from django.contrib import messages
import random
import logging
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
import requests
import re
import secrets
import string
from django.contrib import messages
from RvsfApp.models import ConfirmApplication, EquipmentEntry, EquipmentType, GeneralDetails, PlantCapacity, PollutionDevice, RvsfFacility, RvsfRegistration, VehicleType, WasteRecycled, Payment, RvsfDetails
from RvsfApp.validators import validate_file_size
from SpcbApp.models import CapacityChecklist, EquipmentChecklist, FacilityChecklist, GeneralChecklist, PaymentChecklist, PollutionChecklist, SignupChecklist, StateUsers, UntTrails, WasteRecycleChecklist,ApplicationTrail
from registration.forms import LoginForm
from registration.models import District, State
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from email.mime.text import MIMEText
from email.header import Header
from django.utils.crypto import get_random_string
from django.conf import settings
import django.utils.timezone as dj_timezone
from zoneinfo import ZoneInfo
import time
from .models import *
from registration.models import *

from jose.exceptions import JWTError
from jose import jwt
from registration.models import *
# import jwt
from datetime import datetime, timezone
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
from Cryptodome.Random import get_random_bytes

from utils.email_services import *


# from django.core import signing

import os
from django.http import Http404, FileResponse

def protected_file(request, path):
    # Check for either admin or producer login
    # admin_id = request.session.get('admin_user_id')
    rvsf_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    
    # if neither producer nor admin logged in
    if  not rvsf_id:
        # Redirect based on role (default to producer login)
        if user_role == 'rvsf':
            return redirect('rvsf_home')  # use your producer login view name
        else:
            return redirect('custom_admin_login')

    # File access
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404("File not found")

    return FileResponse(open(file_path, 'rb'), as_attachment=False)

def encrypt_aes(plain_text):
    key = b"16charSecretKey!"
    iv = b"16charSecretIV!!"
    pad_len = 16 - (len(plain_text) % 16)
    padded = plain_text + chr(pad_len) * pad_len
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_bytes = encryptor.update(padded.encode()) + encryptor.finalize()
    return base64.b64encode(encrypted_bytes).decode()


def states_api(request):
    states = State.objects.all().values(
        "state_id",      # or id
        "state_name"
    )
    # print(states)
    return JsonResponse({
        "states": list(states)
    })

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


Send_Grid_Api_Key="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"
aware_now = datetime.now(timezone.utc)

def sendforgetpwdemail(auth_email):
    email = auth_email
    sender_email = 'cpcbepr@cpcbauditempanelment.co.in'
    sender_password = 'airtel@123'
    recipient_email = email
    resetpassword = RvsfRegistration.objects.filter(auth_email = auth_email).first()
    username = resetpassword.username
    new_password = get_random_string(length=8, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
    hashedpassword = make_password(new_password)
    resetpassword.password = hashedpassword
    resetpassword.save()
    subject = 'Welcome to EPR End of Life Vehicle'
    body = f"""
    Dear User,

    Your Username and Password for EPR End of Life Vehicle.

    Username: {username}
    Password: {new_password}

    Please keep these details safe.
    """

    smtp_server = 'smtp.titan.email'
    smtp_port = 587
    imap_server = 'imap.titan.email'
    imap_port = 993

    return send_email(sender_email, sender_password, recipient_email, subject, body, smtp_port, smtp_server, imap_server, imap_port)

class GenerateOTPView(View):

    def post(self, request):
        print('otp generate ho rha hai')
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.'})
        errors = []
        # otp_type = data.get('otp_type')
        # authorization = data.get('authorization', '').strip().lower()
        
        otp_type = (data.get('otp_type') or '').strip().lower()
        authorization = (data.get('authorization') or '').strip().lower()
        print(authorization)

        # if RvsfRegistration.objects.filter(company_email=authorization).exists():
        #     errors.append("Company email already exists.")
        #     return JsonResponse({'success': errors})
        # if RvsfRegistration.objects.filter(auth_email=authorization).exists():
        #     return JsonResponse({'success': errors})
        # if RvsfRegistration.objects.filter(auth_mobile=authorization).exists():
        #     return JsonResponse({'success': errors})

        print('ye1')
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
        
        
        if contact_type == 'email':
            if (
                RvsfRegistration.objects.filter(company_email=authorization).exists() or
                RvsfRegistration.objects.filter(auth_email=authorization).exists()
            ):
                return JsonResponse({'success': False, 'message': 'This email is already used by another user. Please try another.'})
            if is_blocked_domain(authorization):
                return JsonResponse({
                    'success': False,
                    'message': (
                        "Disposable or public email domains are not allowed. "
                        "Please use an official organization email."
                    )
                })

        elif contact_type == 'mobile':
            if RvsfRegistration.objects.filter(auth_mobile=authorization).exists():
                return JsonResponse({'success': False, 'message': 'This mobile number is already used by another user. Please try another.'})

        # Rate limiting OTP requests
        cache_key_requests = f"otp_requests_{authorization}"
        request_count = cache.get(cache_key_requests, 0)
        if request_count >= MAX_OTP_REQUESTS:
            return JsonResponse({'success': False, 'message': 'OTP request limit exceeded. Try again in 1 hour.'})
        cache.set(cache_key_requests, request_count + 1, timeout=OTP_REQUEST_PERIOD)

        # Generate OTP
        otp = str(random.randint(100000, 999999))
        # print(otp)  # remove hardcoded 123456
        # otp="123456"
        otp_hash = hashlib.sha256(f"{otp_type}|{authorization}|{otp}".encode()).hexdigest()

        # Store OTP hash securely in cache
        cache.set(f"otp_{otp_type}_{authorization}", otp_hash, timeout=OTP_EXPIRY)
        cache.set(f"otp_attempts_{otp_type}_{authorization}", 0, timeout=OTP_EXPIRY)

        # Send OTP
        try:
            if contact_type == 'email':
                # sendtitanemail1('', '', authorization, otp)
                sendOtpEmail('', '', authorization, otp)
            else:
                send_sms_otp_direct1(authorization, otp)

            return JsonResponse({'success': True, 'message': f'OTP sent to your {contact_type}.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error sending OTP: {str(e)}'})

class VerifyOTPView1(View):
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


# class VerifyOTPView1(View):
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#         except json.JSONDecodeError:
#             return JsonResponse({'success': False, 'message': 'Invalid JSON.'})

#         # otp_type = data.get('otp_type')
#         # authorization = data.get('authorization', '').strip().lower()
#         otp_type = (data.get('otp_type') or '').strip().lower()
#         authorization = (data.get('authorization') or '').strip().lower()
#         entered_otp = data.get('otp', '').strip()

#         if not authorization or not entered_otp:
#             return JsonResponse({'success': False, 'message': 'Authorization and OTP required.'})
#         if not entered_otp.isdigit() or len(entered_otp) != 6:
#             return JsonResponse({'success': False, 'message': 'Invalid OTP format.'})

#         cache_key_otp = f"otp_{otp_type}_{authorization}"
#         cache_key_attempts = f"otp_attempts_{otp_type}_{authorization}"

#         stored_hash = cache.get(cache_key_otp)
#         attempts = cache.get(cache_key_attempts, 0)

#         if stored_hash is None:
#             return JsonResponse({'success': False, 'message': 'OTP expired or not found.'})

#         if attempts >= MAX_OTP_ATTEMPTS:
#             cache.delete(cache_key_otp)
#             cache.delete(cache_key_attempts)
#             return JsonResponse({'success': False, 'message': 'Maximum OTP attempts reached.'})

#         entered_hash = hashlib.sha256(f"{otp_type}|{authorization}|{entered_otp}".encode()).hexdigest()

#         if entered_hash == stored_hash:
#             # Mark verified securely
#             cache.set(f"otp_verified_{otp_type}_{authorization}", True, timeout=OTP_EXPIRY)
#             cache.delete(cache_key_otp)
#             cache.delete(cache_key_attempts)
#             return JsonResponse({'success': True, 'message': 'OTP verified successfully.'})
#         else:
#             cache.set(cache_key_attempts, attempts + 1, timeout=OTP_EXPIRY)
#             return JsonResponse({'success': False, 'message': 'Invalid OTP. Try again.'})





def send_sms_otp_direct1(number, otp):
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

# def sendtitanemail1(name, username, email_id, otp):
#     # Disable SSL warnings for development (not recommended for production)
#     ssl._create_default_https_context = ssl._create_unverified_context
#     urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#     # Prepare the email
#     message = Mail(
#         from_email='kumar.ashish.cpcb@gmail.com',  # Your verified sender email in SendGrid
#         to_emails=email_id,
#         subject='One Time Password for End of Life Vehicle',
#         # plain_text_content=f'Dear {username}, Your OTP for verification on the ELV EPR Portal is {otp}. Please enter this code to proceed with the verification process. Do not share this OTP with anyone. Regards, CPCB.',
#         html_content=f"""
#                 <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
#                     <p>Dear <strong>{username}</strong>,</p>

#                     <p>Your One-Time Password (OTP) for verification on the <strong>ELV EPR Portal</strong> is:</p>

#                     <p style="font-size: 20px; font-weight: bold; color: #2a7ae2; margin: 10px 0;">
#                         {otp}
#                     </p>

#                     <p>Please enter this code to proceed with the verification process.<br>
#                     <b>Do not share this OTP with anyone.</b></p>

#                     <p>Regards,<br>
#                     Central Pollution Control Board (CPCB)</p>
#                 </div>
#                 """
#     )

#     # Send the email
#     try:
#         sg = SendGridAPIClient(api_key=Send_Grid_Api_Key)
#         response = sg.send(message)
#         print(f"Email sent successfully. Status Code: {response.status_code}")
#         return True

#     except Exception as e:
#         print(f"Error sending email: {e}")
#         return HttpResponse(f"Error sending email: {e}")


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
   
def sendtitanemail1(name, username, email_id, otp):
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
  

def sendtitanemail(username, email_id, otp):
    email = email_id
    userid = username
    sender_email = 'cpcbepr@cpcbauditempanelment.co.in'
    sender_password = 'airtel@123'
    recipient_email = email
    subject = 'One Time Password for End of Life Vehicle'
    body = 'Your One Time Password for login is '+otp

    smtp_server = 'smtp.titan.email'
    smtp_port = 587
    imap_server = 'imap.titan.email'
    imap_port = 993

    return send_email(sender_email, sender_password, recipient_email, subject, body, smtp_port, smtp_server, imap_server, imap_port)


def send_email(sender_email, sender_password, recipient_email, subject, body, smtp_port, smtp_server, imap_server, imap_port):
    message = MIMEText(body, 'plain', 'utf-8')
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = Header(subject, 'utf-8')

    try:
        smtp_obj = smtplib.SMTP(smtp_server, smtp_port)
        smtp_obj.starttls()
        smtp_obj.login(sender_email, sender_password)
        smtp_obj.sendmail(sender_email, recipient_email, message.as_string())
        smtp_obj.quit()
        print('Email sent successfully.')

        imap_obj = imaplib.IMAP4_SSL(imap_server, imap_port)
        imap_obj.login(sender_email, sender_password)
        imap_obj.append('Sent', '',  imaplib.Time2Internaldate(aware_now), message.as_bytes())
        imap_obj.logout()
        print('Email appended to "Sent" folder.')

        return True

    except smtplib.SMTPException as e:
        print('Error sending email:', str(e))
        return False

    except imaplib.IMAP4.error as e:
        print('Error appending email to "Sent" folder:', str(e))
        return False




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

# def check_redis_connection():
#     try:
#         # Try to get a connection and test it
#         conn = cache._cache.get_client()
#         conn.ping()  # Test the connection
#         return True
#     except (redis.ConnectionError, AttributeError, Exception) as e:
#         print(f"Redis connection error: {e}")
#         return False


# def otpviewpage(request):
#     if request.method == 'POST':
#         form = LoginForm(request.POST)
#         if not form.is_valid():
#             # print("Form errors:", form.errors)
#             # print("Form non-field errors:", form.non_field_errors())
#             messages.error(request, "Please correct the errors below.")
#             return render(request, 'authentication/login.html', {'form': form})

#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         fetchemail = RvsfRegistration.objects.filter(username = username).first()
#         email_id = fetchemail.auth_email

#         if not fetchemail:
#             messages.error(request, "Invalid username or password.")
#             return render(request, 'authentication/login.html', {'form': form})

#         # ✅ Step 2: verify password
#         if not fetchemail.check_password(password):   # if you are using Django's hashers
#             messages.error(request, "Invalid username or password.")
#             return render(request, 'authentication/login.html', {'form': form})


#         conn = check_redis_connection()
#         if conn == False:
#             return HttpResponse('Please Try Again Redis Server is not connected')
        
#         stored_otp = cache.get(f"otp_{username}")
#         if stored_otp:
#             messages.error(request, 'OTP Already Sent please try after some time')
#             return redirect('rvsf_home')
#         if form.is_valid():
            
#             # otp = str(random.randint(100000, 999999))
#             otp="123456"
#             cache.set(f"otp_{username}", otp, timeout=120)  # e.g., 5 minutes
#             form = LoginForm()
#             sendtitanemail(username , email_id, otp)
#             context = {'username': username, 'otp': otp , 'password':password , 'form':form}
#             # Ideally, send OTP via email/SMS instead of passing it to template
#             return render(request, 'authentication/otpverify.html', context)
#     else:
#         form = LoginForm()
#     return render(request, 'authentication/login.html', {'form': form})

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


def rsa_decrypt(encrypted_value: str) -> str:
    print("🔐 RSA decrypt start")

    # ✅ Always use absolute path from settings
    with open(settings.RSA_PRIVATE_KEY_PATH, "rb") as f:
        private_key = RSA.import_key(f.read())

    cipher = PKCS1_v1_5.new(private_key)

    decoded = base64.b64decode(encrypted_value)
    sentinel = get_random_bytes(16)

    decrypted = cipher.decrypt(decoded, sentinel)

    if decrypted == sentinel:
        raise ValueError("RSA decryption failed")

    return decrypted.decode("utf-8")
# def otpviewpage(request):
#     print("🔹 Entered otpviewpage view")

#     if request.method == 'POST':
#         print("✅ Request method is POST")

#         form = LoginForm(request.POST)
#         print("🧾 LoginForm initialized with POST data")

#         if not form.is_valid():
#             print("❌ Captcha validation failed")
#             messages.error(request, "Invalid captcha.")
#             return redirect('rvsf_home')
#         print("✅ Captcha validation successful")

#         # Decrypt username & password
#         enc_username = request.POST.get('username')
#         enc_password = request.POST.get('password')
#         print(f"🔒 Encrypted username: {enc_username}")
#         print(f"🔒 Encrypted password: {enc_password}")

#         try:
#             username = decrypt_aes(enc_username)
#             password = decrypt_aes(enc_password)
#             print(f"🔓 Decrypted username: {username}")
#             print(f"🔓 Decrypted password: {password}")
#         except Exception as e:
#             print(f"❌ AES decryption failed: {e}")
#             messages.error(request, "Invalid Credentials.")
#             return redirect('rvsf_home')

#         # ✅ Fetch user
#         print("🔍 Searching for user in RvsfRegistration table...")
#         user = RvsfRegistration.objects.filter(username=username).first()
#         if not user:
#             print(f"❌ No user found for username: {username}")
#             messages.error(request, "User not found1111.")
#             return redirect('rvsf_home')
#         print(f"✅ User found: {user.username} ({user.company_name})")

#         # ✅ Check password
#         print("🔑 Checking password...")
#         if not check_password(password, user.password):
#             print("❌ Password check failed")
#             messages.error(request, "Invalid username or password.")
#             return redirect('rvsf_home')
#         print("✅ Password matched")

#         # OTP logic
#         print("📡 Checking Redis connection...")
#         conn = check_redis_connection()
#         if conn == False:
#             print("❌ Redis connection failed")
#             return HttpResponse('Please try again — Redis not connected.')
#         print("✅ Redis connected successfully")

#         # Check for existing OTP
#         print(f"🧩 Checking if OTP already exists for user: {username}")
#         stored_otp = cache.get(f"otp_{username}")
#         print(f"📦 Stored OTP (if any): {stored_otp}")

#         if stored_otp:
#             print("⚠️ OTP already sent recently — aborting new send")
#             messages.error(request, 'OTP already sent, please wait.')
#             return redirect('rvsf_home')

#         # Generate and cache new OTP
#         otp = str(random.randint(100000, 999999))
#         print(f"🔢 Generated new OTP: {otp}")

#         cache.set(f"otp_{username}", otp, timeout=120)
#         print(f"💾 OTP cached for 120 seconds under key otp_{username}")

#         # Send email and SMS
#         print("📧 Sending OTP email...")
#         sendtitanemail1(user.company_email, username, user.company_email, otp)
#         sendtitanemail1(user.auth_email, username, user.company_email, otp)
#         print("📱 Sending OTP SMS...")
#         send_login_otp_sms(user.auth_mobile, otp)

#         print("✅ OTP sent successfully. Rendering otpverify page...",otp)
#         return render(request, 'authentication/otpverify.html', {
#             'username': username,
#             'otp': otp,
#             'form': LoginForm(),
#         })

#     print("⚠️ Request method not POST — rendering login page")
#     return render(request, 'authentication/login.html', {'form': LoginForm()})


# def otpviewpage(request):
#     form = LoginForm(request.POST or None)
        
#     if request.method == "POST":

        

#         encrypted_username = request.POST.get("username")
#         encrypted_password = request.POST.get("password")

#         if not encrypted_username or not encrypted_password:
#             messages.error(request, "Invalid request.")
#             return redirect("rvsf_home")

#         try:
#             print("ENC USER RAW:", encrypted_username)
#             print("ENC PASS RAW:", encrypted_password)
#             print("LEN USER:", len(encrypted_username))

#             username = rsa_decrypt(encrypted_username).strip()
#             password = rsa_decrypt(encrypted_password)

#             print(username)
#             print(password)

#         except Exception as e:
#             print("RSA ERROR:", e)
#             messages.error(request, "Decryption failed.")
#             return redirect("rvsf_home")

#         user = RvsfRegistration.objects.filter(username=username).first()
#         if not user:
#             messages.error(request, "Invalid username or password1.")
#             return redirect("rvsf_home")
        
#         if not check_password(password, user.password):
#             messages.error(request, "Invalid username or password2.")
#             return redirect("rvsf_home")

#         if cache.get(f"otp_{username}"):
#             messages.error(request, "OTP already sent. Please wait.")
#             return redirect("rvsf_home")

#         otp = str(random.randint(100000, 999999))
#         cache.set(f"otp_{username}", otp, timeout=120)

#         sendtitanemail1(user.company_email, username, user.company_email, otp)
#         send_login_otp_sms(user.auth_mobile, otp)

#         with open(settings.RSA_PUBLIC_KEY_PATH, "rb") as f:
#             public_key_b64 = base64.b64encode(f.read()).decode()

#         return render(request, "authentication/otpverify.html", {
#             "username": username,
#             "public_key_b64": public_key_b64
#         })

#     return render(request, "authentication/login.html",{'form': LoginForm()})


def otpviewpage(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        print("Session data:", dict(request.session))
        if request.session.get('is_rvsf_logged_in'):
            return redirect('rvsf_dashboard')
        

        form = LoginForm(request.POST or None)

        if request.method == "POST":
            print("🧾 LoginForm initialized with POST data")

            encrypted_username = request.POST.get("username")
            encrypted_password = request.POST.get("password")

            if not encrypted_username or not encrypted_password:
                messages.error(request, "Invalid request.")
                return redirect("rvsf_home")

            try:
                username = rsa_decrypt(encrypted_username).strip()
                password = rsa_decrypt(encrypted_password).replace("\x00", "").strip()
            except Exception as e:
                print("RSA ERROR:", e)
                messages.error(request, "Decryption failed.")
                return redirect("rvsf_home")

            user = RvsfRegistration.objects.filter(username=username).first()
            if not user:
                messages.error(request, "Invalid username or password.")
                return redirect("rvsf_home")

            if not check_password(password, user.password):
                messages.error(request, "Invalid username or password.")
                return redirect("rvsf_home")

            if cache.get(f"otp_{username}"):
                messages.error(request, "OTP already sent. Please wait.")
                return redirect("rvsf_home")

            otp = str(random.randint(100000, 999999))
            # otp = "123456"
            cache.set(f"otp_{username}", otp, timeout=120)

            # sendtitanemail1(user.company_name, username, user.company_email, otp)
            sendOtpEmail(user.company_name, username, user.company_email, otp)
            send_login_otp_sms(user.auth_mobile, otp)

            with open(settings.RSA_PUBLIC_KEY_PATH, "rb") as f:
                public_key_b64 = base64.b64encode(f.read()).decode()

            return render(request, "authentication/otpverify.html", {
                "username": username,
                "public_key_b64": public_key_b64,
                'form': form
            })

        return render(request, "authentication/login.html", {'form': form})
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving otpviewpage")
                krishan_logger.error(f"Exact otpviewpage  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact otpviewpage Error: {str(db_error)}")
                messages.error(request, "Something went wrong. Please try again.")
                return redirect("rvsf_home")

# def verify_otp(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         raw_pwd = request.POST.get('password')
#         entered_otp = request.POST.get('otp')

#         stored_otp = cache.get(f"otp_{username}")
#         if stored_otp == entered_otp:
#             cache.delete(f"otp_{username}")
#             user = RvsfRegistration.objects.get(username=username)
#             print(user.password,'fdbfbdbbdfb',raw_pwd,'dasdasdasdas')
#             if user:
#                 if check_password(raw_pwd, user.password):
#                     request.session['user_id'] = user.id
#                     request.session['user_role'] = "rvsf"
#                     return redirect('rvsf_dashboard')
#                 else:
#                     messages.error(request, 'Credentials Not Registered')
#                     return redirect('rvsf_home')

#             else:
#                 message = "Invalid credentials"
#         elif stored_otp is None:
            
#             messages.error(request, 'OTP expired or not found')
#             return redirect('rvsf_home')

#         else:
#             message = "Invalid OTP"
#         return render(request, 'authentication/otpverify.html', {'username': username, 'message': message})
#     return redirect('rvsf_home')      
        

def verify_otp(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        print("🔹 Entered verify_otp view")
        if request.method == 'POST':
            print("✅ Request method is POST")

            form = CaptchaForm(request.POST)
            print("🧩 Captcha form initialized with POST data")

            username = request.POST.get('username')
            print(f"👤 Username received: {username}")

            # ✅ Decrypt the OTP sent from client
            enc_otp = request.POST.get('enc_otp')
            print(f"🔒 Encrypted OTP received: {enc_otp}")

            try:
                entered_otp = decrypt_aes(enc_otp)
                print(f"🔓 Decrypted OTP: {entered_otp}")
            except Exception as e:
                print(f"❌ OTP decryption failed: {e}")
                messages.error(request, "OTP decryption failed.")
                return render(request, 'authentication/otpverify.html', {
                    'username': username,
                    'form': form,
                })

            # Step 1: Validate captcha
            print("🧠 Validating captcha...")
            # print(form)
            if not form.is_valid():
                print("❌ Captcha validation failed")
                messages.error(request, "Invalid captcha. Please try again.")
                return render(request, 'authentication/otpverify.html', {
                    'username': username,
                    'form': form,
                })
            print("✅ Captcha validation successful")

            # Step 2: Validate OTP
            print("🧩 Fetching stored OTP from cache...")
            stored_otp = cache.get(f"otp_{username}")
            print(f"📦 Stored OTP in cache: {stored_otp}")

            if stored_otp is None:
                print("⚠️ No OTP found or expired in cache")
                messages.error(request, 'OTP expired or not found. Please request a new one.')
                return render(request, 'authentication/otpverify.html', {
                    'username': username,
                    'form': form,
                })

            if stored_otp != entered_otp:
                print(f"❌ OTP mismatch — entered: {entered_otp}, expected: {stored_otp}")
                messages.error(request, "Invalid OTP. Please try again.")
                return render(request, 'authentication/otpverify.html', {
                    'username': username,
                    'form': form,
                })

            # Step 3: OTP correct → proceed
            print("✅ OTP verified successfully. Deleting from cache...")
            cache.delete(f"otp_{username}")

            print("🔎 Fetching user record from database...")
            try:
                user = RvsfRegistration.objects.get(username=username)
                print(f"✅ User found: {user}")
            except RvsfRegistration.DoesNotExist:
                print("❌ User not found in database")
                messages.error(request, "User not found.")
                return redirect('home')

            print(f"💾 Setting session data for user_id={user.id}, role=rvsf")
            request.session['user_id'] = user.id
            request.session['user_role'] = "rvsf"

            if user.first_login == 0:
                print("🆕 First login detected — redirecting to change password page")
                return redirect('change-password-first')
            else:
                request.session['is_rvsf_logged_in'] = True
                print("🏠 Returning user — redirecting to dashboard")
                return redirect('rvsf_dashboard')

        print("⚠️ Request method not POST — redirecting to home")
        return redirect('rvsf_home')
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving verifyotp")
                krishan_logger.error(f"Exact verifyotp  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact verifyotp Error: {str(db_error)}")

 

# def rvsf_home(request):
#     if request.method == 'POST':
#         form = LoginForm(request.POST)
#         # print(form)
#         if form.is_valid():
#             # print('jcgasjcgbasjbcsajbjbcbjsacsbjabjcsjbacs')
#             username = form.cleaned_data['username']
#             raw_pwd = form.cleaned_data['password']
           
#             try:
#                 user = RvsfRegistration.objects.get(username=username)
#                 if check_password(raw_pwd, user.password):
#                     request.session['user_id'] = user.id
#                     request.session['user_role'] = "rvsf"
#                     return redirect('rvsf_dashboard')
#                 else:
#                     messages.error(request, 'Credentials Not Registered')
#                     return redirect('rvsf_home')
#             except RvsfRegistration.DoesNotExist:
#                 messages.error(request, 'Credentials Not Registered')
#                 return redirect('rvsf_home')
#     else:
#         print('login error')
#         form = LoginForm()
#         return render(request, 'authentication/login.html' , {'form':form})  # Make sure template exists
def rvsf_home(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        # DEBUG: Check request method
        print(f"DEBUG: Request method = {request.method}")
        
        if request.method == 'POST':
            # DEBUG: Check if form is being received
            print("DEBUG: POST request detected")
            form = LoginForm(request.POST)  
            print(f"DEBUG: Form created with data: {request.POST}")

            if form.is_valid():  
                # DEBUG: Form validation passed
                print("DEBUG: Form is valid")
                username = form.cleaned_data.get('username')
                input_password = form.cleaned_data.get('password')
                print(f"DEBUG: Username = {username}, Password = [HIDDEN]")
                
                # DEBUG: Query database for user
                user = RvsfRegistration.objects.filter(username=username).first()
                print(f"DEBUG: User query result = {user}")
                
                if user is not None:  # check if user exists
                    # DEBUG: User exists, check password
                    print(f"DEBUG: User found: {user.username}")
                    print(f"DEBUG: Stored password hash: {user.password}")
                    
                    if check_password(input_password, user.password):
                        # DEBUG: Password matches
                        print("DEBUG: Password check PASSED")
                        request.session['user_id'] = user.id
                        request.session['user_role'] = "rvsf"
                        print(f"DEBUG: Session set - user_id: {user.id}, user_role: rvsf")
                        
                        # DEBUG: Check session function
                        set_active_session("user", user.id, request)
                        print("DEBUG: Active session set")
                        
                        # DEBUG: Check first login status
                        print(f"DEBUG: user.first_login = {user.first_login}")
                        if user.first_login == 0:
                            print("DEBUG: Redirecting to change-password-first")
                            return redirect('change-password-first')
                        else:
                            print("DEBUG: Redirecting to rvsf_dashboard")
                            return redirect('rvsf_dashboard')
                    else:
                        # DEBUG: Password doesn't match
                        print("DEBUG: Password check FAILED")
                        messages.error(request, "Invalid username or password.")
                        print("DEBUG: Error message set - Invalid credentials")
                        return redirect('rvsf_home')
                else:
                    # DEBUG: User doesn't exist
                    print("DEBUG: User not found in database")
                    messages.error(request, "User Not Found.")
                    print("DEBUG: Error message set - User not found")
                    return redirect('rvsf_home')

            else:
                # DEBUG: Form validation failed
                print("DEBUG: Form is INVALID")
                print(f"DEBUG: Form errors: {form.errors}")
                messages.error(request, "Invalid captcha.")
                print("DEBUG: Error message set - Invalid captcha")
                return render(request, 'authentication/login.html', {'form': form})
        else:
            # DEBUG: GET request
            print("DEBUG: GET request detected")
            form = LoginForm()
            print("DEBUG: Empty form created")
        
        # DEBUG: Final render for GET requests
        print("DEBUG: Rendering login page with form")
        with open(settings.RSA_PUBLIC_KEY_PATH, "rb") as f:
                public_key_b64 = base64.b64encode(f.read()).decode()
        return render(request, 'authentication/login.html', {'form': form,"public_key_b64": public_key_b64})
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving rvsf_home")
                krishan_logger.error(f"Exact rvsf_home  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact rvsf_home Error: {str(db_error)}")

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('rvsf_home')
        return view_func(request, *args, **kwargs)
    return wrapper   
    
def generate_unique_username():
    while True:
        username = str(random.randint(10**9, 10**10 - 1))  # 10-digit number
        if not RvsfRegistration.objects.filter(username=username).exists():
            return username
        
def generate_secure_password():
    """
    Generate a secure 7-character password that includes:
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character from @$!%*?&
    """
    # Define character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special_chars = '@$!%*?&'
    
    # Ensure at least one character from each category
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special_chars)
    ]
    
    # Fill the remaining 3 positions with random choices from all categories
    all_chars = uppercase + lowercase + digits + special_chars
    password.extend(secrets.choice(all_chars) for _ in range(3))
    
    # Shuffle the password to randomize positions
    secrets.SystemRandom().shuffle(password)
    
    # Convert to string
    final_password = ''.join(password)
    
    # Verify the password meets our regex criteria
    regex_pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{7}$'
    
    if re.match(regex_pattern, final_password):
        return final_password
    else:
        # If for some reason it doesn't match, recursively generate again
        return generate_secure_password()

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


# def rvsf_signup_view(request):
#     if request.method == 'POST':
#         username = generate_unique_username()
#         password = generate_secure_password()
#         print(password)
#         # password = request.POST.get('password')
#         hashed_password = make_password(password)
#         # confirm_password = request.POST.get('confirm_password')
        
#         auth_email = request.POST.get('auth_email')
#         auth_mobile = request.POST.get('auth_mobile')
#         auth_pan = request.POST.get('auth_pan')
#         gst_no = request.POST.get('gst_no')
#         company_name = request.POST.get('company_name')
#         legal_name = request.POST.get('legal_name')
#         company_email = request.POST.get('company_email')
#         business_category = request.POST.get('business_category')
#         registered_address = request.POST.get('registered_address')
#         state = request.POST.get('state')
#         district = request.POST.get('district')
#         pin_code = request.POST.get('pin_code')
#         website = request.POST.get('website')
#         company_pan = request.POST.get('company_pan')
#         tin_no = request.POST.get('tin_no')
#         cin = request.POST.get('cin')
#         iec = request.POST.get('iec')

#         # Password confirmation check
#         # if password != confirm_password:
#         #     messages.error(request, "Passwords do not match.")
#         #     return redirect('rvsf_signup')

#         # GST uniqueness check
#         if RvsfRegistration.objects.filter(gst_no=gst_no).exists():
#             messages.error(request, "GST No. is already registered.")
#             return redirect('rvsf_signup')

#         print('ddasdasasdasdasdsdasda')
#         # Save the data
#         RvsfRegistration.objects.create(
#             username=username,
#             password= hashed_password,  # 🔐 hash the password
#             auth_email=auth_email,
#             auth_mobile=auth_mobile,
#             auth_pan=auth_pan,
#             gst_no=gst_no,
#             company_name=company_name,
#             legal_name=legal_name,
#             company_email=company_email,
#             business_category=business_category,
#             registered_address=registered_address,
#             state=state,
#             district=district,
#             pin_code=pin_code,
#             website=website,
#             company_pan=company_pan,
#             tin_no=tin_no,
#             cin=cin,
#             iec=iec
#         )

#         sendsigupemail(username,auth_email,password)

#         messages.success(request, f"Account created successfully. Your username is {username}")

#         return redirect('rvsf_home')  # ✅ Update with your actual route
#     else:
#         states = State.objects.all() 
#         return render(request, 'authentication/registration.html', {'states': states})
# def sendNewPasswordemail(username,auth_email,password):
#     # Disable SSL warnings for development (not recommended for production)
#     ssl._create_default_https_context = ssl._create_unverified_context
#     urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#     # Prepare the email
#     message = Mail(
#         from_email='kumar.ashish.cpcb@gmail.com',  # Your verified sender email in SendGrid
#         to_emails=auth_email,
#         subject='Password Changed Successfully EPR End of Life Vehicle',
#         html_content=f"""
#             <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
#                 <p>Dear <strong>{username}</strong>,</p>

#                 <p>Your password has been successfully changed for the 
#                 <strong>EPR End of Life Vehicle</strong> portal.</p>

#                 <div style="background-color: #f5f7fa; border: 1px solid #ddd; border-radius: 6px; padding: 12px; margin: 15px 0;">
#                     <p style="margin: 4px 0;"><strong>Username:</strong> {username}</p>
#                     <p style="margin: 4px 0;"><strong>Password:</strong> {password}</p>
#                 </div>

#                 <p>Please keep these details safe and do not share them with anyone.</p>

#                 <p>Regards,<br>
#                 Central Pollution Control Board (CPCB)</p>
#             </div>
#             """
#     )

#     # Send the email
#     try:
#         sg = SendGridAPIClient(api_key=Send_Grid_Api_Key)
#         response = sg.send(message)
#         print(f"Email sent successfully. Status Code: {response.status_code}")
#         return True

#     except Exception as e:
#         print(f"Error sending email: {e}")
#         return HttpResponse(f"Error sending email: {e}")

class ChangePasswordFirst(View):

    def get(self, request):
        # print("🔹 Entered ChangePasswordFirst GET method")

        user_id = request.session.get('user_id')
        # print(f"🧑 Session user_id: {user_id}")

        if not user_id:
            # print("❌ No user_id found in session — redirecting to login")
            messages.error(request, "Session expired. Please login again.")
            return redirect('rvsf_home')

        user = RvsfRegistration.objects.filter(id=user_id).first()
        # print(f"🔍 User fetched: {user}")

        if not user:
            # print("❌ User not found in DB — redirecting to login")
            messages.error(request, "User not found.")
            return redirect('rvsf_home')

        # fresh_count = producerGeneralDetails.objects.filter(application_type=0, forwarded_to=user_id).count()
        # resubmit_count = producerGeneralDetails.objects.filter(application_type=1, forwarded_to=user_id).count()
        # print(f"📊 Fresh count: {fresh_count}, Resubmit count1: {resubmit_count}")

        return render(request, 'authentication/change_password.html', {
            'url': 'login/change_password/',
            # 'fresh_count': fresh_count,
            # 'resubmit_count': resubmit_count,
            'form': OTPForm(),
        })

    def post(self, request):
        # print("🔹 Entered ChangePasswordFirst POST method")

        user_id = request.session.get('user_id')
        # print(f"🧑 Session user_id: {user_id}")

        if not user_id:
            print("❌ No user_id in session")
            # messages.error(request, "Session expired. Please login again.")
            return redirect('rvsf_home')
        
        enc_oldPassword = request.POST.get('old_password')
        enc_newPassword = request.POST.get('new_password')
        enc_confirmPassword = request.POST.get('confirm_password')

        # print(f"🔒 Encrypted old_password: {enc_oldPassword}")
        # print(f"🔒 Encrypted new_password: {enc_newPassword}")
        # print(f"🔒 Encrypted confirm_password: {enc_confirmPassword}")

        try:
            old_password = decrypt_aes(enc_oldPassword)
            new_password = decrypt_aes(enc_newPassword)
            confirm_password = decrypt_aes(enc_confirmPassword)
            # print(f"🔓 Decrypted old_password: {old_password}")
            # print(f"🔓 Decrypted new_password: {new_password}")
            # print(f"🔓 Decrypted confirm_password: {confirm_password}")
        except Exception as e:
            # print(f"❌ Password decryption failed: {e}")
            messages.error(request, "Passwords not match")
            return redirect('change-password-first')

        try:
            user = RvsfRegistration.objects.get(id=user_id)
            # print(f"✅ User fetched: {user.username}")
        except RvsfRegistration.DoesNotExist:
            # print("❌ User not found in DB")
            messages.error(request, "User not found.")
            return redirect('change-password-first')

        # print("🔑 Checking old password...")
        if not check_password(old_password, user.password):
            # print("❌ Old password is incorrect")
            messages.error(request, "Old password is incorrect.")
            return redirect('change-password-first')

        if new_password != confirm_password:
            # print("❌ New password and confirm password mismatch")
            messages.error(request, "New password and confirm password do not match.")
            return redirect('change-password-first')

        # print("🧠 Validating new password strength...")
        if not self.is_strong_password(new_password):
            # print("❌ Weak password entered")
            messages.error(request, "Password must be at least 8 characters long and include uppercase, lowercase, digit, and special character.")
            return redirect('change-password-first')

        # Check against last 3 passwords
        # print("📜 Checking password history...")
        password_history = json.loads(user.password_history or '[]')
        recent_passwords = [user.password] + password_history[:2]

        for old_hashed in recent_passwords:
            if check_password(new_password, old_hashed):
                # print("❌ New password matches one of the last 3 passwords")
                messages.error(request, "New password must not match any of the last 3 passwords.")
                return redirect('change-password-first')

        # Update password
        # print("💾 Updating password...")
        new_hashed = make_password(new_password)
        updated_history = [user.password] + password_history
        user.password_history = json.dumps(updated_history[:3])
        user.password = new_hashed
        user.first_login = 1
        user.save()
        # print("✅ Password updated and saved")

        # print("📧 Sending new password email...")
        # sendNewPasswordemail(user.username, user.company_email, new_password)
        sendNewPasswordEmail(user.company_name, user.username, user.company_email, new_password)

        messages.success(request, "Password changed successfully.")
        # print("🏁 Redirecting to rvsf_dashboard")
        return redirect('rvsf_dashboard')

    def is_strong_password(self, password):
        print(f"🧩 Checking password strength for: {password}")
        return (
            len(password) >= 8 and
            re.search(r'[A-Z]', password) and
            re.search(r'[a-z]', password) and
            re.search(r'\d', password) and
            re.search(r'[!@#$%^&*(),.?\":{}|<>]', password)
        )

class ChangePasswordView(View):

    def get(self, request):
        print("🔹 Entered ChangePasswordView GET method")

        user_id = request.session.get('user_id')
        print(f"🧑 Session user_id: {user_id}")

        userdata = RvsfRegistration.objects.filter(id=user_id).first()
        print(f"🔍 User data fetched: {userdata}")

        fresh_count = producerGeneralDetails.objects.filter(application_type=0, forwarded_to=request.user.id).count()
        resubmit_count = producerGeneralDetails.objects.filter(application_type=1, forwarded_to=request.user.id).count()
        print(f"📊 Fresh count: {fresh_count}, Resubmit count2: {resubmit_count}")

        entitytype_list = userdata.entity_types.split(',') if userdata and userdata.entity_types else []
        print(f"🏷 Entity types: {entitytype_list}")

        return render(request, 'authentication/change_password_new.html', {
            'url': 'change-password1',
            'entity_types': [e.strip() for e in entitytype_list],
            'fresh_count': fresh_count,
            'resubmit_count': resubmit_count,
            'form': OTPForm(),
        })

    def post(self, request):
        print("🔹 Entered ChangePasswordView POST method")

        username = request.session.get('username')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        print(f"👤 Username from session: {username}")
        print(f"🔑 Old password entered: {old_password}")
        print(f"🆕 New password: {new_password}")
        print(f"✅ Confirm password: {confirm_password}")

        try:
            user = RvsfRegistration.objects.get(username=username)
            print(f"✅ User fetched: {user.username}")
        except RvsfRegistration.DoesNotExist:
            print("❌ User not found")
            messages.error(request, "User not found.")
            return redirect('change_password')

        print(f"🔍 User current hashed password: {user.password}")

        if not check_password(old_password, user.password):
            print("❌ Old password incorrect")
            messages.error(request, "Old password is incorrect.")
            return redirect('change_password')

        if new_password != confirm_password:
            print("❌ New and confirm password do not match")
            messages.error(request, "New password and confirm password do not match.")
            return redirect('change_password')

        print("🧠 Validating password strength...")
        if not self.is_strong_password(new_password):
            print("❌ Weak password")
            messages.error(request, "New password must be at least 8 characters long, contain uppercase, lowercase, number, and special character.")
            return redirect('change_password')

        print("📜 Checking password history...")
        password_history = json.loads(user.password_history or '[]')
        recent_passwords = [user.password] + password_history[:2]

        for old_hashed in recent_passwords:
            if check_password(new_password, old_hashed):
                print("❌ New password matches a recent one")
                messages.error(request, "New password must not match any of the last 3 passwords.")
                return redirect('change_password')

        print("💾 Updating new password and history...")
        new_hashed = make_password(new_password)
        updated_history = [user.password] + password_history
        user.password_history = json.dumps(updated_history[:3])
        user.password = new_hashed
        user.save()
        print("✅ Password updated successfully")

        messages.success(request, "Password changed successfully.")
        print("🏁 Redirecting to rvsf_dashboard")
        return redirect('rvsf_dashboard')

    def is_strong_password(self, password):
        print(f"🧩 Checking password strength for: {password}")
        return (
            len(password) >= 8 and
            re.search(r'[A-Z]', password) and
            re.search(r'[a-z]', password) and
            re.search(r'\d', password) and
            re.search(r'[!@#$%^&*(),.?\":{}|<>]', password)
        )


def generate_username(gst_number):
    # Get full 4-digit year
    year_str = datetime.now().strftime('%Y')  # e.g., '2025'

    # Get last 2 characters of the GST number
    gst_suffix = gst_number[-2:] if gst_number and len(gst_number) >= 2 else '00'

    # File to store serial number
    sequence_file = 'sequence_rvsf.txt'

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
    return f'R{year_str}{gst_suffix}{serial_str}'

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


class RegistrationrvsfView(View):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        
        def get(self, request):
            states = State.objects.all()
            form = CaptchaForm()
            return render(request, 'authentication/registration.html', {'states': states, 'form': form})
        def post(self, request):
            logger.info("=== Starting post method ===")
            logger.info("Fetching all states from database")
            states = State.objects.all()
            logger.info(f"Retrieved {states.count()} states")
            
            logger.info("Getting POST data")
            post_data = request.POST
            logger.info(f"POST data keys: {list(post_data.keys())}")
            
            logger.info("Initializing CaptchaForm with POST data")
            form = CaptchaForm(request.POST)
            logger.info("Initializing errors list")
            errors = []
            
            logger.info("Checking if form is valid")
            if not form.is_valid():
                logger.info("Form is invalid - Captcha validation failed")
                errors.append("Invalid Captcha. Please try again.")
                logger.info(f"Added error: {errors[-1]}")
                for error in errors:
                    logger.info(f"Adding message for error: {error}")
                    messages.error(request, error)
                logger.info("Rendering registration page with new captcha")
                return render(request, 'authentication/registration.html', {
                    'states': states,
                    'form': CaptchaForm(),  # reload new captcha
                    'form_data': post_data,
                    'errors': errors,
                })
            logger.info("Form is valid - Captcha passed")

            logger.info("Extracting entity list from POST data")
            entity_list = post_data.getlist('entity[]') or [post_data.get('entity')]
            logger.info(f"Entity list: {entity_list}")
            
            logger.info("Extracting GST number")
            gst_no = post_data.get("gst_no", "").strip().upper()
            logger.info(f"GST number: {gst_no}")
            
            logger.info("Extracting verified GST number")
            gst_verified_no = post_data.get("gst_verified_no", "").strip().upper()
            logger.info(f"Verified GST number: {gst_verified_no}")
            
            logger.info("Extracting company email")
            company_email = post_data.get('company_email')
            logger.info(f"Company email: {company_email}")
            
            logger.info("Extracting authorized person email")
            email = post_data.get('authorized_person_email')
            logger.info(f"Authorized person email: {email}")
            
            logger.info("Extracting authorized person name")
            authorized_person_name = post_data.get('authorized_person_name')
            logger.info(f"Authorized person name: {authorized_person_name}")
            
            logger.info("Extracting company name")
            company_name = post_data.get('company_name', '').strip()
            logger.info(f"Company name: {company_name}")
            
            logger.info("Extracting business category")
            business_category = post_data.get('business_category', '').strip()
            logger.info(f"Business category: {business_category}")
            
            logger.info("Extracting state")
            state = post_data.get('state')
            logger.info(f"State: {state}")
            
            logger.info("Extracting district")
            district = post_data.get('district')
            logger.info(f"District: {district}")
            
            logger.info("Extracting company PAN")
            company_pan = post_data.get('pan_no')
            logger.info(f"Company PAN: {company_pan}")
            
            logger.info("Extracting authorized person PAN")
            auth_pan = post_data.get('authorized_person_pan')
            logger.info(f"Authorized person PAN: {auth_pan}")
            
            logger.info("Extracting authorized person mobile")
            authorized_person_mobile = post_data.get('authorized_person_mobile')
            logger.info(f"Authorized person mobile: {authorized_person_mobile}")
            
            logger.info("Extracting registered address")
            registered_address = post_data.get('registered_address', '').strip()
            logger.info(f"Registered address: {registered_address[:100]}..." if len(registered_address) > 100 else f"Registered address: {registered_address}")

            logger.info("Starting GST verification")
            # ------------------ GST Verification ------------------
            api_url = "https://apiservices.cpcb.gov.in/gst/details"
            logger.info(f"GST API URL: {api_url}")
            payload = {"gstNo": gst_no}
            logger.info(f"GST API payload: {payload}")
            headers = {"Content-Type": "application/json"}
            logger.info(f"GST API headers: {headers}")
            
            try:
                logger.info("Sending POST request to GST API")
                response = requests.post(api_url, json=payload, headers=headers, timeout=20, verify=False)
                logger.info(f"GST API response status code: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info("GST API returned 200 OK")
                    result = response.json()
                    logger.info(f"GST API response data: {result}")
                    
                    if not result.get("status") or "data" not in result:
                        logger.warning("GST Number not found or inactive")
                        errors.append("GST Number not found or inactive.")
                        logger.info(f"Added error: {errors[-1]}")
                    else:
                        logger.info("GST data found successfully")
                        gst_data = result["data"]
                        logger.info(f"GST data: {gst_data}")
                        api_gstin = gst_data.get("gstin", "").upper()
                        logger.info(f"API GSTIN: {api_gstin}")
                        # if gst_no != api_gstin or gst_verified_no != api_gstin:
                        #     errors.append("GST Number mismatch. Please fetch GST details again.")

                        logger.info(f"Updating company name from GST data: {gst_data.get('tradeNam', company_name)}")
                        company_name = gst_data.get("tradeNam", company_name)
                        legal_name = gst_data.get("lgnm", "")
                        logger.info(f"Legal name from GST: {legal_name}")
                        logger.info(f"Updating business category from GST data: {gst_data.get('ctb', business_category)}")
                        business_category = gst_data.get("ctb", business_category)
                else:
                    logger.warning(f"GST API returned non-200 status: {response.status_code}")
                    errors.append("Failed to fetch GST details from CPCB. Try again later.")
                    logger.info(f"Added error: {errors[-1]}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error connecting to GST API: {str(e)}", exc_info=True)
                errors.append(f"Error connecting to GST API: {str(e)}")
                logger.info(f"Added error: {errors[-1]}")

            logger.info("Starting email validation")
            # ------------------ Email Validation ------------------
            context = {'states': states, 'form_data': post_data}
            logger.info(f"Context created: {context.keys()}")

            try:
                logger.info(f"Validating company email: {company_email}")
                validate_email(company_email)
                logger.info("Company email validation passed")
            except ValidationError as e:
                logger.warning(f"Company email validation failed: {str(e)}")
                errors.append("Invalid Company Email format.")
                logger.info(f"Added error: {errors[-1]}")

            try:
                logger.info(f"Validating authorized person email: {email}")
                validate_email(email)
                logger.info("Authorized person email validation passed")
            except ValidationError as e:
                logger.warning(f"Authorized person email validation failed: {str(e)}")
                errors.append("Invalid Authorized Person Email format.")
                logger.info(f"Added error: {errors[-1]}")

            logger.info(f"Checking if company email domain is blocked: {company_email}")
            if is_blocked_domain(company_email):
                logger.warning(f"Company email domain is blocked: {company_email}")
                errors.append(
                    "Company email must be an official domain email. "
                    "Disposable or public email domains are not allowed."
                )
                logger.info(f"Added error: {errors[-1]}")

            logger.info(f"Checking if authorized person email domain is blocked: {email}")
            if is_blocked_domain(email):
                logger.warning(f"Authorized person email domain is blocked: {email}")
                errors.append(
                    "Authorized person email must be an official domain email. "
                    "Disposable or public email domains are not allowed."
                )
                logger.info(f"Added error: {errors[-1]}")

            logger.info("Starting OTP verification checks")
            # ------------------ OTP Verification (cache-based) ------------------
            logger.info(f"Checking OTP verification for company email: {company_email}")
            is_company_email_verified = cache.get(f"otp_verified_company_email_{company_email}", False)
            logger.info(f"Company email verified status: {is_company_email_verified}")
            
            logger.info(f"Checking OTP verification for authorized email: {email}")
            is_auth_email_verified = cache.get(f"otp_verified_authorized_person_email_{email}", False)
            logger.info(f"Authorized email verified status: {is_auth_email_verified}")
            
            logger.info(f"Checking OTP verification for mobile: {authorized_person_mobile}")
            is_mobile_verified = cache.get(f"otp_verified_authorized_person_mobile_{authorized_person_mobile}", False)
            logger.info(f"Mobile verified status: {is_mobile_verified}")

            logger.info("Checking if company email and authorized email are the same")
            if company_email and email and company_email.lower() == email.lower():
                logger.warning(f"Company email and authorized email are the same: {company_email}")
                errors.append("Company Email and Authorized Person Email should not be same.")
                logger.info(f"Added error: {errors[-1]}")

            if not is_company_email_verified:
                logger.warning("Company Email OTP not verified")
                errors.append("Company Email OTP not verified.")
                logger.info(f"Added error: {errors[-1]}")
            if not is_auth_email_verified:
                logger.warning("Authorized Person Email OTP not verified")
                errors.append("Authorized Person Email OTP not verified.")
                logger.info(f"Added error: {errors[-1]}")
            if not is_mobile_verified:
                logger.warning("Mobile OTP not verified")
                errors.append("Mobile OTP not verified.")
                logger.info(f"Added error: {errors[-1]}")

            logger.info("Starting duplicate checks")
            # ------------------ Duplicate Checks ------------------
            logger.info(f"Checking if GST number already exists: {gst_no}")
            if RvsfRegistration.objects.filter(gst_no=gst_no).exists():
                logger.warning(f"GST number already registered: {gst_no}")
                errors.append("GST Number is already registered.")
                logger.info(f"Added error: {errors[-1]}")
            elif not company_name or not business_category:
                logger.warning(f"Company name or business category missing - company_name: {company_name}, business_category: {business_category}")
                errors.append("GST Number not found or inactive.")
                logger.info(f"Added error: {errors[-1]}")

            logger.info(f"Checking if company email already exists: {company_email}")
            if RvsfRegistration.objects.filter(company_email=company_email).exists():
                logger.warning(f"Company email already exists: {company_email}")
                errors.append("Company email already exists.")
                logger.info(f"Added error: {errors[-1]}")
            
            logger.info(f"Checking if authorized person email already exists: {email}")
            if RvsfRegistration.objects.filter(auth_email=email).exists():
                logger.warning(f"Authorized person email already exists: {email}")
                errors.append("Authorized person email already exists.")
                logger.info(f"Added error: {errors[-1]}")
            
            logger.info(f"Checking if authorized person mobile already exists: {authorized_person_mobile}")
            if RvsfRegistration.objects.filter(auth_mobile=authorized_person_mobile).exists():
                logger.warning(f"Authorized person mobile already exists: {authorized_person_mobile}")
                errors.append("Authorized person contact already exists.")
                logger.info(f"Added error: {errors[-1]}")

            logger.info(f"Checking if state and district are provided - state: {state}, district: {district}")
            if not state or not district:
                logger.warning("State or district missing")
                errors.append("State and District are required.")
                logger.info(f"Added error: {errors[-1]}")

            logger.info(f"Total errors collected: {len(errors)}")
            if errors:
                logger.warning(f"Returning with {len(errors)} errors")
                for error in errors:
                    logger.info(f"Adding message for error: {error}")
                    messages.error(request, error)
                logger.info("Rendering registration page with errors")
                return render(request, 'authentication/registration.html', {
                    'states': states,
                    'form_data': post_data,
                    'entity_selected': entity_list,
                    'errors': errors,
                    'is_company_email_verified': is_company_email_verified,
                    'is_auth_email_verified': is_auth_email_verified,
                    'is_mobile_verified': is_mobile_verified,
                })

            logger.info("No errors found. Proceeding with user creation")
            # ------------------ Create User ------------------
            logger.info(f"Generating username from GST number: {gst_no}")
            username = generate_username(gst_no)
            logger.info(f"Generated username: {username}")
            
            logger.info("Generating password")
            password = generate_password()
            print(password)
            print(username)
            logger.info(f"Generated password (masked): {'*' * len(password)}")
            
            logger.info("Hashing password")
            password_hashed = make_password(password)
            logger.info("Password hashed successfully")

            logger.info("Creating RvsfRegistration object")
            registration = RvsfRegistration.objects.create(
                gst_no=gst_no,
                company_name=company_name,
                legal_name=post_data.get('legal_name'),
                company_email=company_email,
                business_category=business_category,
                registered_address=registered_address,
                state=state,
                district=district,
                website=post_data.get('website'),
                pin_code=post_data.get('pin_code'),
                company_pan=company_pan,
                tin_no=post_data.get('tin'),
                cin=post_data.get('cin'),
                password=password_hashed,
                username=username,
                auth_email=email,
                auth_mobile=authorized_person_mobile,
                auth_pan=auth_pan,
                # entity_types=','.join(entity_list),
                authorized_person_name=authorized_person_name,
                auth_designation=post_data.get('authorized_person_designation'),
                # authorized_person_pan=auth_pan,
            )
            logger.info(f"Registration object created with ID: {registration.id if hasattr(registration, 'id') else 'unknown'}")

            logger.info("Saving registration to database")
            registration.save()
            logger.info("Registration saved successfully")

            logger.info("Starting credential sending process")
            # ------------------ Send Credentials ------------------
            try:
                logger.info("Sending signup emails and SMS")
                # sendsigupemail(company_name, username, company_email, password)
                # sendsigupemail(authorized_person_name, username, email, password)
                # sendsigupemail(authorized_person_name, username, company_email, password)
                logger.info(f"Sending signup email to authorized person: {authorized_person_name} at {email}")
                sendSignupEmail(authorized_person_name, username, email, password)
                logger.info("Email sent to authorized person")
                
                logger.info(f"Sending signup email to company: {company_name} at {company_email}")
                sendSignupEmail(company_name, username, company_email, password)
                logger.info("Email sent to company")
                
                logger.info(f"Sending signup SMS to: {authorized_person_mobile}")
                send_signup_sms(authorized_person_mobile)
                logger.info("SMS sent successfully")
                
                # Clear OTP verification cache
                logger.info(f"Clearing OTP verification cache for company email: {company_email}")
                cache.delete(f"otp_verified_company_email_{company_email}")
                logger.info(f"Clearing OTP verification cache for authorized email: {email}")
                cache.delete(f"otp_verified_authorized_email_{email}")
                logger.info(f"Clearing OTP verification cache for mobile: {authorized_person_mobile}")
                cache.delete(f"otp_verified_mobile_{authorized_person_mobile}")
                logger.info("All OTP caches cleared")
                
                logger.info("Returning registration success page")
                return render(request, 'authentication/registration.html', {'registration_success': True})
            except Exception as e:
                logger.error(f"Failed to send credentials: {str(e)}", exc_info=True)
                logger.warning(f"Registration saved, but failed to send credentials: {e}")
                messages.warning(request, f"Registration saved, but failed to send credentials: {e}")
                logger.info("Redirecting to RVSF home page")
                return redirect('rvsf_home')
        # def post(self, request):
        #     states = State.objects.all()
        #     post_data = request.POST
        #     form = CaptchaForm(request.POST)
        #     errors = []
            
        #     if not form.is_valid():
        #         errors.append("Invalid Captcha. Please try again.")
        #         for error in errors:
        #             messages.error(request, error)
        #         return render(request, 'authentication/registration.html', {
        #             'states': states,
        #             'form': CaptchaForm(),  # reload new captcha
        #             'form_data': post_data,
        #             'errors': errors,
        #         })

        #     entity_list = post_data.getlist('entity[]') or [post_data.get('entity')]
        #     gst_no = post_data.get("gst_no", "").strip().upper()
        #     gst_verified_no = post_data.get("gst_verified_no", "").strip().upper()
        #     company_email = post_data.get('company_email')
        #     email = post_data.get('authorized_person_email')
        #     authorized_person_name = post_data.get('authorized_person_name')
        #     company_name = post_data.get('company_name', '').strip()
        #     business_category = post_data.get('business_category', '').strip()
        #     state = post_data.get('state')
        #     district = post_data.get('district')
        #     company_pan = post_data.get('pan_no')
        #     auth_pan = post_data.get('authorized_person_pan')
        #     authorized_person_mobile = post_data.get('authorized_person_mobile')
        #     registered_address = post_data.get('registered_address', '').strip()

            

        #     # ------------------ GST Verification ------------------
        #     api_url = "https://apiservices.cpcb.gov.in/gst/details"
        #     payload = {"gstNo": gst_no}
        #     headers = {"Content-Type": "application/json"}
        #     try:
        #         response = requests.post(api_url, json=payload, headers=headers, timeout=20, verify=False)
        #         if response.status_code == 200:
        #             result = response.json()
        #             if not result.get("status") or "data" not in result:
        #                 errors.append("GST Number not found or inactive.")
        #             else:
        #                 gst_data = result["data"]
        #                 api_gstin = gst_data.get("gstin", "").upper()
        #                 # if gst_no != api_gstin or gst_verified_no != api_gstin:
        #                 #     errors.append("GST Number mismatch. Please fetch GST details again.")

        #                 company_name = gst_data.get("tradeNam", company_name)
        #                 legal_name = gst_data.get("lgnm", "")
        #                 business_category = gst_data.get("ctb", business_category)
        #         else:
        #             errors.append("Failed to fetch GST details from CPCB. Try again later.")
        #     except requests.exceptions.RequestException as e:
        #         errors.append(f"Error connecting to GST API: {str(e)}")

        #     # ------------------ Email Validation ------------------
        #     context = {'states': states, 'form_data': post_data}

        #     try:
        #         validate_email(company_email)
        #     except ValidationError:
        #         errors.append("Invalid Company Email format.")

        #     try:
        #         validate_email(email)
        #     except ValidationError:
        #         errors.append("Invalid Authorized Person Email format.")

        #     if is_blocked_domain(company_email):
        #         errors.append(
        #             "Company email must be an official domain email. "
        #             "Disposable or public email domains are not allowed."
        #         )

        #     if is_blocked_domain(email):
        #         errors.append(
        #             "Authorized person email must be an official domain email. "
        #             "Disposable or public email domains are not allowed."
        #         )

        #     # ------------------ OTP Verification (cache-based) ------------------
        #     is_company_email_verified = cache.get(f"otp_verified_company_email_{company_email}", False)
        #     is_auth_email_verified = cache.get(f"otp_verified_authorized_person_email_{email}", False)
        #     is_mobile_verified = cache.get(f"otp_verified_authorized_person_mobile_{authorized_person_mobile}", False)

        #     if company_email and email and company_email.lower() == email.lower():
        #         errors.append("Company Email and Authorized Person Email should not be same.")

        #     if not is_company_email_verified:
        #         errors.append("Company Email OTP not verified.")
        #     if not is_auth_email_verified:
        #         errors.append("Authorized Person Email OTP not verified.")
        #     if not is_mobile_verified:
        #         errors.append("Mobile OTP not verified.")

        #     # ------------------ Duplicate Checks ------------------
        #     if RvsfRegistration.objects.filter(gst_no=gst_no).exists():
        #         errors.append("GST Number is already registered.")
        #     elif not company_name or not business_category:
        #         errors.append("GST Number not found or inactive.")

        #     if RvsfRegistration.objects.filter(company_email=company_email).exists():
        #         errors.append("Company email already exists.")
        #     if RvsfRegistration.objects.filter(auth_email=email).exists():
        #         errors.append("Authorized person email already exists.")
        #     if RvsfRegistration.objects.filter(auth_mobile=authorized_person_mobile).exists():
        #         errors.append("Authorized person contact already exists.")

        #     if not state or not district:
        #         errors.append("State and District are required.")

        #     if errors:
        #         for error in errors:
        #             messages.error(request, error)
        #         return render(request, 'authentication/registration.html', {
        #             'states': states,
        #             'form_data': post_data,
        #             'entity_selected': entity_list,
        #             'errors': errors,
        #             'is_company_email_verified': is_company_email_verified,
        #             'is_auth_email_verified': is_auth_email_verified,
        #             'is_mobile_verified': is_mobile_verified,
        #         })

        #     # ------------------ Create User ------------------
        #     username = generate_username(gst_no)
        #     password = generate_password()
        #     print(password)
        #     print(username)
        #     password_hashed = make_password(password)

        #     registration = RvsfRegistration.objects.create(
        #         gst_no=gst_no,
        #         company_name=company_name,
        #         legal_name=post_data.get('legal_name'),
        #         company_email=company_email,
        #         business_category=business_category,
        #         registered_address=registered_address,
        #         state=state,
        #         district=district,
        #         website=post_data.get('website'),
        #         pin_code=post_data.get('pin_code'),
        #         company_pan=company_pan,
        #         tin_no=post_data.get('tin'),
        #         cin=post_data.get('cin'),
        #         password=password_hashed,
        #         username=username,
        #         auth_email=email,
        #         auth_mobile=authorized_person_mobile,
        #         auth_pan=auth_pan,
        #         # entity_types=','.join(entity_list),
        #         authorized_person_name=authorized_person_name,
        #         auth_designation=post_data.get('authorized_person_designation'),
        #         # authorized_person_pan=auth_pan,
        #     )

        #     registration.save()

        #     # ------------------ Send Credentials ------------------
        #     try:
        #         # sendsigupemail(company_name, username, company_email, password)
        #         # sendsigupemail(authorized_person_name, username, email, password)
        #         # sendsigupemail(authorized_person_name, username, company_email, password)
        #         sendSignupEmail(authorized_person_name, username, email, password)
        #         sendSignupEmail(company_name, username, company_email, password)
        #         send_signup_sms(authorized_person_mobile)
        #         # Clear OTP verification cache
        #         cache.delete(f"otp_verified_company_email_{company_email}")
        #         cache.delete(f"otp_verified_authorized_email_{email}")
        #         cache.delete(f"otp_verified_mobile_{authorized_person_mobile}")
        #         return render(request, 'authentication/registration.html', {'registration_success': True})
        #     except Exception as e:
        #         messages.warning(request, f"Registration saved, but failed to send credentials: {e}")
        #         return redirect('rvsf_home') 
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving registrationrvsf view")
                krishan_logger.error(f"Exact registrationrvsf view  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact registrationrvsf view Error: {str(db_error)}")

def load_districts(request):
    state_id = request.GET.get('state_id')
    districts = District.objects.filter(state_id=state_id).values('city_id', 'city_name')
    return JsonResponse(list(districts), safe=False)  # Send data as JSON
@login_required
def dashboard(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        userid = request.session.get('user_id')
        data = RvsfRegistration.objects.filter(id=userid).first()
        statename = State.objects.filter(state_id=data.state).first()
        districtname = District.objects.filter(city_id=data.district).first()
        conapplication = ConfirmApplication.objects.filter(userid=userid).first()

        # Session expiry
        request.session.set_expiry(timedelta(hours=1))
        remaining_seconds = request.session.get_expiry_age()
        appstatus = conapplication.appstatus if conapplication else 0
        has_application = conapplication is not None
        print(has_application)
        # Encrypt all values
        encrypted_context = {
            'user_encrypted': encrypt_aes(data.company_name),
            'email_encrypted': encrypt_aes(data.company_email),
            'gst_encrypted': encrypt_aes(data.gst_no),
            'pan_encrypted': encrypt_aes(data.auth_pan),
            'mobile_encrypted': encrypt_aes(data.auth_mobile),
            'state_encrypted': encrypt_aes(statename.state_name),
            'district_encrypted': encrypt_aes(districtname.city_name),
            'pincode_encrypted': encrypt_aes(str(data.pin_code)),
            # 'confirm_encrypted': encrypt_aes(str(conapplication.appstatus)),
            'confirm_encrypted': encrypt_aes(str(appstatus)), 
            'remaining_encrypted': encrypt_aes(str(remaining_seconds)),
            'encrypted_userid': encrypt_aes(str(data.id)),
            'has_application': has_application,
            'certificate':data,
        }

        return render(request, 'user/dashboard.html', encrypted_context)
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving dashboard")
                krishan_logger.error(f"Exact dashboard  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact dashboard Error: {str(db_error)}")

# def dashboard(request):
#     userid = request.session.get('user_id')
#     data = RvsfRegistration.objects.filter(id = userid).first()
#     statename = State.objects.filter(state_id = data.state).first()
#     districtname = District.objects.filter(city_id = data.district).first()
#     conapplication = ConfirmApplication.objects.filter(userid = userid).first()
    
#     # request.session.set_expiry(timedelta(seconds=180))
#     request.session.set_expiry(timedelta(hours=1))
#     remaining_seconds = request.session.get_expiry_age()
#     return render(request, 'user/dashboard.html',{ 'user':data , 'statename' : statename, 'districtname':districtname , 'confirm': conapplication , 'remaining_seconds': remaining_seconds})



@login_required
def checkapplication(request):
    user_id = int(request.session.get('user_id'))
    return ConfirmApplication.objects.filter(userid=user_id).count()


def check_user_status(request):

    if request.method == "POST":
        userid = request.POST.get('userid')

        record = ConfirmApplication.objects.filter(userid=userid).first()

        if record and record.incomplete == 1:   # your condition
            return JsonResponse({
                'status': 1,
                'message': 'Your application needs clarification. Please continue.',
                'redirect_url': reverse('TrackApplication')   # important
            })

        return JsonResponse({'status': 0})


# def rvsfdetails(request):

#     userid = request.session.get('user_id')
#     appcount = checkapplication(request)
#     states = State.objects.all() 
#     generalcheck=GeneralDetails.objects.filter(userid=userid,status='general').exist()
#     if appcount > 0:
#         messages.error(request, "You already have an active application!")
#         return redirect('rvsf_dashboard')
#     if request.method == 'POST':
#         address = request.POST.get('address')
#         latitude = request.POST.get('latitude')
#         longitude = request.POST.get('longitude')
#         state = request.POST.get('state')
#         # district = request.POST.get('district')
#         # pin_code = request.POST.get('pin_code')


#         cto_number = request.POST.get('cto_number')
#         consent_validity = request.POST.get('consent_validity')
#         cto_pdf = request.FILES.get('cto_pdf')

#         howm_validity = request.POST.get('howm_validity')
#         howm_pdf = request.FILES.get('howm_pdf')

#         dic_validity = request.POST.get('dic_validity')
#         dic_pdf = request.FILES.get('dic_pdf')

#         rvsf_reg_no = request.POST.get('rvsf_reg_no')
#         rvsf_validity = request.POST.get('rvsf_validity')
#         rvsf_pdf = request.FILES.get('rvsf_pdf')

#         process_flow_pdf = request.FILES.get('process_flow_pdf')
#         material_balance_pdf = request.FILES.get('material_balance_pdf')
#         annual_returns_pdf = request.FILES.get('annual_returns_pdf')
#         # tin_pdf = request.FILES.get('tin_pdf')
#         # pan_pdf = request.FILES.get('pan_pdf')
#         # gst_pdf = request.FILES.get('gst_pdf')
#         # cin_pdf = request.FILES.get('cin_pdf')
#         # iec_pdf = request.FILES.get('iec_pdf')
#         # Validate PDF files
#         pdf_files = {
#             'CTO PDF': cto_pdf,
#             'HOWM PDF': howm_pdf,
#             'DIC PDF': dic_pdf,
#             'RVSF PDF': rvsf_pdf,
#             'Process Flow PDF': process_flow_pdf,
#             'Material Balance PDF': material_balance_pdf,
#             'Annual Returns PDF': annual_returns_pdf,
#             # 'Tin  PDF' : tin_pdf,
#             # 'Pan PDF' : pan_pdf,
#             # 'Gst PDF' : gst_pdf,
#             # 'CIN PDF' : cin_pdf,
#             # 'IEC PDF' : iec_pdf
#         }

#         for label, file in pdf_files.items():
#             if file and not file.name.lower().endswith('.pdf'):
#                 messages.error(request, f"{label} must be a PDF.")
#                 return redirect('rvsfdetails')

#         # Check if record exists
#         general = RvsfDetails.objects.filter(userid=userid).first()

#         if general:
#             # Update existing record
#             general.address = address
#             general.latitude = latitude
#             general.longitude = longitude
#             general.state = state
#             general.status = 'rvsf'
#             # general.district = district
#             # general.pin_code = pin_code

#             general.cto_number = cto_number
#             general.consent_validity = consent_validity
#             if cto_pdf:
#                 general.cto_pdf = cto_pdf

#             general.howm_validity = howm_validity
#             if howm_pdf:
#                 general.howm_pdf = howm_pdf

#             general.dic_validity = dic_validity
#             if dic_pdf:
#                 general.dic_pdf = dic_pdf

#             general.rvsf_reg_no = rvsf_reg_no
#             general.rvsf_validity = rvsf_validity
#             if rvsf_pdf:
#                 general.rvsf_pdf = rvsf_pdf

#             if process_flow_pdf:
#                 general.process_flow_pdf = process_flow_pdf

#             if material_balance_pdf:
#                 general.material_balance_pdf = material_balance_pdf

#             if annual_returns_pdf:
#                 general.annual_returns_pdf = annual_returns_pdf
#             # if pan_pdf:
#             #     general.pan_pdf = pan_pdf
#             # if cin_pdf:
#             #     general.cin_pdf = cin_pdf
#             # if tin_pdf:
#             #     general.tin_pdf = tin_pdf
#             # if gst_pdf:
#             #     general.gst_pdf = gst_pdf
#             # if iec_pdf:
#             #     general.iec_pdf = iec_pdf    

#             general.save()
#             messages.success(request, "RVSF details updated successfully.")
#         else:
#             # Create new record
#             RvsfDetails.objects.create(
#                 address=address,
#                 latitude=latitude,
#                 longitude=longitude,
#                 state=state,
#                 # district = district,
#                 # pin_code = pin_code,
#                 cto_number=cto_number,
#                 consent_validity=consent_validity,
#                 cto_pdf=cto_pdf,
#                 howm_validity=howm_validity,
#                 howm_pdf=howm_pdf,
#                 dic_validity=dic_validity,
#                 dic_pdf=dic_pdf,
#                 rvsf_reg_no=rvsf_reg_no,
#                 rvsf_validity=rvsf_validity,
#                 rvsf_pdf=rvsf_pdf,
#                 process_flow_pdf=process_flow_pdf,
#                 material_balance_pdf=material_balance_pdf,
#                 annual_returns_pdf=annual_returns_pdf,
#                 # tin_pdf = tin_pdf,
#                 # pan_pdf = pan_pdf,
#                 # gst_pdf = gst_pdf,
#                 # cin_pdf = cin_pdf,
#                 # iec_pdf = iec_pdf,
#                 status='rvsf',
#                 userid=userid
#             )
#             messages.success(request, "RVSF details saved successfully.")
        
#         # return redirect('generaldetails')
#         return redirect('equipmentDetails')

#     # GET Request
#     data = RvsfRegistration.objects.filter(id=userid).first()
#     generaldata = RvsfDetails.objects.filter(userid=userid).first()

#     statename = State.objects.filter(state_id=data.state).first()
#     districtname = District.objects.filter(city_id=data.district).first()

#     return render(request, 'user/rvsfdetails.html', {
#         'states': states,
#         'statename': statename,
#         'districtname': districtname,
#         'general': generaldata,
#         'data': data,
#     })
    


# Set up logging
@login_required
def rvsfdetails(request):
    krishan_logger = logging.getLogger('elv_logger')
    krishan_logger.info(f"=== Starting rvsfdetails view for request {request.method} ===")
    
    try:
        userid = request.session.get('user_id')
        krishan_logger.info(f"Session user_id: {userid}")
        
        if not userid:
            krishan_logger.warning("No user_id found in session")
            messages.error(request, "Please login first!")
            return redirect('login')
        
        # Check if GeneralDetails exists for this user
        krishan_logger.info("Checking if GeneralDetails exists...")
        general_exists = GeneralDetails.objects.filter(userid=userid, status='general').exists()
        krishan_logger.info(f"GeneralDetails exists: {general_exists}")
        
        # Redirect if GeneralDetails doesn't exist
        # if not general_exists:
        #     messages.error(request, "Please complete general details first!")
        #     return redirect('generaldetails')
        
        krishan_logger.info("Checking application count...")
        appcount = checkapplication(request)
        krishan_logger.info(f"Application count: {appcount}")
        
        states = State.objects.all() 
        krishan_logger.info(f"Found {states.count()} states")
        
        if appcount > 0:
            krishan_logger.warning(f"User {userid} already has an active application")
            messages.error(request, "You already have an active application!")
            return redirect('rvsf_dashboard')
            
        if request.method == 'POST':
            krishan_logger.info("Processing POST request...")
            
            # Extract form data
            address = request.POST.get('address')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            state = request.POST.get('state')
            district = request.POST.get('district')
            cto_number = request.POST.get('cto_number')
            encorp_year = request.POST.get('encorp_year')
            unit_commencement_year = request.POST.get('unit_commencement_year')
            consent_validity = request.POST.get('consent_validity')
            cto_pdf = request.FILES.get('cto_pdf')
            
            krishan_logger.debug(f"Basic fields - Address: {address[:50] if address else 'None'}, State: {state}, District: {district}")
            
            howm_validity = request.POST.get('howm_validity')
            howm_pdf = request.FILES.get('howm_pdf')
            
            dic_validity = request.POST.get('dic_validity')
            dic_pdf = request.FILES.get('dic_pdf')
            
            rvsf_reg_no = request.POST.get('rvsf_reg_no')
            rvsf_validity = request.POST.get('rvsf_validity')
            rvsf_pdf = request.FILES.get('rvsf_pdf')
            
            process_flow_pdf = request.FILES.get('process_flow_pdf')
            material_balance_pdf = request.FILES.get('material_balance_pdf')
            annual_returns_pdf = request.FILES.get('annual_returns_pdf')
            annual_returns_pdf1 = request.FILES.get('annual_returns_pdf1')
            annual_returns_pdf2 = request.FILES.get('annual_returns_pdf2')
            
            krishan_logger.info(f"File uploads - CTO PDF: {cto_pdf}, RVSF PDF: {rvsf_pdf}")
            
            # Field validation logging
            rvsf_fields = {
                'address': address,
                'latitude': latitude,
                'longitude': longitude,
                'state': state,
                'district': district,
                'cto_number': cto_number,
                'rvsf_reg_no': rvsf_reg_no,
                'encorp_year': encorp_year,
                'unit_commencement_year': unit_commencement_year,
            }
            
            krishan_logger.info("Starting field validation...")
            for field, value in rvsf_fields.items():
                krishan_logger.debug(f"Validating field {field} => {value}")
                
                if value:
                    value = value.strip()
                    krishan_logger.debug(f"Stripped value for {field}: {value}")
                    
                    if field in ['address','state','cto_number','rvsf_reg_no','district','encorp_year','unit_commencement_year']:
                        import re
                        if re.search(r'[^a-zA-Z0-9\s]', value):
                            krishan_logger.error(f"Special characters found in {field}: {value}")
                            messages.error(
                                request,
                                f"{field.replace('_', ' ').title()} should not contain special characters."
                            )
                            return redirect('rvsfdetails')
            
            krishan_logger.info("Field validation completed successfully")
            
            # PDF validation
            # PDF validation - only validate new uploads, allow existing files
            krishan_logger.info("Starting PDF validation...")

            # Check if we're updating an existing record
            general = RvsfDetails.objects.filter(userid=userid).first()

            # List of required PDF fields
            required_pdfs = [
                ("CTO PDF", cto_pdf, general.cto_pdf if general else None),
                ("HOWM PDF", howm_pdf, general.howm_pdf if general else None),
                ("DIC PDF", dic_pdf, general.dic_pdf if general else None),
                ("RVSF Registration PDF", rvsf_pdf, general.rvsf_pdf if general else None),
            ]

            for label, new_pdf, existing_pdf in required_pdfs:
                # Check if field is required (no existing file AND no new upload)
                if not new_pdf and not existing_pdf:
                    krishan_logger.error(f"{label} is required but not provided")
                    messages.error(request, f"{label} is required.")
                    return redirect('rvsfdetails')
                
                # Validate new uploads only
                if new_pdf:
                    krishan_logger.debug(f"Validating new {label}: {new_pdf.name}")
                    
                    # Size check
                    if new_pdf.size > 2 * 1024 * 1024:
                        krishan_logger.error(f"{label} size too large: {new_pdf.size} bytes")
                        messages.error(request, f"{label} must be less than 2MB.")
                        return redirect('rvsfdetails')
                    
                    # Valid PDF check
                    if not is_valid_pdf(new_pdf):
                        krishan_logger.error(f"{label} failed PDF validation")
                        messages.error(request, f"{label} is not a valid PDF file.")
                        return redirect('rvsfdetails')

            krishan_logger.info("Required PDF validation completed")
            
            # Optional PDF validation
            optional_pdfs = {
                'Process Flow PDF': process_flow_pdf,
                'Material Balance PDF': material_balance_pdf,
                'Annual Returns PDF': annual_returns_pdf,
                'Annual Returns PDF1': annual_returns_pdf1,
                'Annual Returns PDF2': annual_returns_pdf2,
            }
            
            for label, file in optional_pdfs.items():
                if file:
                    krishan_logger.debug(f"Checking optional {label}: {file.name}")
                    if not file.name.lower().endswith('.pdf'):
                        krishan_logger.error(f"{label} is not a PDF: {file.name}")
                        messages.error(request, f"{label} must be a PDF.")
                        return redirect('rvsfdetails')
            
            krishan_logger.info("Optional PDF validation completed")
            
            # Check if record exists
            krishan_logger.info("Checking for existing RvsfDetails record...")
            general = RvsfDetails.objects.filter(userid=userid).first()
            krishan_logger.info(f"Existing record found: {general is not None}")
            
            try:
                if general:
                    krishan_logger.info("Updating existing RvsfDetails record...")
                    # Update existing record
                    general.address = address
                    general.latitude = latitude
                    general.longitude = longitude
                    general.state = state
                    general.district = district
                    general.encorp_year = encorp_year
                    general.unit_commencement_year = unit_commencement_year
                    general.status = 'rvsf'
                    
                    general.cto_number = cto_number
                    general.consent_validity = consent_validity
                    if cto_pdf:
                        krishan_logger.debug("Updating CTO PDF")
                        general.cto_pdf = cto_pdf
                    
                    general.howm_validity = howm_validity
                    if howm_pdf:
                        krishan_logger.debug("Updating HOWM PDF")
                        general.howm_pdf = howm_pdf
                    
                    general.dic_validity = dic_validity
                    if dic_pdf:
                        krishan_logger.debug("Updating DIC PDF")
                        general.dic_pdf = dic_pdf
                    
                    general.rvsf_reg_no = rvsf_reg_no
                    general.rvsf_validity = rvsf_validity
                    if rvsf_pdf:
                        krishan_logger.debug("Updating RVSF PDF")
                        general.rvsf_pdf = rvsf_pdf
                    
                    if process_flow_pdf:
                        krishan_logger.debug("Updating Process Flow PDF")
                        general.process_flow_pdf = process_flow_pdf
                    
                    if material_balance_pdf:
                        krishan_logger.debug("Updating Material Balance PDF")
                        general.material_balance_pdf = material_balance_pdf
                    
                    if annual_returns_pdf:
                        krishan_logger.debug("Updating Annual Returns PDF")
                        general.annual_returns_pdf = annual_returns_pdf
                    
                    if annual_returns_pdf1:
                        krishan_logger.debug("Updating Annual Returns PDF1")
                        general.annual_returns_pdf1 = annual_returns_pdf1

                    if annual_returns_pdf2:
                        krishan_logger.debug("Updating Annual Returns PDF2")
                        general.annual_returns_pdf2 = annual_returns_pdf2
                    
                    general.save()
                    krishan_logger.info("Successfully updated RvsfDetails record")
                    messages.success(request, "RVSF details updated successfully.")
                else:
                    krishan_logger.info("Creating new RvsfDetails record...")
                    # Create new record
                    new_record = RvsfDetails.objects.create(
                        address=address,
                        latitude=latitude,
                        longitude=longitude,
                        state=state,
                        district=district,
                        cto_number=cto_number,
                        consent_validity=consent_validity,
                        cto_pdf=cto_pdf,
                        howm_validity=howm_validity,
                        howm_pdf=howm_pdf,
                        dic_validity=dic_validity,
                        dic_pdf=dic_pdf,
                        rvsf_reg_no=rvsf_reg_no,
                        rvsf_validity=rvsf_validity,
                        rvsf_pdf=rvsf_pdf,
                        process_flow_pdf=process_flow_pdf,
                        material_balance_pdf=material_balance_pdf,
                        annual_returns_pdf=annual_returns_pdf,
                        annual_returns_pdf1=annual_returns_pdf1,
                        annual_returns_pdf2=annual_returns_pdf2,
                        status='rvsf',
                        userid=userid,
                        encorp_year=encorp_year,
                        unit_commencement_year=unit_commencement_year
                    )
                    krishan_logger.info(f"Successfully created new RvsfDetails record with ID: {new_record.id}")
                    messages.success(request, "RVSF details saved successfully.")
                
                krishan_logger.info("Redirecting to Capacity...")
                return redirect('Capacity')
                
            except Exception as save_error:
                krishan_logger.error(f"Error saving RvsfDetails: {str(save_error)}", exc_info=True)
                messages.error(request, f"Error saving details: {str(save_error)}")
                return redirect('rvsfdetails')
        
        # GET Request - Only reachable if GeneralDetails exists
        krishan_logger.info("Processing GET request...")
        
        data = RvsfRegistration.objects.filter(id=userid).first()
        krishan_logger.info(f"Found RvsfRegistration data: {data is not None}")
        
        generaldata = RvsfDetails.objects.filter(userid=userid).first()
        krishan_logger.info(f"Found existing RvsfDetails: {generaldata is not None}")
        
        if data:
            statename = State.objects.filter(state_id=data.state).first()
            krishan_logger.info(f"State name: {statename}")
            
            districtname = District.objects.filter(city_id=data.district).first()
            krishan_logger.info(f"District name: {districtname}")
        else:
            krishan_logger.warning(f"No RvsfRegistration found for userid: {userid}")
            data = RvsfRegistration.objects.filter(id=userid).first()
            # generaldata = RvsfDetails.objects.filter(userid=userid).first()

            # statename = State.objects.filter(state_id=data.state).first()
            # print(statename)
            districtname = District.objects.filter(city_id=data.district).first()
            
        
        krishan_logger.info("Rendering rvsfdetails.html template...")
        return render(request, 'user/rvsfdetails.html', {
            'states': states,
            'statename': statename,
            'districtname': districtname,
            'general': generaldata,
            'data': data,
        })
        
    except Exception as e:
        krishan_logger.error(f"Unhandled error in rvsfdetails view: {str(e)}", exc_info=True)
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('error_page')  # Make sure you have an error page URL
    
    finally:
        krishan_logger.info("=== Completed rvsfdetails view execution ===")
# def rvsfdetails(request):
#     userid = request.session.get('user_id')
    
#     # Check if GeneralDetails exists for this user
#     general_exists = GeneralDetails.objects.filter(userid=userid, status='general').exists()
    
#     # Redirect if GeneralDetails doesn't exist
#     # if not general_exists:
#     #     messages.error(request, "Please complete general details first!")
#     #     return redirect('generaldetails')
    
#     appcount = checkapplication(request)
#     states = State.objects.all() 
    
#     if appcount > 0:
#         messages.error(request, "You already have an active application!")
#         return redirect('rvsf_dashboard')
        
#     if request.method == 'POST':
#         address = request.POST.get('address')
#         latitude = request.POST.get('latitude')
#         longitude = request.POST.get('longitude')
#         state = request.POST.get('state')
#         district = request.POST.get('district')
#         # district = request.POST.get('district')
#         # pin_code = request.POST.get('pin_code')

#         cto_number = request.POST.get('cto_number')
#         encorp_year = request.POST.get('encorp_year')
#         consent_validity = request.POST.get('consent_validity')
#         cto_pdf = request.FILES.get('cto_pdf')

#         howm_validity = request.POST.get('howm_validity')
#         howm_pdf = request.FILES.get('howm_pdf')

#         dic_validity = request.POST.get('dic_validity')
#         dic_pdf = request.FILES.get('dic_pdf')

#         rvsf_reg_no = request.POST.get('rvsf_reg_no')
#         rvsf_validity = request.POST.get('rvsf_validity')
#         rvsf_pdf = request.FILES.get('rvsf_pdf')

#         rvsf_fields = {
#             'address': address,
#             'latitude': latitude,
#             'longitude': longitude,
#             'state': state,
#             'district': district,
#             'cto_number': cto_number,
#             'rvsf_reg_no': rvsf_reg_no,
#             'encorp_year': encorp_year,
#         }
#         for field, value in rvsf_fields.items():
#             print(f"Validating field {field} => {value}")

#             if value:
#                 value = value.strip()
#                 print(f"Stripped value for {field}: {value}")

                
#                 # Validate that TIN, CIN, IEC don't have special characters
#                 # (excluding spaces since your regex allows spaces)
#                 if field in ['address','state','cto_number','rvsf_reg_no','district','encorp_year']:
#                     # Check if has special characters (excluding allowed ones)
#                     # We'll use a simpler check
#                     import re
#                     # Allow alphanumeric and spaces only
#                     if re.search(r'[^a-zA-Z0-9\s]', value):
#                         print(f"Special characters found in {field}")
#                         messages.error(
#                             request,
#                             f"{field.replace('_', ' ').title()} should not contain special characters."
#                         )
#                         return redirect('rvsfdetails')

#         process_flow_pdf = request.FILES.get('process_flow_pdf')
#         material_balance_pdf = request.FILES.get('material_balance_pdf')
#         annual_returns_pdf = request.FILES.get('annual_returns_pdf')
#         annual_returns_pdf1 = request.FILES.get('annual_returns_pdf1')

#         # Collect PDFs
#         pdf_fields = {
#             "CTO PDF": cto_pdf,
#             "HOWM PDF": howm_pdf,
#             "DIC PDF": dic_pdf,
#             "RVSF Registration PDF": rvsf_pdf,
#         }

#         for label, pdf in pdf_fields.items():
#             if not pdf:
#                 messages.error(request, f"{label} is required.")
#                 return redirect('rvsfdetails')

#             # Size check (2MB – adjust if needed)
#             if pdf.size > 2 * 1024 * 1024:
#                 messages.error(request, f"{label} must be less than 2MB.")
#                 return redirect('rvsfdetails')

#             # Valid PDF check (NO modification)
#             if not is_valid_pdf(pdf):
#                 messages.error(request, f"{label} is not a valid PDF file.")
#                 return redirect('rvsfdetails')


#         # Validate PDF files
#         pdf_files = {
#             'CTO PDF': cto_pdf,
#             'HOWM PDF': howm_pdf,
#             'DIC PDF': dic_pdf,
#             'RVSF PDF': rvsf_pdf,
#             'Process Flow PDF': process_flow_pdf,
#             'Material Balance PDF': material_balance_pdf,
#             'Annual Returns PDF': annual_returns_pdf,
#             'Annual Returns PDF1': annual_returns_pdf1,
#         }

#         for label, file in pdf_files.items():
#             if file and not file.name.lower().endswith('.pdf'):
#                 messages.error(request, f"{label} must be a PDF.")
#                 return redirect('rvsfdetails')

#         # Check if record exists
#         general = RvsfDetails.objects.filter(userid=userid).first()

#         if general:
#             # Update existing record
#             general.address = address
#             general.latitude = latitude
#             general.longitude = longitude
#             general.state = state
#             general.district = district
#             general.encorp_year = encorp_year
#             general.status = 'rvsf'

#             general.cto_number = cto_number
#             general.consent_validity = consent_validity
#             if cto_pdf:
#                 general.cto_pdf = cto_pdf

#             general.howm_validity = howm_validity
#             if howm_pdf:
#                 general.howm_pdf = howm_pdf

#             general.dic_validity = dic_validity
#             if dic_pdf:
#                 general.dic_pdf = dic_pdf

#             general.rvsf_reg_no = rvsf_reg_no
#             general.rvsf_validity = rvsf_validity
#             if rvsf_pdf:
#                 general.rvsf_pdf = rvsf_pdf

#             if process_flow_pdf:
#                 general.process_flow_pdf = process_flow_pdf

#             if material_balance_pdf:
#                 general.material_balance_pdf = material_balance_pdf

#             if annual_returns_pdf:
#                 general.annual_returns_pdf = annual_returns_pdf

#             if annual_returns_pdf1:
#                 general.annual_returns_pdf1 = annual_returns_pdf1

#             general.save()
#             messages.success(request, "RVSF details updated successfully.")
#         else:
#             # Create new record
#             RvsfDetails.objects.create(
#                 address=address,
#                 latitude=latitude,
#                 longitude=longitude,
#                 state=state,
#                 district=district,
#                 cto_number=cto_number,
#                 consent_validity=consent_validity,
#                 cto_pdf=cto_pdf,
#                 howm_validity=howm_validity,
#                 howm_pdf=howm_pdf,
#                 dic_validity=dic_validity,
#                 dic_pdf=dic_pdf,
#                 rvsf_reg_no=rvsf_reg_no,
#                 rvsf_validity=rvsf_validity,
#                 rvsf_pdf=rvsf_pdf,
#                 process_flow_pdf=process_flow_pdf,
#                 material_balance_pdf=material_balance_pdf,
#                 annual_returns_pdf=annual_returns_pdf,
#                 annual_returns_pdf1=annual_returns_pdf1,
#                 status='rvsf',
#                 userid=userid,
#                 encorp_year=encorp_year
#             )
#             messages.success(request, "RVSF details saved successfully.")
        
#         return redirect('equipmentDetails')

#     # GET Request - Only reachable if GeneralDetails exists
#     data = RvsfRegistration.objects.filter(id=userid).first()
#     generaldata = RvsfDetails.objects.filter(userid=userid).first()

#     statename = State.objects.filter(state_id=data.state).first()
#     print(statename)
#     districtname = District.objects.filter(city_id=data.district).first()
#     print(districtname)

#     return render(request, 'user/rvsfdetails.html', {
#         'states': states,
#         'statename': statename,
#         'districtname': districtname,
#         'general': generaldata,
#         'data': data,
#     })


# def generaldetails(request):

#     userid = request.session.get('user_id')
#     appcount = checkapplication(request)
#     states = State.objects.all() 
    
#     if appcount > 0:
#         messages.error(request, "You already have an active application!")
#         return redirect('rvsf_dashboard')
#     if request.method == 'POST':
#         address = request.POST.get('address')
#         latitude = request.POST.get('latitude')
#         longitude = request.POST.get('longitude')
#         state = request.POST.get('state')
#         district = request.POST.get('district')
#         pin_code = request.POST.get('pin_code')


#         cto_number = request.POST.get('cto_number')
#         consent_validity = request.POST.get('consent_validity')
#         cto_pdf = request.FILES.get('cto_pdf')

#         howm_validity = request.POST.get('howm_validity')
#         howm_pdf = request.FILES.get('howm_pdf')

#         dic_validity = request.POST.get('dic_validity')
#         dic_pdf = request.FILES.get('dic_pdf')

#         rvsf_reg_no = request.POST.get('rvsf_reg_no')
#         rvsf_validity = request.POST.get('rvsf_validity')
#         rvsf_pdf = request.FILES.get('rvsf_pdf')

#         process_flow_pdf = request.FILES.get('process_flow_pdf')
#         material_balance_pdf = request.FILES.get('material_balance_pdf')
#         annual_returns_pdf = request.FILES.get('annual_returns_pdf')
#         tin_pdf = request.FILES.get('tin_pdf')
#         pan_pdf = request.FILES.get('pan_pdf')
#         gst_pdf = request.FILES.get('gst_pdf')
#         cin_pdf = request.FILES.get('cin_pdf')
#         iec_pdf = request.FILES.get('iec_pdf')
#         # Validate PDF files
#         pdf_files = {
#             'CTO PDF': cto_pdf,
#             'HOWM PDF': howm_pdf,
#             'DIC PDF': dic_pdf,
#             'RVSF PDF': rvsf_pdf,
#             'Process Flow PDF': process_flow_pdf,
#             'Material Balance PDF': material_balance_pdf,
#             'Annual Returns PDF': annual_returns_pdf,
#             'Tin  PDF' : tin_pdf,
#             'Pan PDF' : pan_pdf,
#             'Gst PDF' : gst_pdf,
#             'CIN PDF' : cin_pdf,
#             'IEC PDF' : iec_pdf
#         }

#         for label, file in pdf_files.items():
#             if file and not file.name.lower().endswith('.pdf'):
#                 messages.error(request, f"{label} must be a PDF.")
#                 return redirect('generaldetails')

#         # Check if record exists
#         general = GeneralDetails.objects.filter(userid=userid).first()

#         if general:
#             # Update existing record
#             general.address = address
#             general.latitude = latitude
#             general.longitude = longitude
#             general.state = state
#             general.district = district
#             general.pin_code = pin_code

#             general.cto_number = cto_number
#             general.consent_validity = consent_validity
#             if cto_pdf:
#                 general.cto_pdf = cto_pdf

#             general.howm_validity = howm_validity
#             if howm_pdf:
#                 general.howm_pdf = howm_pdf

#             general.dic_validity = dic_validity
#             if dic_pdf:
#                 general.dic_pdf = dic_pdf

#             general.rvsf_reg_no = rvsf_reg_no
#             general.rvsf_validity = rvsf_validity
#             if rvsf_pdf:
#                 general.rvsf_pdf = rvsf_pdf

#             if process_flow_pdf:
#                 general.process_flow_pdf = process_flow_pdf

#             if material_balance_pdf:
#                 general.material_balance_pdf = material_balance_pdf

#             if annual_returns_pdf:
#                 general.annual_returns_pdf = annual_returns_pdf
#             if pan_pdf:
#                 general.pan_pdf = pan_pdf
#             if cin_pdf:
#                 general.cin_pdf = cin_pdf
#             if tin_pdf:
#                 general.tin_pdf = tin_pdf
#             if gst_pdf:
#                 general.gst_pdf = gst_pdf
#             if iec_pdf:
#                 general.iec_pdf = iec_pdf    

#             general.save()
#             messages.success(request, "General details updated successfully.")
#         else:
#             # Create new record
#             GeneralDetails.objects.create(
#                 address=address,
#                 latitude=latitude,
#                 longitude=longitude,
#                 state=state,
#                 district = district,
#                 pin_code = pin_code,
#                 cto_number=cto_number,
#                 consent_validity=consent_validity,
#                 cto_pdf=cto_pdf,
#                 howm_validity=howm_validity,
#                 howm_pdf=howm_pdf,
#                 dic_validity=dic_validity,
#                 dic_pdf=dic_pdf,
#                 rvsf_reg_no=rvsf_reg_no,
#                 rvsf_validity=rvsf_validity,
#                 rvsf_pdf=rvsf_pdf,
#                 process_flow_pdf=process_flow_pdf,
#                 material_balance_pdf=material_balance_pdf,
#                 annual_returns_pdf=annual_returns_pdf,
#                 tin_pdf = tin_pdf,
#                 pan_pdf = pan_pdf,
#                 gst_pdf = gst_pdf,
#                 cin_pdf = cin_pdf,
#                 iec_pdf = iec_pdf,
#                 userid=userid
#             )
#             messages.success(request, "General details saved successfully.")
        
#         # return redirect('generaldetails')
#         return redirect('equipmentDetails')

#     # GET Request
#     data = RvsfRegistration.objects.filter(id=userid).first()
#     generaldata = GeneralDetails.objects.filter(userid=userid).first()
#     print(generaldata)
#     print(data)
#     print(userid)

#     statename = State.objects.filter(state_id=data.state).first()
#     districtname = District.objects.filter(city_id=data.district).first()

#     return render(request, 'user/generaldetails.html', {
#         'states': states,
#         'statename': statename,
#         'districtname': districtname,
#         'general': generaldata,
#         'data': data,
#     })
# def has_special_characters(value):
#     """
#     Allows only letters, numbers and spaces
#     """
#     return bool(re.search(r'[^a-zA-Z0-9\s]', value))


# def generaldetails(request):
#     userid = request.session.get('user_id')
#     appcount = checkapplication(request)
#     states = State.objects.all()

#     if appcount > 0:
#         messages.error(request, "You already have an active application!")
#         return redirect('rvsf_dashboard')

#     if request.method == 'POST':
#         # --- Certificate numbers to save in RvsfRegistration ---
#         certificate_fields = {
#             'tin_no': request.POST.get('tin_no'),
#             # 'tin_no': 'fghsdgsd@@!@#',
#             'cin': request.POST.get('cin_no'),
#             'iec': request.POST.get('iec_no'),
#         }
#         for field, value in certificate_fields.items():
#             if value:
#                 value = value.strip()

#                 # Email validation (future-safe)
#                 if 'email' in field.lower():
#                     try:
#                         validate_email(value)
#                     except ValidationError:
#                         messages.error(request, "Please enter a valid email address.")
#                         return redirect('generaldetails')

#                 # Other text fields → no special characters
#                 else:
#                     if has_special_characters(value):
#                         messages.error(
#                             request,
#                             f"{field.replace('_', ' ').title()} should not contain special characters."
#                         )
#                         return redirect('generaldetails')

#         # --- PDF files to save in GeneralDetails ---
#         file_fields = {
#             'tin_pdf': request.FILES.get('tin_pdf'),
#             'pan_pdf': request.FILES.get('pan_pdf'),
#             'gst_pdf': request.FILES.get('gst_pdf'),
#             'cin_pdf': request.FILES.get('cin_pdf'),
#             'iec_pdf': request.FILES.get('iec_pdf'),
#         }

#         # --- Validate PDF files ---
#         for label, file in file_fields.items():
#             # if file and not file.name.lower().endswith('.pdf'):
#             #     messages.error(request, f"{label.replace('_', ' ').title()} must be a PDF file.")
#             #     return redirect('generaldetails')
#             if file:
#                 # Size check (2MB – adjust if needed)
#                 if file.size > 2 * 1024 * 1024:
#                     messages.error(request, f"{label} must be less than 2MB.")
#                     return redirect('generaldetails')

#                 # Real PDF validation (NO modification)
#                 if not is_valid_pdf(file):
#                     messages.error(request, f"{label} is not a valid PDF file.")
#                     return redirect('generaldetails')
#         # --- Update RvsfRegistration with certificate numbers ---
#         rvsf_registration = RvsfRegistration.objects.filter(id=userid).first()
#         if rvsf_registration:
#             print(certificate_fields)
#             for field, value in certificate_fields.items():
#                 if value not in [None, '']:
#                     # print('trying to insert')
#                     setattr(rvsf_registration, field, value)
#                     # print('inserted')
#             try:
#                 rvsf_registration.save()
#             except IntegrityError:
#                 messages.error(request, "Error saving certificate data.")
#                 return redirect('generaldetails')

#         # --- Check if GeneralDetails record exists ---
#         general = GeneralDetails.objects.filter(userid=userid).first()

#         if general:
#             # --- Update existing GeneralDetails record with PDF files ---
#             for field, file in file_fields.items():
#                 if file:
#                     setattr(general, field, file)

#             try:
#                 # general.save()
#                 messages.success(request, "General details updated successfully.")
#             except IntegrityError:
#                 messages.error(request, "Error saving file data.")
#                 return redirect('generaldetails')

#         else:
#             # --- Create new GeneralDetails record with PDF files ---
#             GeneralDetails.objects.create(
#                 userid=userid,
#                 status='general',
#                 **{k: v for k, v in file_fields.items() if v}  # Only include non-empty files
#             )
#             messages.success(request, "General details saved successfully.")

#         return redirect('rvsfdetails')

#     # --- GET Request ---
#     data = RvsfRegistration.objects.filter(id=userid).first()
#     generaldata = GeneralDetails.objects.filter(userid=userid).first()

#     statename = State.objects.filter(state_id=data.state).first() if data else None
#     districtname = District.objects.filter(city_id=data.district).first() if data else None

#     return render(request, 'user/generaldetails.html', {
#         'states': states,
#         'statename': statename,
#         'districtname': districtname,
#         'general': generaldata,
#         'data': data,
#         'sidebar_userid': userid,
#     })
@login_required
def generaldetails(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        print("Entered generaldetails view")

        userid = request.session.get('user_id')
        print("User ID:", userid)

        appcount = checkapplication(request)
        print("Application count:", appcount)

        states = State.objects.all()
        print("States fetched:", states.count())

        if appcount > 0:
            print("Active application exists, redirecting")
            messages.error(request, "You already have an active application!")
            return redirect('rvsf_dashboard')

        if request.method == 'POST':
            print("Request method POST")

            certificate_fields = {
                'tin_no': request.POST.get('tin_no'),
                'cin': request.POST.get('cin_no'),
                'iec': request.POST.get('iec_no'),
            }
            print("Certificate fields:", certificate_fields)

            for field, value in certificate_fields.items():
                print(f"Validating field {field} => {value}")

                if value:
                    value = value.strip()
                    print(f"Stripped value for {field}: {value}")

                    # Skip validation for fields that might be emails
                    # (though TIN, CIN, IEC are not emails)
                    
                    # Validate that TIN, CIN, IEC don't have special characters
                    # (excluding spaces since your regex allows spaces)
                    if field in ['tin_no', 'cin', 'iec']:
                        # Check if has special characters (excluding allowed ones)
                        # We'll use a simpler check
                        import re
                        # Allow alphanumeric and spaces only
                        if re.search(r'[^a-zA-Z0-9\s]', value):
                            print(f"Special characters found in {field}")
                            messages.error(
                                request,
                                f"{field.replace('_', ' ').title()} should not contain special characters."
                            )
                            return redirect('generaldetails')
            # for field, value in certificate_fields.items():
            #     print(f"Validating field {field} => {value}")

            #     if value:
            #         value = value.strip()
            #         print(f"Stripped value for {field}: {value}")

            #         if 'email' in field.lower():
            #             print("Email validation triggered")
            #             try:
            #                 validate_email(value)
            #                 print("Email valid")
            #             except ValidationError:
            #                 print("Email validation failed")
            #                 messages.error(request, "Please enter a valid email address.")
            #                 return redirect('generaldetails')
            #         else:
            #             print(value,'sdfgslkdjfg')
            #             if has_special_characters(value):
            #                 print(f"Special characters found in {field}")
            #                 messages.error(
            #                     request,
            #                     f"{field.replace('_', ' ').title()} should not contain special characters."
            #                 )
            #                 return redirect('generaldetails')

            file_fields = {
                'tin_pdf': request.FILES.get('tin_pdf'),
                'pan_pdf': request.FILES.get('pan_pdf'),
                'gst_pdf': request.FILES.get('gst_pdf'),
                'cin_pdf': request.FILES.get('cin_pdf'),
                'iec_pdf': request.FILES.get('iec_pdf'),
            }
            print("File fields received:", file_fields)

            for label, file in file_fields.items():
                print(f"Checking file field {label}")

                if file:
                    print(f"{label} file name:", file.name)
                    print(f"{label} file size:", file.size)

                    if file.size > 2 * 1024 * 1024:
                        print(f"{label} size exceeds limit")
                        messages.error(request, f"{label} must be less than 2MB.")
                        return redirect('generaldetails')

                    if not is_valid_pdf(file):
                        print(f"{label} invalid PDF")
                        messages.error(request, f"{label} is not a valid PDF file.")
                        return redirect('generaldetails')

                    print(f"{label} passed validation")

            rvsf_registration = RvsfRegistration.objects.filter(id=userid).first()
            print("Fetched RvsfRegistration:", rvsf_registration)

            if rvsf_registration:
                for field, value in certificate_fields.items():
                    if value not in [None, '']:
                        print(f"Updating RvsfRegistration.{field} = {value}")
                        setattr(rvsf_registration, field, value)

                try:
                    rvsf_registration.save()
                    print("RvsfRegistration saved successfully")
                except IntegrityError as e:
                    print("Error saving RvsfRegistration:", e)
                    messages.error(request, "Error saving certificate data.")
                    return redirect('generaldetails')

            general = GeneralDetails.objects.filter(userid=userid).first()
            print("Fetched GeneralDetails:", general)

            if general:
                print("Updating existing GeneralDetails")
                for field, file in file_fields.items():
                    if file:
                        print(f"Updating file field {field}")
                        setattr(general, field, file)

                try:
                    general.save()
                    print("GeneralDetails updated successfully")
                    messages.success(request, "General details updated successfully.")
                except IntegrityError as e:
                    print("Error saving GeneralDetails:", e)
                    messages.error(request, "Error saving file data.")
                    return redirect('generaldetails')

            else:
                print("Creating new GeneralDetails record")
                GeneralDetails.objects.create(
                    userid=userid,
                    status='general',
                    **{k: v for k, v in file_fields.items() if v}
                )
                print("GeneralDetails created")
                messages.success(request, "General details saved successfully.")

            print("Redirecting to rvsfdetails")
            return redirect('rvsfdetails')

        print("Request method GET")

        data = RvsfRegistration.objects.filter(id=userid).first()
        print("Fetched registration data:", data)

        generaldata = GeneralDetails.objects.filter(userid=userid).first()
        print("Fetched general data:", generaldata)

        statename = State.objects.filter(state_id=data.state).first() if data else None
        print("Resolved state:", statename)

        districtname = District.objects.filter(city_id=data.district).first() if data else None
        print("Resolved district:", districtname)

        print("Rendering generaldetails.html")
        return render(request, 'user/generaldetails.html', {
            'states': states,
            'statename': statename,
            'districtname': districtname,
            'general': generaldata,
            'data': data,
            'sidebar_userid': userid,
        })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving generaldetails")
                krishan_logger.error(f"Exact generaldetails  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact generaldetails Error: {str(db_error)}")


# RvsfApp/context_processors.py
def sidebar_user(request):
    userid = request.session.get('user_id')
    if userid:
        return {"logged_user": RvsfRegistration.objects.filter(id=userid).first()}
    return {"logged_user": None}


@login_required
def capacity_declaration(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        userid = request.session.get('user_id')
        capacitydata = PlantCapacity.objects.filter(userid=userid).first()
        appcount = checkapplication(request)
        pollutioncheck = PollutionDevice.objects.filter(userid=userid, status='pollution').exists()
        
        # Redirect if equipment details don't exist
        # if not pollutioncheck:
        #     messages.error(request, "Please complete Pollution details first!")
        #     return redirect('pollutiondetails')

        if appcount > 0:
            messages.error(request, "You already have an active application!")
            return redirect('rvsf_dashboard')

        if request.method == "POST":
            undertaking_file = request.FILES.get('Undertaking_pdf')

            # Validate file type
            # if undertaking_file and not undertaking_file.name.lower().endswith('.pdf'):
            #     messages.error(request, "Undertaking must be a PDF file.")
            #     return redirect('capacityanddeclaration')
            if undertaking_file:
                # Size check (2MB – adjust if needed)
                if undertaking_file.size > 2 * 1024 * 1024:
                    messages.error(request, "Undertaking PDF must be less than 2MB.")
                    return redirect('capacityanddeclaration')

                # Real PDF validation (NO modification)
                if not is_valid_pdf(undertaking_file):
                    messages.error(request, "Undertaking is not a valid PDF file.")
                    return redirect('capacityanddeclaration')

            general = RvsfRegistration.objects.filter(id=userid).first()

            if general:
                if undertaking_file:
                    # delete old file if exists
                    if general.undertaking:
                        old_path = general.undertaking.path
                        if os.path.exists(old_path):
                            os.remove(old_path)

                    general.undertaking = undertaking_file
                    general.status = 'declaration'

                try:
                    general.save()
                    messages.success(request, "Declaration details updated successfully.")
                except IntegrityError:
                    messages.error(request, "Error saving file data.")
                    return redirect('capacityanddeclaration')
            else:
                # In case record doesn’t exist
                RvsfRegistration.objects.create(
                    id=userid,
                    undertaking=undertaking_file if undertaking_file else None,
                    status = 'declaration'
                )
                messages.success(request, "Declaration details saved successfully.")

            return redirect('paymentsection')

        # --- GET Request ---
        data = RvsfRegistration.objects.filter(id=userid).first()
        # file_url = data.undertaking.url if data and data.undertaking else None
        file_url = '/media/RVSFDocs/undertaking/Undertaking1.pdf'
        # file_url = '/media/RVSFDocs/undertaking/Undertaking_Format_for_Registered_Vehicle_Scrapping_Facility.docs'
        print(file_url)

        return render(request, 'user/capacityanddeclaration.html', {
            'capacitydata': capacitydata,
            'file_url': file_url,
            'data': data,
        })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving capcitydeclaration")
                krishan_logger.error(f"Exact capcitydeclaration  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact capcitydeclaration Error: {str(db_error)}")



# def calculate_fee_based_on_capacity(capacity):
#     """Calculate fee based on capacity ranges"""
#     capacity = float(capacity) if capacity else 0
    
#     if capacity < 6000:
#         return 25000
#     elif 6000 <= capacity < 15000:
#         return 50000
#     elif 15000 <= capacity < 30000:
#         return 75000
#     elif capacity >= 30000:
#         return 100000
#     return 0
# @login_required
# def payment_section(request):
#     userid = request.session.get('user_id')
#     capacitydata = PlantCapacity.objects.filter(userid=userid).first()
#     rvsf_fees = RVSFRegistrationFee.objects.all()
#     appcount = checkapplication(request)
#     states = State.objects.all()

#     # Calculate current required fee based on capacity
#     current_capacity = capacitydata.installed_vehicles if capacitydata else 0
#     calculated_amount = calculate_fee_based_on_capacity(current_capacity)

#     # Get latest successful payment
#     latest_payment = Payment.objects.filter(
#         owner_id=userid, 
#         status='success'
#     ).first()

#     payment_status = {
#         'has_successful_payment': False,
#         'requires_additional_payment': False,
#         'additional_amount': 0,
#         'calculated_amount': calculated_amount,
#         'paid_amount': 0
#     }

#     if latest_payment:
#         payment_status['has_successful_payment'] = True
#         payment_status['paid_amount'] = latest_payment.amount_initiated
        
#         # Check if additional payment is required
#         if calculated_amount > latest_payment.amount_initiated:
#             payment_status['requires_additional_payment'] = True
#             payment_status['additional_amount'] = calculated_amount - latest_payment.amount_initiated

#     if request.POST:
#         print(request.POST, 'sfhsjfkhsfsfjsdklflk')
#         return redirect('paymentsection')

#     return render(request, 'user/paymentsection.html', {
#         'capacitydata': capacitydata,
#         'rvsf_fees': rvsf_fees,
#         'payment_status': payment_status,
#         'paymentdetail': latest_payment
#     })

# def initiateAdditionalPayment(request):
#     if request.method == 'POST':
#         userid = request.session.get('user_id')
#         additional_amount = request.POST.get('additional_amount')
#         calculated_amount = request.POST.get('calculated_amount')
        
      
#         return redirect('paymentsection')
    
#     return redirect('paymentsection')
# def payment_section(request):
#     userid = request.session.get('user_id')
#     capacitydata = PlantCapacity.objects.filter(userid=userid).first()
#     rvsf_fees = RVSFRegistrationFee.objects.all()
#     # print(rvsf_fees)
      
#     appcount = checkapplication(request)
#     states = State.objects.all() 

#     # if appcount > 0:
#     #     messages.error(request, "You already have an active application!")
#     #     return redirect('rvsf_dashboard')

#     if(request.POST):
#         print(request.POST,'sfhsjfkhsfsfjsdklflk')
#         return redirect('paymentsection')
#     payment_success = Payment.objects.filter(owner_id=userid, status='success').exists()
#     payment_success1 = Payment.objects.filter(owner_id=userid, status='success').values_list('amount_initiated', flat=True).first()
#     print(payment_success1)
#     # for p in payment_success:
#     #     print(p.__dict__)
#     print(payment_success)
    

   
#     return render(request, 'user/paymentsection.html', {
#         'capacitydata': capacitydata,
#         'rvsf_fees':rvsf_fees,
#         'paymentdata':payment_success,
#         'paymentdetail':payment_success1
#     })

def send_sms_forgot_password(number,user_username,user_password):
    """
    Send Reset Password via the updated SMS API
    """
    print("Send Reset Password via the updated SMS API")
    # API credentials & configuration
    username = "CPCB_IT"
    password = "Smscpcb#2026"
    senderid = "CPCBEL"
    dept_secure_key = "106a9ed9-00c4-442d-a857-3447d308c9d9"
    templateid = "1307175188767634262"
    entity_id = "1301158798803147760"

    # OTP message
    # message = (
    #     f"Dear User, Your password has been reset successfully . Please find the updated credentials below.
    #     Login ID - {user_username} 
    #     password - {user_password}".
    # )
    message = (
        f"Dear User, your password reset request was received. "
        f"Please click the link to reset your password: {user_username},{user_password}"
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
        print("Failed to send Reset Password:", str(e))
        return f"API call failed: {str(e)}"


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



# def resend_otp_rvsf(request):
    
    
#     if request.method == "POST":
#         # Logic to resend OTP here print("OTP resend triggered")
#         user1 = RvsfRegistration.objects.get(username=request.POST['username'])
#         # Fetching session data
#         # user_id = request.session.get('user_id')
#         user_id = user1.id
#         admin_user_id = request.session.get('admin_user_id')
        
#         # -------------------------------
#         # RVSF USER SECTION
#         # -------------------------------
#         if user_id:
            
#             try:
#                 user = RvsfRegistration.objects.get(id=user_id)
                

#                 # Re-save session data
#                 request.session['user_id'] = user.id
#                 request.session['username'] = user.username
                

#                 # Check if OTP already exists
#                 get_otp = request.session.get('otp')
#                 created_at_str = request.session.get('otp_created_at')
                

#                 # Handle OTP expiration
#                 if get_otp and created_at_str:
#                     created_at = datetime.fromisoformat(created_at_str)
                    
#                     age = datetime.now() - created_at
                    

#                     if age > timedelta(seconds=60):
                        
#                         del request.session['otp']
#                         del request.session['otp_created_at']
#                     else:
#                         print("⏱️ OTP still valid — but will regenerate anyway")

#                 # Generate new OTP
#                 # otp = "123456"  # Temporary static OTP
#                 otp = str(random.randint(100000, 999999))
#                 # request.session['otp'] = otp
#                 # request.session['otp_created_at'] = datetime.now().isoformat()
                

#                 # Send SMS
                
#                 cache.set(f"otp_{user.username}", otp, timeout=120)
#                 print(f"💾 OTP cached for 120 seconds under key otp_{user.username}")

#                 # Send email and SMS
#                 print("📧 Sending OTP email...")
#                 sendtitanemail1(user.company_name, user.username, user.company_email, otp)
#                 print("📱 Sending OTP SMS...")
#                 send_sms_otp_direct(user.auth_mobile, otp)
#                 # send_login_otp_sms(user.auth_mobile, otp)
                

                
#                 return render(request, 'authentication/otpverify.html', {'form': OTPForm()})

#             except RvsfRegistration.DoesNotExist:
                
#                 messages.error(request, "Invalid username or password.")

        
#         # -------------------------------
#         # NO VALID SESSION FOUND
#         # -------------------------------
#         else:
            
#             messages.error(request, "Invalid captcha.")
    
#     else:
        
#         form = LoginForm()

    
#     return render(request, 'admin/admin_login.html', {'form': form})


# def resend_otp_rvsf(request):
#     if request.method == "POST":
#         try:
#             user1 = RvsfRegistration.objects.get(username=request.POST['username'])
#             username = user1.username
            
#             # -------------------------------
#             # SIMPLE RATE LIMITING CHECK
#             # -------------------------------
#             rate_limit_key = f"otp_count_{username}"
#             current_count = cache.get(rate_limit_key, 0)
            
#             if current_count >= 5:
#                 # User has already sent 5 OTPs
#                 messages.error(
#                     request,
#                     "⚠️ Rate limit exceeded! You can only send 5 OTPs per 5 minutes. "
#                     "Please wait before requesting another OTP."
#                 )
#                 return JsonResponse({
#                     'status': 'error',
#                     'message': 'Rate limit exceeded! Please wait 5 minutes.'
#                 })
            
#             # Increment the counter
#             cache.set(rate_limit_key, current_count + 1, timeout=300)  # 5 minutes
            
#             # -------------------------------
#             # SEND OTP
#             # -------------------------------
#             user = RvsfRegistration.objects.get(id=user1.id)
            
#             # Generate new OTP
#             otp = str(random.randint(100000, 999999))
            
#             # Store OTP in cache
#             cache.set(f"otp_{user.username}", otp, timeout=120)
            
#             # Send email and SMS
#             sendtitanemail1(user.company_name, user.username, user.company_email, otp)
#             send_sms_otp_direct(user.auth_mobile, otp)
            
#             # Calculate remaining attempts
#             remaining = 5 - (current_count + 1)
            
#             messages.success(
#                 request,
#                 f"✅ OTP sent! {remaining} attempts remaining in next 5 minutes."
#             )
            
#             return JsonResponse({
#                 'status': 'success',
#                 'message': f'OTP sent! {remaining} attempts remaining.'
#             })
            
#         except RvsfRegistration.DoesNotExist:
#             return JsonResponse({
#                 'status': 'error',
#                 'message': 'Invalid username.'
#             })
#         except Exception as e:
#             return JsonResponse({
#                 'status': 'error',
#                 'message': str(e)
#             })
    
#     return JsonResponse({
#         'status': 'error',
#         'message': 'Invalid request method.'
#     })

@csrf_exempt
def resend_otp_rvsf(request):
    if request.method == "POST":
        try:
            user1 = RvsfRegistration.objects.get(username=request.POST['username'])
            username = user1.username
            
            # -------------------------------
            # SIMPLE RATE LIMITING CHECK
            # -------------------------------
            rate_limit_key = f"otp_count_{username}"
            current_count = cache.get(rate_limit_key, 0)
            
            if current_count >= 5:
                # User has already sent 5 OTPs
                messages.error(
                    request,
                    "⚠️ Rate limit exceeded! You can only send 5 OTPs per 5 minutes. "
                    "Please wait before requesting another OTP."
                )
                # Store messages in messages1 for template
                storage = messages.get_messages(request)
                messages1_list = []
                for message in storage:
                    messages1_list.append(message)
                # Keep messages for next request
                storage.used = False
                
                return JsonResponse({
                    'status': 'error',
                    'message': 'Rate limit exceeded! Please wait 5 minutes.',
                    'has_messages1': True,
                    'messages1': [{'message': str(m), 'tags': m.tags} for m in messages1_list]
                })
            
            # Increment the counter
            cache.set(rate_limit_key, current_count + 1, timeout=300)  # 5 minutes
            
            # -------------------------------
            # SEND OTP
            # -------------------------------
            user = RvsfRegistration.objects.get(id=user1.id)
            
            # Generate new OTP
            otp = str(random.randint(100000, 999999))
            # otp = "123456"
            
            # Store OTP in cache
            cache.set(f"otp_{user.username}", otp, timeout=120)
            
            # Send email and SMS
            # sendtitanemail1(user.company_name, user.username, user.company_email, otp)
            sendOtpEmail(user.company_name, user.username, user.company_email, otp)
            send_sms_otp_direct(user.auth_mobile, otp)
            
            # Calculate remaining attempts
            remaining = 5 - (current_count + 1)
            
            messages.success(
                request,
                f"✅ OTP sent! {remaining} attempts remaining in next 5 minutes."
            )
            
            # Store messages in messages1 for template
            storage = messages.get_messages(request)
            messages1_list = []
            for message in storage:
                messages1_list.append(message)
            # Keep messages for next request
            storage.used = False
            
            return JsonResponse({
                'status': 'success',
                'message': f'OTP sent! {remaining} attempts remaining.',
                'has_messages1': True,
                'messages1': [{'message': str(m), 'tags': m.tags} for m in messages1_list]
            })
            
        except RvsfRegistration.DoesNotExist:
            
            krishan_logger.exception("❌ ERROR while saving resend1")
            krishan_logger.error(f"Exact resend1  Error: {str(db_error)}")
            
            krishan_logger.info(f"Exact resend1 Error: {str(db_error)}")
            messages.error(request, '❌ Invalid username.')
            storage = messages.get_messages(request)
            messages1_list = []
            for message in storage:
                messages1_list.append(message)
            storage.used = False
            
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username.',
                'has_messages1': True,
                'messages1': [{'message': str(m), 'tags': m.tags} for m in messages1_list]
            })
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            krishan_logger.exception("❌ ERROR while saving resend2")
            krishan_logger.error(f"Exact resend2  Error: {str(db_error)}")
            
            krishan_logger.info(f"Exact resend2 Error: {str(db_error)}")
            storage = messages.get_messages(request)
            messages1_list = []
            for message in storage:
                messages1_list.append(message)
            storage.used = False
            
            return JsonResponse({
                'status': 'error',
                'message': str(e),
                'has_messages1': True,
                'messages1': [{'message': str(m), 'tags': m.tags} for m in messages1_list]
            })
    
    messages.error(request, '❌ Invalid request method.')
    storage = messages.get_messages(request)
    messages1_list = []
    for message in storage:
        messages1_list.append(message)
    storage.used = False
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.',
        'has_messages1': True,
        'messages1': [{'message': str(m), 'tags': m.tags} for m in messages1_list]
    })
# def is_real_pdf(uploaded_file):
#     uploaded_file.seek(0)
#     header = uploaded_file.read(5)
#     uploaded_file.seek(0)
#     return header == b'%PDF-'
    
# def is_safe_pdf(uploaded_file):
#     try:
#         reader = PdfReader(uploaded_file)
#         if len(reader.pages) == 0:
#             return False
#         return True
#     except Exception:
#         return False
def is_valid_pdf(uploaded_file):
    try:
        # Header check
        uploaded_file.seek(0)
        if uploaded_file.read(5) != b'%PDF-':
            return False
        uploaded_file.seek(0)

        # Structural check
        reader = PdfReader(uploaded_file)
        return len(reader.pages) > 0
    except Exception:
        return False


@login_required
def equipmentdetails(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        krishan_logger.info("=" * 50)
        krishan_logger.info("Entering equipmentdetails view")
        
        userid = request.session.get('user_id')
        krishan_logger.info(f"User ID from session: {userid}")
        
        appcount = checkapplication(request)
        krishan_logger.info(f"Application count from checkapplication: {appcount}")
        
        incompeteapp = ConfirmApplication.objects.filter(userid=userid, incomplete=1).count()
        krishan_logger.info(f"Incomplete applications count: {incompeteapp}")
        
        # Check if RVSF details exist for this user
        rvsfcheck = RvsfDetails.objects.filter(userid=userid, status='rvsf').exists()
        krishan_logger.info(f"RVSF details exist: {rvsfcheck}")
        
        # Redirect if RVSF details don't exist
        # if not rvsfcheck:
        #     messages.error(request, "Please complete RVSF details first!")
        #     return redirect('rvsfdetails')
        
        if appcount > 0 and incompeteapp == 0:
            krishan_logger.info("Active application exists - redirecting to dashboard")
            messages.error(request, "You already have an active application!")
            return redirect('rvsf_dashboard')
        
        if request.method == 'POST':
            krishan_logger.info("Processing POST request")
            
            equipment_id = request.POST.get('equipment_name')
            krishan_logger.info(f"Equipment ID from POST: {equipment_id}")
            krishan_logger.info('cgasjcbgasjc')
            krishan_logger.info(f"Equipment ID: {equipment_id}")
            
            if equipment_id == '7':
                equipment_type = request.POST.get('other_equipment')
                krishan_logger.info(f"Other equipment type: {equipment_type}")
            else:
                getname = EquipmentType.objects.filter(id=equipment_id).first()
                krishan_logger.info(f"Equipment name from DB: {getname.name if getname else 'None'}")
                equipment_type = getname.name if getname else None
            
            equipment_count = request.POST.get('equipment_count')
            krishan_logger.info(f"Equipment count: {equipment_count}")
            
            geo_pdf = request.FILES.get('geo_pdf')
            krishan_logger.info(f"Geo PDF: {geo_pdf}")
            
            power_rating = request.POST.get('power_rating')
            krishan_logger.info(f"Power rating: {power_rating}")
            
            operating_hours = request.POST.get('operating_hours')
            krishan_logger.info(f"Operating hours: {operating_hours}")
            
            capacity_equipment_perton = request.POST.get('capacity_equipment_perton')
            krishan_logger.info(f"Capacity per ton: {capacity_equipment_perton}")
            
            equipment_description = request.POST.get('equipment_description')
            krishan_logger.info(f"Equipment description: {equipment_description}")

            equipment_fields = {
                'equipment_type': equipment_type,
                'equipment_count': equipment_count,
                'power_rating': power_rating,
                'operating_hours': operating_hours,
                'capacity_equipment_perton': capacity_equipment_perton,
                'equipment_description': equipment_description,
            }
            
            krishan_logger.info("Starting field validation")
            for field, value in equipment_fields.items():
                krishan_logger.info(f"Validating field {field} => {value}")

                if value:
                    value = value.strip()
                    krishan_logger.info(f"Stripped value for {field}: {value}")

                    # Validate that fields don't have special characters
                    if field in ['equipment_type', 'equipment_description', 'equipment_count', 'power_rating', 'operating_hours', 'capacity_equipment_perton']:
                        import re
                        krishan_logger.info(f"Checking special characters for {field}")
                        
                        if re.search(r'[^a-zA-Z0-9\s]', value):
                            krishan_logger.info(f"Special characters found in {field}")
                            messages.error(
                                request,
                                f"{field.replace('_', ' ').title()} should not contain special characters."
                            )
                            krishan_logger.info("Redirecting due to special characters")
                            return redirect('equipmentDetails')

            # ---------------------------
            # PDF VALIDATION (SECURITY)
            # ---------------------------
            krishan_logger.info("Starting PDF validation")
            
            geo_pdf = request.FILES.get('geo_pdf')
            krishan_logger.info(f"PDF file for validation: {geo_pdf}")

            if not geo_pdf:
                krishan_logger.info("No PDF file provided")
                messages.error(request, "Geo-tagged PDF is required.")
                return redirect('equipmentDetails')

            # Extension check
            ext = os.path.splitext(geo_pdf.name)[1].lower()
            krishan_logger.info(f"PDF file extension: {ext}")
            
            if ext != '.pdf':
                krishan_logger.info(f"Invalid extension: {ext}")
                messages.error(request, "Only PDF files are allowed.")
                return redirect('equipmentDetails')

            # MIME type check
            krishan_logger.info(f"PDF content type: {geo_pdf.content_type}")
            if geo_pdf.content_type != 'application/pdf':
                krishan_logger.info(f"Invalid MIME type: {geo_pdf.content_type}")
                messages.error(request, "Invalid PDF file.")
                return redirect('equipmentDetails')

            # Size check (2MB)
            file_size = geo_pdf.size
            krishan_logger.info(f"PDF file size: {file_size} bytes")
            
            if file_size > 2 * 1024 * 1024:
                krishan_logger.info(f"File too large: {file_size} bytes")
                messages.error(request, "PDF file size must be less than 2MB.")
                return redirect('equipmentDetails')

            # Real PDF header check
            krishan_logger.info("Checking PDF header validity")
            if not is_valid_pdf(geo_pdf):
                krishan_logger.info("Invalid PDF header detected")
                messages.error(request, "Not a valid PDF file.")
                return redirect('equipmentDetails')

            krishan_logger.info("Creating EquipmentEntry object")
            EquipmentEntry.objects.create(
                equipment_type=equipment_type,
                equipment_id=equipment_id,
                power_rating=power_rating,
                operating_hours=operating_hours,
                capacity_equipment_perton=capacity_equipment_perton,
                quantity=equipment_count,
                geo_tagged_pdf=geo_pdf,
                status='equipment',
                userid=userid,
                equipment_description=equipment_description
            )
            krishan_logger.info("EquipmentEntry created successfully")
            
            messages.success(request, "Equipment details saved successfully.")
            krishan_logger.info("Redirecting to equipmentDetails after successful save")
            
            return redirect('equipmentDetails')
            
        else:
            krishan_logger.info("Processing GET request")
            
            equipmentdata = EquipmentType.objects.all().order_by('id').exclude(id=5)
            krishan_logger.info(f"Total equipment types: {equipmentdata.count()}")
            
            data = EquipmentEntry.objects.filter(userid=userid)
            krishan_logger.info(f"Existing equipment entries for user: {data.count()}")
            
            facilitydata = RvsfFacility.objects.filter(user_id=userid).first()
            krishan_logger.info(f"Facility data found: {facilitydata is not None}")

            # Get the IDs of already selected equipment types from EquipmentEntry
            selected_equipment_ids = data.values_list('equipment_id', flat=True)
            krishan_logger.info(f"Selected equipment IDs: {list(selected_equipment_ids)}")

            # Filter equipmentdata to exclude already selected ones
            available_equipment = equipmentdata.exclude(id__in=selected_equipment_ids)
            krishan_logger.info(f"Available equipment count: {available_equipment.count()}")
            krishan_logger.info(f"Available equipment IDs: {list(available_equipment.values_list('id', flat=True))}")

            krishan_logger.info("Rendering equipmentdetails template")
            return render(request, 'user/equipmentdetails.html', {
                'equipment': equipmentdata,
                'data': data,
                'facility': facilitydata,
                'all_equipment': equipmentdata
            })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving equipmentdetails")
                krishan_logger.error(f"Exact equipmentdetails  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact equipmentdetails Error: {str(db_error)}")
# def equipmentdetails(request):
#     userid = request.session.get('user_id')
#     appcount = checkapplication(request)
#     incompeteapp = ConfirmApplication.objects.filter(userid = userid , incomplete = 1).count()
#     if appcount > 0 and incompeteapp == 0:
#         messages.error(request, "You already have an active application!")
#         return redirect('rvsf_dashboard')
    
#     if request.method == 'POST':
#         equipment_id = request.POST.get('equipment_name')
#         print('cgasjcbgasjc')
#         print(equipment_id)
#         if equipment_id == '7':
#             equipment_type = request.POST.get('other_equipment')
#             print(equipment_type)
#         else:
#             getname = EquipmentType.objects.filter(id = equipment_id).first()
#             equipment_type = getname.name
        
#         equipment_count = request.POST.get('equipment_count')
#         geo_pdf = request.FILES.get('geo_pdf')
#         userid = request.session.get('user_id')
#         power_rating = request.POST.get('power_rating')
#         operating_hours = request.POST.get('operating_hours')
#         capacity_equipment_perton =request.POST.get('capacity_equipment_perton')

#         EquipmentEntry.objects.create(
#             equipment_type = equipment_type,
#             equipment_id = equipment_id,
#             power_rating = power_rating,
#             operating_hours = operating_hours,
#             capacity_equipment_perton = capacity_equipment_perton,
#             quantity = equipment_count,
#             geo_tagged_pdf = geo_pdf,
#             status='equipment',
#             userid = userid 
#         )
#         messages.success(request, "Equipment details saved successfully.")
#         countincomplete = ConfirmApplication.objects.filter(userid = userid , incomplete = 1).count()
#         if countincomplete > 0:
#             return redirect('editEquipmentDetails') 
        
#         return redirect('equipmentDetails')
        
#     else:
#         equipmentdata = EquipmentType.objects.all().order_by('id')
#         data = EquipmentEntry.objects.filter(userid = userid)
#         facilitydata = RvsfFacility.objects.filter(user_id = userid).first()
        
#         return render(request, 'user/equipmentdetails.html', {'equipment': equipmentdata , 'data':data , 'facility':facilitydata})

 
@login_required
def facilityDetails(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        userid = request.session.get('user_id')
        appcount = checkapplication(request)

        if appcount > 0:
            messages.error(request, "You already have an active application!")
            return redirect('rvsf_dashboard')

        if request.method == 'POST':
            geo_video = request.FILES.get('geo_video')
            total_area = request.POST.get('total_area')
            shifts = request.POST.get('shifts_per_day')
            employees = request.POST.get('no_of_employees')
            sectioned_power = request.POST.get('sectioned_power')
            storage_parking_area = request.POST.get('storage_parking_area')
            storage_depolluted_fluids = request.POST.get('storage_depolluted_fluids')
            storage_hazardous_waste = request.POST.get('storage_hazardous_waste')
            storage_processed_scrap = request.POST.get('storage_processed_scrap')
            storage_segregated_spares = request.POST.get('storage_segregated_spares')
            storage_others = request.POST.get('storage_others')
            storage_others_description = request.POST.get('storage_others_description')

            facility_fields = {
                'sectioned_power': sectioned_power,
                'employees': employees,
                'shifts': shifts,
                'total_area': total_area,
                'storage_parking_area': storage_parking_area,
                'storage_depolluted_fluids': storage_depolluted_fluids,
                'storage_hazardous_waste': storage_hazardous_waste,
                'storage_processed_scrap': storage_processed_scrap,
                'storage_segregated_spares': storage_segregated_spares,
                'storage_others': storage_others,
                'storage_others_description': storage_others_description
            }
            for field, value in facility_fields.items():
                print(f"Validating field {field} => {value}")

                if value:
                    value = value.strip()
                    print(f"Stripped value for {field}: {value}")

                    
                    # Validate that TIN, CIN, IEC don't have special characters
                    # (excluding spaces since your regex allows spaces)
                    if field in ['sectioned_power', 'employees', 'shifts','total_area','storage_parking_area','storage_depolluted_fluids','storage_hazardous_waste','storage_processed_scrap','storage_segregated_spares','storage_others','storage_others_description']:
                        # Check if has special characters (excluding allowed ones)
                        # We'll use a simpler check
                        import re
                        # Allow alphanumeric and spaces only
                        if re.search(r'[^a-zA-Z0-9\.\s]', value):
                            print(f"Special characters found in {field}")
                            messages.error(
                                request,
                                f"{field.replace('_', ' ').title()} should not contain special characters."
                            )
                            return redirect('facilityDetails')

            if geo_video:
            # Check if file is a video
                allowed_video_types = ['video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo', 'video/x-ms-wmv', 'video/webm', 'video/ogg']
                
                # Get file content type
                content_type = geo_video.content_type
                
                # Also check file extension as backup
                file_name = geo_video.name.lower()
                allowed_extensions = ['.mp4', '.mpeg', '.mov', '.avi', '.wmv', '.webm', '.ogg', '.mkv']
                
                is_video = False
                
                # Method 1: Check MIME type
                if content_type in allowed_video_types:
                    is_video = True
                # Method 2: Check file extension
                elif any(file_name.endswith(ext) for ext in allowed_extensions):
                    is_video = True
                # Method 3: Check if content type starts with 'video/'
                elif content_type.startswith('video/'):
                    is_video = True
                
                if not is_video:
                    messages.error(request, "Please upload only video files (MP4, MPEG, MOV, AVI, WMV, WebM, OGG, MKV).")
                    # Render the form again with existing data if needed
                    # You may want to pass context with previous form data here
                    return redirect('editEquipmentDetails') # Replace with your actual template name

        if not userid:
            messages.error(request, "User session not found. Please log in.")
            return redirect('login')

        # Check if RVSF facility already exists for the user
        try:
            facility = RvsfFacility.objects.get(user_id=userid)
            # Update the existing facility
            facility.geo_video = geo_video if geo_video else facility.geo_video
            facility.total_area = total_area
            facility.shifts_per_day = shifts
            facility.no_of_employees = employees
            facility.status='facility'
            facility.sectioned_power = sectioned_power
            facility.storage_parking_area = storage_parking_area
            facility.storage_depolluted_fluids = storage_depolluted_fluids
            facility.storage_hazardous_waste = storage_hazardous_waste
            facility.storage_processed_scrap = storage_processed_scrap
            facility.storage_segregated_spares = storage_segregated_spares
            facility.storage_others = storage_others
            facility.storage_others_description = storage_others_description
            facility.save()
        except RvsfFacility.DoesNotExist:
            # Create a new facility if not exists
            RvsfFacility.objects.create(
                user_id=userid,
                geo_video=geo_video,
                total_area=total_area,
                shifts_per_day=shifts,
                no_of_employees=employees,
                status='facility',
                sectioned_power=sectioned_power,
                storage_parking_area=storage_parking_area,
                storage_depolluted_fluids=storage_depolluted_fluids,
                storage_hazardous_waste=storage_hazardous_waste,
                storage_processed_scrap=storage_processed_scrap,
                storage_segregated_spares=storage_segregated_spares,
                storage_others=storage_others,
                storage_others_description=storage_others_description
            )
            
            messages.success(request, "Equipment & Facility details saved successfully.")
        # countincomplete = ConfirmApplication.objects.filter(userid = userid , incomplete = 1).count()
        # if countincomplete > 0:
        #         return redirect('editEquipmentDetails')

        return redirect('pollutiondetails')
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving facilitydetails")
                krishan_logger.error(f"Exact facilitydetails  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact facilitydetails Error: {str(db_error)}")


    
# @login_required
# def edit_profile(request):
#     data = RvsfRegistration.objects.filter().first()
#     statename = State.objects.filter(state_id=data.state).first()
#     districtname = District.objects.filter(city_id=data.district).first()
#     # print(districtname)

#     return render(request , 'user/editprofile.html', {'data': data , 'statename':statename , 'districtname': districtname})

@login_required
def edit_profile(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        form = CaptchaForm(request.POST or None)
        
        if request.method == 'POST':
            print('Processing profile update...')
            
            # Get form data
            username = request.POST.get('username')
            userid = request.session.get('user_id')
            email = request.POST.get('auth_email')
            mobile = request.POST.get('auth_mobile')
            email_verified = request.POST.get('email_verified') == 'true'
            mobile_verified = request.POST.get('mobile_verified') == 'true'
            original_email = request.POST.get('original_email', '')
            original_mobile = request.POST.get('original_mobile', '')

            # Validate CAPTCHA
            if not form.is_valid():
                messages.error(request, "Invalid CAPTCHA. Please try again.")
                return redirect('edit_profile')
            
            # Get user data
            usereg = RvsfRegistration.objects.filter(id=userid).first()
            if not usereg:
                messages.error(request, 'User not found.')
                return redirect('edit_profile')
            
            # Check if email has changed and needs verification
            if email != usereg.auth_email and not email_verified:
                messages.error(request, "Email has been changed. Please verify your new email before saving.")
                return redirect('edit_profile')
            
            # Check if mobile has changed and needs verification
            if mobile != usereg.auth_mobile and not mobile_verified:
                messages.error(request, "Mobile number has been changed. Please verify your new mobile number before saving.")
                return redirect('edit_profile')
            
            # Validate email format
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                messages.error(request, "Invalid email format.")
                return redirect('edit_profile')

            import re
            mobile = mobile.strip()
            
            # Check for special characters (allow only digits 0-9)
            if re.search(r'[^0-9]', mobile):
                messages.error(request, "Mobile number should contain only digits (0-9), no special characters or letters.")
                return redirect('edit_profile')

            # Validate mobile format
            if not re.match(r'^\d{10}$', mobile):
                messages.error(request, "Mobile number must be 10 digits.")
                return redirect('edit_profile')

            # Check if email is same as company email
            if email == usereg.company_email:
                messages.error(request, "Company Email and Authorized Person Email cannot be the same")
                return redirect('edit_profile')

            # Update user data
            usereg.auth_email = email
            usereg.auth_mobile = mobile
            
            usereg.save()
            
            messages.success(request, 'Profile updated successfully.')
            return redirect('rvsf_dashboard')

        else:
            userid = request.session.get('user_id')
            data = RvsfRegistration.objects.filter(id=userid).first()
            state = State.objects.filter(state_id=data.state).first()
            district = District.objects.filter(city_id=data.district).first()
            form = CaptchaForm()
            
            return render(request, 'user/editprofile.html', {
                'data': data,
                'statename': state,
                'districtname': district,
                'form': form,
                'userid': userid
            })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving edit_profile")
                krishan_logger.error(f"Exact edit_profile  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact edit_profile Error: {str(db_error)}")

def send_verification_otp11(request):
    userid = request.session.get('user_id')
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            verification_type = data.get('type')  # 'email' or 'mobile'
            value = data.get('value')
            user_id = data.get('user_id')
            
            # Generate 6-digit OTP
            otp = ''.join(random.choices(string.digits, k=6))
            
            # Store OTP in cache with expiration (5 minutes)
            cache_key = f"otp_{verification_type}_{user_id}"
            cache.set(cache_key, {
                'otp': otp,
                'value': value,
                'timestamp': datetime.now().isoformat()
            }, timeout=300)  # 5 minutes
            
            if verification_type == 'email':
                # Send email OTP
                subject = 'Email Verification OTP'
                message = f'Your OTP for email verification is: {otp}. This OTP will expire in 5 minutes.'
                print(message)
                rvsfinfo = RvsfRegistration.objects.filter(id=userid).first()
                if rvsfinfo and rvsfinfo.auth_mobile:
                    send_sms_otp_direct1(rvsfinfo.auth_mobile, otp)
                # send_mail(
                #     subject,
                #     message,
                #     settings.DEFAULT_FROM_EMAIL,
                #     [value],
                #     fail_silently=False,
                # )
            elif verification_type == 'mobile':
                print('aa rha hu')
                rvsfinfo = RvsfRegistration.objects.filter(id=userid).first()
                if rvsfinfo and rvsfinfo.auth_mobile:
                    send_sms_otp_direct1(rvsfinfo.auth_mobile, otp)
                # Here you would integrate with an SMS service
                # For now, we'll just store it and you can implement SMS sending
                pass
            
            return JsonResponse({
                'success': True,
                'message': f'OTP sent to {value}',
                'session_id': cache_key
            })
            
        except Exception as e:
            krishan_logger.info(f"Exact otpviewpage Error: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Failed to send OTP: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def verify_otp11(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            verification_type = data.get('type')
            user_otp = data.get('otp')
            session_id = data.get('session_id')
            
            # Retrieve OTP from cache
            cached_data = cache.get(session_id)
            
            if not cached_data:
                return JsonResponse({
                    'success': False,
                    'message': 'OTP expired or invalid session'
                })
            
            if cached_data['otp'] == user_otp:
                # OTP verified successfully
                cache.delete(session_id)
                
                # Store verification status in session
                verification_key = f"{verification_type}_verified_{session_id.split('_')[-1]}"
                request.session[verification_key] = True
                
                return JsonResponse({
                    'success': True,
                    'message': 'OTP verified successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid OTP'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Verification failed: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
# def edit_profile(request):
#     form = CaptchaForm(request.POST or None)
#     if request.method == 'POST':
#         print('cgashcasc')
#         # password = request.POST.get('password')
#         username = request.POST.get('username')
#         userid = request.session.get('user_id')
#         email = request.POST.get('auth_email')
#         mobile = request.POST.get('auth_mobile')

#         if not form.is_valid():
#             messages.error(request, "Invalid CAPTCHA. Please try again.")
#             return redirect('edit_profile')
            
#         if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
#             messages.error(request, "Invalid email format.")
#             return redirect('edit_profile')

#         if not re.match(r'^\d{10}$', mobile):
#             messages.error(request, "Mobile number must be 10 digits.")
#             return redirect('edit_profile')

#         usereg = RvsfRegistration.objects.filter(id=userid).first()

#         if email == usereg.company_email:
#             messages.error(request , "Company Email and Authorized Person Email Cannot be Same")
#             return redirect('edit_profile')


#         if usereg:
#             # Update username
#             email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
#             if not re.match(email_pattern, email):
#                 messages.error(request, 'Enter a valid email address.')
#                 return redirect('edit_profile')
            
#             if not re.match(r'^\d{10}$', mobile):
#                 messages.error(request, 'Mobile number must be exactly 10 digits.')
#                 return redirect('edit_profile')
            

            

#             # Validate and update password only if provided
#             # if password:
#             #     pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
#             #     if not re.match(pattern, password):
#             #         messages.error(request, 'Password must be at least 8 characters long and include one uppercase, one lowercase, one number, and one special character.')
#             #         return redirect('edit_profile')

#                 # usereg.password = make_password(password)

#             usereg.auth_email = email
#             usereg.auth_mobile = mobile
#             usereg.username = username

#             usereg.save()
#             messages.success(request, 'Profile updated successfully.')
#             return redirect('rvsf_dashboard')

#         else:
#             messages.error(request, 'User not found.')
#             return redirect('edit_profile')

#     else:
#         userid = request.session.get('user_id')
#         data = RvsfRegistration.objects.filter(id=userid).first()
#         state = State.objects.filter(state_id=data.state).first()
#         district = District.objects.filter(city_id=data.district).first()
#         form = CaptchaForm()
#         return render(request, 'user/editprofile.html', {
#             'data': data,
#             'statename': state,
#             'districtname': district,
#             'form': form
#         })
    


@login_required
def RvsfCapacity(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        userid = request.session.get('user_id')
        appcount = checkapplication(request)
        
        # Check if equipment details exist for this user
        equipmentcheck = EquipmentEntry.objects.filter(userid=userid, status='equipment').exists()
        
        # Redirect if equipment details don't exist
        # if not equipmentcheck:
        #     messages.error(request, "Please complete equipment details first!")
        #     return redirect('equipmentDetails')
        
        if appcount > 0:
            messages.error(request, "You already have an active application!")
            return redirect('rvsf_dashboard')

        # If no vehicles, delete all plant capacity safely
        if not VehicleType.objects.filter(userid=userid).exists():
            PlantCapacity.objects.filter(userid=userid).delete()

        today = datetime.today()
        current_year = today.year if today.month >= 4 else today.year - 1

        # Generate last 3 financial years: e.g. ['2024–25', '2023–24', '2022–23']
        financial_years = [f"{fy}-{str(fy + 1)[-2:]}" for fy in range(current_year - 2, current_year + 1)]
        vehicleTypeData = VehicleType.objects.filter(userid=userid)
        capacitydata = PlantCapacity.objects.filter(userid=userid).first()
        capacitycount = PlantCapacity.objects.filter(userid=userid).count()
        curryear = datetime.now().year
        year1 = curryear-3
        year2 = curryear-2
        year3 = curryear-1
        year5 = curryear-4
        year4 = curryear

        
        context = {
        'Vehicledata': vehicleTypeData,
        'capacitydata': capacitydata,
        'cpacitycount': capacitycount,
        'year1' : year1,
        'year2' : year2,
        'year3' : year3,
        'year4' : year4,
        'year5' : year5
        }
        
        
        
        return render(request, 'user/capacity.html', context)
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving capacity")
                krishan_logger.error(f"Exact capacity  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact capacity Error: {str(db_error)}")
# def RvsfCapacity(request):
    
#     userid = request.session.get('user_id')
#     appcount = checkapplication(request)
#     if appcount > 0:
#         messages.error(request, "You already have an active application!")
#         return redirect('rvsf_dashboard')

#     # If no vehicles, delete all plant capacity safely
#     if not VehicleType.objects.filter(userid=userid).exists():
#         PlantCapacity.objects.filter(userid=userid).delete()


#     today = datetime.today()
#     current_year = today.year if today.month >= 4 else today.year - 1

#     # Generate last 3 financial years: e.g. ['2024–25', '2023–24', '2022–23']
#     financial_years = [f"{fy}-{str(fy + 1)[-2:]}" for fy in range(current_year - 2, current_year + 1)]
#     vehicleTypeData = VehicleType.objects.filter(userid=userid)
#     capacitydata = PlantCapacity.objects.filter(userid=userid).first()
#     capacitycount = PlantCapacity.objects.filter(userid=userid).count()
#     curryear = datetime.now().year
#     year1 = curryear-3
#     year2 = curryear-2
#     year3 = curryear-1

    
#     context = {
#     'Vehicledata': vehicleTypeData,
#     'capacitydata': capacitydata,
#     'cpacitycount': capacitycount,
#     'year1' : year1,
#     'year2' : year2,
#     'year3' : year3
#      }
       
     
    
#     return render(request, 'user/capacity.html', context)


@login_required

def submit_plant_capacity(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == "POST":
            userid = request.session.get('user_id')

            # Capture all input values
            installed_vehicles = request.POST.get('installed_vehicles')
            installed_steel = request.POST.get('installed_steel')

            operating_vehicles1 = request.POST.get('operating_vehicles1')
            operating_vehicles2 = request.POST.get('operating_vehicles2')
            operating_vehicles3 = request.POST.get('operating_vehicles3')

            operating_steel1 = request.POST.get('operating_steel1')
            operating_steel2 = request.POST.get('operating_steel2')
            operating_steel3 = request.POST.get('operating_steel3')

            year1 = request.POST.get('year1')
            year2 = request.POST.get('year2')
            year3 = request.POST.get('year3')

            capacity_fields = {
                'installed_vehicles': installed_vehicles,
                'installed_steel': installed_steel,
                'operating_vehicles1': operating_vehicles1,
                'operating_vehicles2': operating_vehicles2,
                'operating_vehicles3': operating_vehicles3,
                'operating_steel1': operating_steel1,
                'operating_steel2': operating_steel2,
                'operating_steel3': operating_steel3,
                
            }
            for field, value in capacity_fields.items():
                print(f"Validating field {field} => {value}")

                if value:
                    value = value.strip()
                    print(f"Stripped value for {field}: {value}")

                    
                    # Validate that TIN, CIN, IEC don't have special characters
                    # (excluding spaces since your regex allows spaces)
                    if field in ['installed_vehicles', 'installed_steel', 'operating_vehicles1','operating_vehicles2','operating_vehicles3','operating_steel1','operating_steel2','operating_steel3']:
                        # Check if has special characters (excluding allowed ones)
                        # We'll use a simpler check
                        import re
                        # Allow alphanumeric and spaces only
                        if re.search(r'[^a-zA-Z0-9\.]', value):
                            print(f"Special characters found in {field}")
                            messages.error(
                                request,
                                f"{field.replace('_', ' ').title()} should not contain special characters."
                            )
                            return redirect('Capacity')

            # Check if a record exists
            existing = PlantCapacity.objects.filter(userid=userid).first()
            if existing:
                # Update
                existing.installed_vehicles = installed_vehicles
                existing.installed_steel = installed_steel
                existing.operating_vehicles1 = operating_vehicles1
                existing.operating_vehicles2 = operating_vehicles2
                existing.operating_vehicles3 = operating_vehicles3
                existing.operating_steel1 = operating_steel1
                existing.operating_steel2 = operating_steel2
                existing.operating_steel3 = operating_steel3
                existing.year1 = year1
                existing.year2 = year2
                existing.year3 = year3
                existing.status='capacity'
                existing.save()
            else:
                # Create
                PlantCapacity.objects.create(
                    userid=userid,
                    installed_vehicles=installed_vehicles,
                    installed_steel=installed_steel,
                    operating_vehicles1=operating_vehicles1,
                    operating_vehicles2=operating_vehicles2,
                    operating_vehicles3=operating_vehicles3,
                    operating_steel1=operating_steel1,
                    operating_steel2=operating_steel2,
                    operating_steel3=operating_steel3,
                    year1=year1,
                    year2=year2,
                    year3=year3,
                    status='capacity'
                )



            # Code Needs to be added
            messages.success(request, "Plant capacity details saved successfully.")
            # checkincompletesattus = ConfirmApplication.objects.filter(userid = userid , incomplete = 1).count()
            # if checkincompletesattus > 0 :
            #   return redirect('viewRvsfCapacity')
            
            return redirect('equipmentDetails')
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving submit plant capacity")
                krishan_logger.error(f"Exact submit plant capacity  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact submit plant capacity Error: {str(db_error)}")
        # return redirect('rvsf_dashboard')  # replace with your actual view name
    
@login_required
def pollutiondetails(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        userid = request.session.get('user_id')
        appcount = checkapplication(request)
        capcacitycheck = PlantCapacity.objects.filter(userid=userid, status='capacity').exists()
        
        # Redirect if equipment details don't exist
        # if not capcacitycheck:
        #     messages.error(request, "Please complete Capcity details first!")
        #     return redirect('Capacity')
        if appcount > 0:
            messages.error(request, "You already have an active application!")
            return redirect('rvsf_dashboard')
        print(userid)
        try:
            devicedata = PollutionDevice.objects.filter(userid=userid).order_by('-created_at')
            wastedata = WasteRecycled.objects.filter(userid = userid).order_by('-created_at')
            print(devicedata)
        except PollutionDevice.DoesNotExist:
            devicedata = None
        return render(request, 'user/pollutiondetails.html', {'devices': devicedata , 'wastes':wastedata})
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving pollution details")
                krishan_logger.error(f"Exact pollution details  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact pollution details Error: {str(db_error)}")
                
@login_required
def delete_device(request):
    userid = request.session.get('user_id') 
    if request.method == 'POST':
        dev_id = request.POST.get('device_id')
        dev = get_object_or_404(PollutionDevice, id=dev_id)
        dev.delete()
        countcheck = UntTrails.objects.filter(industryid = userid , EditMode = 6).count()
        if countcheck > 0:
            return redirect('editPollutionDetail')
    return redirect('pollutiondetails')  # or whichever view shows the device list
@login_required
def delete_waste(request):
    userid = request.session.get('user_id')
    if request.method == 'POST':
        waste_id = request.POST.get('waste_id')
        wastedel =get_object_or_404(WasteRecycled, id = waste_id)
        wastedel.delete()
        countcheck = UntTrails.objects.filter(industryid = userid , EditMode = 6).count()
        if countcheck > 0:
            return redirect('editPollutionDetail')
    return redirect('pollutiondetails') 

@login_required
def add_device(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == 'POST':
            pollutionType = request.POST.get('pollutionType')
            pollution_control_name = request.POST.get('pollution_control_name')
            number_of_devices = request.POST.get('number_of_devices')
            device_doc = request.FILES.get('device_doc')
            userid = request.session.get('user_id')

            if device_doc:
                # Get the file extension
                file_name = device_doc.name.lower()
                
                # List of allowed image extensions
                allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif']
                
                # Check if file has a valid image extension
                is_valid_image = any(file_name.endswith(ext) for ext in allowed_extensions)
                
                if not is_valid_image:
                    messages.error(
                        request,
                        f"Invalid file format. Please upload an image file (allowed formats: JPG, JPEG, PNG, GIF, BMP, WEBP, TIFF)."
                    )
                    return redirect('pollutiondetails')
                
                # Check file size (optional: limit to 5MB)
                if device_doc.size > 5 * 1024 * 1024:  # 5MB
                    messages.error(
                        request,
                        "File is too large. Maximum allowed size is 5MB."
                    )
                    return redirect('pollutiondetails')
            
            device_fields = {
                'number_of_devices': number_of_devices,
                'pollution_control_name': pollution_control_name,
                
                
            }
            for field, value in device_fields.items():
                print(f"Validating field {field} => {value}")

                if value:
                    value = value.strip()
                    print(f"Stripped value for {field}: {value}")

                    
                    # Validate that TIN, CIN, IEC don't have special characters
                    # (excluding spaces since your regex allows spaces)
                    if field in ['number_of_devices', 'pollution_control_name']:
                        # Check if has special characters (excluding allowed ones)
                        # We'll use a simpler check
                        import re
                        # Allow alphanumeric and spaces only
                        if re.search(r'[^a-zA-Z0-9\s]', value):
                            print(f"Special characters found in {field}")
                            messages.error(
                                request,
                                f"{field.replace('_', ' ').title()} should not contain special characters."
                            )
                            return redirect('pollutiondetails')

            PollutionDevice.objects.create(
                userid = userid,
                device_type = pollutionType,
                name = pollution_control_name,
                quantity = number_of_devices,
                device_doc = device_doc,
                status='pollution'
            )
            countcheck = UntTrails.objects.filter(industryid = userid , EditMode = 6).count()
            if countcheck > 0:
                return redirect('editPollutionDetail')

            return redirect('pollutiondetails')
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving add device")
                krishan_logger.error(f"Exact add device  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact add device Error: {str(db_error)}")


@login_required
def add_waste(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == 'POST':
            category = request.POST.get('category')
            if category == 'Other':
                category = request.POST.get('category_other')

            qty_recovered = request.POST.get('qty_recovered')
            qty_recycled = request.POST.get('qty_recycled')
            recycler_name = request.POST.get('recycler_name')
            agreement_details = request.POST.get('agreement_details')
            agreement = request.FILES.get('agreement')
            userid = request.session.get('user_id')

            waste_fields = {
                'agreement_details': agreement_details,
                'recycler_name': recycler_name,
                'qty_recycled': qty_recycled,
                'qty_recovered': qty_recovered,
                'category': category
            }
            for field, value in waste_fields.items():
                print(f"Validating field {field} => {value}")

                if value:
                    value = value.strip()
                    print(f"Stripped value for {field}: {value}")

                    
                    # Validate that TIN, CIN, IEC don't have special characters
                    # (excluding spaces since your regex allows spaces)
                    if field in ['agreement_details', 'recycler_name', 'qty_recycled','qty_recovered','category']:
                        # Check if has special characters (excluding allowed ones)
                        # We'll use a simpler check
                        import re
                        # Allow alphanumeric and spaces only
                        if re.search(r'[^a-zA-Z0-9\s]', value):
                            print(f"Special characters found in {field}")
                            messages.error(
                                request,
                                f"{field.replace('_', ' ').title()} should not contain special characters."
                            )
                            return redirect('pollutiondetails')


            agreement = request.FILES.get('agreement')

            if not agreement:
                messages.error(request, "Agreement PDF is required.")
                return redirect('pollutiondetails')

            # Size check (2MB – adjust if needed)
            if agreement.size > 2 * 1024 * 1024:
                messages.error(request, "Agreement PDF must be less than 2MB.")
                return redirect('pollutiondetails')

            # Valid PDF check (NO modification)
            if not is_valid_pdf(agreement):
                messages.error(request, "Agreement is not a valid PDF file.")
                return redirect('pollutiondetails')

            WasteRecycled.objects.create(
                category = category,
                qty_recovered = qty_recovered,
                qty_recycled = qty_recycled,
                recycler_name = recycler_name,
                agreement_details = agreement_details,
                agreement = agreement,
                userid = userid,
                status='waste'
            
            )

            countcheck = UntTrails.objects.filter(industryid = userid , EditMode = 6).count()
            if countcheck > 0:
                return redirect('editPollutionDetail')

            return redirect('pollutiondetails')
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving add waste")
                krishan_logger.error(f"Exact add waste  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact add waste Error: {str(db_error)}")





@login_required
def check_username(request):
    username = request.GET.get('username')
    print(username)
    exists = RvsfRegistration.objects.filter(username=username).exists()
    print(exists)
    return JsonResponse({'exists': exists})    


def fetch_gst(request):

    gst_no = request.GET.get("gst_no", "").strip()

    if not gst_no or len(gst_no) != 15:
        return JsonResponse({"error": "Please enter a valid 15-digit GST Number"}, status=400)
    
    if RvsfRegistration.objects.filter(gst_no=gst_no).exists():
        return JsonResponse({"error": "GST Number already registered."}, status=400)

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


@login_required   
def delequipment(request):
    userid = request.session.get('user_id')
    if request.method == 'POST':
        equipmentid = request.POST.get('equip_id')
        equipment = get_object_or_404(EquipmentEntry, id=equipmentid)
        equipment.delete()
        messages.success(request, "Equipment entry deleted successfully.")
    
    # countincomplete = ConfirmApplication.objects.filter(userid = userid , incomplete = 1).count()
    # if countincomplete > 0:
    #         return redirect('editEquipmentDetails')
    return redirect('equipmentDetails') 

# def AddVehicleType(request):
#     if request.method == 'POST':
#         vehicle_type = request.POST.get('vehicle_type')
    
#         if vehicle_type == 'Others':
#             vehicle_type = request.POST.get('other_name')
#         userid = request.session.get('user_id')
    
#     VehicleType.objects.create(
#         vehicle_type = vehicle_type,
#         userid = userid,
#         Remarks = 'NA'
#     )
#     checkincompletesattus = ConfirmApplication.objects.filter(userid = userid , incomplete = 1).count()
#     if checkincompletesattus > 0 :
#         return redirect('viewRvsfCapacity')
#     return redirect('Capacity')

# def AddVehicleType(request):
#     userid = request.session.get('user_id')
#     print("Complete POST data:", request.POST)
#     if request.method == 'POST':
#         selected_vehicles_json = request.POST.get('selected_vehicles')
       
#         if selected_vehicles_json:
#             selected_vehicles = json.loads(selected_vehicles_json)

            
           
#             for vehicle in selected_vehicles:
#                     vehicle_type = {
#             'vehicle_type': vehicle
            
            
#         }
#         for field, value in vehicle_type.items():
#             print(f"Validating field {field} => {value}")

#             if value:
#                 value = value.strip()
#                 print(f"Stripped value for {field}: {value}")

                
#                 # Validate that TIN, CIN, IEC don't have special characters
#                 # (excluding spaces since your regex allows spaces)
#                 if field in ['vehicle_type']:
#                     # Check if has special characters (excluding allowed ones)
#                     # We'll use a simpler check
#                     import re
#                     # Allow alphanumeric and spaces only
#                     if re.search(r'[^a-zA-Z0-9\s]', value):
#                         print(f"Special characters found in {field}")
#                         messages.error(
#                             request,
#                             f"{field.replace('_', ' ').title()} should not contain special characters."
#                         )
#                         return redirect('Capacity')
#                 if vehicle.startswith('Other:'):
                    
                
#                     # Handle custom vehicle types
#                     vehicle_type = vehicle[6:]  # Remove "Other:" prefix
#                     VehicleType.objects.create(
#                         vehicle_type="Others",
#                         userid=userid,
#                         Remarks=vehicle_type
#                     )
#                 else:
#                     # Handle standard vehicle types
#                     VehicleType.objects.create(
#                         vehicle_type=vehicle,
#                         userid=userid,
#                         Remarks='NA'
#                     )
       
#         # checkincompletesattus = ConfirmApplication.objects.filter(userid=userid, incomplete=1).count()
#         # if checkincompletesattus > 0:
#         #     return redirect('Capacity')
#         return redirect('Capacity')

# def AddVehicleType(request):
#     userid = request.session.get('user_id')
#     print("Complete POST data:", request.POST)

#     if request.method == 'POST':
#         selected_vehicles_json = request.POST.get('selected_vehicles')

#         if not selected_vehicles_json:
#             messages.error(request, "No vehicle type selected.")
#             return redirect('Capacity')

#         selected_vehicles = json.loads(selected_vehicles_json)

#         for vehicle in selected_vehicles:
#             if not vehicle:
#                 continue

#             vehicle = vehicle.strip()
#             print("Processing vehicle:", vehicle)

#             # --- Handle "Other:" case ---
#             if vehicle.startswith('Other:'):
#                 custom_vehicle = vehicle[6:].strip()

#                 # Validate custom vehicle text
#                 if re.search(r'[^a-zA-Z0-9\s]', custom_vehicle):
#                     messages.error(
#                         request,
#                         "Other vehicle type should not contain special characters."
#                     )
#                     return redirect('Capacity')

#                 VehicleType.objects.create(
#                     vehicle_type="Others",
#                     userid=userid,
#                     Remarks=custom_vehicle
#                 )

#             # --- Standard vehicle types ---
#             else:
#                 # Validate standard vehicle
#                 if re.search(r'[^a-zA-Z0-9\s]', vehicle):
#                     messages.error(
#                         request,
#                         "Vehicle type should not contain special characters."
#                     )
#                     return redirect('Capacity')

#                 VehicleType.objects.create(
#                     vehicle_type=vehicle,
#                     userid=userid,
#                     Remarks='NA'
#                 )

#         return redirect('Capacity')


ALLOWED_VEHICLES = {"2W", "3W", "LMV", "MMV", "HMV", "Others"}

def AddVehicleType(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        userid = request.session.get("user_id")

        if request.method != "POST":
            return redirect("Capacity")

        selected_vehicles_json = request.POST.get("selected_vehicles")

        if not selected_vehicles_json:
            messages.error(request, "No vehicle type selected.")
            return redirect("Capacity")

        # ---- Safe JSON parsing ----
        try:
            selected_vehicles = json.loads(selected_vehicles_json)
            if not isinstance(selected_vehicles, list):
                raise ValueError
        except Exception:
            messages.error(request, "Invalid request data.")
            return redirect("Capacity")

        for vehicle in selected_vehicles:
            if not isinstance(vehicle, str):
                continue

            vehicle = strip_tags(vehicle).strip()  # 🔐 XSS protection

            # ---- Handle Others ----
            if vehicle.startswith("Other:"):
                custom_vehicle = vehicle[6:].strip()

                if not custom_vehicle:
                    messages.error(request, "Other vehicle type cannot be empty.")
                    return redirect("Capacity")

                if not re.fullmatch(r"[A-Za-z0-9\s]{2,50}", custom_vehicle):
                    messages.error(
                        request,
                        "Other vehicle type contains invalid characters."
                    )
                    return redirect("Capacity")

                VehicleType.objects.create(
                    vehicle_type="Others",
                    userid=userid,
                    Remarks=custom_vehicle
                )

            # ---- Standard vehicles ----
            else:
                if vehicle not in ALLOWED_VEHICLES:
                    messages.error(
                        request,
                        "Unauthorized vehicle type detected."
                    )
                    return redirect("Capacity")

                VehicleType.objects.create(
                    vehicle_type=vehicle,
                    userid=userid,
                    Remarks="NA"
                )

        messages.success(request, "Vehicle types added successfully.")
        return redirect("Capacity")
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving add vehicle type")
                krishan_logger.error(f"Exact add vehicle type  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact add vehicle type Error: {str(db_error)}")

def delete_vehicle_type(request):
    vehicle_id = request.POST.get('vehicle_id')
    user_id = request.session.get('user_id')

    if vehicle_id:
        vehicle = get_object_or_404(VehicleType, id=vehicle_id, userid=user_id)
        vehicle.delete()
    else:
        vehicle = get_object_or_404(PlantCapacity, userid=user_id)
        vehicle.delete()

    # checkincompletesattus = ConfirmApplication.objects.filter(userid = user_id , incomplete = 1).count()
    # if checkincompletesattus > 0 :
    #     return redirect('viewRvsfCapacity')
    return redirect('Capacity')  # Replace 'capacity' with your page's URL name

@login_required
def confirmapp(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        userid = request.session.get('user_id')
        appcount = checkapplication(request)
        if appcount > 0:
            messages.error(request, "You already have an active application!")
            return redirect('rvsf_dashboard')
        entity = RvsfRegistration.objects.filter(id = userid).first()
        generaldata = GeneralDetails.objects.filter(userid=userid).first()
        statename = State.objects.filter(state_id=entity.state).first()
        districtname = District.objects.filter(city_id=entity.district).first()
        
        equipmentdata = EquipmentType.objects.all().order_by('id')
        data = EquipmentEntry.objects.filter(userid = userid)
        facilitydata = RvsfFacility.objects.filter(user_id = userid).first()
        vehicleTypeData = VehicleType.objects.filter(userid=userid)
        capacityPlant = PlantCapacity.objects.filter(userid =  userid).first()
        pollutiondetails = PollutionDevice.objects.filter(userid = userid)
        wasterecycled = WasteRecycled.objects.filter(userid = userid)
    
        

        return render(request,'user/confirm.html', {'entity' : entity ,
        'general' : generaldata , 'statename': statename, 'districtname':districtname,
        'equipmentdata': equipmentdata, 'data':data, 'facilitydata': facilitydata,
        'VechileType': vehicleTypeData, 'capacitydata':capacityPlant,'pollutiondetails':pollutiondetails,'wasterecycled':wasterecycled                                          
        })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving confirm app")
                krishan_logger.error(f"Exact confirm app  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact confirm app Error: {str(db_error)}")

def generate_application_number():
    return f"APP-{uuid.uuid4().hex[:10].upper()}"

def calculate_registration_fees(quantity_installed: int) -> int:
    """
    Determines registration fees based on quantity_installed:
    - ≤ 6,000 → 25,000
    - 6,001–15,000 → 50,000
    - 15,001–30,000 → 75,000
    - > 30,000 → 100,000
    """
    if quantity_installed <= 6000:
        return 25000
    elif quantity_installed <= 15000:
        return 50000
    elif quantity_installed <= 30000:
        return 75000
    else:
        return 100000

@login_required
def postconfirmapp(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == 'POST':
            userid = request.session.get('user_id')
            appno = generate_application_number()
            regstate = RvsfRegistration.objects.filter(id= userid).first()

            fetchstateid  = State.objects.filter(state_id = regstate.state).first()
            stateid = fetchstateid.state_id
            statename = fetchstateid.state_name

            # return HttpResponse(fetchstateid.state_id)
            


        try:
            quantity_installed = int(request.POST.get('quantity_installed'))
        except (TypeError, ValueError):
            # Invalid input — handle appropriately
            # For example, return an error response or set a default
            quantity_installed = 0
            

            registration_fees = calculate_registration_fees(quantity_installed)        
            paymentModeStatus = 'Initiated'
            transactionNo = str(appno) + str(userid)
            checkpayment = ConfirmApplication.objects.filter(userid = userid)
            if checkpayment!= None:
                ConfirmApplication.objects.create(
                    userid = userid,
                    appno = appno,
                    paymentModeStatus = paymentModeStatus,
                    transactionNo = transactionNo,
                    registrationfees = registration_fees,
                    state_id = stateid,
                    statename = statename,
                    role_id = 1

        
                )

                return redirect('rvsf_dashboard')
            else:
                return HttpResponse('Payment Already Inititated')
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving post confirmapp")
                krishan_logger.error(f"Exact post confirmapp  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact post confirmapp Error: {str(db_error)}")
 
    
    
@csrf_exempt
def initiate_payment(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            order_id = data.get('order_id')
            amount = data.get('amount')
            customer_id = data.get('customer_id')
            return_url = data.get('return_url')

            # Construct the payload
            payload = {
                "merchant_id": "111077",
                "order_id": order_id,
                "amount": amount,
                "customer_id": customer_id,
                "return_url": return_url
            }

            # Generate checksum
            MERCHANT_ID = '111077'
            CLIENT_ID = '59194fe5-4c27-4e6e-8deb-4e59f8f4fd7b'
            CLIENT_SECRET = '024dd66a367549b380bd322ff6c3b279'
            END_POINT = 'https://pluraluat.v2.pinepg.in/api/pay/v1'


            checksum_str = f"{MERCHANT_ID}|{order_id}|{amount}|{CLIENT_SECRET}"
            checksum = hashlib.sha256(checksum_str.encode()).hexdigest()
            payload["checksum"] = checksum

            # Send the request to Pine Labs
            headers = {'Content-Type': 'application/json'}
            response = requests.post(END_POINT, headers=headers, data=json.dumps(payload))

            return JsonResponse(response.json())
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400) 
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving initiate_payment")
                krishan_logger.error(f"Exact initiate_payment  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact initiate_payment Error: {str(db_error)}")  

@login_required
def track_application(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        user_id = request.session.get('user_id')
        try:
            application = ConfirmApplication.objects.get(userid=user_id)
        except ConfirmApplication.DoesNotExist:
            application = None

        steps = []
        if application:
            steps = [
                {
                    "title": "Submitted",
                    "completed": application.appstatus > 0,
                    "current": False,
                    "updated_at": application.created_at,
                },

                {
                    "title": "Payment",
                    "completed": application.paymentstatus == 1,
                    "current": application.paymentstatus == 0,
                    "updated_at": application.updated_at,
                },

                {
                    "title": "Processing",
                    "completed": application.appstatus > 2 and application.incomplete != 1,
                    "current": application.appstatus > 2 and application.incomplete != 1,
                    "updated_at": application.updated_at,
                },

                {
                    "title": "Query Raised",
                    "completed": application.incomplete != 1,     # incomplete=1 → NOT completed
                    "current": application.incomplete == 1,       # show in progress
                    "updated_at": application.updated_at,
                },

                {
                    "title": "Approved",
                    "completed": application.appstatus == 9,
                    "current": False,
                    "updated_at": application.updated_at,
                },
            ]

            # mark current if none completed
            for step in steps:
                if step["completed"] == False and step["current"] == False:
                    step["current"] = True
                    break

            latest = next((s for s in reversed(steps) if s["completed"]), None)
            latest_update = f"{latest['title']} at {latest['updated_at']:%b %d, %Y}" if latest else ""
        else:
            latest_update = ""
        
        return render(request, 'user/trackapplication.html', {
            'application': application, 'steps': steps, 'latest_update': latest_update
        })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving track application")
                krishan_logger.error(f"Exact track application  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact track application Error: {str(db_error)}")
# Fetch ChecklistData with StateBoards Comments
@login_required
def viewchecklist(request):
    print('hfskhfsjfjkhfskhsfskh')
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            print(industryid)
            AppNo = request.POST.get('appno')
            
            commentgiven = UntTrails.objects.filter(industryid = industryid)
            editone = UntTrails.objects.filter(industryid = industryid , EditMode = 1).first()
            edittwo = UntTrails.objects.filter(industryid = industryid , EditMode = 2).first()
            editthree = UntTrails.objects.filter(industryid = industryid , EditMode = 3).first()
            editfour = UntTrails.objects.filter(industryid = industryid , EditMode = 4).first()
            editfive = UntTrails.objects.filter(industryid = industryid , EditMode = 5).first()
            editSix = UntTrails.objects.filter(industryid = industryid , EditMode = 6).first()
            fectchsignup = SignupChecklist.objects.filter(industryid = industryid).first()
            fetchgeneral = GeneralChecklist.objects.filter(Industryid = industryid).first()
            fetchequipment = EquipmentChecklist.objects.filter(industryid = industryid).first()
            fetchfacility = FacilityChecklist.objects.filter(industryid = industryid).first()
            fetchcapacity = CapacityChecklist.objects.filter(industryid = industryid).first()
            fetchpollution = PollutionChecklist.objects.filter(industryid = industryid).first()
            fetchwasterec = WasteRecycleChecklist.objects.filter(industryid = industryid).first()
            fetchpayment = PaymentChecklist.objects.filter(industryid = industryid).first()
            print(fetchgeneral)

            
            return render(request,'user/viewchecklist.html', {
                'comment': commentgiven,
                'signup': fectchsignup,
                'general': fetchgeneral,
                'equipment': fetchequipment,
                'facility': fetchfacility,
                'capacity': fetchcapacity,
                'pollution': fetchpollution,
                'wasterec': fetchwasterec,
                'fetchpayment': fetchpayment,
                'edit1' : editone,
                'edit2' : edittwo,
                'edit3' : editthree,
                'edit4' : editfour,
                'edit5' : editfive,
                'edit6' : editSix, 
            })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving viewchecklist")
                krishan_logger.error(f"Exact viewchecklist  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact viewchecklist Error: {str(db_error)}")



# -------------------------------------------------------------------
# HELPER TO PICK NEW FILE OR KEEP EXISTING ONE
# -------------------------------------------------------------------
def get_file(request, key):
    """Return uploaded file if present, else None so old value stays untouched."""
    return request.FILES[key] if key in request.FILES else None


# def update_if_present(instance, field, req, key):
#     """Update only if the field came in POST and has a value."""
#     if key in req and req.get(key) not in [None, "", "null"]:
#         setattr(instance, field, req.get(key))
def update_if_present(instance, field, req, key, clean_address=False):
    """Update only if the field came in POST and has a value."""
    if key in req and req.get(key) not in [None, "", "null"]:
        value = req.get(key)

        # Special cleaning ONLY when requested
        if clean_address:
            value = value.split(",")[0].strip()

        setattr(instance, field, value)



# def resubmit_application(request):
#     userid = request.session.get("user_id")
        
#     # if request.method == "POST":
#     #     print("POST DATA:", request.POST)
#     #     print("FILES:", request.FILES)

#     #     # ==============================================================
#     #     # 1) SIGNUP TABLE → RvsfRegistration
#     #     # ==============================================================

#     #     signup = RvsfRegistration.objects.get(id=userid)

#     #     signup.company_name = request.POST.get("company_name_signup")
#     #     signup.registered_address = request.POST.get("address_signup")
#     #     signup.company_email = request.POST.get("company_email_signup")

#     #     # undertaking file
#     #     signup.undertaking = get_file(request, "Undertaking_pdf")

#     #     # signup.save()



#     #     # ==============================================================
#     #     # 2) GENERAL DOCUMENTS → GeneralDetails
#     #     # ==============================================================

#     #     general = GeneralDetails.objects.get(userid=userid)

#     #     general.gst_pdf = get_file(request, "gst_pdf_signup")
#     #     general.pan_pdf = get_file(request, "pan_pdf_signup")
#     #     general.tin_pdf = get_file(request, "tin_pdf_signup")
#     #     general.cin_pdf = get_file(request, "cin_pdf_signup")
#     #     general.iec_pdf = get_file(request, "iec_pdf_signup")

#     #     # general.save()



#     #     # ==============================================================
#     #     # 3) RVSF DETAILS (consents, registrations) → RvsfDetails
#     #     # ==============================================================

#     #     rvsf = RvsfDetails.objects.get(userid=userid)

#     #     rvsf.address = request.POST.get("address_rvsf")
#     #     rvsf.latitude = request.POST.get("latitude_rvsf")
#     #     rvsf.longitude = request.POST.get("longitude_rvsf")
#     #     rvsf.state = request.POST.get("state_rvsf")

#     #     rvsf.cto_number = request.POST.get("cto_number_rvsf")
#     #     rvsf.consent_validity = request.POST.get("consent_validity_rvsf")

#     #     rvsf.cto_pdf = get_file(request, "cto_pdf_rvsf")
#     #     rvsf.howm_validity = request.POST.get("howm_validity_rvsf")
#     #     rvsf.howm_pdf = get_file(request, "howm_pdf_rvsf")

#     #     rvsf.dic_validity = request.POST.get("dic_validity_rvsf")
#     #     rvsf.dic_pdf = get_file(request, "dic_pdf_rvsf")

#     #     rvsf.rvsf_reg_no = request.POST.get("rvsf_reg_no_rvsf")
#     #     rvsf.rvsf_validity = request.POST.get("rvsf_validity_rvsf")
#     #     rvsf.rvsf_pdf = get_file(request, "pdf_rvsf")

#     #     rvsf.process_flow_pdf = get_file(request, "process_flow_pdf_rvsf")
#     #     rvsf.material_balance_pdf = get_file(request, "material_balance_pdf_rvsf")

#     #     rvsf.annual_returns_pdf = get_file(request, "annual_returns_pdf_rvsf_0")
#     #     rvsf.annual_returns_pdf1 = get_file(request, "annual_returns_pdf_rvsf_1")

#     #     # rvsf.save()



#     #     # ==============================================================
#     #     # 4) FACILITY DETAILS → RvsfFacility
#     #     # ==============================================================

#     #     facility = RvsfFacility.objects.get(user_id=userid)

#     #     facility.total_area = request.POST.get("total_area")
#     #     facility.shifts_per_day = request.POST.get("shifts_per_day")
#     #     facility.no_of_employees = request.POST.get("no_of_employees")
#     #     facility.sectioned_power = request.POST.get("sectioned_power")

#     #     facility.geo_video = get_file(request, "geo_video")

#     #     # facility.save()



#     #     # ==============================================================
#     #     # 5) EQUIPMENTS → EquipmentEntry (MULTIPLE ROWS)
#     #     # ==============================================================

#     #     existing_equipment = EquipmentEntry.objects.filter(userid=userid)
#     #     existing_equipment.delete()

#     #     index = 1
#     #     while True:
#     #         eq_type = request.POST.get(f"equipment_{index}_type")
#     #         if not eq_type:
#     #             break

#     #         # EquipmentEntry.objects.create(
#     #         #     userid=userid,
#     #         #     equipment_type=eq_type,
#     #         #     equipment_id=index,
#     #         #     power_rating=request.POST.get(f"equipment_{index}_power"),
#     #         #     operating_hours=request.POST.get(f"equipment_{index}_hours"),
#     #         #     capacity_equipment_perton=request.POST.get(f"equipment_{index}_capacity"),
#     #         #     quantity=request.POST.get(f"equipment_{index}_qty"),
#     #         #     geo_tagged_pdf=get_file(request, f"equipment_{index}_geo_tagged_pdf")
#     #         # )

#     #         index += 1



#     #     # ==============================================================
#     #     # 6) CAPACITY → PlantCapacity + VehicleType
#     #     # ==============================================================

#     #     # PlantCapacity (one row)
#     #     # capacity, _ = PlantCapacity.objects.get_or_create(userid=userid)
#     #     # capacity.installed_vehicles = request.POST.get("installed_vehicle_total") or 0
#     #     # capacity.installed_steel = request.POST.get("installed_steel_total") or 0
#     #     # capacity.operating_vehicles1 = request.POST.get("oper_veh_1") or 0
#     #     # capacity.operating_vehicles2 = request.POST.get("oper_veh_2") or 0
#     #     # capacity.operating_vehicles3 = request.POST.get("oper_veh_3") or 0
#     #     # capacity.operating_steel1 = request.POST.get("oper_steel_1") or 0
#     #     # capacity.operating_steel2 = request.POST.get("oper_steel_2") or 0
#     #     # capacity.operating_steel3 = request.POST.get("oper_steel_3") or 0

#     #     # capacity.year1 = request.POST.get("year_1")
#     #     # capacity.year2 = request.POST.get("year_2")
#     #     # capacity.year3 = request.POST.get("year_3")
#     #     # capacity.save()

#     #     # Vehicle types (multiple)
#     #     VehicleType.objects.filter(userid=userid).delete()
#     #     vehicles = request.POST.getlist("selected_vehicles")
#     #     for v in vehicles:
#     #         VehicleType.objects.create(userid=userid, vehicle_type=v)



#     #     # ==============================================================
#     #     # 7) POLLUTION DEVICES → PollutionDevice (MULTIPLE ROWS)
#     #     # ==============================================================

#     #     PollutionDevice.objects.filter(userid=userid).delete()
#     #     idx = 1
#     #     while True:
#     #         dev_type = request.POST.get(f"device_{idx}_type")
#     #         if not dev_type:
#     #             break

#     #         # PollutionDevice.objects.create(
#     #         #     userid=userid,
#     #         #     device_type=dev_type,
#     #         #     name=request.POST.get(f"device_{idx}_name"),
#     #         #     quantity=request.POST.get(f"device_{idx}_qty"),
#     #         #     device_doc=get_file(request, f"device_{idx}_doc")
#     #         # )
#     #         idx += 1



#     #     # ==============================================================
#     #     # 8) WASTE RECYCLED → WasteRecycled (MULTIPLE ROWS)
#     #     # ==============================================================

#     #     WasteRecycled.objects.filter(userid=userid).delete()

#     #     w = 1
#     #     while True:
#     #         cat = request.POST.get(f"waste_{w}_category")
#     #         if not cat:
#     #             break

#     #         # WasteRecycled.objects.create(
#     #         #     userid=userid,
#     #         #     category=cat,
#     #         #     qty_recovered=request.POST.get(f"waste_{w}_qty_recovered") or 0,
#     #         #     qty_recycled=request.POST.get(f"waste_{w}_qty_recycled") or 0,
#     #         #     recycler_name=request.POST.get(f"waste_{w}_recycler"),
#     #         #     agreement_details=request.POST.get(f"waste_{w}_agreement_details"),
#     #         #     agreement=get_file(request, f"waste_{w}_agreement")
#     #         # )
#     #         # w += 1

#     #         return redirect("viewchecklist1")
#     #     return redirect("viewchecklist1")
#     if request.method == "POST":
#         print("POST DATA:", request.POST)
#         print("FILES:", request.FILES)

#         # ==============================================================
#         # 1) SIGNUP TABLE → RvsfRegistration
#         # ==============================================================

#         signup = RvsfRegistration.objects.get(id=userid)

#         update_if_present(signup, "company_name", request.POST, "company_name_signup")
#         # update_if_present(signup, "registered_address", request.POST, "address_signup")
#         update_if_present(signup, "registered_address", request.POST, "address_signup", clean_address=True)

#         update_if_present(signup, "company_email", request.POST, "company_email_signup")

#         # File (only update if uploaded)
#         file = get_file(request, "Undertaking_pdf")
#         if file:
#             signup.undertaking = file

#         signup.save()

#         # ==============================================================
#         # 2) GENERAL DOCUMENTS → GeneralDetails
#         # ==============================================================

#         general = GeneralDetails.objects.get(userid=userid)

#         for field, key in [
#             ("gst_pdf", "gst_pdf_signup"),
#             ("pan_pdf", "pan_pdf_signup"),
#             ("tin_pdf", "tin_pdf_signup"),
#             ("cin_pdf", "cin_pdf_signup"),
#             ("iec_pdf", "iec_pdf_signup"),
#         ]:
#             file = get_file(request, key)
#             if file:
#                 setattr(general, field, file)

#         general.save()

#         # ==============================================================
#         # 3) RVSF DETAILS → RvsfDetails
#         # ==============================================================

#         rvsf = RvsfDetails.objects.get(userid=userid)

#         text_fields = [
#             ("address", "address_rvsf"),
#             ("latitude", "latitude_rvsf"),
#             ("longitude", "longitude_rvsf"),
#             ("state", "state_rvsf"),
#             ("cto_number", "cto_number_rvsf"),
#             ("consent_validity", "consent_validity_rvsf"),
#             ("howm_validity", "howm_validity_rvsf"),
#             ("dic_validity", "dic_validity_rvsf"),
#             ("rvsf_reg_no", "rvsf_reg_no_rvsf"),
#             ("rvsf_validity", "rvsf_validity_rvsf"),
#         ]

#         for field, key in text_fields:
#             update_if_present(rvsf, field, request.POST, key)

#         file_fields = [
#             ("cto_pdf", "cto_pdf_rvsf"),
#             ("howm_pdf", "howm_pdf_rvsf"),
#             ("dic_pdf", "dic_pdf_rvsf"),
#             ("rvsf_pdf", "pdf_rvsf"),
#             ("process_flow_pdf", "process_flow_pdf_rvsf"),
#             ("material_balance_pdf", "material_balance_pdf_rvsf"),
#             ("annual_returns_pdf", "annual_returns_pdf_rvsf_0"),
#             ("annual_returns_pdf1", "annual_returns_pdf_rvsf_1"),
#         ]

#         for field, key in file_fields:
#             file = get_file(request, key)
#             if file:
#                 setattr(rvsf, field, file)

#         rvsf.save()

#         # ==============================================================
#         # 4) FACILITY DETAILS → RvsfFacility
#         # ==============================================================

#         facility = RvsfFacility.objects.get(user_id=userid)

#         for field, key in [
#             ("total_area", "total_area"),
#             ("shifts_per_day", "shifts_per_day"),
#             ("no_of_employees", "no_of_employees"),
#             ("sectioned_power", "sectioned_power"),
#         ]:
#             update_if_present(facility, field, request.POST, key)

#         file = get_file(request, "geo_video")
#         if file:
#             facility.geo_video = file

#         facility.save()

#         # ==============================================================
#         # 5) EQUIPMENT → EquipmentEntry
#         # ==============================================================

#         # EquipmentEntry.objects.filter(userid=userid).delete()

#         index = 1
#         while True:
#             eq_type = request.POST.get(f"equipment_{index}_type")
#             if not eq_type:
#                 break

#             EquipmentEntry.objects.create(
#                 quantity=request.POST.get(f"equipment_{index}_qty") or 0,
#                 geo_tagged_pdf=get_file(request, f"equipment_{index}_geo_tagged_pdf_existing"),
#                 submitted_at=timezone.now(),
#                 equipment_type=eq_type,
#                 userid=userid,
#                 equipment_id=index,
#                 capacity_equipment_perton=request.POST.get(f"equipment_{index}_capacity") or 0,
#                 operating_hours=request.POST.get(f"equipment_{index}_hours") or 0,
#                 power_rating=request.POST.get(f"equipment_{index}_power") or 0,
                
#             )

#             index += 1

#         # ==============================================================
#         # 6) PLANT CAPACITY + VEHICLE TYPES
#         # ==============================================================

#         capacity, created = PlantCapacity.objects.get_or_create(userid=userid)

#         for field, key in [
#             ("installed_vehicles", "installed_vehicle_total"),
#             ("installed_steel", "installed_steel_total"),
#             ("operating_vehicles1", "oper_veh_1"),
#             ("operating_vehicles2", "oper_veh_2"),
#             ("operating_vehicles3", "oper_veh_3"),
#             ("operating_steel1", "oper_steel_1"),
#             ("operating_steel2", "oper_steel_2"),
#             ("operating_steel3", "oper_steel_3"),
#             ("year1", "year_1"),
#             ("year2", "year_2"),
#             ("year3", "year_3"),
#         ]:
#             update_if_present(capacity, field, request.POST, key)

#         capacity.save()

#         # VehicleType.objects.filter(userid=userid).delete()
#         for v in request.POST.getlist("selected_vehicles"):
#             VehicleType.objects.create(userid=userid, vehicle_type=v)

#         # ==============================================================
#         # 7) POLLUTION DEVICES
#         # ==============================================================

#         # PollutionDevice.objects.filter(userid=userid).delete()

#         idx = 1
#         while True:
#             dev_type = request.POST.get(f"device_{idx}_type")
#             if not dev_type:
#                 break

#             PollutionDevice.objects.create(
#                 userid=userid,
#                 device_type=dev_type,
#                 name=request.POST.get(f"device_{idx}_name"),
#                 quantity=request.POST.get(f"device_{idx}_qty"),
#                 device_doc=get_file(request, f"device_{idx}_doc"),
#             )

#             idx += 1

#         # ==============================================================
#         # 8) WASTE RECYCLED
#         # ==============================================================

#         # WasteRecycled.objects.filter(userid=userid).delete()

#         w = 1
#         while True:
#             cat = request.POST.get(f"waste_{w}_category")
#             if not cat:
#                 break

#             WasteRecycled.objects.create(
#                 userid=userid,
#                 category=cat,
#                 qty_recovered=request.POST.get(f"waste_{w}_qty_recovered") or 0,
#                 qty_recycled=request.POST.get(f"waste_{w}_qty_recycled") or 0,
#                 recycler_name=request.POST.get(f"waste_{w}_recycler"),
#                 agreement_details=request.POST.get(f"waste_{w}_agreement_details"),
#                 agreement=get_file(request, f"waste_{w}_agreement"),
#             )
#             w += 1

#         return redirect("viewchecklist1")

def resubmit_application(request):
    userid = request.session.get("user_id")
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == "POST":
            print("POST DATA:", request.POST)
            print("FILES:", request.FILES)
            
            # ==============================================================
            # 1) SIGNUP TABLE → RvsfRegistration
            # ==============================================================
            try:
                signup = RvsfRegistration.objects.get(id=userid)
                
                update_if_present(signup, "company_name", request.POST, "company_name_signup")
                update_if_present(signup, "company_email", request.POST, "company_email_signup")
                update_if_present(signup, "registered_address", request.POST, "address_signup", clean_address=True)
                update_if_present(signup, "gst_no", request.POST, "gst_no")
                update_if_present(signup, "company_pan", request.POST, "pan_no")
                update_if_present(signup, "tin_no", request.POST, "tin_no")
                update_if_present(signup, "cin", request.POST, "cin_no")
                update_if_present(signup, "iec", request.POST, "iec_no")
                

                # Handle address
                # address = request.POST.get("address_signup")
                # if address:
                #     signup.registered_address = address
                
                # Handle undertaking file
                undertaking_file = get_file(request, "Undertaking_pdf")
                if undertaking_file:
                    signup.undertaking = undertaking_file
                
                signup.save()
            except RvsfRegistration.DoesNotExist:
                print("Signup record not found for user:", userid)
            
            # ==============================================================
            # 2) GENERAL DOCUMENTS → GeneralDetails
            # ==============================================================
            try:
                general = GeneralDetails.objects.get(userid=userid)
                
                # Update GST, PAN, TIN, CIN, IEC numbers
                
                # Update files
                file_fields = [
                    ("gst_pdf", "gst_pdf_signup"),
                    ("pan_pdf", "pan_pdf_signup"),
                    ("tin_pdf", "tin_pdf_signup"),
                    ("cin_pdf", "cin_pdf_signup"),
                    ("iec_pdf", "iec_pdf_signup"),
                ]
                
                for field, key in file_fields:
                    file = get_file(request, key)
                    if file:
                        setattr(general, field, file)
                
                general.save()
            except GeneralDetails.DoesNotExist:
                print("GeneralDetails record not found for user:", userid)
            
            # ==============================================================
            # 3) RVSF DETAILS → RvsfDetails
            # ==============================================================
            try:
                rvsf = RvsfDetails.objects.get(userid=userid)
                
                text_fields = [
                    ("address", "address_rvsf"),
                    ("latitude", "latitude_rvsf"),
                    ("longitude", "longitude_rvsf"),
                    ("state", "state_rvsf"),
                    ("cto_number", "cto_number_rvsf"),
                    ("consent_validity", "consent_validity_rvsf"),
                    ("howm_validity", "howm_validity_rvsf"),
                    ("dic_validity", "dic_validity_rvsf"),
                    ("rvsf_reg_no", "rvsf_reg_no_rvsf"),
                    ("rvsf_validity", "rvsf_validity_rvsf"),
                ]
                
                for field, key in text_fields:
                    value = request.POST.get(key)
                    if value is not None:
                        setattr(rvsf, field, value)
                
                file_fields = [
                    ("cto_pdf", "cto_pdf_rvsf"),
                    ("howm_pdf", "howm_pdf_rvsf"),
                    ("dic_pdf", "dic_pdf_rvsf"),
                    ("rvsf_pdf", "pdf_rvsf"),
                    ("process_flow_pdf", "process_flow_pdf_rvsf"),
                    ("material_balance_pdf", "material_balance_pdf_rvsf"),
                    ("annual_returns_pdf", "annual_returns_pdf_rvsf_0"),
                    ("annual_returns_pdf1", "annual_returns_pdf_rvsf_1"),
                ]
                
                for field, key in file_fields:
                    file = get_file(request, key)
                    if file:
                        setattr(rvsf, field, file)
                
                rvsf.save()
            except RvsfDetails.DoesNotExist:
                print("RvsfDetails record not found for user:", userid)
            
            # ==============================================================
            # 4) FACILITY DETAILS → RvsfFacility
            # ==============================================================
            try:
                facility = RvsfFacility.objects.get(user_id=userid)
                
                facility_fields = [
                    ("total_area", "total_area"),
                    ("shifts_per_day", "shifts_per_day"),
                    ("no_of_employees", "no_of_employees"),
                    ("sectioned_power", "sectioned_power"),
                ]
                
                for field, key in facility_fields:
                    value = request.POST.get(key)
                    if value is not None:
                        setattr(facility, field, value)
                
                file = get_file(request, "geo_video")
                if file:
                    facility.geo_video = file
                
                facility.save()
            except RvsfFacility.DoesNotExist:
                print("RvsfFacility record not found for user:", userid)
            
            # ==============================================================
            # 5) EQUIPMENT → EquipmentEntry (UPDATE EXISTING)
            # ==============================================================
            try:
                existing_equipment = EquipmentEntry.objects.filter(userid=userid)
                
                for equipment in existing_equipment:
                    # Use equipment_id from the model
                    eq_id = equipment.equipment_id
                    
                    # Get values from POST data
                    qty = request.POST.get(f"equipment_{eq_id}_qty")
                    power = request.POST.get(f"equipment_{eq_id}_power")
                    hours = request.POST.get(f"equipment_{eq_id}_hours")
                    capacity = request.POST.get(f"equipment_{eq_id}_capacity")
                    eq_type = request.POST.get(f"equipment_{eq_id}_type")
                    
                    # Update fields if present
                    if qty is not None:
                        equipment.quantity = qty
                    if power is not None:
                        equipment.power_rating = power
                    if hours is not None:
                        equipment.operating_hours = hours
                    if capacity is not None:
                        equipment.capacity_equipment_perton = capacity
                    if eq_type is not None:
                        equipment.equipment_type = eq_type
                    
                    # Handle file upload
                    file_key = f"equipment_{eq_id}_geo_tagged_pdf"
                    file = get_file(request, file_key)
                    if file:
                        equipment.geo_tagged_pdf = file
                    
                    equipment.save()
            except Exception as e:
                print(f"Error updating equipment: {e}")
            
            # ==============================================================
            # 6) PLANT CAPACITY + VEHICLE TYPES
            # ==============================================================
            try:
                capacity, created = PlantCapacity.objects.get_or_create(userid=userid)
                
                # These should match your form field names from capacity section
                capacity_fields = [
                    ("installed_vehicles", "installed_vehicles"),
                    ("installed_steel", "installed_steel"),
                    ("operating_vehicles1", "operating_vehicles1"),
                    ("operating_vehicles2", "operating_vehicles2"),
                    ("operating_vehicles3", "operating_vehicles3"),
                    ("operating_steel1", "operating_steel1"),
                    ("operating_steel2", "operating_steel2"),
                    ("operating_steel3", "operating_steel3"),
                    ("year1", "year1"),
                    ("year2", "year2"),
                    ("year3", "year3"),
                ]
                
                for field, key in capacity_fields:
                    value = request.POST.get(key)
                    if value is not None:
                        setattr(capacity, field, value)
                
                capacity.save()
                
                # Handle vehicle types
                selected_vehicles = request.POST.get("selected_vehicles")
                if selected_vehicles:
                    # Clear existing and add new
                    VehicleType.objects.filter(userid=userid).delete()
                    # Assuming selected_vehicles is a comma-separated string
                    vehicles_list = selected_vehicles.split(',')
                    for vehicle in vehicles_list:
                        if vehicle.strip():
                            VehicleType.objects.create(
                                userid=userid, 
                                vehicle_type=vehicle.strip()
                            )
            except Exception as e:
                print(f"Error updating capacity: {e}")
            
            # ==============================================================
            # 7) POLLUTION DEVICES (UPDATE EXISTING)
            # ==============================================================
            try:
                existing_devices = PollutionDevice.objects.filter(userid=userid)
                
                for device in existing_devices:
                    # Use database ID since PollutionDevice doesn't have device_id field
                    device_id = device.id
                    
                    # Get values from POST data
                    device_type = request.POST.get(f"device_{device_id}_type")
                    name = request.POST.get(f"device_{device_id}_name")
                    qty = request.POST.get(f"device_{device_id}_qty")
                    
                    if device_type is not None:
                        device.device_type = device_type
                    if name is not None:
                        device.name = name
                    if qty is not None:
                        device.quantity = qty
                    
                    # Handle file upload
                    file = get_file(request, f"device_{device_id}_doc")
                    if file:
                        device.device_doc = file
                    
                    device.save()
            except Exception as e:
                print(f"Error updating devices: {e}")
            
            # ==============================================================
            # 8) WASTE RECYCLED (UPDATE EXISTING)
            # ==============================================================
            try:
                existing_wastes = WasteRecycled.objects.filter(userid=userid)
                
                for waste in existing_wastes:
                    # Use database ID since WasteRecycled doesn't have waste_id field
                    waste_id = waste.id
                    
                    # Get values from POST data
                    category = request.POST.get(f"waste_{waste_id}_category")
                    qty_recovered = request.POST.get(f"waste_{waste_id}_qty_recovered")
                    qty_recycled = request.POST.get(f"waste_{waste_id}_qty_recycled")
                    recycler = request.POST.get(f"waste_{waste_id}_recycler")
                    
                    if category is not None:
                        waste.category = category
                    if qty_recovered is not None:
                        waste.qty_recovered = qty_recovered
                    if qty_recycled is not None:
                        waste.qty_recycled = qty_recycled
                    if recycler is not None:
                        waste.recycler_name = recycler
                    
                    # Handle file upload
                    file = get_file(request, f"waste_{waste_id}_agreement")
                    if file:
                        waste.agreement = file
                    
                    waste.save()
            except Exception as e:
                print(f"Error updating waste: {e}")
            
            # ==============================================================
            # 9) UPDATE INDUSTRY COMMENT
            # ==============================================================
            # industry_comment = request.POST.get("industry_comment")
            # industryid = request.POST.get("industryid")
            Response = ConfirmApplication.objects.filter(userid = userid).first()
            industryRemark = request.POST.get('industry_comment')
            Response.IndustryRemark = industryRemark
            Response.incomplete = 0
            Response.response = 1
            Response.save()
            
            userinfo = RvsfRegistration.objects.get(id=userid)
            ApplicationTrail.objects.create(
                    AppNo=Response.appno,
                    stateid=Response.state_id,
                    marked_to_designation='recommending',
                    marked_by_designation=userinfo.username+'user',
                    marked_to_role=2,
                    marked_by_role=0,
                    comment=industryRemark,
                    added_by_userid=0,
                    added_by_person=userinfo.username+'user',
                    added_to_person='recommending',
                    added_to_userid=Response.marked_to_id,
                    industry_user_id=userid
                )
            # if industry_comment and industryid:
            #     try:
            #         # Assuming you have a model to store comments
            #         # Or update the checklist status
            #         checklist = Checklist.objects.filter(industryid=industryid).first()
            #         if checklist:
            #             checklist.industry_comment = industry_comment
            #             checklist.save()
            #     except Exception as e:
            #         print(f"Error updating industry comment: {e}")
            
            return redirect('TrackApplication')
        
        return redirect('TrackApplication')
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving resubmit_application")
                krishan_logger.error(f"Exact resubmit_application  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact resubmit_application Error: {str(db_error)}")


# -------------------------------------------------------------------
# MAIN CHECKLIST SAVE
# -------------------------------------------------------------------
@login_required
def viewchecklist1(request):
    userid = request.session.get("user_id")
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == "POST":
            print("POST DATA:", request.POST)
            print("FILES:", request.FILES)

        industryid = request.POST.get('industryid')
        
        print(industryid)
        AppNo = request.POST.get('appno')
        
        commentgiven = UntTrails.objects.filter(industryid = industryid)
        editone = UntTrails.objects.filter(industryid = industryid , EditMode = 1).first()
        edittwo = UntTrails.objects.filter(industryid = industryid , EditMode = 2).first()
        editthree = UntTrails.objects.filter(industryid = industryid , EditMode = 3).first()
        editfour = UntTrails.objects.filter(industryid = industryid , EditMode = 4).first()
        editfive = UntTrails.objects.filter(industryid = industryid , EditMode = 5).first()
        editSix = UntTrails.objects.filter(industryid = industryid , EditMode = 6).first()
        fectchsignup = SignupChecklist.objects.filter(industryid = industryid).first()
        fetchgeneral = GeneralChecklist.objects.filter(Industryid = industryid).first()
        fetchequipment = EquipmentChecklist.objects.filter(industryid = industryid).first()
        fetchfacility = FacilityChecklist.objects.filter(industryid = industryid).first()
        fetchcapacity = CapacityChecklist.objects.filter(industryid = industryid).first()
        fetchpollution = PollutionChecklist.objects.filter(industryid = industryid).first()
        fetchwasterec = WasteRecycleChecklist.objects.filter(industryid = industryid).first()
        fetchpayment = PaymentChecklist.objects.filter(industryid = industryid).first()
        print(fetchgeneral)

        data = RvsfRegistration.objects.filter(id=userid).first()
        generaldata = GeneralDetails.objects.filter(userid=userid).first()
        generaldata1 = RvsfDetails.objects.filter(userid=userid).first()
        

        statename = State.objects.filter(state_id=data.state).first() if data else None
        districtname = District.objects.filter(city_id=data.district).first() if data else None
        states = State.objects.all()
        equipmentdata = EquipmentType.objects.all().order_by('id')
        data1 = EquipmentEntry.objects.filter(userid = userid)
        facilitydata = RvsfFacility.objects.filter(user_id = userid).first()
        vehicleTypeData = VehicleType.objects.filter(userid=userid)
        capacitydata = PlantCapacity.objects.filter(userid=userid).first()
        capacitycount = PlantCapacity.objects.filter(userid=userid).count()
        curryear = datetime.now().year
        year1 = curryear-3
        year2 = curryear-2
        year3 = curryear-1
        devicedata = PollutionDevice.objects.filter(userid=userid).order_by('-created_at')
        wastedata = WasteRecycled.objects.filter(userid = userid).order_by('-created_at')
        payment = Payment.objects.filter(owner_id=userid, status='success').aggregate(total=Sum('amount_initiated'))['total'] or 0
        print(payment)
        file_url = '/media/RVSFDocs/undertaking/Undertaking1.pdf'
        applicationstatus = ConfirmApplication.objects.filter(userid=userid).first()
        # if applicationstatus:
        #     print(applicationstatus.incompleteRemark)


        context = {
        'Vehicledata': vehicleTypeData,
        'capacitydata': capacitydata,
        'cpacitycount': capacitycount,
        'year1' : year1,
        'year2' : year2,
        'year3' : year3
        }
        current_year = datetime.now().year
    # Generate dynamic FY values
        current_year = datetime.now().year
    # Create list of last 3 financial years
        fy_list = []
        for i in reversed(range(3)):
            year = current_year - i
            fy_list.append(f"FY:{year-1}-{year}")

        

        return render(request,'user/viewchecklist_new.html', {
            'comment': commentgiven,
            'financial_years': fy_list,
            'signup': fectchsignup,
            'general2': fetchgeneral,
            'equipments': fetchequipment,
            'facility1': fetchfacility,
            'capacity': fetchcapacity,
            'pollution': fetchpollution,
            'wasterec': fetchwasterec,
            'fetchpayment': fetchpayment,
                'edit1' : editone,
                'edit2' : edittwo,
                'edit3' : editthree,
                'edit4' : editfour,
                'edit5' : editfive,
                'edit6' : editSix,
            #  'equipment' : '',
                'states': states,
            'statename': statename,
            'districtname': districtname,
            'general': generaldata,
            'general1': generaldata1,
            'data1': data,
            'sidebar_userid': userid,
            'equipment': equipmentdata ,
                'data':data1 , 
                'facility':facilitydata,
                'Vehicledata': vehicleTypeData,
            'capacitydata': capacitydata,
            'cpacitycount': capacitycount,
            'year1' : year1,
            'year2' : year2,
            'year3' : year3,
            'devices': devicedata ,
            'wastes':wastedata,
        'file_url': file_url,
        'payment':payment,
        'applicationstatus':applicationstatus,
        
            
        })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving viewchecklist1")
                krishan_logger.error(f"Exact viewchecklist1  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact viewchecklist1 Error: {str(db_error)}")


@login_required        
def editGeneralDetails(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            print(industryid)
            checkvalidity = UntTrails.objects.filter(industryid = industryid , EditMode = 1).count()
            print(checkvalidity)
        # if checkvalidity > 0:
        data = RvsfRegistration.objects.filter(id= industryid).first()
        generaldata = GeneralDetails.objects.filter(userid= industryid).first()

        statename = State.objects.filter(state_id=data.state).first()
        districtname = District.objects.filter(city_id=data.district).first()

        return render(request, 'edit/editGeneralDetails.html', {
        'statename': statename,
        'districtname': districtname,
        'general': generaldata
            })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving edit general details")
                krishan_logger.error(f"Exact edit general details  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact edit general details Error: {str(db_error)}")
                
@login_required        
def AddGeneralDetails(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == 'POST':
            address = request.POST.get('address')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            state = request.POST.get('state')
            userid = request.session.get('user_id')

            cto_number = request.POST.get('cto_number')
            consent_validity = request.POST.get('consent_validity')
            cto_pdf = request.FILES.get('cto_pdf')

            howm_validity = request.POST.get('howm_validity')
            howm_pdf = request.FILES.get('howm_pdf')

            dic_validity = request.POST.get('dic_validity')
            dic_pdf = request.FILES.get('dic_pdf')

            rvsf_reg_no = request.POST.get('rvsf_reg_no')
            rvsf_validity = request.POST.get('rvsf_validity')
            rvsf_pdf = request.FILES.get('rvsf_pdf')

            process_flow_pdf = request.FILES.get('process_flow_pdf')
            material_balance_pdf = request.FILES.get('material_balance_pdf')
            annual_returns_pdf = request.FILES.get('annual_returns_pdf')

            # Validate PDF files
            pdf_files = {
                'CTO PDF': cto_pdf,
                'HOWM PDF': howm_pdf,
                'DIC PDF': dic_pdf,
                'RVSF PDF': rvsf_pdf,
                'Process Flow PDF': process_flow_pdf,
                'Material Balance PDF': material_balance_pdf,
                'Annual Returns PDF': annual_returns_pdf,
            }

            for label, file in pdf_files.items():
                if file and not file.name.lower().endswith('.pdf'):
                    messages.error(request, f"{label} must be a PDF.")
                    return redirect('generaldetails')

            # Check if record exists
            general = GeneralDetails.objects.filter(userid=userid).first()

            if general:
                # Update existing record
                general.address = address
                general.latitude = latitude
                general.longitude = longitude
                general.state = state

                general.cto_number = cto_number
                general.consent_validity = consent_validity
                if cto_pdf:
                    general.cto_pdf = cto_pdf

                general.howm_validity = howm_validity
                if howm_pdf:
                    general.howm_pdf = howm_pdf

                general.dic_validity = dic_validity
                if dic_pdf:
                    general.dic_pdf = dic_pdf

                general.rvsf_reg_no = rvsf_reg_no
                general.rvsf_validity = rvsf_validity
                if rvsf_pdf:
                    general.rvsf_pdf = rvsf_pdf

                if process_flow_pdf:
                    general.process_flow_pdf = process_flow_pdf

                if material_balance_pdf:
                    general.material_balance_pdf = material_balance_pdf

                if annual_returns_pdf:
                    general.annual_returns_pdf = annual_returns_pdf

                general.save()
                messages.success(request, "General details updated successfully.")
            else:
                # Create new record
                GeneralDetails.objects.create(
                    address=address,
                    latitude=latitude,
                    longitude=longitude,
                    state=state,
                    cto_number=cto_number,
                    consent_validity=consent_validity,
                    cto_pdf=cto_pdf,
                    howm_validity=howm_validity,
                    howm_pdf=howm_pdf,
                    dic_validity=dic_validity,
                    dic_pdf=dic_pdf,
                    rvsf_reg_no=rvsf_reg_no,
                    rvsf_validity=rvsf_validity,
                    rvsf_pdf=rvsf_pdf,
                    process_flow_pdf=process_flow_pdf,
                    material_balance_pdf=material_balance_pdf,
                    annual_returns_pdf=annual_returns_pdf,
                    userid=userid
                )
                messages.success(request, "General details saved successfully.")
            
            return redirect('TrackApplication')
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving add general details")
                krishan_logger.error(f"Exact add general details  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact add general details Error: {str(db_error)}")
        
        
       
@login_required    
@login_required    
def editEquipmentDetails(request):
    userid = request.session.get('user_id')
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == 'POST':
            # Check which form was submitted
            if 'equipment_name' in request.POST:
                # Handle equipment form
                equipment_id = request.POST.get('equipment_name')
                if equipment_id == '7':  # Assuming 7 is "Other"
                    equipment_type = request.POST.get('other_equipment')
                else:
                    getname = EquipmentType.objects.filter(id=equipment_id).first()
                    equipment_type = getname.name if getname else ""
                
                equipment_count = request.POST.get('equipment_count')
                geo_pdf = request.FILES.get('geo_pdf')
                
                EquipmentEntry.objects.create(
                    equipment_type=equipment_type,
                    equipment_id=equipment_id,
                    quantity=equipment_count,
                    geo_tagged_pdf=geo_pdf,
                    userid=userid 
                )
                messages.success(request, "Equipment details saved successfully.")
                return redirect('editEquipmentDetails')
                
            elif 'total_area' in request.POST:
                # Handle facility form
                geo_video = request.FILES.get('geo_video')
                total_area = request.POST.get('total_area')
                shifts = request.POST.get('shifts_per_day')
                employees = request.POST.get('no_of_employees')
                sectioned_power = request.POST.get('sectioned_power')
                storage_parking_area = request.POST.get('storage_parking_area')
                storage_depolluted_fluids = request.POST.get('storage_depolluted_fluids')
                storage_hazardous_waste = request.POST.get('storage_hazardous_waste')
                storage_processed_scrap = request.POST.get('storage_processed_scrap')
                storage_segregated_spares = request.POST.get('storage_segregated_spares')
                storage_others = request.POST.get('storage_others')
                storage_others_description = request.POST.get('storage_others_description')

                # Check if RVSF facility already exists for the user
                try:
                    facility = RvsfFacility.objects.get(user_id=userid)
                    # Update the existing facility
                    if geo_video:  # Only update if new video is provided
                        facility.geo_video = geo_video
                    facility.total_area = total_area
                    facility.shifts_per_day = shifts
                    facility.no_of_employees = employees
                    facility.sectioned_power = sectioned_power
                    facility.storage_parking_area = storage_parking_area
                    facility.storage_depolluted_fluids = storage_depolluted_fluids
                    facility.storage_hazardous_waste = storage_hazardous_waste
                    facility.storage_processed_scrap = storage_processed_scrap
                    facility.storage_segregated_spares = storage_segregated_spares
                    facility.storage_others = storage_others
                    facility.storage_others_description = storage_others_description
                    facility.save()
                    messages.success(request, "Facility details updated successfully!")
                except RvsfFacility.DoesNotExist:
                    # Create a new facility if not exists
                    RvsfFacility.objects.create(
                        user_id=userid,
                        geo_video=geo_video,
                        total_area=total_area,
                        shifts_per_day=shifts,
                        no_of_employees=employees,
                        sectioned_power=sectioned_power,
                        storage_parking_area=storage_parking_area,
                        storage_depolluted_fluids=storage_depolluted_fluids,
                        storage_hazardous_waste=storage_hazardous_waste,
                        storage_processed_scrap=storage_processed_scrap,
                        storage_segregated_spares=storage_segregated_spares,
                        storage_others=storage_others,
                        storage_others_description=storage_others_description
                    )
                    messages.success(request, "Facility details saved successfully!")
                
                return redirect('editEquipmentDetails')
        
        # GET request - show the form
        checkvalidity = UntTrails.objects.filter(
            (Q(industryid=userid) & Q(EditMode=2)) | Q(EditMode=3)
        ).count()
        
        equipmentdata = EquipmentType.objects.all().order_by('id') 
        data = EquipmentEntry.objects.filter(userid=userid)
        facilitydata = RvsfFacility.objects.filter(user_id=userid).first()
        
        return render(request, 'edit/editEquipmentDetails.html', {
            'equipment': equipmentdata,
            'data': data,
            'facility': facilitydata
        })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving edit equipment details")
                krishan_logger.error(f"Exact edit equipment details  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact edit equipment details Error: {str(db_error)}")        

@login_required        
def AddEquipmentDetails(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == 'POST':
            equipment_id = request.POST.get('equipment_name')
            print('cgasjcbgasjc')
            print(equipment_id)
            if equipment_id == '7':
                equipment_type = request.POST.get('other_equipment')
                print(equipment_type)
            else:
                getname = EquipmentType.objects.filter(id = equipment_id).first()
                equipment_type = getname.name
            
            equipment_count = request.POST.get('equipment_count')
            geo_pdf = request.FILES.get('geo_pdf')
            userid = request.session.get('user_id')
            EquipmentEntry.objects.create(
                equipment_type = equipment_type,
                equipment_id = equipment_id,
                quantity = equipment_count,
                geo_tagged_pdf = geo_pdf,
                userid = userid 
            )
            messages.success(request, "Equipment details saved successfully.")
            
            return redirect('editEquipmentDetails')
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving add equipment detail")
                krishan_logger.error(f"Exact add equipment detail  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact add equipment detail Error: {str(db_error)}")
    
    
@login_required
def AddRvsfFacility(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        if request.method == 'POST':
            print(request.POST,'123456789')
            geo_video = request.FILES.get('geo_video')
            total_area = request.POST.get('total_area')
            shifts = request.POST.get('shifts_per_day')
            employees = request.POST.get('no_of_employees')
            sectioned_power = request.POST.get('sectioned_power')
            storage_parking_area = request.POST.get('storage_parking_area')
            storage_depolluted_fluids = request.POST.get('storage_depolluted_fluids')
            storage_hazardous_waste = request.POST.get('storage_hazardous_waste')
            storage_processed_scrap = request.POST.get('storage_processed_scrap')
            storage_segregated_spares = request.POST.get('storage_segregated_spares')
            storage_others = request.POST.get('storage_others')
            storage_others_description = request.POST.get('storage_others_description')
            
            userid = request.session.get('user_id')

        if not userid:
            messages.error(request, "User session not found. Please log in.")
            return redirect('login')

        # Check if RVSF facility already exists for the user
        try:
            facility = RvsfFacility.objects.get(user_id=userid)
            # Update the existing facility
            facility.geo_video = geo_video if geo_video else facility.geo_video
            facility.total_area = total_area
            facility.shifts_per_day = shifts
            facility.no_of_employees = employees
            facility.sectioned_power = sectioned_power
            facility.storage_parking_area = storage_parking_area
            facility.storage_depolluted_fluids = storage_depolluted_fluids
            facility.storage_hazardous_waste = storage_hazardous_waste
            facility.storage_processed_scrap = storage_processed_scrap
            facility.storage_segregated_spares = storage_segregated_spares
            facility.storage_others = storage_others
            facility.storage_others_description = storage_others_description
            # facility.save()
        except RvsfFacility.DoesNotExist:
            # Create a new facility if not exists
            RvsfFacility.objects.create(
                user_id=userid,
                geo_video=geo_video,
                total_area=total_area,
                shifts_per_day=shifts,
                no_of_employees=employees,
                sectioned_power=sectioned_power,
                storage_parking_area=storage_parking_area,
                storage_depolluted_fluids=storage_depolluted_fluids,
                storage_hazardous_waste=storage_hazardous_waste,
                storage_processed_scrap=storage_processed_scrap,
                storage_segregated_spares=storage_segregated_spares,
                storage_others=storage_others,
                storage_others_description=storage_others_description
            )
        return redirect('editEquipmentDetails')
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving add rvsf facility")
                krishan_logger.error(f"Exact add rvsf facility  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact add rvsf facility Error: {str(db_error)}")


# def AddRvsfFacility(request):
#     if request.method == 'POST':
#         print(request.POST,'123456789')
#         geo_video = request.FILES.get('geo_video')
#         total_area = request.POST.get('total_area')
#         shifts = request.POST.get('shifts_per_day')
#         employees = request.POST.get('no_of_employees')
#         userid = request.session.get('user_id')


#     if not userid:
#         messages.error(request, "User session not found. Please log in.")
#         return redirect('login')

#     # Check if RVSF facility already exists for the user
#     try:
#         facility = RvsfFacility.objects.get(user_id=userid)
#         # Update the existing facility
#         facility.geo_video = geo_video if geo_video else facility.geo_video
#         facility.total_area = total_area
#         facility.shifts_per_day = shifts
#         facility.no_of_employees = employees
#         facility.save()
#     except RvsfFacility.DoesNotExist:
#         # Create a new facility if not exists
#         RvsfFacility.objects.create(
#             user_id=userid,
#             geo_video=geo_video,
#             total_area=total_area,
#             shifts_per_day=shifts,
#             no_of_employees=employees
#         )
#     return redirect('editEquipmentDetails')

    

@login_required
def editPollutionDetail(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        userid = request.session.get('user_id')     
        checkvalidity = UntTrails.objects.filter((Q(industryid=userid) & Q(EditMode=4)) | Q(EditMode=5)).count()
        print(checkvalidity)
        if checkvalidity > 0:
                devicedata = PollutionDevice.objects.filter(userid=userid).order_by('-created_at')
                wastedata = WasteRecycled.objects.filter(userid = userid).order_by('-created_at')
                print(devicedata)    
        return render(request, 'edit/editPollutionDetails.html', {'devices': devicedata , 'wastes':wastedata})
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving edit pollution")
                krishan_logger.error(f"Exact edit pollution  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact edit pollution Error: {str(db_error)}")


@login_required
def viewRvsfCapacity(request):
    userid = request.session.get('user_id')

    krishan_logger = logging.getLogger('elv_logger')
    try:
        today = datetime.today()
        current_year = today.year if today.month >= 4 else today.year - 1

        # Generate last 3 financial years: e.g. ['2024–25', '2023–24', '2022–23']
        financial_years = [f"{fy}-{str(fy + 1)[-2:]}" for fy in range(current_year - 2, current_year + 1)]
        vehicleTypeData = VehicleType.objects.filter(userid=userid)
        capacitydata = PlantCapacity.objects.filter(userid=userid).first()
        capacitycount = PlantCapacity.objects.filter(userid=userid).count()
        curryear = datetime.now().year
        year1 = curryear-3
        year2 = curryear-2
        year3 = curryear-1

        
        context = {
        'Vehicledata': vehicleTypeData,
        'capacitydata': capacitydata,
        'cpacitycount': capacitycount,
        'year1' : year1,
        'year2' : year2,
        'year3' : year3
        }
        return render(request, 'edit/editCapacityDetails.html' , context)
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving view rvsf capcity")
                krishan_logger.error(f"Exact view rvsf capcity  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact view rvsf capcity Error: {str(db_error)}")

@login_required
def AddResponse(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        industryid = request.POST.get('industryid')
        if request.method == 'POST':
            editmode = request.POST.get('editmode')
            industry_response  = request.POST.get('industry_response')
            response = UntTrails.objects.filter(industryid = industryid , EditMode = editmode).first()
            response.UnitComments = industry_response
            response.UnitCommentDate = datetime.now()
            response.save()
        return redirect('TrackApplication')
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving add response")
                krishan_logger.error(f"Exact add response  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact add response Error: {str(db_error)}")

@login_required
def AddFinalResponse(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        userid = request.session.get('user_id')
        if request.method == 'POST':
            
            Response = ConfirmApplication.objects.filter(userid = userid).first()
            industryRemark = request.POST.get('industry_comment')
            Response.IndustryRemark = industryRemark
            Response.incomplete = 0
            Response.response = 1
            Response.save()
            
            ApplicationTrail.objects.create(
                    AppNo=Response.appno,
                    stateid=Response.state_id,
                    marked_to_designation='recommending',
                    marked_by_designation='user',
                    marked_to_role=2,
                    marked_by_role=0,
                    comment=industryRemark,
                    added_by_userid=0,
                    added_by_person='user',
                    added_to_person='recommending',
                    added_to_userid=Response.marked_to_id,
                    industry_user_id=userid
                )
        return redirect('TrackApplication')
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving add final response")
                krishan_logger.error(f"Exact add final response  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact add final response Error: {str(db_error)}")
        
@login_required
def submittedapplication(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        userid = request.session.get('user_id')
        entity = RvsfRegistration.objects.filter(id = userid).first()
        # generaldata = GeneralDetails.objects.filter(userid=userid).first()
        generaldata = RvsfDetails.objects.filter(userid=userid).first()
        statename = State.objects.filter(state_id=entity.state).first()
        districtname = District.objects.filter(city_id=entity.district).first()
        
        equipmentdata = EquipmentType.objects.all().order_by('id')
        data = EquipmentEntry.objects.filter(userid = userid)
        facilitydata = RvsfFacility.objects.filter(user_id = userid).first()
        vehicleTypeData = VehicleType.objects.filter(userid=userid)
        capacityPlant = PlantCapacity.objects.filter(userid =  userid).first()
        pollutiondetails = PollutionDevice.objects.filter(userid = userid)
        wasterecycled = WasteRecycled.objects.filter(userid = userid)
    
        

        return render(request,'user/submittedapplication.html', {'entity' : entity ,
        'general' : generaldata , 'statename': statename, 'districtname':districtname,
        'equipmentdata': equipmentdata, 'data':data, 'facilitydata': facilitydata,
        'VechileType': vehicleTypeData, 'capacitydata':capacityPlant,'pollutiondetails':pollutiondetails,'wasterecycled':wasterecycled                                          
        })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving submit application")
                krishan_logger.error(f"Exact submit application  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact submit application Error: {str(db_error)}")


import time
from django.core.cache import cache

def is_rate_limited(key, max_attempts, block_minutes):
    """
    Returns True if too many attempts were made within block_minutes.
    Uses Django cache (Redis in your case).
    """
    data = cache.get(key)

    if data:
        attempts, first_attempt_time = data
        elapsed_minutes = (time.time() - first_attempt_time) / 60

        if elapsed_minutes < block_minutes:
            # Still in blocked time window
            if attempts >= max_attempts:
                return True
            else:
                # Increment attempt count
                cache.set(key, (attempts + 1, first_attempt_time), block_minutes * 60)
        else:
            # Time window expired → reset counter
            cache.set(key, (1, time.time()), block_minutes * 60)

    else:
        # First attempt
        cache.set(key, (1, time.time()), block_minutes * 60)

    return False

def sendforgetpwdemail_forgotpwd(username, company_email):
    # Disable SSL warnings for development (not recommended for production)
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    user = RvsfRegistration.objects.filter(username=username, company_email=company_email).first()

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
            send_sms_forgot_password(user.auth_mobile,user.username,user.password)
            response = sg.send(message)
            user.save()
            print(f"Email sent successfully. Status Code: {response.status_code}")
            return True, "New password has been sent to your registered Company email.", username

        except Exception as e:
            print(f"Error sending email: {e}")
            return False, f"Error sending email: {e}", username  # Return 3 values here too
        
    else:
        return False, "Invalid Username or Email.", username  # Return 3 values here too

def forgetpassword(request):
    form = CaptchaForm()
    return render(request , 'forgot_password/forget_password.html', {'form': form})
    
def resetpassword(request):
    print('yha bhi')
    """Handle password reset requests with full validation and rate limiting."""
    form = CaptchaForm(request.POST or None)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        company_email = request.POST.get('company_email', '').strip()
        user_ip = get_client_ip(request)

        # === 1️⃣ Validate inputs ===
        if not username or not company_email:
            messages.error(request, "Both username and company email are required.")
            return render(request, 'forgot_password/forget_password.html', {'form': form})

        # === 2️⃣ Validate CAPTCHA ===
        if not form.is_valid():
            messages.error(request, "Invalid CAPTCHA. Please try again.")
            return render(request, 'forgot_password/forget_password.html', {'form': CaptchaForm()})

        # === 3️⃣ Rate Limiting ===
        rate_key_user_rvsf = f"reset_attempts_user_{username}_rvsf"
        rate_key_ip_rvsf = f"reset_attempts_ip_{user_ip}_rvsf"

        max_attempts_rvsf = 3
        block_time_rvsf = 10  # in minutes

        if is_rate_limited(rate_key_user_rvsf, max_attempts_rvsf, block_time_rvsf) or \
           is_rate_limited(rate_key_ip_rvsf, max_attempts_rvsf, block_time_rvsf):
            messages.error(request, "Too many attempts. Please try again later.")
            return render(request, 'forgot_password/forget_password.html', {'form': CaptchaForm()})

        # === 4️⃣ Verify username and email ===
        user = RvsfRegistration.objects.filter(username=username, company_email=company_email).first()
        if not user:
            messages.error(request, "Invalid username or email address.")
            return render(request, 'forgot_password/forget_password.html', {'form': CaptchaForm()})

        # === 5️⃣ Send password reset email ===
        # success, msg, _ = sendforgetpwdemail_forgotpwd(username, company_email)  # Use underscore to ignore third value
        success, msg = sendForgetPwdEmail(username, company_email)
        if success:
            messages.success(request, msg)
            return redirect('rvsf_home')
        else:
            messages.error(request, msg)
            return render(request, 'forgot_password/forget_password.html', {'form': CaptchaForm()})

    # GET → show form
    return render(request, 'forgot_password/forget_password.html', {'form': form})

# def resetpassword(request):
#     if request.method == 'POST':
#         email = request.POST.get('auth_email')
#         sendforgetpwdemail(email)
#         messages.success(request, "Updated Credentials Sent on Your email id")
#         return redirect('rvsf_home')
     
    
    
# --------------------------------------------------- Payment Section ----------------------------------------------------

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


# def initiate_rvsf_payment(request):
#     user_id = request.session.get('user_id')
#     print(user_id,'fsnm')
    
#     registration_fee = 0

#     # quantity = int(float(request.POST.get("quatity_installed_fees")))
#     # print("dsfds")
#     # print(quantity)# get raw input
#     value = request.POST.get("quatity_installed_fees")
#     # value = request.POST.get("quatity_installed_fees")
#     request.session['quatity_installed_fees'] = value

#     # validate and convert
#     if value and value.strip():  # not None or empty
#         try:
#             quantity = int(float(value))
#         except ValueError:
#             # If input is not a valid number, handle gracefully
#             return JsonResponse({"error": "Invalid quantity value"}, status=400)
#     else:
#         return JsonResponse({"error": "Quantity is required"}, status=400)
    
#     fee_record = RVSFRegistrationFee.objects.filter(
#         models.Q(min_turnover__lte=quantity) | models.Q(min_turnover__isnull=True)
        
#     ).filter(
#         models.Q(max_turnover__gte=quantity) | models.Q(max_turnover__isnull=True)
#     ).first()

#     # print(fee_record)
#     if fee_record:
#         registration_fee = fee_record.registration_fee
    
#     # print(registration_fee)
    
    
#     if request.method == 'POST':
#         order_id = uuid.uuid4().hex[:20]
#         amount = registration_fee
#         # amount = registration_fee
        
#         redirect_url = request.build_absolute_uri('/rvsf/payment/status/')

#         # india_time = datetime.now(timezone('Asia/Kolkata')).replace(microsecond=0)
#         india_time = datetime.now(ZoneInfo("Asia/Kolkata")).replace(microsecond=0)
#         order_date = india_time.isoformat()

#         # Final Order Payload
#         payload = {
#             "mercid": settings.BILLDESK_MERCHANT_ID,
#             "orderid": order_id,
#             "amount": amount,
#             "order_date": order_date,
#             "currency": "356",
#             "ru": redirect_url,
#             "itemcode": "DIRECT",
#             "device": {
#                 "init_channel": "internet",
#                 "ip": get_client_ip(request),
#                 "user_agent": request.META.get('HTTP_USER_AGENT', 'DjangoTestAgent')
#             },
#             "additional_info": {
#                 "additional_info1": "NA",
#                 "additional_info2": "NA",
#                 "additional_info3": "NA",
#                 "additional_info4": "NA"
#             }
#         }
        
#         # HTTP Headers for the request
#         trace_id = uuid.uuid4().hex[:32]
#         timestamp = str(int(time.time()))

#         # JWS Header (for signing)
#         jws_header = {
#             "alg": "HS256",
#             "clientid": settings.BILLDESK_CLIENT_ID,
#         }


#         http_headers = {
#             "Content-Type": "application/jose",
#             "Accept": "application/jose",
#             "BD-Traceid": trace_id,
#             "BD-Timestamp": timestamp,
#             "ClientId": settings.BILLDESK_CLIENT_ID,
#         }


#         # Sign the payload to get a JWS compact token
#         jws_token = jwt.encode(
#             claims=payload,
#             key=settings.BILLDESK_KEY_ID,
#             algorithm="HS256",
#             headers=jws_header
#         )
        
#         # print("Headers:", http_headers)
#         # print("Payload:", payload)
#         # print("JWS Token:", jws_token)

#         try:
#             response = requests.post(
#                 settings.BILLDESK_API_ENDPOINT,
#                 headers=http_headers,  
#                 data=jws_token           
#             )
#             # print("Response",  response.text)

#             if response.status_code != 200:
#                 return HttpResponse(f"BillDesk error: {response.text}", status=500)

#             # Decode JWS Response from BillDesk
#             decoded = jwt.decode(
#                 token=response.text,
#                 key=settings.BILLDESK_KEY_ID,
#                 algorithms=["HS256"]
#             )
            
#             # print("Decoded : ",decoded)

#             redirect_link = None
#             for link in decoded.get('links', []):
#                 if link.get('rel') == 'redirect':
#                     redirect_link = link
#                     break

#             if not redirect_link:
#                 return HttpResponse(f"Redirect link not found in BillDesk response. Full response: {decoded}", status=500)

#             redirect_url = redirect_link.get('href')
#             parameters = redirect_link.get('parameters', {})
            

#             authorization_token = redirect_link.get('headers', {}).get('authorization')
            
#             print("Redirect URL:", redirect_url)
#             # print("Parameters:", parameters)
#             # print("Authorization:", authorization_token)
            
#             Payment.objects.create(
#                 owner_id=user_id,
#                 order_id=order_id,
#                 amount_initiated=amount,
#                 status='initiated'
#             )


#             # return render(request, 'auth/redirect_to_billdesk.html', {
#             #     'redirect_url': redirect_url,
#             #     'parameters': parameters,
#             #     'authorization': authorization_token
#             # })
            
#             return render(request, 'payment/redirect_to_billdesk.html', {
#                 'bd_order_id': decoded.get('bdorderid'),
#                 'auth_token': redirect_link['headers'].get('authorization'),
#                 'merchant_id': settings.BILLDESK_MERCHANT_ID,
#                 'return_url': redirect_url
#             })

#         except Exception as e:
#             return HttpResponse("Error during BillDesk communication: " + str(e), status=500)

#     return redirect('rvsf_dashboard')


# @csrf_exempt
# def paymentResponse(request):
#     print('sfsjh')
#     value = request.session.get('value')
#     print(value,'nhi aayi')
#     if request.method != 'POST':
#         return HttpResponse("Invalid method", status=405)

#     # End Code for Code Application
#     encoded_response = request.POST.get('transaction_response')
#     if not encoded_response:
#         return HttpResponse("No response received", status=400)

#     try:
#         decoded_data = jwt.decode(
#             token=encoded_response,
#             key=settings.BILLDESK_KEY_ID,
#             algorithms=["HS256"]
#         )
#         print(decoded_data)

#         order_id = decoded_data.get("orderid")
#         txn_id = decoded_data.get("transactionid")
#         status = decoded_data.get("transaction_error_type", "").lower()
#         amount = decoded_data.get("amount", "0.00")
#         ru_time = decoded_data.get("transaction_date")

#         if not order_id:
#             return HttpResponse("Missing order ID in payment response.", status=400)

#         # ✅ Instead of using session, fetch Payment entry
#         transaction = Payment.objects.filter(order_id=order_id).first()
#         if not transaction:
#             return HttpResponse("No transaction found for this order ID", status=404)

#         user_id = transaction.owner_id
#         user = RvsfRegistration.objects.filter(id=user_id).first()
#         if not user:
#             return HttpResponse("User not found for this transaction", status=404)

#         email = user.auth_email

#         # update/create payment record
#         Payment.objects.update_or_create(
#             order_id=order_id,
#             defaults={
#                 "owner_id": user_id,
#                 "txn_id": txn_id,
#                 "email": email,
#                 "amount_initiated": int(float(amount)),
#                 "was_success": status == "success",
#                 "status": status,
#                 "log": json.dumps(decoded_data, indent=2),
#                 "ru_date": ru_time,
#                 "txn_date": dj_timezone.now(),
#             }
#         )

#         # fetch state safely
#         fetchstateid = State.objects.filter(state_id=user.state).first()
#         stateid = fetchstateid.state_id if fetchstateid else None
#         statename = fetchstateid.state_name if fetchstateid else None
#         # stateuser=StateUsers.objects.filter(State_id=stateid and RoleAcess=2).first()
#         stateuser = StateUsers.objects.filter(State_id=stateid,RoleAccess=2,DisableStatus=0).first()

#         if status == "success":
#             # confirm application if needed
#             ConfirmApplication.objects.update_or_create(
#                 userid=user_id,
#                 defaults={
#                     "appno": generate_application_number(),
#                     "paymentModeStatus": "Completed" if status == "success" else "Failed",
#                     "transactionNo": str(order_id) + str(user_id),
#                     "paymentstatus":'1',
#                     # "registrationfees": calculate_registration_fees(int(float(amount))),
#                     "registrationfees": int(float(amount)),
#                     "state_id": stateid,
#                     "statename": statename,
#                     "role_id": 2,
#                     "marked_to_id": stateuser.id if stateuser else None
#                 }
#             )

#             return render(request, 'payment/payment_receipt.html', {
#                 'status': status,
#                 'order_id': order_id,
#                 'transaction_id': txn_id,
#                 'transaction_date': ru_time,
#                 "amount": amount,
#             })
#         else:
#             messages.error(request, "Payment failed! Please try again.")
#             return redirect('rvsf_dashboard')

#     except JWTError as e:
#         return HttpResponse("JWT decoding failed: " + str(e), status=400)
#     except Exception as e:
#         return HttpResponse("Unexpected error: " + str(e), status=500)

def calculate_fee_based_on_capacity(capacity):
    """Calculate fee based on capacity ranges"""
    capacity = float(capacity) if capacity else 0
    
    if capacity < 6000:
        return 25000
    elif 6000 <= capacity < 15000:
        return 50000
    elif 15000 <= capacity < 30000:
        return 75000
    elif capacity >= 30000:
        return 100000
    return 0

# def payment_section(request):
#     userid = request.session.get('user_id')
#     capacitydata = PlantCapacity.objects.filter(userid=userid).first()
#     rvsf_fees = RVSFRegistrationFee.objects.all()
#     generalcheck=GeneralDetails.objects.filter(userid=user_id,status='general').exist()
#     rvsfcheck=RvsfDetails.objects.filter(userid=user_id,status='rvsf').exist()
#     equipmentcheck=EquipmentEntry.objects.filter(userid=user_id,status='equipment').exist()
#     capcacitycheck=PlantCapacity.objects.filter(userid=user_id,status='capacity').exist()
#     pollutioncheck=PollutionDevice.objects.filter(userid=user_id,status='pollution').exist()
#     declarationcheck=RvsfRegistration.objects.filter(id=user_id,status='declaration').exist()
#     declarationcheck=WasteRecycled.objects.filter(id=user_id,status='waste').exist()
#     # Calculate current required fee based on capacity
#     current_capacity = capacitydata.installed_vehicles if capacitydata else 0
#     calculated_amount = calculate_fee_based_on_capacity(current_capacity)

#     # Get latest successful payment
#     latest_payment = Payment.objects.filter(
#         owner_id=userid, 
#         status='success'
#     ).order_by('txn_date').first()

#     # Calculate total successful payments
#     total_successful_payments = Payment.objects.filter(
#         owner_id=userid, 
#         status='success'
#     ).aggregate(total_amount=Sum('amount_initiated'))['total_amount'] or 0

#     payment_status = {
#         'has_successful_payment': latest_payment is not None,
#         'requires_additional_payment': calculated_amount > total_successful_payments,
#         'additional_amount': max(calculated_amount - total_successful_payments, 0),
#         'calculated_amount': calculated_amount,
#         'paid_amount': latest_payment.amount_initiated if latest_payment else 0,
#         'total_paid_amount': total_successful_payments
#     }

#     return render(request, 'user/paymentsection.html', {
#         'capacitydata': capacitydata,
#         'rvsf_fees': rvsf_fees,
#         'payment_status': payment_status,
#         'paymentdetail': latest_payment
#     })
from django.db.models import Q
def payment_section(request):
    krishan_logger = logging.getLogger('elv_logger')
    try:
        userid = request.session.get('user_id')
        capacitydata = PlantCapacity.objects.filter(userid=userid).first()
        rvsf_fees = RVSFRegistrationFee.objects.all()
        declarationcheck = RvsfRegistration.objects.filter(id=userid, status='declaration').exists()
        # Redirect if equipment details don't exist
        # if not declarationcheck:
        #     messages.error(request, "Please complete Declaration details first!")
        #     return redirect('pollutiondetails')
        
        # Check if all required forms are filled
        generalcheck = GeneralDetails.objects.filter(userid=userid, status='general').exists()
        # rvsfcheck = RvsfDetails.objects.filter(userid=userid, status='rvsf').exists()
        rvsfcheck = RvsfDetails.objects.filter(
                                            userid=userid,
                                            status='rvsf'
                                        ).exclude(
                                            Q(unit_commencement_year__isnull=True) |
                                            Q(unit_commencement_year='')
                                        ).exists()

        equipmentcheck = EquipmentEntry.objects.filter(userid=userid, status='equipment').exists()
        capcacitycheck = PlantCapacity.objects.filter(userid=userid, status='capacity').exists()
        pollutioncheck = PollutionDevice.objects.filter(userid=userid, status='pollution').exists()
        declarationcheck = RvsfRegistration.objects.filter(id=userid, status='declaration').exists()
        wastecheck = WasteRecycled.objects.filter(userid=userid, status='waste').exists()
        
        # Check if all forms are filled
        all_forms_filled = all([
            generalcheck,
            rvsfcheck,
            equipmentcheck,
            capcacitycheck,
            pollutioncheck,
            declarationcheck,
            wastecheck
        ])

        # Calculate current required fee based on capacity
        current_capacity = capacitydata.installed_vehicles if capacitydata else 0
        calculated_amount = calculate_fee_based_on_capacity(current_capacity)

        # Get latest successful payment
        latest_payment = Payment.objects.filter(
            owner_id=userid, 
            status='success'
        ).order_by('txn_date').first()

        # Calculate total successful payments
        total_successful_payments = Payment.objects.filter(
            owner_id=userid, 
            status='success'
        ).aggregate(total_amount=Sum('amount_initiated'))['total_amount'] or 0

        payment_status = {
            'has_successful_payment': latest_payment is not None,
            'requires_additional_payment': calculated_amount > total_successful_payments,
            'additional_amount': max(calculated_amount - total_successful_payments, 0),
            'calculated_amount': calculated_amount,
            'paid_amount': latest_payment.amount_initiated if latest_payment else 0,
            'total_paid_amount': total_successful_payments
        }

        return render(request, 'user/paymentsection.html', {
            'capacitydata': capacitydata,
            'rvsf_fees': rvsf_fees,
            'payment_status': payment_status,
            'paymentdetail': latest_payment,
            # Form status variables
            'generalcheck': generalcheck,
            'rvsfcheck': rvsfcheck,
            'equipmentcheck': equipmentcheck,
            'capcacitycheck': capcacitycheck,
            'pollutioncheck': pollutioncheck,
            'declarationcheck': declarationcheck,
            'wastecheck': wastecheck,
            'all_forms_filled': all_forms_filled
        })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving payment_section")
                krishan_logger.error(f"Exact payment_section  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact payment_section Error: {str(db_error)}")

krishan_logger = logging.getLogger('elv_logger')
def initiate_rvsf_payment(request):
    try:
        krishan_logger.info(f"=== Starting initiate_rvsf_payment view for request {request.method} ===")
        
        user_id = request.session.get('user_id')

        
        print(user_id, 'fsnm')
        
        if request.method != 'POST':
            krishan_logger.warning(f"Non-POST request received: {request.method}")
            return redirect('rvsf_dashboard')

        # Check if this is an additional payment
        is_additional_payment = request.POST.get('is_additional_payment') == 'true'
        additional_amount = request.POST.get('additional_amount')
        
        krishan_logger.info(f"Payment initiation - User ID: {user_id}, Additional Payment: {is_additional_payment}")
        
        if is_additional_payment and additional_amount:
            # For additional payment, use the provided additional amount
            registration_fee = int(float(additional_amount))
            # Store payment type in log field temporarily
            payment_log_note = f"ADDITIONAL_PAYMENT: {additional_amount}"
            krishan_logger.info(f"Additional payment amount: {additional_amount}")
        else:
            # Original payment logic
            value = request.POST.get("quatity_installed_fees")
            
            # Validate and convert
            if value and value.strip():
                try:
                    quantity = int(float(value))
                    krishan_logger.info(f"Quantity installed: {quantity}")
                except ValueError:
                    krishan_logger.error(f"Invalid quantity value: {value}")
                    return JsonResponse({"error": "Invalid quantity value"}, status=400)
            else:
                krishan_logger.error("Quantity is required but not provided")
                return JsonResponse({"error": "Quantity is required"}, status=400)
            
            fee_record = RVSFRegistrationFee.objects.filter(
                Q(min_turnover__lte=quantity) | Q(min_turnover__isnull=True)
            ).filter(
                Q(max_turnover__gte=quantity) | Q(max_turnover__isnull=True)
            ).first()

            registration_fee = fee_record.registration_fee if fee_record else 0
            payment_log_note = "INITIAL_PAYMENT"
            krishan_logger.info(f"Registration fee determined: {registration_fee}")

        # Generate order ID and create payment record
        order_id = uuid.uuid4().hex[:20]
        amount = registration_fee
        
        krishan_logger.info(f"Creating payment record - Order ID: {order_id}, Amount: {amount}")
        
        # Create payment record WITHOUT the new fields
        payment_record = Payment.objects.create(
            owner_id=user_id,
            order_id=order_id,
            amount_initiated=amount,
            status='initiated',
            log=payment_log_note  # Using log field to store payment type temporarily
        )

        redirect_url = request.build_absolute_uri('/rvsf/payment/status/')
        india_time = datetime.now(ZoneInfo("Asia/Kolkata")).replace(microsecond=0)
        order_date = india_time.isoformat()

        # Final Order Payload
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
                "user_agent": request.META.get('HTTP_USER_AGENT', 'DjangoTestAgent')
            },
            "additional_info": {
                "additional_info1": "NA",
                "additional_info2": "NA",
                "additional_info3": "NA",
                "additional_info4": "NA"
            }
        }
        
        krishan_logger.info(f"BillDesk payload created for order: {order_id}")
        
        # HTTP Headers for the request
        trace_id = uuid.uuid4().hex[:32]
        timestamp = str(int(time.time()))

        # JWS Header (for signing)
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

        try:
            krishan_logger.info("Initiating BillDesk API call...")
            # Sign the payload to get a JWS compact token
            jws_token = jwt.encode(
                claims=payload,
                key=settings.BILLDESK_KEY_ID,
                algorithm="HS256",
                headers=jws_header
            )
            
            response = requests.post(
                settings.BILLDESK_API_ENDPOINT,
                headers=http_headers,  
                data=jws_token           
            )

            if response.status_code != 200:
                krishan_logger.error(f"BillDesk API error - Status: {response.status_code}, Response: {response.text}")
                # Update payment status to failed
                payment_record.status = 'failed'
                payment_record.log = f"BillDesk API error: {response.text}"
                payment_record.save()
                return HttpResponse(f"BillDesk error: {response.text}", status=500)

            krishan_logger.info(f"BillDesk API response received - Status: {response.status_code}")
            
            # Decode JWS Response from BillDesk
            decoded = jwt.decode(
                token=response.text,
                key=settings.BILLDESK_KEY_ID,
                algorithms=["HS256"]
            )
            
            redirect_link = None
            for link in decoded.get('links', []):
                if link.get('rel') == 'redirect':
                    redirect_link = link
                    break

            if not redirect_link:
                krishan_logger.error("Redirect link not found in BillDesk response")
                payment_record.status = 'failed'
                payment_record.log = "Redirect link not found in BillDesk response"
                payment_record.save()
                return HttpResponse(f"Redirect link not found in BillDesk response. Full response: {decoded}", status=500)

            redirect_url = redirect_link.get('href')
            krishan_logger.info(f"Redirect URL obtained: {redirect_url}")
            print(redirect_url,'sfgsdfbhdf')
            
            krishan_logger.info(f"Payment initiation successful for order: {order_id}")
            return render(request, 'payment/redirect_to_billdesk.html', {
                'bd_order_id': decoded.get('bdorderid'),
                'auth_token': redirect_link['headers'].get('authorization'),
                'merchant_id': settings.BILLDESK_MERCHANT_ID,
                'return_url': redirect_url
            })

        except Exception as e:
            krishan_logger.error(f"Exception during payment initiation: {str(e)}", exc_info=True)
            # Update payment record with error
            payment_record.status = 'failed'
            payment_record.log = f"Exception during payment initiation: {str(e)}"
            payment_record.save()
            return HttpResponse("Error during BillDesk communication: " + str(e), status=500)
        
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving initiate rvsf payment")
                krishan_logger.error(f"Exact initiate rvsf payment  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact initiate rvsf payment Error: {str(db_error)}")

@csrf_exempt
def paymentResponse(request):
    try:
        krishan_logger.info(f"=== Starting paymentResponse view for request {request.method} ===")
        print('Payment response received')
        
        if request.method != 'POST':
            krishan_logger.warning(f"Non-POST request received: {request.method}")
            return HttpResponse("Invalid method", status=405)

        encoded_response = request.POST.get('transaction_response')
        if not encoded_response:
            krishan_logger.error("No transaction_response received in POST data")
            return HttpResponse("No response received", status=400)

        try:
            krishan_logger.info("Decoding JWT payment response...")
            decoded_data = jwt.decode(
                token=encoded_response,
                key=settings.BILLDESK_KEY_ID,
                algorithms=["HS256"]
            )
            krishan_logger.info(f"Decoded payment response - Order ID: {decoded_data.get('orderid')}")
            print("Decoded payment response:", decoded_data)

            order_id = decoded_data.get("orderid")
            txn_id = decoded_data.get("transactionid")
            status = decoded_data.get("transaction_error_type", "").lower()
            amount = decoded_data.get("amount", "0.00")
            ru_time = decoded_data.get("transaction_date")

            if not order_id:
                krishan_logger.error("Missing order ID in payment response")
                return HttpResponse("Missing order ID in payment response.", status=400)

            # Fetch payment record
            payment_record = Payment.objects.filter(order_id=order_id).first()
            if not payment_record:
                krishan_logger.error(f"No payment record found for order ID: {order_id}")
                return HttpResponse("No transaction found for this order ID", status=404)

            user_id = payment_record.owner_id
            user = RvsfRegistration.objects.filter(id=user_id).first()
            if not user:
                krishan_logger.error(f"No user found for ID: {user_id}")
                return HttpResponse("User not found for this transaction", status=404)

            email = user.auth_email

            # Check if this is an additional payment by reading the log field
            is_additional_payment = payment_record.log and "ADDITIONAL_PAYMENT" in payment_record.log
            krishan_logger.info(f"Payment details - User: {user_id}, Status: {status}, Amount: {amount}, Additional: {is_additional_payment}")

            # Update payment record with final status
            payment_record.txn_id = txn_id
            payment_record.email = email
            payment_record.amount_initiated = int(float(amount))
            payment_record.was_success = status == "success"
            payment_record.status = status
            payment_record.log = json.dumps(decoded_data, indent=2)
            payment_record.ru_date = ru_time
            payment_record.txn_date = dj_timezone.now()
            payment_record.save()
            
            krishan_logger.info(f"Payment record updated - Status: {status}, Txn ID: {txn_id}")

            # Fetch state safely
            fetchstateid = State.objects.filter(state_id=user.state).first()
            stateid = fetchstateid.state_id if fetchstateid else None
            statename = fetchstateid.state_name if fetchstateid else None
            stateuser = StateUsers.objects.filter(State_id=stateid, RoleAccess=2, DisableStatus=0).first()

            if status == "success":
                krishan_logger.info(f"Payment successful for order: {order_id}")
                if is_additional_payment:
                    # For additional payment, update the existing application with new total
                    confirm_app = ConfirmApplication.objects.filter(userid=user_id).first()
                    if confirm_app:
                        # Calculate total registration fees (existing + additional)
                        total_fees = confirm_app.registrationfees + int(float(amount))
                        confirm_app.registrationfees = total_fees
                        confirm_app.save()
                        krishan_logger.info(f"Additional payment processed - Existing: {confirm_app.registrationfees - int(float(amount))}, Additional: {amount}, Total: {total_fees}")
                        messages.success(request, f"Additional payment of ₹{amount} successful! Total paid: ₹{total_fees}")
                    else:
                        krishan_logger.error(f"No application found for user {user_id} for additional payment")
                        messages.error(request, "Application not found for additional payment")
                else:
                    # Original logic for initial payment
                    app_no = generate_application_number()
                    krishan_logger.info(f"Creating application record - App No: {app_no}")
                    ConfirmApplication.objects.update_or_create(
                        userid=user_id,
                        defaults={
                            "appno": app_no,
                            "paymentModeStatus": "Completed",
                            "transactionNo": f"{order_id}{user_id}",
                            "paymentstatus": '1',
                            "registrationfees": int(float(amount)),
                            "state_id": stateid,
                            "statename": statename,
                            "role_id": 2,
                            # "marked_to_id": stateuser.id if stateuser else None
                            "marked_to_id": 0
                        }
                    )
                    krishan_logger.info(f"Application record created/updated for user: {user_id}")

                krishan_logger.info(f"Rendering payment receipt for order: {order_id}")
                return render(request, 'payment/payment_receipt.html', {
                    'status': status,
                    'order_id': order_id,
                    'transaction_id': txn_id,
                    'transaction_date': ru_time,
                    "amount": amount,
                    'is_additional_payment': is_additional_payment,
                })
            else:
                krishan_logger.warning(f"Payment failed for order: {order_id}, Status: {status}")
                messages.error(request, "Payment failed! Please try again.")
                return redirect('rvsf_dashboard')

        except JWTError as e:
            krishan_logger.error(f"JWT decoding failed: {str(e)}", exc_info=True)
            return HttpResponse("JWT decoding failed: " + str(e), status=400)
        except Exception as e:
            krishan_logger.error(f"Unexpected error in paymentResponse: {str(e)}", exc_info=True)
            return HttpResponse("Unexpected error: " + str(e), status=500)
        
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving payment response")
                krishan_logger.error(f"Exact payment response  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact payment response Error: {str(db_error)}")

def paymentreciept(request):
    try:
        krishan_logger.info(f"=== Starting paymentreciept view for request {request.method} ===")
        
        userid = request.session.get('user_id')
        if not userid:
            krishan_logger.warning("User not logged in, redirecting to login")
            # Handle case where user is not logged in
            return redirect('login')  # Adjust to your login URL
        
        krishan_logger.info(f"User ID: {userid}")
        
        # Get all successful payments for this user
        data = Payment.objects.filter(owner_id=userid, status='success')
        payment_list = list(data.values())
        
        # Calculate total amount from all successful payments
        total_amount = data.aggregate(total=Sum('amount_initiated'))['total'] or 0
        
        # Get the latest payment for transaction details
        latest_payment = data.order_by('-txn_date').first()
        
        # Get payee details
        payee_detail = RvsfRegistration.objects.filter(id=userid).first()
        
        # Initialize address variables
        payee_address = ""
        districtname = ""
        statename = ""
        
        if payee_detail:
            krishan_logger.info(f"Processing payee details for user: {userid}")
            # Get district and state names safely
            if payee_detail.district:
                district_obj = District.objects.filter(city_id=payee_detail.district).first()
                districtname = district_obj.city_name if district_obj else ""
            if payee_detail.state:
                state_obj = State.objects.filter(state_id=payee_detail.state).first()
                statename = state_obj.state_name if state_obj else ""
            
            # Build address string from non-empty components
            address_parts = []
            if payee_detail.registered_address:
                address_parts.append(payee_detail.registered_address)
            if districtname:
                address_parts.append(districtname)
            if statename:
                address_parts.append(statename)
            if payee_detail.pin_code:
                address_parts.append(str(payee_detail.pin_code))
            payee_address = ", ".join(address_parts)
            
            krishan_logger.info(f"Payee address constructed: {payee_address}")
        
        krishan_logger.info(f"Rendering receipt - Total payments: {len(payment_list)}, Total amount: {total_amount}")
        
        return render(request, 'payment/view_receipt.html', {
            'payment_list': payment_list,
            'total_amount': total_amount,
            'latest_payment': latest_payment,
            'payee_detail': payee_detail,
            'payee_address': payee_address,  # Fixed variable name
            # 'districtname': districtname,    # Added these to template
            # 'statename': statename,          # for individual access if needed
        })
    except Exception as db_error:
                krishan_logger.exception("❌ ERROR while saving payment reciept")
                krishan_logger.error(f"Exact payment reciept  Error: {str(db_error)}")
                
                krishan_logger.info(f"Exact payment reciept Error: {str(db_error)}")
# def initiate_rvsf_payment(request):
#     user_id = request.session.get('user_id')

    
#     print(user_id, 'fsnm')
    
#     if request.method != 'POST':
#         return redirect('rvsf_dashboard')

#     # Check if this is an additional payment
#     is_additional_payment = request.POST.get('is_additional_payment') == 'true'
#     additional_amount = request.POST.get('additional_amount')
    
#     if is_additional_payment and additional_amount:
#         # For additional payment, use the provided additional amount
#         registration_fee = int(float(additional_amount))
#         # Store payment type in log field temporarily
#         payment_log_note = f"ADDITIONAL_PAYMENT: {additional_amount}"
#     else:
#         # Original payment logic
#         value = request.POST.get("quatity_installed_fees")
        
#         # Validate and convert
#         if value and value.strip():
#             try:
#                 quantity = int(float(value))
#             except ValueError:
#                 return JsonResponse({"error": "Invalid quantity value"}, status=400)
#         else:
#             return JsonResponse({"error": "Quantity is required"}, status=400)
        
#         fee_record = RVSFRegistrationFee.objects.filter(
#             Q(min_turnover__lte=quantity) | Q(min_turnover__isnull=True)
#         ).filter(
#             Q(max_turnover__gte=quantity) | Q(max_turnover__isnull=True)
#         ).first()

#         registration_fee = fee_record.registration_fee if fee_record else 0
#         payment_log_note = "INITIAL_PAYMENT"

#     # Generate order ID and create payment record
#     order_id = uuid.uuid4().hex[:20]
#     amount = registration_fee
    
#     # Create payment record WITHOUT the new fields
#     payment_record = Payment.objects.create(
#         owner_id=user_id,
#         order_id=order_id,
#         amount_initiated=amount,
#         status='initiated',
#         log=payment_log_note  # Using log field to store payment type temporarily
#     )

#     redirect_url = request.build_absolute_uri('/rvsf/payment/status/')
#     india_time = datetime.now(ZoneInfo("Asia/Kolkata")).replace(microsecond=0)
#     order_date = india_time.isoformat()

#     # Final Order Payload
#     payload = {
#         "mercid": settings.BILLDESK_MERCHANT_ID,
#         "orderid": order_id,
#         # "amount": amount,
#         "amount": 1,
#         "order_date": order_date,
#         "currency": "356",
#         "ru": redirect_url,
#         "itemcode": "DIRECT",
#         "device": {
#             "init_channel": "internet",
#             "ip": get_client_ip(request),
#             "user_agent": request.META.get('HTTP_USER_AGENT', 'DjangoTestAgent')
#         },
#         "additional_info": {
#             "additional_info1": "NA",
#             "additional_info2": "NA",
#             "additional_info3": "NA",
#             "additional_info4": "NA"
#         }
#     }
    
#     # HTTP Headers for the request
#     trace_id = uuid.uuid4().hex[:32]
#     timestamp = str(int(time.time()))

#     # JWS Header (for signing)
#     jws_header = {
#         "alg": "HS256",
#         "clientid": settings.BILLDESK_CLIENT_ID,
#     }

#     http_headers = {
#         "Content-Type": "application/jose",
#         "Accept": "application/jose",
#         "BD-Traceid": trace_id,
#         "BD-Timestamp": timestamp,
#         "ClientId": settings.BILLDESK_CLIENT_ID,
#     }

#     try:
#         # Sign the payload to get a JWS compact token
#         jws_token = jwt.encode(
#             claims=payload,
#             key=settings.BILLDESK_KEY_ID,
#             algorithm="HS256",
#             headers=jws_header
#         )
        
#         response = requests.post(
#             settings.BILLDESK_API_ENDPOINT,
#             headers=http_headers,  
#             data=jws_token           
#         )

#         if response.status_code != 200:
#             # Update payment status to failed
#             payment_record.status = 'failed'
#             payment_record.log = f"BillDesk API error: {response.text}"
#             payment_record.save()
#             return HttpResponse(f"BillDesk error: {response.text}", status=500)

#         # Decode JWS Response from BillDesk
#         decoded = jwt.decode(
#             token=response.text,
#             key=settings.BILLDESK_KEY_ID,
#             algorithms=["HS256"]
#         )
        
#         redirect_link = None
#         for link in decoded.get('links', []):
#             if link.get('rel') == 'redirect':
#                 redirect_link = link
#                 break

#         if not redirect_link:
#             payment_record.status = 'failed'
#             payment_record.log = "Redirect link not found in BillDesk response"
#             payment_record.save()
#             return HttpResponse(f"Redirect link not found in BillDesk response. Full response: {decoded}", status=500)

#         redirect_url = redirect_link.get('href')
#         print(redirect_url,'sfgsdfbhdf')
        
#         return render(request, 'payment/redirect_to_billdesk.html', {
#             'bd_order_id': decoded.get('bdorderid'),
#             'auth_token': redirect_link['headers'].get('authorization'),
#             'merchant_id': settings.BILLDESK_MERCHANT_ID,
#             'return_url': redirect_url
#         })

#     except Exception as e:
#         # Update payment record with error
#         payment_record.status = 'failed'
#         payment_record.log = f"Exception during payment initiation: {str(e)}"
#         payment_record.save()
#         return HttpResponse("Error during BillDesk communication: " + str(e), status=500)

# @csrf_exempt
# def paymentResponse(request):
#     print('Payment response received')
#     if request.method != 'POST':
#         return HttpResponse("Invalid method", status=405)

#     encoded_response = request.POST.get('transaction_response')
#     if not encoded_response:
#         return HttpResponse("No response received", status=400)

#     try:
#         decoded_data = jwt.decode(
#             token=encoded_response,
#             key=settings.BILLDESK_KEY_ID,
#             algorithms=["HS256"]
#         )
#         print("Decoded payment response:", decoded_data)

#         order_id = decoded_data.get("orderid")
#         txn_id = decoded_data.get("transactionid")
#         status = decoded_data.get("transaction_error_type", "").lower()
#         amount = decoded_data.get("amount", "0.00")
#         ru_time = decoded_data.get("transaction_date")

#         if not order_id:
#             return HttpResponse("Missing order ID in payment response.", status=400)

#         # Fetch payment record
#         payment_record = Payment.objects.filter(order_id=order_id).first()
#         if not payment_record:
#             return HttpResponse("No transaction found for this order ID", status=404)

#         user_id = payment_record.owner_id
#         user = RvsfRegistration.objects.filter(id=user_id).first()
#         if not user:
#             return HttpResponse("User not found for this transaction", status=404)

#         email = user.auth_email

#         # Check if this is an additional payment by reading the log field
#         is_additional_payment = payment_record.log and "ADDITIONAL_PAYMENT" in payment_record.log

#         # Update payment record with final status
#         payment_record.txn_id = txn_id
#         payment_record.email = email
#         payment_record.amount_initiated = int(float(amount))
#         payment_record.was_success = status == "success"
#         payment_record.status = status
#         payment_record.log = json.dumps(decoded_data, indent=2)
#         payment_record.ru_date = ru_time
#         payment_record.txn_date = dj_timezone.now()
#         payment_record.save()

#         # Fetch state safely
#         fetchstateid = State.objects.filter(state_id=user.state).first()
#         stateid = fetchstateid.state_id if fetchstateid else None
#         statename = fetchstateid.state_name if fetchstateid else None
#         stateuser = StateUsers.objects.filter(State_id=stateid, RoleAccess=2, DisableStatus=0).first()

#         if status == "success":
#             if is_additional_payment:
#                 # For additional payment, update the existing application with new total
#                 confirm_app = ConfirmApplication.objects.filter(userid=user_id).first()
#                 if confirm_app:
#                     # Calculate total registration fees (existing + additional)
#                     total_fees = confirm_app.registrationfees + int(float(amount))
#                     confirm_app.registrationfees = total_fees
#                     confirm_app.save()
                    
#                     messages.success(request, f"Additional payment of ₹{amount} successful! Total paid: ₹{total_fees}")
#                 else:
#                     messages.error(request, "Application not found for additional payment")
#             else:
#                 # Original logic for initial payment
#                 ConfirmApplication.objects.update_or_create(
#                     userid=user_id,
#                     defaults={
#                         "appno": generate_application_number(),
#                         "paymentModeStatus": "Completed",
#                         "transactionNo": f"{order_id}{user_id}",
#                         "paymentstatus": '1',
#                         "registrationfees": int(float(amount)),
#                         "state_id": stateid,
#                         "statename": statename,
#                         "role_id": 2,
#                         # "marked_to_id": stateuser.id if stateuser else None
#                         "marked_to_id": 20
#                     }
#                 )

#             return render(request, 'payment/payment_receipt.html', {
#                 'status': status,
#                 'order_id': order_id,
#                 'transaction_id': txn_id,
#                 'transaction_date': ru_time,
#                 "amount": amount,
#                 'is_additional_payment': is_additional_payment,
#             })
#         else:
#             messages.error(request, "Payment failed! Please try again.")
#             return redirect('rvsf_dashboard')

#     except JWTError as e:
#         return HttpResponse("JWT decoding failed: " + str(e), status=400)
#     except Exception as e:
#         return HttpResponse("Unexpected error: " + str(e), status=500)
# def paymentreciept(request):
#     userid = request.session.get('user_id')
#     print(userid)
#     data = Payment.objects.filter(owner_id=userid, status='success')
#     payment_list = list(data.values())

#     return render(request, 'payment/view_receipt.html', {
#         'payment_list': payment_list,
#         # 'order_id': order_id,
#         # 'transaction_id': txn_id,
#         # 'transaction_date': ru_time,
#         # "amount": amount,
#     })
# def paymentreciept(request):
#     userid = request.session.get('user_id')
#     if not userid:
#         # Handle case where user is not logged in
#         return redirect('login')  # Adjust to your login URL
    
#     print(f"User ID: {userid}")
    
#     # Get all successful payments for this user
#     data = Payment.objects.filter(owner_id=userid, status='success')
#     payment_list = list(data.values())
    
#     # Calculate total amount from all successful payments
#     total_amount = data.aggregate(total=Sum('amount_initiated'))['total'] or 0
    
#     # Get the latest payment for transaction details
#     latest_payment = data.order_by('-txn_date').first()
    
#     # Get payee details
#     payee_detail = RvsfRegistration.objects.filter(id=userid).first()
    
#     # Initialize address variables
#     payee_address = ""
#     districtname = ""
#     statename = ""
    
#     if payee_detail:
#         # Get district and state names safely
#         if payee_detail.district:
#             district_obj = District.objects.filter(city_id=payee_detail.district).first()
#             districtname = district_obj.city_name if district_obj else ""
#         if payee_detail.state:
#             state_obj = State.objects.filter(state_id=payee_detail.state).first()
#             statename = state_obj.state_name if state_obj else ""
        
#         # Build address string from non-empty components
#         address_parts = []
#         if payee_detail.registered_address:
#             address_parts.append(payee_detail.registered_address)
#         if districtname:
#             address_parts.append(districtname)
#         if statename:
#             address_parts.append(statename)
#         if payee_detail.pin_code:
#             address_parts.append(str(payee_detail.pin_code))
#         payee_address = ", ".join(address_parts)
#         # if payee_detail.registered_address:
#         #     address_parts.append(payee_detail.registered_address)
#         # if districtname:
#         #     address_parts.append(districtname)
#         # if statename:
#         #     address_parts.append(statename)
#         # if payee_detail.pin_code:
#         #     address_parts.append(str(payee_detail.pin_code))
        
#         # payee_address = ", ".join(filter(None, address_parts))
    
#     # Debug prints
#     # print(f"Total payments: {len(payment_list)}")
#     # print(f"Total amount: {total_amount}")
#     print(f"Payee address: {payee_address}")
    
#     return render(request, 'payment/view_receipt.html', {
#         'payment_list': payment_list,
#         'total_amount': total_amount,
#         'latest_payment': latest_payment,
#         'payee_detail': payee_detail,
#         'payee_address': payee_address,  # Fixed variable name
#         # 'districtname': districtname,    # Added these to template
#         # 'statename': statename,          # for individual access if needed
#     })
# def paymentreciept(request):
#     userid = request.session.get('user_id')
#     print(userid)
    
#     # Get all successful payments
#     data = Payment.objects.filter(owner_id=userid, status='success')
#     payment_list = list(data.values())
    
#     # Calculate total amount from all successful payments
#     total_amount = data.aggregate(total=Sum('amount_initiated'))['total'] or 0
    
#     # Get the latest payment for transaction details
#     latest_payment = data.order_by('-txn_date').first()
#     payee_detail = RvsfRegistration.objects.filter(id=userid).first()
#     districtname = District.objects.filter(city_id=payee_detail.district).first()
#     statename = State.objects.filter(state_id=payee_detail.state).first()
#     payee_addres=payee_detail['registered_address']+','+ statename + ',' + districtname + payee_detail.pin_code
    
#     return render(request, 'payment/view_receipt.html', {
#         'payment_list': payment_list,
#         'total_amount': total_amount,
#         'latest_payment': latest_payment,
#         'payee_detail':payee_detail,
#         'payee_addres':payee_addres,
#     })     
            

# @csrf_exempt
# def paymentResponse(request):
    
#     if request.method == 'POST':
#         # Code For Confirming Application
#         userid = request.session.get('user_id')
#         print(userid)
#         appno = generate_application_number()
#         regstate = RvsfRegistration.objects.filter(id= userid).first()
#         print(regstate)

#         fetchstateid  = State.objects.filter(state_id = regstate.state).first()
#         stateid = fetchstateid.state_id
#         statename = fetchstateid.state_name

#         # return HttpResponse(fetchstateid.state_id)
        


#     try:
#         quantity_installed = int(request.POST.get('quantity_installed'))
#     except (TypeError, ValueError):
#         # Invalid input — handle appropriately
#         # For example, return an error response or set a default
#         quantity_installed = 0
        

#         registration_fees = calculate_registration_fees(quantity_installed)        
#         paymentModeStatus = 'Initiated'
#         transactionNo = str(appno) + str(userid)
#         checkpayment = ConfirmApplication.objects.filter(userid = userid)
#         if checkpayment!= None:
#             ConfirmApplication.objects.create(
#                 userid = userid,
#                 appno = appno,
#                 paymentModeStatus = paymentModeStatus,
#                 transactionNo = transactionNo,
#                 registrationfees = registration_fees,
#                 state_id = stateid,
#                 statename = statename,
#                 role_id = 1

    
#             )



#         # End Code for Code Application
#         encoded_response = request.POST.get('transaction_response')
#         if not encoded_response:
#             return HttpResponse("No response received", status=400)

#         try:
#             decoded_data = jwt.decode(
#                 token=encoded_response,
#                 key=settings.BILLDESK_KEY_ID,
#                 algorithms=["HS256"]
#             )

#             order_id = decoded_data.get("orderid")
#             txn_id = decoded_data.get("transactionid")
#             status = decoded_data.get("transaction_error_type", "").lower()
#             amount = decoded_data.get("amount", "0.00")
#             ru_time = decoded_data.get("transaction_date")

#             if not order_id:
#                 return HttpResponse("Missing order ID in payment response.", status=400)

#             # Lookup existing transaction by order_id
#             transaction = Payment.objects.filter(order_id=order_id).first()
#             # user_id = transaction.owner_id if transaction else None
#             # email = ""
#             if transaction:
#                 user_id = transaction.owner_id
#                 user = RvsfRegistration.objects.filter(id=user_id).first()
#                 email = user.auth_email

#                 # Update or create transaction record (update existing)
#                 Payment.objects.update_or_create(
#                     order_id=order_id,
#                     defaults={
#                         "owner_id": user_id,
#                         "txn_id": txn_id,
#                         "email": email,
#                         "amount_initiated": int(float(amount)),
#                         "was_success": status == "success",
#                         "status": status,
#                         "log": json.dumps(decoded_data, indent=2),
#                         "ru_date": ru_time,
#                         "txn_date": dj_timezone.now(),
#                     }
#                 )
                

#                 return render(request, 'payment/payment_receipt.html', {
#                     'status': status,
#                     'order_id': order_id,
#                     'transaction_id': txn_id,
#                     'transaction_date': ru_time,
#                     "amount": amount,
#                 })

#         except JWTError as e:
#             return HttpResponse("JWT decoding failed: " + str(e), status=400)
#         except Exception as e:
#             return HttpResponse("Unexpected error: " + str(e), status=500)

#     return HttpResponse("Invalid method", status=405)
CONSENT_BASE_URL = getattr(settings, "CONSENT_BASE_URL", "https://apiservices.cpcb.gov.in/services/api/consent/details")
@csrf_exempt
@require_POST
def get_consent_details(request):
    print('Consent details API called')
    try:
        data = json.loads(request.body)
        print("Received data:", data)
        
        # Build payload exactly like Postman - consent_id as string, not int
        consent_id = str(data.get("consent_id", "")).strip()  # Convert to string
        statecode = data.get("statecode", "").strip()
        status = data.get("status", 0)
        
        if not consent_id or not statecode:
            return JsonResponse({'error': 'consent_id and statecode are required'}, status=400)
        
        payload = {
            "consent_id": consent_id,  # Keep as string like in Postman
            "statecode": statecode,
            "status": int(status),
        }
        
        gpcbid = data.get("gpcbid", "").strip()
        if gpcbid:
            payload["gpcbid"] = gpcbid
            
        print(f"Sending payload to consent API: {payload}")
        
        # Use exact same headers as Postman
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        
        # Make the request exactly like Postman
        resp = requests.post(
            CONSENT_BASE_URL,
            json=payload,  # This sends as JSON like Postman
            headers=headers,
            timeout=30,
            verify=False
        )
        
        print(f"External API response status: {resp.status_code}")
        print(f"External API response: {resp.text}")
        print(resp,'hfffhweiuhfwhefl')
        # If successful, return the data
        if resp.status_code == 200:
            response_data = resp.json()
            print(response_data,'gdgxfdhdfdfhdfh')
            return JsonResponse(response_data, safe=False)
        else:
            # Return the error from external API
            return JsonResponse({
                'error': 'External API error',
                'status_code': resp.status_code,
                'response': resp.text
            }, status=resp.status_code)
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")
        return JsonResponse({'error': 'External API error', 'details': str(e)}, status=502)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)

def logoutrvsf(request):
    request.session.flush()  # Clears all session data
    return redirect('home')

@csrf_exempt
@require_http_methods(["GET"])
def get_annual_report_data_api(request):
    
    rvsf_id = request.session.get("user_id")
    fy_year = request.GET.get('fy_year')
    annual_qtr = request.GET.get('annual_qtr')

    if not rvsf_id:
        return JsonResponse({'success': False, 'error': 'User not logged in'}, status=401)

    if not fy_year or not annual_qtr:
        return JsonResponse({'success': False, 'error': 'Missing parameters'}, status=400)

    try:
        from Transfer_Certificate.models import WasteProcessing, DenominationDetail
        from RvsfApp.models import VehicleScrapDetail

        start_dt, end_dt = get_fy_date_range(fy_year, annual_qtr)

        if not start_dt:
            return JsonResponse({'success': False, 'error': 'Invalid FY/QTR'}, status=400)
        from datetime import time
        start_date = datetime.combine(start_dt, time.min)   # 00:00:00
        end_date = datetime.combine(end_dt, time.max)       # 23:59:59.999999
        
        procurement_data = ProcurementData.objects.filter(rvsf_id=rvsf_id,
            procurement_date__range=(start_dt, end_dt),   
            vehicle_type__isnull=False
        ).exclude(
            vehicle_type=""
        ).values(
            'vehicle_type'
        ).annotate(
            elvs_received=Sum('number_of_elvs')
        )

        # ================= PRODUCTION DATA =================
        # ELVs SCRAPPED + WEIGHT + STEEL

        production_data = ProductionForm.objects.filter(
            rvsf_id=rvsf_id,
            scrapping_date__range=(start_dt, end_dt),  # DateTimeField
            elv_type__isnull=False
        ).exclude(
            elv_type=""
        ).values(
            'elv_type'
        ).annotate(
            elvs_scrapped=Sum('scrapped_qty'),   # ✅ FIXED (Sum instead of Count)
            total_weight=Sum('scrapped_weight'),
            steel_recovered=Sum('steel_scrap_recovered')
        )

        # ================= CONVERT TO MAP =================

        proc_map = {
            item['vehicle_type']: item['elvs_received'] or 0
            for item in procurement_data
        }

        prod_map = {
            item['elv_type']: {
                'elvs_scrapped': item['elvs_scrapped'] or 0,
                'total_weight': float(item['total_weight'] or 0),
                'steel_recovered': float(item['steel_recovered'] or 0)
            }
            for item in production_data
        }

        # ================= MERGE DATA =================

        all_vehicle_types = set(proc_map.keys()) | set(prod_map.keys())

        final_data = []

        for vt in all_vehicle_types:
            final_data.append({
                'vehicle_type': vt,
                'elvs_received': proc_map.get(vt, 0),
                'elvs_scrapped': prod_map.get(vt, {}).get('elvs_scrapped', 0),
                'total_weight': prod_map.get(vt, {}).get('total_weight', 0),
                'steel_scrap': prod_map.get(vt, {}).get('steel_recovered', 0)
            })
        # print('11111111111111111111111111111', final_data)
        # =========================
        # Waste Processing
        # =========================
        waste_qs = WasteProcessing.objects.filter(
            rvsf_id=rvsf_id,
            sale_date__range=(start_date, end_date),
            financial_year=fy_year
        )

        recycled_materials = []
        disposal_materials = []

        for w in waste_qs:
            data = {
                'waste_type': w.waste_type,
                'processed_qty': str(w.processed_qty),
                'buyer_name': w.buyer_name,
                'activity': w.activity,
                'gst_number': w.gst_number
            }

            if w.activity == 'disposal':
                disposal_materials.append(data)
            else:
                recycled_materials.append(data)
        print(recycled_materials,'1111')
        print(disposal_materials,'2222')
        # =========================
        # Vehicle Details
        # =========================
        # vehicle_details = list(
        #     VehicleScrapDetail.objects.filter(
        #         report__userid=rvsf_id,
        #         report__fy_year=fy_year,
        #         report__annual_qtr=annual_qtr
        #     ).values(
        #         'vehicle_type',
        #         'elvs_received',
        #         'elvs_scrapped',
        #         'total_weight',
        #         'steel_scrap'
        #     )
        # )
        vehicle_details = final_data
        # vehicle_details = [
        #                     {
        #                         'vehicle_type': final_data,
        #                         'elvs_received': 0,
        #                         'elvs_scrapped': 0,
        #                         'total_weight': 0,
        #                         'steel_scrap': 0
        #                     }                            
        #                 ]
        
        # =========================
        # Certificates - MODIFIED: Added value calculation
        # =========================
        
        # For generated certificates - get both count and total value
        generated_data = DenominationDetail.objects.filter(
            denomination_master__rvsf_id=rvsf_id,
            status='generated',
            denomination_master__financial_year=fy_year
        ).aggregate(
            count=Count('id'),
            total_value=Sum(F('denomination_kg') * F('quantity'))
        )
        
        countgenrated = generated_data['count'] or 0
        valuegenerated = generated_data['total_value'] or 0
        
        # For transferred certificates - get both count and total value
        transferred_data = DenominationDetail.objects.filter(
            denomination_master__rvsf_id=rvsf_id,
            status='transferred',
            denomination_master__financial_year=fy_year
        ).aggregate(
            count=Count('id'),
            total_value=Sum(F('denomination_kg') * F('quantity'))
        )
        
        counttransferred = transferred_data['count'] or 0
        valuetransferred = transferred_data['total_value'] or 0

        return JsonResponse({
            'success': True,
            'recycled_materials': recycled_materials,
            'disposal_materials': disposal_materials,
            'vehicle_details': vehicle_details,
            'countgenrated': countgenrated,
            'counttransferred': counttransferred,
            'valuegenerated': valuegenerated,      # ✅ NEW
            'valuetransferred': valuetransferred   # ✅ NEW
        })

    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

def ar_edit_rvsf(request):

    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")

    if not rvsf_id or user_role != "rvsf":
        messages.error(request, "Unauthorized access.")
        return redirect("rvsf_home")

    from RvsfApp.models import RvsfRegistration, PlantCapacity, VehicleScrapDetail, AnnualReport
    from Transfer_Certificate.models import WasteProcessing, DenominationDetail
    from django.db.models import Sum, F, Count
    # from masters.models import State, District

    rvsfinfo = RvsfRegistration.objects.filter(id=rvsf_id).first()
    capacityinfo = PlantCapacity.objects.filter(userid=rvsf_id).first()
    statename = State.objects.filter(state_id=rvsfinfo.state).first() if rvsfinfo else None
    districtname = District.objects.filter(city_id=rvsfinfo.district).first() if rvsfinfo else None

    fy_year = request.GET.get('fy_year')
    annual_qtr = request.GET.get('annual_qtr')

    waste_detail = []
    recycled_materials = []
    disposal_materials = []
    vehicle_details = []

    countgenrated = 0
    counttransferred = 0
    valuegenerated = 0      # ✅ NEW
    valuetransferred = 0    # ✅ NEW

    if fy_year and annual_qtr:

        start_date, end_date = get_fy_date_range(fy_year, annual_qtr)

        waste_detail = WasteProcessing.objects.filter(
            rvsf_id=rvsf_id,
            sale_date__range=(start_date, end_date),
            financial_year=fy_year
        )

        recycled_materials = [w for w in waste_detail if w.activity != 'disposal']
        disposal_materials = [w for w in waste_detail if w.activity == 'disposal']

        vehicle_details = VehicleScrapDetail.objects.filter(
            report__userid=rvsf_id,
            report__fy_year=fy_year,
            report__annual_qtr=annual_qtr
        )

        # For generated certificates - get both count and total value
        generated_data = DenominationDetail.objects.filter(
            denomination_master__rvsf_id=rvsf_id,
            status='generated',
            denomination_master__financial_year=fy_year
        ).aggregate(
            count=Count('id'),
            total_value=Sum(F('denomination_kg') * F('quantity'))
        )
        
        countgenrated = generated_data['count'] or 0
        valuegenerated = generated_data['total_value'] or 0
        
        # For transferred certificates - get both count and total value
        transferred_data = DenominationDetail.objects.filter(
            denomination_master__rvsf_id=rvsf_id,
            status='transferred',
            denomination_master__financial_year=fy_year
        ).aggregate(
            count=Count('id'),
            total_value=Sum(F('denomination_kg') * F('quantity'))
        )
        
        counttransferred = transferred_data['count'] or 0
        valuetransferred = transferred_data['total_value'] or 0
        
    from django.db.models import Sum, Q

    total_amount = Payment.objects.filter(
        owner_id=rvsf_id,
        was_success=1,
        status='success',
        log__isnull=False
    ).exclude(log='').aggregate(
        total=Sum('amount_initiated')
    )['total']
    # rvsf_fee=Payment.objects.filter(owner_id=rvsf_id,was_success=1,status=1,logs!=''or null)
    from datetime import date
    today = date.today()

    context = {
        "user_type": user_role,
        "user_info": rvsfinfo,
        "cap_info": capacityinfo,
        "state": statename,
        "district": districtname,
        "today": today,
        "countgenrated": countgenrated,
        "counttransferred": counttransferred,
        "valuegenerated": valuegenerated,        # ✅ NEW
        "valuetransferred": valuetransferred,    # ✅ NEW
        "recycled_materials": recycled_materials,
        "disposal_materials": disposal_materials,
        "vehicle_details": vehicle_details,
        'rvsf_fee':total_amount,
    }

    if request.method == "POST":

        report = AnnualReport.objects.create(
            userid=rvsf_id,
            fy_year=request.POST.get('fy_year'),
            annual_qtr=request.POST.get('annual_qtr'),
            fy_yr1=request.POST.get('fy_yr1'),
            annual_yr=request.POST.get('annual_yr'),
            num_epr_cert_gen=request.POST.get('num_epr_cert_gen'),
            num_epr_cert_exchange=request.POST.get('num_epr_cert_exchange'),
            decl_date=request.POST.get('decl_date'),
        )

        return redirect('rvsf_dashboard')

    return render(request, "user/annualreportedit.html", context)



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

def verify_otp_cert(request):
    userid = request.session.get('user_id')
    print("🔹 Entered verify_otp view")
    if request.method == 'POST':
        print("✅ Request method is POST")

        

        # ✅ Decrypt the OTP sent from client
        enc_otp = request.POST.get('enc_otp')
        print(enc_otp)
        print(f"🔒 Encrypted OTP received: {enc_otp}")

        try:
            entered_otp = decrypt_aes_cert(enc_otp)
            print(f"🔓 Decrypted OTP: {entered_otp}")
        except Exception as e:
            print(f"❌ OTP decryption failed: {e}")
            messages.error(request, "OTP decryption failed.")
            return  redirect('certificate_transfer_dashboard')

       
        # Step 2: Validate OTP
        user_number=RvsfRegistration.objects.filter(id=userid).first()
        print("🧩 Fetching stored OTP from cache...")
        stored_otp = cache.get(f"otp_{user_number.username}")
        print(enc_otp,stored_otp,'tops')
        print(f"📦 Stored OTP in cache: {stored_otp}")

        if stored_otp is None:
            print("⚠️ No OTP found or expired in cache")
            messages.error(request, 'OTP expired or not found. Please request a new one.')
            return  redirect('certificate_transfer_dashboard')

        if stored_otp != entered_otp:
            return JsonResponse({"status": "error", "message": "Invalid OTP"})

        cache.delete(f"otp_{user_number.username}")

        return JsonResponse({"status": "success"})


        # Step 3: OTP correct → proceed
        print("✅ OTP verified successfully. Deleting from cache...")
        cache.delete(f"otp_{user_number.username}")

        print("🔎 Fetching user record from database...")
                
        request.session['is_rvsf_logged_in'] = True
        print("🏠 Returning user — redirecting to dashboard")
        return redirect('certificate_transfer_dashboard')

    print("⚠️ Request method not POST — redirecting to home")
    return redirect('certificate_transfer_dashboard')

def send_sms_otp_for_transfer(request):
    if request.method == "POST":

        userid = request.session.get('user_id')
        user_number = RvsfRegistration.objects.filter(id=userid).first()

        otp =str(random.randint(100000, 999999))
        # otp = "123456"
        cache.set(f"otp_{user_number.username}", otp, timeout=120)
    # API credentials & configuration
    username = "CPCB_IT"
    password = "Smscpcb#2026"
    senderid = "CPCBEL"
    dept_secure_key = "106a9ed9-00c4-442d-a857-3447d308c9d9"
    templateid = "1307175188771815034"
    entity_id = "1301158798803147760"

    # OTP message
    message = (
        f"Dear User, Your OTP for Transfer Certificate ELV EPR Portal is {otp}. Please enter this code to complete the Transfer Certificate Verification. Do not share this OTP with anyone. Regards, CPCB."
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
        "mobileno": user_number.auth_mobile.strip(),
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

        return JsonResponse({"status": "success", "message": "OTP sent successfully"})

    except requests.RequestException as e:
        print("Failed to send OTP:", str(e))
        return JsonResponse({"status": "error"}, status=400)










def protected_cert_file(request, path):
    # Check for either admin or producer login
    # admin_id = request.session.get('admin_user_id')
    # rvsf_id = request.session.get('user_id')
    # user_role = request.session.get('user_role')
    # rvsf_id = 49
    rvsf_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    # user_role = 'rvsf'
    
    # if neither producer nor admin logged in
    if not rvsf_id:
        # Redirect based on role (default to producer login)
        if user_role == 'rvsf':
            return redirect('rvsf_home')  # use your producer login view name
        else:
            return redirect('custom_admin_login')

    # File access
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404("File not found")

    return FileResponse(open(file_path, 'rb'), as_attachment=False)



def get_current_financial_year():
    today = date.today()

    if today.month >= 4:
        return f"{today.year}-{today.year + 1}"
    else:
        return f"{today.year - 1}-{today.year}"
    

# def get_fy_from_date(date_obj):
#     if date_obj.month >= 4:  # April or later
#         return f"{date_obj.year}-{date_obj.year + 1}"
#     else:
#         return f"{date_obj.year - 1}-{date_obj.year}"

def get_fy_from_date(date_obj):
    """
    Accepts date / datetime object
    Returns FY in YYYY-YYYY format
    """
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%d-%m-%Y").date()

    if date_obj.month >= 4:  # April or later
        return f"{date_obj.year}-{date_obj.year + 1}"
    else:
        return f"{date_obj.year - 1}-{date_obj.year}"
    
    
def generate_fy_range(start_fy, end_fy):
    """
    start_fy, end_fy: 'YYYY-YYYY'
    """
    start_year = int(start_fy.split("-")[0])
    end_year = int(end_fy.split("-")[0])

    return [
        f"{y}-{y+1}" for y in range(start_year, end_year + 1)
    ]


def is_valid_pdf(uploaded_file, max_size_mb=2):
    try:
        max_bytes = max_size_mb * 1024 * 1024
        if uploaded_file.size > max_bytes:
            return False
        # 1️⃣ Single Extension Check

        filename = uploaded_file.name

        # Must contain only one dot before extension
        name, ext = os.path.splitext(filename)

        if ext.lower() != ".pdf":
            return False

        if "." in name:   # prevents file.pdf.exe or file.test.pdf
            return False

        # 2️⃣ Header Check
        uploaded_file.seek(0)
        if uploaded_file.read(5) != b'%PDF-':
            return False
        uploaded_file.seek(0)

        # 3️⃣ Structural Check
        reader = PdfReader(uploaded_file)
        if len(reader.pages) == 0:
            return False

        uploaded_file.seek(0)
        return True

    except Exception:
        return False
    
      
def opening_balance(request):
    try:
        # TEMP login
        # rvsf_id = 49  # remove later
        rvsf_id = request.session.get('user_id')
        # user_role = request.session.get('user_role')
        user_role = request.session.get("user_role")
        is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

        if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
            messages.error(request, "Unauthorized access.")
            return redirect("logoutrvsf")
        if not rvsf_id:
            messages.error(request, "RVSF not logged in")
            return redirect("login")

        rvsf = RvsfRegistration.objects.get(id=rvsf_id)

        # ------------------------------------
        # STEP 1: Determine allowed FY
        # ------------------------------------
        # incorp_fy = get_fy_from_date(rvsf.year_of_incorporation)
        incorp_fy = get_fy_from_date("01-05-2022")  # testing

        if incorp_fy < "2025-2026":
            fy_string = "2025-2026"
            financial_year_obj, created = FinancialYear.objects.get_or_create(
                rvsf=rvsf,
                financial_year=fy_string,
                defaults={"is_active": True},
            )
        else:
            fy_string = get_current_financial_year()
            financial_year_obj, created = FinancialYear.objects.get_or_create(
                rvsf=rvsf,
                financial_year=fy_string,
                defaults={"is_active": True},
            )
            return redirect("procurement_dashboard")

        
        
        # print(financial_year_obj)

        # ------------------------------------
        # STEP 3: Check if Opening Balance already submitted
        # ------------------------------------
        if OpeningBalance.objects.filter(
            financial_year=financial_year_obj
        ).exists():
            messages.info(
                request,
                "Opening balance already submitted for this financial year."
            )
            return redirect("procurement_dashboard")

        # ------------------------------------
        # STEP 4: Fetch ELV Types
        # ------------------------------------
        elv_types = VehicleType.objects.filter(userid=rvsf_id)

        # ------------------------------------
        # STEP 5: POST – Save Opening Balance
        # ------------------------------------
        if request.method == "POST":
            saved = False

            for t in elv_types:
                qty = request.POST.get(f"qty_{t.id}")

                if qty and int(qty) > 0:
                    OpeningBalance.objects.create(
                        financial_year=financial_year_obj,
                        elv_type=t.vehicle_type,
                        opening_balance_quantity=int(qty),
                    )
                    saved = True

            if not saved:
                messages.error(
                    request,
                    "Please enter opening balance for at least one ELV type."
                )
                return redirect("opening_balance")

            messages.success(
                request,
                "Opening balance saved successfully."
            )
            return redirect("procurement_dashboard")

        # ------------------------------------
        # STEP 6: Render Form
        # ------------------------------------
        return render(
            request,
            "procurement_detail/opening_balance_form.html",
            {
                "financial_year": fy_string,
                "elv_types": elv_types,
            },
        )

    except Exception as e:
        messages.error(request, "Something went wrong. Please try again.")
        return redirect("procurement_dashboard")

def procurement_dashboard(request):
    # rvsf_id = 49  # remove later
    rvsf_id = request.session.get('user_id')
    # user_role = request.session.get('user_role')
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    rvsf = RvsfRegistration.objects.get(id=rvsf_id)

    # ------------------------------------
    # STEP 1: Determine FY range
    # ------------------------------------
    incorp_fy = get_fy_from_date("01-05-2022")  # e.g. '2022-2023'
    current_fy = get_current_financial_year()  # e.g. '2025-2026'

    BASE_FY = "2025-2026"

    # Choose later FY (BASE_FY vs Incorporation FY)
    start_fy = (
        incorp_fy
        if int(incorp_fy.split("-")[0]) > int(BASE_FY.split("-")[0])
        else BASE_FY
    )

    # Generate FY dropdown list
    fy_list = generate_fy_range(start_fy, current_fy)

    # Selected FY
    selected_fy = request.GET.get("fy", current_fy)

    # -------------------------------
    # Financial Year object
    # -------------------------------
    fy_obj = FinancialYear.objects.filter(
        rvsf=rvsf_id,
        financial_year=selected_fy
    ).first()

    # -------------------------------
    # Opening Balance
    # -------------------------------
    opening_dict = {}

    if fy_obj:
        opening_balances = (
            OpeningBalance.objects
            .filter(financial_year=fy_obj)
            .values("elv_type")
            .annotate(opening_qty=Sum("opening_balance_quantity"))
        )
        opening_dict = {
            ob["elv_type"]: ob["opening_qty"]
            for ob in opening_balances
        }

    # -------------------------------
    # Procured ELVs
    # -------------------------------
    procured_data = (
        ProcurementData.objects
        .filter(rvsf_id=rvsf_id, financial_year=selected_fy, procurement_type='ELV')
        .values("vehicle_type")
        .annotate(procured_qty=Sum("number_of_elvs"))
    )

    procured_dict = {
        p["vehicle_type"]: p["procured_qty"]
        for p in procured_data
    }
    
    automobile_qty = (
        ProcurementData.objects
        .filter(
            rvsf_id=rvsf_id,
            financial_year=selected_fy,
            procurement_type="AUTOMOBILE"
        )
        .aggregate(total_qty=Sum("number_of_elvs"))
    )["total_qty"] or 0
    # print(automobile_qty)

    # -------------------------------
    # Merge Data
    # -------------------------------
    final_rows = []
    total_opening = total_procured = 0

    elv_types = VehicleType.objects.filter(userid=rvsf_id)

    for elv in elv_types:
        elv_name = elv.vehicle_type

        opening_qty = opening_dict.get(elv_name, 0)
        procured_qty = procured_dict.get(elv_name, 0)

        total_opening += opening_qty
        total_procured += procured_qty

        final_rows.append({
            "elv_name": elv_name,
            "opening_qty": opening_qty,
            "procured_qty": procured_qty,
            "available_qty": opening_qty + procured_qty,
        })

    context = {
        "rows": final_rows,
        "fy_list": fy_list,
        "selected_fy": selected_fy,
        "total_opening": total_opening,
        "total_procured": total_procured,
        "total_available": total_opening + total_procured,
        "automobile_qty" : automobile_qty,
    }

    return render(
        request,
        "procurement_detail/procurement_dashboard.html",
        context
    )

@csrf_exempt
def add_procurement_details(request):
    # rvsf_id = 49  # TODO: session based
    rvsf_id = request.session.get('user_id')
    # user_role = request.session.get('user_role')
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    rvsf = RvsfRegistration.objects.get(id=rvsf_id)

    # FY logic
    incorp_fy = get_fy_from_date("01-05-2022")
    current_fy = get_current_financial_year()
    BASE_FY = "2025-2026"
    start_fy = incorp_fy if int(incorp_fy.split("-")[0]) > int(BASE_FY.split("-")[0]) else BASE_FY
    fy_list = generate_fy_range(start_fy, current_fy)

    elv_types = VehicleType.objects.filter(userid=rvsf_id)
    procurement_entries = ProcurementData.objects.filter(rvsf=rvsf).order_by("-created_at")
    producers=Registration.objects.all()
    
    # ---------- COMMON CONTEXT ----------
    context = {
        "elv_types": elv_types,
        "fy_list": fy_list,
        "selected_fy": current_fy,
        "producers": producers,
        "procurement_entries": procurement_entries,
        "old": {},
    }

    if request.method == "POST":
        if not check_upload_limit(ProcurementData, rvsf_id, limit=5, minutes=10):
            messages.error(
                request,
                "Upload limit exceeded. You can upload only 5 files within 10 minutes."
            )
            return render(request, "procurement_detail/add_procurement_details.html", context)
        context["old"] = request.POST  # 🔑 keep old data
        vehicle_old_data = [
            {
                "vehicle_type": vt,
                "fuel_type": ft,
                "elv_count": ec,
                "invoice_number": inv
            }
            for vt, ft, ec, inv in zip(
                request.POST.getlist("vehicleType[]"),
                request.POST.getlist("fuelType[]"),
                request.POST.getlist("elvCount[]"),
                request.POST.getlist("invoiceNumber[]"),
            )
            if vt or ft or ec or inv
        ]
        context['vehicle_old_data'] = json.dumps(vehicle_old_data)
        
        allowed_vehicle_types = [v.vehicle_type for v in elv_types]
        allowed_fuel_types = ["Petrol", "Diesel", "EV", "Hybrid"]
        try:
            # -------------------------
            # COMMON REQUIRED FIELDS
            # -------------------------
            fy = request.POST.get("financial_year")
            procurement_date = request.POST.get("procurement_date")
            procurement_type = request.POST.get("procurement_type")

            if not fy or not procurement_date or not procurement_type:
                messages.error(request, "Financial Year, Procurement Date and Procurement Type are required.")
                return render(request, "procurement_detail/add_procurement_details.html", context)

            # -------------------------
            # ELV PROCUREMENT
            # -------------------------
            if procurement_type == "ELV":
                collection_type = request.POST.get("collection_type")

                if not collection_type:
                    messages.error(request, "Collection Centre Type is required.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                source_name = request.POST.get("source_name")
                gst_number = request.POST.get("source_gst")
                address = request.POST.get("source_address")
                email = request.POST.get("source_email")
                
                # Allow only letters, numbers and spaces in name
                if source_name and not re.match(r'^[A-Za-z0-9 ]+$', source_name):
                    messages.error(request, "Special characters are not allowed in Name.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                # Address allows letters, numbers, space, dot and slash
                if address and not re.match(r'^[A-Za-z0-9 ./-]+$', address):
                    messages.error(request, "Only letters, numbers, space, dot (.) and slash (/) allowed in Address.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                # Email validation (basic safe format)
                if email and not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
                    messages.error(request, "Invalid email format.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                
                
                if collection_type in ["collection-centres", "insurance-companies"]:
                    if not is_valid_gst(gst_number):
                        messages.error(request, "Invalid GST Number format")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                    if not all([source_name, gst_number, address, email]):
                        messages.error(request, "All source details are required.")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                elif collection_type == "owner-elvs":
                    if not all([source_name, address, email]):
                        messages.error(request, "Owner name, address and email are required.")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                elif collection_type in ["bulk-consumer", "producers"]:
                    if not is_valid_gst(gst_number):
                        messages.error(request, "Invalid GST Number format")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                    if not source_name:
                        messages.error(request, "Supplier / Entity name is required.")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                # -------------------------
                # VEHICLE ROW DATA
                # -------------------------
                vehicle_types = request.POST.getlist("vehicleType[]")
                fuel_types = request.POST.getlist("fuelType[]")
                elv_counts = request.POST.getlist("elvCount[]")
                invoice_numbers = request.POST.getlist("invoiceNumber[]")

                total_rows = len(vehicle_types)
                has_error = False

                # -------------------------
                # VALIDATION
                # -------------------------
                for i in range(total_rows):
                    # VALIDATE DROPDOWN VALUES
                    # -------------------------
                    if vehicle_types[i] not in allowed_vehicle_types:
                        messages.error(request, f"Invalid Vehicle Type selected (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                    if fuel_types[i] not in allowed_fuel_types:
                        messages.error(request, f"Invalid Fuel Type selected (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)
                    
                    cert_file = request.FILES.get(f"certificateUpload[{i}]")
                    invoice_file = request.FILES.get(f"invoiceFile[{i}]")
                    if not cert_file or not invoice_file:
                        messages.error(request, f"Certificate and Invoice file required (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)
                    if not (
                            cert_file.name.lower().endswith(".pdf") and
                            invoice_file.name.lower().endswith(".pdf") and
                            cert_file.content_type == "application/pdf" and
                            invoice_file.content_type == "application/pdf"
                        ):
                        messages.error(request, f"Both Certificate and Invoice must be valid PDF files (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                    # Optional: Check file size (5MB each)
                    if cert_file.size > 2 * 1024 * 1024 or invoice_file.size > 2 * 1024 * 1024:
                        messages.error(request, f"Each file must be under 2MB (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)
                    
                    if not is_valid_pdf(cert_file):
                        messages.error(request, f"Invalid Certificate PDF format (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                    if not is_valid_pdf(invoice_file):
                        messages.error(request, f"Invalid Invoice PDF format (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)
                    
                    row_filled = any([
                        vehicle_types[i],
                        fuel_types[i],
                        elv_counts[i],
                        invoice_numbers[i],
                        cert_file,
                        invoice_file,
                    ])

                    if i == 0 or row_filled:
                        if not vehicle_types[i]:
                            messages.error(request, f"Vehicle Type required in row {i+1}")
                            has_error = True
                        if not fuel_types[i]:
                            messages.error(request, f"Fuel Type required in row {i+1}")
                            has_error = True
                        if not elv_counts[i]:
                            messages.error(request, f"ELV Quantity required in row {i+1}")
                            has_error = True
                        if elv_counts[i] and not elv_counts[i].isdigit():
                            messages.error(request, f"ELV Quantity must be numeric (Row {i+1}).")
                            return render(request, "procurement_detail/add_procurement_details.html", context)
                        if not cert_file:
                            messages.error(request, f"Certificate file required in row {i+1}")
                            has_error = True
                        if not invoice_numbers[i]:
                            messages.error(request, f"Invoice Number required in row {i+1}")
                            has_error = True
                        if invoice_numbers[i] and not re.match(r'^[A-Za-z0-9-]+$', invoice_numbers[i]):
                            messages.error(request, f"Invalid characters in Invoice Number (Row {i+1}).")
                            return render(request, "procurement_detail/add_procurement_details.html", context)
                        if not invoice_file:
                            messages.error(request, f"Invoice file required in row {i+1}")
                            has_error = True

                if has_error:
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                # -------------------------
                # SAVE VEHICLE ROWS
                # -------------------------
                for i in range(total_rows):
                    cert_file = request.FILES.get(f"certificateUpload[{i}]")
                    invoice_file = request.FILES.get(f"invoiceFile[{i}]")

                    row_filled = any([
                        vehicle_types[i],
                        fuel_types[i],
                        elv_counts[i],
                        invoice_numbers[i],
                        cert_file,
                        invoice_file,
                    ])

                    if i == 0 or row_filled:
                        ProcurementData.objects.create(
                            rvsf=rvsf,
                            financial_year=fy,
                            procurement_date=procurement_date,
                            procurement_type="ELV",
                            collection_type=collection_type,
                            source_name=source_name,
                            gst_number=gst_number,
                            address=address,
                            email=email,
                            vehicle_type=vehicle_types[i],
                            fuel_type=fuel_types[i],
                            number_of_elvs=elv_counts[i],
                            certificate_of_deposit=cert_file,
                            invoice_number=invoice_numbers[i],
                            invoice_file=invoice_file,
                        )

            # -------------------------
            # SCRAP PROCUREMENT
            # -------------------------
            elif procurement_type == "AUTOMOBILE":
                scrap_entity = request.POST.get("scrap_entity_name")
                scrap_gst = request.POST.get("scrap_gst")
                scrap_address = request.POST.get("scrap_address")
                scrap_email = request.POST.get("scrap_email")
                scrap_qty = request.POST.get("scrapQuantity")
                scrap_invoice = request.POST.get("scrapInvoiceNumber")
                scrap_invoice_file = request.FILES.get("scrapInvoiceFile")
                if scrap_invoice and not re.match(r'^[A-Za-z0-9-]+$', scrap_invoice):
                    messages.error(request, "Invalid characters in Scrap Invoice Number.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                # Name validation
                if scrap_entity and not re.match(r'^[A-Za-z0-9 ]+$', scrap_entity):
                    messages.error(request, "Special characters are not allowed in Entity Name.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                # Address validation
                if scrap_address and not re.match(r'^[A-Za-z0-9 ./-]+$', scrap_address):
                    messages.error(request, "Only letters, numbers, space, dot (.) and slash (/) allowed in Address.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                # Email validation
                if scrap_email and not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', scrap_email):
                    messages.error(request, "Invalid email format.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                if not all([scrap_entity, scrap_gst, scrap_address, scrap_qty, scrap_invoice, scrap_invoice_file]):
                    messages.error(request, "All Scrap fields are mandatory.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                if not scrap_qty.isdigit():
                    messages.error(request, "Scrap Quantity must be numeric.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                if not is_valid_gst(scrap_gst):
                    messages.error(request, "Invalid GST Number format")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                if not is_valid_pdf(scrap_invoice_file):
                    messages.error(request, "Invalid Scrap Invoice PDF.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                ProcurementData.objects.create(
                    rvsf=rvsf,
                    financial_year=fy,
                    procurement_date=procurement_date,
                    procurement_type="AUTOMOBILE",
                    source_name=scrap_entity,
                    gst_number=scrap_gst,
                    address=scrap_address,
                    email=scrap_email,
                    number_of_elvs=scrap_qty,
                    invoice_number=scrap_invoice,
                    invoice_file=scrap_invoice_file,
                )

            messages.success(request, "Procurement details saved successfully.")
            return redirect("add_procurement_details")

        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
            return render(request, "procurement_detail/add_procurement_details.html", context)

    return render(request, "procurement_detail/add_procurement_details.html", context)


def production_dashboard(request):
    # ------------------------------------
    # SESSION CHECK
    # ------------------------------------
    rvsf_id = request.session.get('user_id')
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    rvsf = RvsfRegistration.objects.get(id=rvsf_id)

    # ------------------------------------
    # CATEGORIES
    # ------------------------------------
    # elv_category = Category.objects.get(name__iexact="Type of ELV")
    elv_category = Category.objects.get(name__iexact="End Of Life Vehicle (ELV)")
    automobile = Category.objects.get(name__iexact="Automobile Steel Scrap")

    # ------------------------------------
    # CURRENT FINANCIAL YEAR
    # ------------------------------------
    current_fy = get_current_financial_year()

    # =====================================================
    # 1. OPENING BALANCE (FY + RVSF WISE)
    # =====================================================
    opening_dict = {
        row["elv_type"]: row["opening_qty"] or 0
        for row in (
            OpeningBalance.objects
            .filter(
                financial_year__financial_year=current_fy,
                financial_year__rvsf_id=rvsf_id
            )
            .values("elv_type")
            .annotate(opening_qty=Sum("opening_balance_quantity"))
        )
    }

    # =====================================================
    # 2. PROCURED ELVs (FY WISE)
    # =====================================================
    procured_dict = {
        row["vehicle_type"]: row["procured_qty"] or 0
        for row in (
            ProcurementData.objects
            .filter(
                rvsf_id=rvsf_id,
                financial_year=current_fy,
                procurement_type="ELV"
            )
            .values("vehicle_type")
            .annotate(procured_qty=Sum("number_of_elvs"))
        )
    }

    # =====================================================
    # 3. PRODUCTION DATA (ELV WISE)
    # =====================================================
    production_data = (
        ProductionForm.objects
        .filter(category=elv_category)
        .values("elv_type")
        .annotate(
            total_scrapped_qty=Sum("scrapped_qty"),
            total_scrapped_weight=Sum("scrapped_weight"),
            total_steel_recovered=Sum("steel_scrap_recovered"),
            total_other_recovered=Sum("other_scrap_recovered"),
            total_cert_potential=Sum("cert_generating_potential"),
        )
    )

    production_map = {
        row["elv_type"]: row
        for row in production_data
    }

    # =====================================================
    # 4. FINAL ELV TABLE (REGISTERED VEHICLE TYPES)
    # =====================================================
    elv_data = []

    elv_types = VehicleType.objects.filter(userid=rvsf_id)

    for elv in elv_types:
        elv_type = elv.vehicle_type
        prod = production_map.get(elv_type, {})

        opening_qty = opening_dict.get(elv_type, 0)
        procured_qty = procured_dict.get(elv_type, 0)
        total_available = opening_qty + procured_qty

        scrapped_qty = prod.get("total_scrapped_qty", 0) or 0

        elv_data.append({
            "elv_type": elv_type,
            "opening_qty": opening_qty,
            "procured_qty": total_available,
            "total_available_qty": total_available,
            "total_scrapped_qty": scrapped_qty,
            "remaining_qty": total_available - scrapped_qty,
            "total_scrapped_weight": prod.get("total_scrapped_weight", 0) or 0,
            "total_steel_recovered": prod.get("total_steel_recovered", 0) or 0,
            "total_other_recovered": prod.get("total_other_recovered", 0) or 0,
            "total_cert_potential": prod.get("total_cert_potential", 0) or 0,
        })

    # =====================================================
    # 5. ELV TOTALS
    # =====================================================
    elv_totals = {
        "opening_qty": sum(r["opening_qty"] for r in elv_data),
        "procured_qty": sum(r["procured_qty"] for r in elv_data),
        "total_available_qty": sum(r["total_available_qty"] for r in elv_data),
        "total_scrapped_qty": sum(r["total_scrapped_qty"] for r in elv_data),
        "total_remaining_qty": sum(r["remaining_qty"] for r in elv_data),
        "total_scrapped_weight": sum(r["total_scrapped_weight"] for r in elv_data),
        "total_steel_recovered": sum(r["total_steel_recovered"] for r in elv_data),
        "total_other_recovered": sum(r["total_other_recovered"] for r in elv_data),
        "total_cert_potential": sum(r["total_cert_potential"] for r in elv_data),
    }

    # =====================================================
    # 6. AUTOMOBILE STEEL SCRAP
    # =====================================================
    auto_agg = (
        ProductionForm.objects
        .filter(category=automobile)
        .aggregate(
            total_processed=Sum("automobile_scrap_processed"),
            total_steel_recovered=Sum("steel_scrap_recovered"),
            total_cert_potential=Sum("cert_generating_potential"),
        )
    )

    # auto_procured = 9564  # keep static if required
    auto_procured = (
            ProcurementData.objects
            .filter(
                rvsf_id=rvsf_id,
                financial_year=current_fy,
                procurement_type="AUTOMOBILE"
            )
            .aggregate(total_qty=Sum("number_of_elvs"))
        )["total_qty"] or 0
    auto_processed = auto_agg["total_processed"] or 0
    auto_recovered = auto_agg["total_steel_recovered"] or 0

    auto_data = [{
        "scrap_name": "Automobile Steel Scrap",
        "processed_qty": auto_processed,
        "procured_qty": auto_procured,
        "total_steel_recovered": auto_recovered,
        "remaining_qty": auto_procured - auto_processed,
        "total_cert_potential": auto_agg["total_cert_potential"] or 0,
    }]

    auto_totals = {
        "procured_qty": auto_procured,
        "processed_qty": auto_processed,
        "total_steel_recovered": auto_recovered,
        "total_remaining_qty": auto_procured - auto_recovered,
        "total_cert_potential": auto_agg["total_cert_potential"] or 0,
    }

    # =====================================================
    # 7. OTHER SCRAP
    # =====================================================
    wasteType = (
        OtherScrap.objects
        .values("wasteType")
        .annotate(total_qty=Sum("quantity"))
    )

    other_scrap = [{
        "wasteType": row["wasteType"],
        "total_qty": row["total_qty"] or 0
    } for row in wasteType]

    other_scrap_totals = {
        "total_qty": sum(r["total_qty"] for r in other_scrap),
    }

    # =====================================================
    # RENDER
    # =====================================================
    context = {
        "elv_data": elv_data,
        "elv_totals": elv_totals,
        "auto_data": auto_data,
        "auto_totals": auto_totals,
        "other_scrap": other_scrap,
        "other_scrap_totals": other_scrap_totals,
    }

    return render(
        request,
        "production_details/production_dashboard.html",
        context
    )



def production_form(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not user_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not user_id:
        return redirect("logoutrvsf")

    # ------------------------------------
    # Master data
    # ------------------------------------
    elv_types = VehicleType.objects.filter(userid=user_id)
    plantCapacity = PlantCapacity.objects.filter(userid=user_id).first()
    # categories = Category.objects.all().order_by('-id')
    categories = Category.objects.order_by('id').values('id', 'name')

    # ------------------------------------
    # Financial Year
    # ------------------------------------
    current_fy = get_current_financial_year()

    # ------------------------------------
    # Opening Balance (FY + RVSF)
    # ------------------------------------
    opening_dict = {
        row["elv_type"]: row["qty"] or 0
        for row in (
            OpeningBalance.objects
            .filter(
                financial_year__financial_year=current_fy,
                financial_year__rvsf_id=user_id
            )
            .values("elv_type")
            .annotate(qty=Sum("opening_balance_quantity"))
        )
    }

    # ------------------------------------
    # Procured ELVs (FY)
    # ------------------------------------
    procured_dict = {
        row["vehicle_type"]: row["qty"] or 0
        for row in (
            ProcurementData.objects
            .filter(
                rvsf_id=user_id,
                financial_year=current_fy,
                procurement_type="ELV"
            )
            .values("vehicle_type")
            .annotate(qty=Sum("number_of_elvs"))
        )
    }

    # ------------------------------------
    # Total Available ELVs (ALL TYPES)
    # ------------------------------------
    total_available_elvs = sum(
        opening_dict.get(v.vehicle_type, 0) +
        procured_dict.get(v.vehicle_type, 0)
        for v in elv_types
    )

    # ------------------------------------
    # History
    # ------------------------------------
    history = (
        ProductionForm.objects
        .select_related("category")
        .filter(rvsf_id=user_id)
        .order_by("-created_at")
    )
    print(categories.values(), "11111111111111111111111")
    context = {
        "category": categories,
        "elvType": elv_types,                  # 🔥 FIXED name
        "plantCapacity": plantCapacity,
        "procuredElvs": total_available_elvs,  # 🔥 REAL value
        "history": history,
    }

    return render(
        request,
        "production_details/scrap_generation_form.html",
        context
    )



# @csrf_exempt
def save_production_form(request):

    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid request"},
            status=400
        )

    user_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not user_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not user_id:
        return redirect("logoutrvsf")
    # RATE LIMIT CHECK (5 per 10 min)
    # ===============================
    if not check_upload_limit(ProductionForm, user_id, limit=5, minutes=10):
        return JsonResponse({
            "status": "error",
            "message": "Upload limit exceeded. You can submit only 5 production entries within 10 minutes."
        }, status=429)
        
    elv_types = VehicleType.objects.filter(userid=user_id)
    allowed_elv_types = {v.vehicle_type for v in elv_types}
    try:
        data = json.loads(request.body)
        category_id = data.get("category")

        # Check category is provided
        if not category_id:
            return JsonResponse({
                "status": "error",
                "message": "Category is required."
            }, status=400)

        # Check category exists
        category = Category.objects.filter(id=category_id).first()

        if not category:
            return JsonResponse({
                "status": "error",
                "message": "Invalid category selected."
            }, status=400)
        # STRICT NUMERIC VALIDATION
        # (Only Positive Integer or Decimal)
        # ===============================
        decimal_pattern = re.compile(r'^\d+(\.\d+)?$')

        numeric_fields = [
            "automobile_scrap_processed",
            "steel_scrap_recovered",
            "scrapped_weight",
            "scrapped_qty",
            "other_scrap_recovered",
            "cert_generating_potential",
        ]

        for field in numeric_fields:
            value = data.get(field)

            if value not in (None, "", 0):
                value_str = str(value).strip()

                # 1️⃣ Format validation
                if not decimal_pattern.match(value_str):
                    return JsonResponse({
                        "status": "error",
                        "message": f"Invalid numeric value for {field}. Only positive numbers are allowed."
                    }, status=400)

                # 2️⃣ Extra negative safety check (double protection)
                if Decimal(value_str) < 0:
                    return JsonResponse({
                        "status": "error",
                        "message": f"{field} cannot be negative."
                    }, status=400)


        # Validate nested other_scraps quantities
        name_pattern = re.compile(r'^[A-Za-z0-9 -]+$')
        for scrap in data.get("other_scraps", []):
            waste_type = scrap.get("wasteType")
            qty = scrap.get("quantity")
             # Validate waste type (letters, numbers, spaces only)
            if waste_type and not name_pattern.match(waste_type):
                return JsonResponse({
                    "status": "error",
                    "message": "Waste Type can contain only letters, numbers and spaces."
                }, status=400)
            if qty not in (None, "", 0):
                qty_str = str(qty).strip()

                if not decimal_pattern.match(qty_str):
                    return JsonResponse({
                        "status": "error",
                        "message": "Invalid numeric value in other scraps quantity."
                    }, status=400)

                if Decimal(qty_str) < 0:
                    return JsonResponse({
                        "status": "error",
                        "message": "Other scrap quantity cannot be negative."
                    }, status=400)
        # fy = request.POST.get("financial_year") Need to uncomment when front end send the financial year
        fy = get_current_financial_year()
        # Convert to Decimal safely
        # if data.get("automobile_scrap_processed"):
        #     scrapped_weight = Decimal(str(data.get("automobile_scrap_processed", 0)))
        other_scrap_recovered = None
        steel_scrap_recovered = Decimal("0")    

        if data.get("automobile_scrap_processed"):

            scrapped_weight = Decimal(str(data.get("automobile_scrap_processed", 0)))
            steel_scrap_recovered = Decimal(str(data.get("steel_scrap_recovered", 0)))

            auto_agg = (
                ProductionForm.objects
                .filter(category_id= 2)
                .aggregate(
                    total_processed=Sum("automobile_scrap_processed"),
                )
            )

            auto_procured = (
                    ProcurementData.objects
                    .filter(
                        rvsf_id=user_id,
                        procurement_type="AUTOMOBILE"
                    )
                    .aggregate(total_qty=Sum("number_of_elvs"))
                )["total_qty"] or Decimal("0")
            already_processed = auto_agg["total_processed"] or Decimal("0")

            remaining_weight = [{
                "remaining_qty": auto_procured - already_processed,
                }]

            # remaining_weight = max_elv_weight - already_processed

            if scrapped_weight < steel_scrap_recovered:
                return JsonResponse({
                    "status": "error",
                    "message": "Automobile scrap processed cannot be greater than Steel Scrap Recovered"
                }, status=400)
                
            if scrapped_weight > remaining_weight[0]["remaining_qty"]:
                return JsonResponse({
                    "status": "error",
                    "message": "Automobile scrap processed cannot exceed remaining Automobile steel scrap weight"
                }, status=400)

        # else:
        #     scrapped_weight = Decimal(str(data.get("scrapped_weight", 0)))


        else:
            scrapped_weight = Decimal(str(data.get("scrapped_weight", 0)))
            scrapped_qty = Decimal(str(data.get("scrapped_qty", 0)))
            elv_type = data.get("elv_type")
            
            if elv_type not in allowed_elv_types:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid ELV type selected."
                }, status=400)

            # 1️⃣ Already scrapped ELVs
            elv_agg = (
                ProductionForm.objects
                .filter(
                    rvsf_id=user_id,
                    elv_type=elv_type
                )
                .aggregate(total_scrapped=Sum("scrapped_qty"))
            )
            already_scrapped_qty = elv_agg["total_scrapped"] or Decimal("0")

            # 2️⃣ Procured ELVs
            elv_procured = (
                ProcurementData.objects
                .filter(
                    rvsf_id=user_id,
                    procurement_type="ELV",
                    vehicle_type=elv_type
                )
                .aggregate(total_qty=Sum("number_of_elvs"))
            )["total_qty"] or Decimal("0")

            financial_year_obj = FinancialYear.objects.filter(
                rvsf_id=user_id,
            ).first()

            opening_balance_qty = Decimal("0")

            if financial_year_obj:
                opening_balance_qty = (
                    OpeningBalance.objects
                    .filter(
                        financial_year=financial_year_obj,
                        elv_type=elv_type
                    )
                    .aggregate(total=Sum("opening_balance_quantity"))
                )["total"] or Decimal("0")
            remaining_qty = elv_procured + opening_balance_qty - already_scrapped_qty
            
            # 3️⃣ Validation
            if scrapped_qty > remaining_qty:
                return JsonResponse({
                    "status": "error",
                    "message": (
                        f"Scrapped quantity ({scrapped_qty}) exceeds "
                        f"remaining ELV quantity ({remaining_qty}) for ELV type {elv_type}"
                    )
                }, status=400)

            steel_scrap_recovered = Decimal(str(data.get("steel_scrap_recovered", 0)))
            # other_scrap_recovered = Decimal(str(data.get("other_scrap_recovered", 0)))
            other_scrap_recovered = Decimal(str(data.get("other_scrap_recovered", 0)))

            # ===============================
            # VALIDATIONS
            # ===============================

            max_steel = scrapped_weight * Decimal("0.65")
            # max_other = scrapped_weight * Decimal("0.35")
            
            base_weight = scrapped_weight - steel_scrap_recovered
            max_other = base_weight
            min_other = base_weight * Decimal("0.80")

            if steel_scrap_recovered > max_steel:
                return JsonResponse({
                    "status": "error",
                    "message": "Steel scrap recovered cannot exceed 65% of scrapped weight"
                }, status=400)

            if not (min_other <= other_scrap_recovered <= max_other):
                return JsonResponse({
                    "status": "error",
                    "message": "Entered quantity of other waste is not in range limit."
                }, status=400)
                
            if other_scrap_recovered > steel_scrap_recovered:
                return JsonResponse({
                    "status": "error",
                    "message": "Other scrap recovered cannot be greater than Steel Scrap Recovered"
                }, status=400)


        
        category = Category.objects.get(id=data["category"])
        scrapping_date = parse_date(data["scrapping_date"])

        # ===============================
        # SAVE DATA (TRANSACTION SAFE)
        # ===============================
        with transaction.atomic():

            entry = ProductionForm.objects.create(
                rvsf_id=user_id,
                category=category,
                scrapping_date=scrapping_date,
                financial_year=fy,
                elv_type=data.get("elv_type"),
                scrapped_qty=data.get("scrapped_qty") or 0,
                scrapped_weight=scrapped_weight,

                automobile_scrap_processed=data.get("automobile_scrap_processed") or 0,

                steel_scrap_recovered=steel_scrap_recovered,
                other_scrap_recovered=other_scrap_recovered,
                cert_generating_potential=data.get("cert_generating_potential") or 0,
            )

            for scrap in data.get("other_scraps", []):
                qty = Decimal(str(scrap.get("quantity", 0)))
                if qty > 0:
                    OtherScrap.objects.create(
                        rvsf_id=user_id,
                        production=entry,
                        financial_year=fy,
                        wasteType=scrap.get("wasteType"),
                        quantity=qty
                    )

        return JsonResponse({
            "status": "success",
            "message": "Production entry saved successfully",
            "id": entry.id
        })

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )



def waste_dashboard(request):

    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")
    selected_fy = request.GET.get("fyyear")
    # -------------------------
    # Recovered quantities
    # -------------------------
    recovered_qs = OtherScrap.objects.filter(rvsf_id=rvsf_id)

    if selected_fy:
        recovered_qs = recovered_qs.filter(financial_year=selected_fy)

    recovered_qs = (
        recovered_qs
        .values("wasteType")
        .annotate(recovered_qty=Sum("quantity"))
    )

    recovered_map = {
        (row["wasteType"]): row["recovered_qty"]
        for row in recovered_qs
    }

    # -------------------------
    # Processed quantities
    # -------------------------
    processed_qs = (
        WasteProcessing.objects
        .filter(rvsf_id=rvsf_id)
        .values("waste_type", "activity")
        .annotate(total_qty=Sum("processed_qty"))
    )
    financial_years_list = (
        OtherScrap.objects
        .filter(rvsf_id=rvsf_id)
        .values_list("financial_year", flat=True)
        .distinct()
    )
    print(processed_qs, "11111111111111111111")
    # Build structure
    dashboard_data = {}

    for (waste), qty in recovered_map.items():
        dashboard_data[(waste)] = {
            "recovered_waste": waste,
            "recovered_qty": qty or Decimal("0"),
            "qty_recycled": Decimal("0"),
            "qty_refurbished": Decimal("0"),
            "qty_disposed": Decimal("0"),
             
        }

    for row in processed_qs:
        waste = row["waste_type"]
        activity = row["activity"]
        qty = row["total_qty"] or Decimal("0")

        if (waste) not in dashboard_data:
            continue

        if activity == "recycled":
            dashboard_data[(waste)]["qty_recycled"] = qty
        elif activity == "refurbish":
            dashboard_data[(waste)]["qty_refurbished"] = qty
        elif activity == "disposal":
            dashboard_data[(waste)]["qty_disposed"] = qty

    # -------------------------
    # Remaining quantity
    # -------------------------
    elv_data = []
    for data in dashboard_data.values():
        total_processed = (
            data["qty_recycled"]
            + data["qty_refurbished"]
            + data["qty_disposed"]
        )
        data["remaining_qty"] = data["recovered_qty"] - total_processed
        elv_data.append(data)
    print(elv_data, "22222222222222222222222")
    return render(
        request,
        "waste_detail/waste_dashboard.html",
        {
            "elv_data": elv_data,
         "financial_years_list": financial_years_list
         }
        
    )
        


def waste_form(request):

    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    try:

        # =========================
        # OTHER SCRAP SUMMARY (Total Generated)
        # =========================
        waste_summary_qs = (
            OtherScrap.objects
            .filter(rvsf_id=rvsf_id)
            .values("wasteType")
            .annotate(total_quantity=Sum("quantity"))
        )

        # =========================
        # PROCESSED WASTE SUMMARY (For Remaining Calculation)
        # =========================
        processed_summary = (
            WasteProcessing.objects
            .filter(rvsf_id=rvsf_id)
            .values("waste_type")
            .annotate(total_quantity=Sum("processed_qty"))
        )

        # Convert processed summary into dictionary
        processed_map = {
            item["waste_type"]: item["total_quantity"] or Decimal("0")
            for item in processed_summary
        }

        # =========================
        # CALCULATE REMAINING QUANTITY
        # =========================
        adjusted_waste_list = []

        for item in waste_summary_qs:
            waste_type = item["wasteType"]
            total_qty = item["total_quantity"] or Decimal("0")

            processed_qty = processed_map.get(waste_type, Decimal("0"))
            remaining_qty = total_qty - processed_qty

            if remaining_qty > 0:
                adjusted_waste_list.append({
                    "wasteType": waste_type,
                    "remaining_quantity": remaining_qty
                })

        # =========================
        # FULL TABLE DATA (Using values())
        # =========================
        waste_list = (
            WasteProcessing.objects
            .filter(rvsf_id=rvsf_id)
            .values(
                "id",
                "waste_type",
                "activity",
                "processed_qty",
                "buyer_name",
                "gst_number",
                "sale_date",
                "invoice",
                "invoice_number"
            )
            .order_by("-id")
        )

        context = {
            "waste_summary": adjusted_waste_list,
            "waste_list": waste_list,
        }
        print(context, "111111111111111111111111111")
        return render(
            request,
            "waste_detail/add_waste_details.html",
            context
        )

    except Exception as e:
        messages.error(request, f"Unexpected error occurred: {e}")
        return render(
            request,
            "waste_detail/add_waste_details.html",
            {
                "waste_summary": [],
                "waste_list": [],
            }
        )


def save_waste_form(request):
    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    if request.method == "POST":
        if not check_upload_limit(WasteProcessing, rvsf_id, limit=5, minutes=10):
            messages.error(
                request,
                "Upload limit exceeded. You can submit only 5 waste entries within 10 minutes."
            )
            return redirect("waste_form")

        waste_type = request.POST.get("waste_type")
        activity = request.POST.get("activity")
        qty = request.POST.get("qty")
        buyer_name = request.POST.get("buyer_name")
        gst = request.POST.get("gst")
        buyer_address = request.POST.get("address")
        email = request.POST.get("email")
        sale_date = request.POST.get("sale_date")
        invoice_number = request.POST.get("invoice_number")
        current_fy = get_current_financial_year()
        invoice = request.FILES.get("invoice")
        manifest_document = request.FILES.get("manifest_document")
        tsdf_document = request.FILES.get("tsdf_document")


        if not all([waste_type, activity, qty, buyer_name, gst, buyer_address, sale_date]):
            messages.error(request, "Please fill all required fields.")
            return redirect("waste_form")
        allowed_activities = {"recycled", "refurbish", "disposal"}

        if activity not in allowed_activities:
            messages.error(request, "Invalid activity selected.")
            return redirect("waste_form")
        # Validate waste type exists in OtherScrap
        if not OtherScrap.objects.filter(rvsf_id=rvsf_id, wasteType=waste_type).exists():
            messages.error(request, "Invalid Waste Type selected.")
            return redirect("waste_form")
        if buyer_name and not re.match(r'^[A-Za-z0-9 ]+$', buyer_name):
            messages.error(request, "Special characters are not allowed in Buyer Name.")
            return redirect("waste_form")

        # Address
        if buyer_address and not re.match(r'^[A-Za-z0-9 ./-]+$', buyer_address):
            messages.error(request, "Only letters, numbers, space, dot (.) and slash (/) allowed in Address.")
            return redirect("waste_form")

        # Email
        if email and not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
            messages.error(request, "Invalid email format.")
            return redirect("waste_form")

        # Invoice Number
        if invoice_number and not re.match(r'^[A-Za-z0-9-]+$', invoice_number):
            messages.error(request, "Invalid characters in Invoice Number.")
            return redirect("waste_form")

        # Quantity (positive decimal only)
        if not re.match(r'^\d*\.?\d+$', str(qty)):
            messages.error(request, "Quantity must be a positive number.")
            return redirect("waste_form")
        if not invoice:
            messages.error(request, "Invoice document is required.")
            return redirect("waste_form")

        if not is_valid_pdf(invoice):
            messages.error(request, "Invoice must be a valid PDF under 2MB.")
            return redirect("waste_form")
        

        if not is_valid_gst(gst):
                messages.error(request, "Invalid GST Number format")
                return redirect("waste_form")
                
        # Disposal-specific validation
        if activity.lower() == "disposal":
            if not manifest_document or not tsdf_document:
                messages.error(
                    request,
                    "Manifest and TSDF document are required for disposal activity."
                )
                return redirect("waste_form")

        if manifest_document:
            # Validate both
            if not is_valid_pdf(manifest_document):
                messages.error(request, "Manifest document must be a valid PDF under 2MB.")
                return redirect("waste_form")
        if tsdf_document:
            if not is_valid_pdf(tsdf_document):
                messages.error(request, "TSDF document must be a valid PDF under 2MB.")
                return redirect("waste_form")

        try:
            qty = Decimal(qty)

            total_recovered = (
                OtherScrap.objects
                .filter(rvsf_id=rvsf_id, wasteType=waste_type)
                .aggregate(total=Sum("quantity"))
            )["total"] or Decimal("0")

            total_processed = (
                WasteProcessing.objects
                .filter(rvsf_id=rvsf_id, waste_type=waste_type)
                .aggregate(total=Sum("processed_qty"))
            )["total"] or Decimal("0")

            remaining_qty = total_recovered - total_processed

            if qty > remaining_qty:
                messages.error(
                    request,
                    f"Entered quantity ({qty}) exceeds available scrap ({remaining_qty})."
                )
                return redirect("waste_form")

            # ✅ Save
            WasteProcessing.objects.create(
                rvsf_id=rvsf_id,
                waste_type=waste_type,
                activity=activity,
                processed_qty=qty,
                buyer_name=buyer_name,
                buyer_address=buyer_address,
                buyer_email=email,
                gst_number=gst,
                sale_date=sale_date,
                invoice_number=invoice_number,
                invoice=invoice,
                manifest_document=manifest_document,
                agreement_tsdf_certificate=tsdf_document,
                financial_year = current_fy 
            )

            messages.success(request, "✅ Waste details submitted successfully.")
            return redirect("waste_form")

        except Exception as e:
            messages.error(request, f"❌ Error while saving data: {str(e)}")
            return redirect("waste_form")

    messages.error(request, "Invalid request.")
    return redirect("waste_form")



def certificate_generation_dashboard(request):
    
    user_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not user_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not user_id:
        return redirect("logoutrvsf")

    try:
        ratio_data = calculate_steel_recovery_data(user_id)
    except ValueError as e:
        messages.error(request, str(e))
        return render(
        request, "epr_certificate_generation/epr_certificate_generation_dashboard.html")

    qtySteelRecovered = ratio_data["qtySteelRecovered"]

    # ---------------------------------------
    # 6️⃣ Certificate Potential
    # ---------------------------------------

    certGeneratedPotential = (
        ProductionForm.objects
        .filter(rvsf_id=user_id)
        .aggregate(total=Sum("cert_generating_potential"))
    )["total"] or Decimal("0")

    steelScrapSold = ratio_data["steel_scrap_sold"]

    # Prevent overselling
    steelScrapSold = min(steelScrapSold, qtySteelRecovered)

    remainSteelScrap = qtySteelRecovered - steelScrapSold

    eprCertGenerated = steelScrapSold

    remainCertPotential = max(
        certGeneratedPotential - eprCertGenerated,
        Decimal("0")
    )
    
    context = {
        "qtySteelRecovered": qtySteelRecovered,
        "certGeneratedPotential": certGeneratedPotential,
        "steelScrapSold": steelScrapSold,
        "remainSteelScrap": remainSteelScrap,
        "eprCertGenerated": eprCertGenerated,
        "remainCertPotential": remainCertPotential,
    }

    return render(
        request,
        "epr_certificate_generation/epr_certificate_generation_dashboard.html",
        context
    )




def certificate_generation_form(request):

    user_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not user_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not user_id:
        return redirect("logoutrvsf")

    history = (
        SteelScrapSale.objects
        .filter(rvsf_id=user_id)
        .order_by("-created_at")
    )

    context = {
        "history": history
    }

    if request.method == "POST":
        if not check_upload_limit(SteelScrapSale, user_id, limit=5, minutes=10):
            messages.error(
                request,
                "Upload limit exceeded. You can submit only 5 steel sale entries within 10 minutes."
            )
            return redirect("certificate_generation_form")
        try:
            required_fields = [
                "date_of_sale", "buyer_type", "buyer_name",
                "buyer_address", "gst_number", "email",
                "quantity_sold", "invoice_amount", "invoice_number",
            ]
            for field in required_fields:
                if not request.POST.get(field):
                    messages.error(request, f"Please fill all {field} details.")
                    return redirect("certificate_generation_form")
            buyer_name = request.POST.get("buyer_name")
            buyer_address = request.POST.get("buyer_address")
            email = request.POST.get("email")
            invoice_number = request.POST.get("invoice_number")
            invoice_amount = request.POST.get("invoice_amount")
            quantity_sold = request.POST.get("quantity_sold")
            gst_number = request.POST.get("gst_number")
            buyer_type = request.POST.get("buyer_type")
            allowed_buyer_types = {
                "Blast Furnace",
                "Induction Furnace",
                "Electric Arc Furnace",
                "Scrap Recyclers",
                "Steel Mills",
                "Others"
            }

            if buyer_type not in allowed_buyer_types:
                messages.error(request, "Invalid Buyer Type selected.")
                return redirect("certificate_generation_form")

            # Buyer Name (letters, numbers, space only)
            if buyer_name and not re.match(r'^[A-Za-z0-9 ]+$', buyer_name):
                messages.error(request, "Special characters are not allowed in Buyer Name.")
                return redirect("certificate_generation_form")

            # Address (allow . and /)
            if buyer_address and not re.match(r'^[A-Za-z0-9 ./-]+$', buyer_address):
                messages.error(request, "Only letters, numbers, space, dot (.) and slash (/) allowed in Address.")
                return redirect("certificate_generation_form")

            # Email validation
            if email and not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
                messages.error(request, "Invalid email format.")
                return redirect("certificate_generation_form")

            # Invoice number (letters, numbers, dash only)
            if invoice_number and not re.match(r'^[A-Za-z0-9-]+$', invoice_number):
                messages.error(request, "Invalid characters in Invoice Number.")
                return redirect("certificate_generation_form")

            # GST validation
            if not is_valid_gst(gst_number):
                messages.error(request, "Invalid GST Number format.")
                return redirect("certificate_generation_form")

            # Quantity sold (positive decimal only)
            if not re.match(r'^\d+(\.\d+)?$', str(quantity_sold)):
                messages.error(request, "Quantity sold must be a positive number.")
                return redirect("certificate_generation_form")

            # Invoice amount (positive decimal only)
            if not re.match(r'^\d+(\.\d+)?$', str(invoice_amount)):
                messages.error(request, "Invoice amount must be a positive number.")
                return redirect("certificate_generation_form")
            # ------------------------
            # FILE VALIDATION
            # ------------------------

            invoice_file = request.FILES.get("invoice_file")

            # Required Check
            if not invoice_file:
                messages.error(request, "Invoice file is required.")
                return redirect("certificate_generation_form")

            # PDF Validation (Size + Structure + Extension)
            if not is_valid_pdf(invoice_file):
                messages.error(request, "Invoice must be a valid PDF file under 2MB.")
                return redirect("certificate_generation_form")

            # 🔥 NEW COMPLETE BUSINESS LOGIC (13:7 WITH VALIDATION)
            current_fy = get_current_financial_year()
            # 1️⃣ Total Other Scrap Recovered
            total_other_scrap_recovered = (
                OtherScrap.objects
                .filter(rvsf_id=user_id)
                .aggregate(total=Sum("quantity"))
            )["total"] or Decimal("0")

            # 2️⃣ Total Other Scrap Processed
            total_other_scrap_processed = (
                WasteProcessing.objects
                .filter(rvsf_id=user_id)
                .aggregate(total=Sum("processed_qty"))
            )["total"] or Decimal("0")

            # 3️⃣ HARD VALIDATION
            if total_other_scrap_processed > total_other_scrap_recovered:
                messages.error(
                    request,
                    "Processed waste exceeds total recovered scrap. Please correct waste entries."
                )
                return redirect("certificate_generation_form")

            
            try:
                ratio_data = calculate_steel_recovery_data(user_id)
            except ValueError as e:
                messages.error(request, str(e))
                return render(request, "epr_certificate_generation/epr_certificate_form.html",)

            qtySteelRecovered = ratio_data["qtySteelRecovered"]
            steelScrapSold = ratio_data["steel_scrap_sold"]

            remainSteelScrap = qtySteelRecovered - steelScrapSold

            # 9️⃣ Sale Validation
            quantity_sold = Decimal(request.POST.get("quantity_sold"))

            if quantity_sold > remainSteelScrap:
                messages.error(
                    request,
                    "Sale quantity can't exceeds Remaining steel Scrap Quantity at RVSF(MT)."
                )
                return redirect("certificate_generation_form")

            # ============================================================
            # SAVE DATA
            # ============================================================

            with transaction.atomic():

                
                if buyer_type == "Others":
                    buyer_type = f"Others - {request.POST.get('other_buyer_type')}"

                SteelScrapSale.objects.create(
                    rvsf_id=user_id,
                    sale_date=request.POST.get("date_of_sale"),
                    buyer_type=buyer_type,
                    buyer_name=request.POST.get("buyer_name"),
                    buyer_address=request.POST.get("buyer_address"),
                    gst_number=request.POST.get("gst_number"),
                    email=request.POST.get("email"),
                    quantity_sold=quantity_sold,
                    invoice_amount=request.POST.get("invoice_amount"),
                    invoice_number=request.POST.get("invoice_number"),
                    invoice_pdf=invoice_file,
                    financial_year = current_fy 
                )

            messages.success(request, "✅ Steel sale recorded successfully.")
            return redirect("certificate_generation_form")

        except Exception as e:
            messages.error(request, "Error 500.")
            return redirect("certificate_generation_form")

    else:
        return render(
            request,
            "epr_certificate_generation/epr_certificate_form.html",
            context
        )

def denominate_epr_dashboard(request):
    
    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    # -------------------------
    # FETCH GENERATED CERTS
    # -------------------------
    cert_generated = (
        SteelScrapSale.objects
        .filter(rvsf_id=rvsf_id)
        .aggregate(total=Sum("quantity_sold"))
        .get("total") or Decimal("0")
    )
    today = now()

    certDenominated = (DenominatedCertificate.objects
        .filter(rvsf_id=rvsf_id,
                expiry_date__gte=today)
        .aggregate(total=Sum("total_certificate_value_denominated"))
        .get("total") or Decimal("0")
    )
    remainCertAvailDenominated = cert_generated - certDenominated
    denomination_details = (
        DenominationDetail.objects
        .filter(
            rvsf_id=rvsf_id,
            denomination_master__expiry_date__gte=today
        )
        .select_related("denomination_master")
        .values(
            "unique_id",
            "denomination_kg",
            "quantity",
            "denomination_master__denomination_date",
            "denomination_master__expiry_date",
        )
        .order_by("-denomination_master__denomination_date")
    )
    context = {
        "certGenerated" : cert_generated,
        "certDenominated" : certDenominated,
        "remainCertAvailDenominated" : remainCertAvailDenominated,
        "denomination_details": denomination_details,
    }
    
    return render(request, "denominate_epr_certificate/denominate_dashboard.html", context) 


def denominate_epr_certificate(request):
    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")
    today = now()
    if request.method == 'POST':
        
        try:
            decimal_pattern = re.compile(r'^\d+(\.\d+)?$')
            integer_pattern = re.compile(r'^\d+$')

            total_mt_raw = request.POST.get("total_certificate_value_denominated", "").strip()

            if not decimal_pattern.match(total_mt_raw):
                messages.error(request, "Total certificate value must be a positive number.")
                return redirect("denominate_dashboard")

            if Decimal(total_mt_raw) <= 0:
                messages.error(request, "Total certificate value must be greater than zero.")
                return redirect("denominate_dashboard")

            # Validate denomination quantities (must be positive integers only)
            denomination_fields = ["kg_100", "kg_200", "kg_500", "kg_1000", "kg_10000"]

            if not any(request.POST.get(field) for field in denomination_fields):
                messages.error(request, "Please enter at least one denomination quantity.")
                return redirect("denominate_dashboard")
            for field in denomination_fields:
                value = request.POST.get(field, "").strip()

                if value:
                    if not integer_pattern.match(value):
                        messages.error(request, f"Invalid quantity for {field}. Only positive integers allowed.")
                        return redirect("denominate_dashboard")

                    if int(value) < 0:
                        messages.error(request, f"{field} quantity cannot be negative.")
                        return redirect("denominate_dashboard")
            total_mt = Decimal(request.POST.get("total_certificate_value_denominated", "0"))
            state_code = RvsfRegistration.objects.get(id=rvsf_id).state
            print("111111111111111111")
            denomination_map = {
                100: request.POST.get("kg_100"),
                200: request.POST.get("kg_200"),
                500: request.POST.get("kg_500"),
                1000: request.POST.get("kg_1000"),
                10000: request.POST.get("kg_10000"),
            }

            # ------------------------
            # VALIDATION
            # ------------------------
            total_kg = Decimal("0")

            for kg, qty in denomination_map.items():
                # qty = Decimal(qty or 0)
                qty = Decimal(str(qty or 0))
                total_kg += kg * qty

            if (total_kg / Decimal("1000")) != total_mt:
                messages.error(
                    request,
                    "Denomination total must exactly match certificate value."
                )
                return redirect("denominate_dashboard")
            current_year = get_current_financial_year()
            # ------------------------
            # SAVE (DB SEQUENCE SAFE)
            # ------------------------
            with transaction.atomic():

                master = DenominatedCertificate.objects.create(
                    rvsf_id=rvsf_id,
                    total_certificate_value_denominated=total_mt,
                    denomination_date=now(),
                    financial_year = current_year
                )

                for kg, qty in denomination_map.items():
                    qty = int(qty or 0)
                    if qty <= 0:
                        continue

                    # Save first to get DB sequence (id)
                    detail = DenominationDetail.objects.create(
                        denomination_master=master,
                        rvsf_id=rvsf_id,
                        denomination_kg=kg,
                        quantity=qty,
                        unique_id="TEMP"
                    )

                    # Generate unique ID using DB PK
                    unique_id = (
                        f"{rvsf_id}_"
                        f"{now().strftime('%Y%m%d')}_"
                        f"{state_code}_"
                        f"{random.randint(1000,9999)}_"
                        f"{detail.id}"
                    )

                    detail.unique_id = unique_id
                    detail.save(update_fields=["unique_id"])

            messages.success(request, "EPR Certificate denominated successfully.")
            return redirect("denominate_epr_dashboard")

        except Exception as e:
            # Any error → rollback + user feedback
            messages.error(
                request,
                "Something went wrong while saving denomination. Please try again."
            )

            # 🔍 Optional (recommended): log real error
            print("Denomination Error:", str(e))

            return redirect("denominate_epr_certificate")
    
    
    else:
        denomination_details = (
            DenominationDetail.objects
            .filter(
                rvsf_id=rvsf_id,
                denomination_master__expiry_date__gte=today
            )
            .select_related("denomination_master")
            .values(
                "unique_id",
                "denomination_kg",
                "quantity",
                "denomination_master__denomination_date",
                "denomination_master__expiry_date",
            )
            .order_by("-denomination_master__denomination_date")
        )
        return render(request, "denominate_epr_certificate/denominate_dashboard.html", denomination_details)

def certificate_transfer_dashboard(request):

    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    today = now()

    # -------------------------
    # FETCH DENOMINATED CERTS (MT)
    # -------------------------
    cert_denominated_mt = (
        DenominatedCertificate.objects
        .filter(
            rvsf_id=rvsf_id,
         
            expiry_date__gte=today   # only active certificates
        )
        .aggregate(total=Sum("total_certificate_value_denominated"))
        .get("total") or Decimal("0")
    )

    # -------------------------
    # CONVERT MT → KG
    # -------------------------
    certDenominated = cert_denominated_mt * Decimal("1000")

    # -------------------------
    # TRANSFERRED (for now 0)
    # -------------------------
    producer_name_subquery = Registration.objects.filter(
                            id=OuterRef("transaction__producer_id")
                        ).values("company_name")[:1]

    certTransferred = (
                    CertificateTransfer.objects
                    .filter(transaction__rvsf_id=rvsf_id)
                    .annotate(
                        total_weight=ExpressionWrapper(
                            F("denomination_detail__denomination_kg") *
                            F("denomination_detail__quantity"),
                            output_field=DecimalField()
                        ),
                        denomination_status=F("denomination_detail__status"),
                        company_name=Subquery(producer_name_subquery)
                    )
                )
    transaction_details=list(certTransferred.values())
    # total_transferred_weight = certTransferred.aggregate(
    #                                 total=Sum("total_weight")
    #                             )["total"] or 0
    total_transferred_weight = certTransferred.filter(
            transaction__status="accepted"
        ).aggregate(
            total=Sum("total_weight")
        )["total"] or 0
    remainCertAvailTransferred = certDenominated - total_transferred_weight

    context = {
        "certDenominated": certDenominated,            # KG
        "certTransferred": certTransferred,            # KG
        "remainCertAvailTransferred": remainCertAvailTransferred,
        "transaction_details": transaction_details,
        "total_transferred_weight": total_transferred_weight, 
    }
    print(context, "1111111111111111")
    return render(request, "transfer_certificate/transfer_certificate_dashboard.html", context)


def transfer_certificate(request):
    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")

    if not rvsf_id:
        return redirect("logoutrvsf")
    rvsf_user_info = RvsfRegistration.objects.filter(id=rvsf_id).first()

    today = now()
    for_expiry_check = timezone.now().date()
    producers = Registration.objects.all()
    if request.method == "POST":

        try:
            detail_ids = request.POST.getlist("denomination_detail_id")
            producer_id = request.POST.get("producer_id")

            if not detail_ids or not producer_id:
                messages.error(request, "All fields are required.")
                return redirect("transfer_certificate")
            # Producer ID must be numeric
            if not re.match(r'^\d+$', str(producer_id)):
                messages.error(request, "Invalid producer selected.")
                return redirect("transfer_certificate")

            # Ensure producer exists
            if not Registration.objects.filter(id=producer_id).exists():
                messages.error(request, "Selected producer does not exist.")
                return redirect("transfer_certificate")

            # Validate certificate unique_id format
            for uid in detail_ids:
                # Your unique_id format:
                # rvsfId_YYYYMMDD_state_random_detailid
                if not re.match(r'^[A-Za-z0-9_]+$', uid):
                    messages.error(request, "Invalid certificate selection.")
                    return redirect("transfer_certificate")
                
            txn_id = generate_transaction_id(rvsf_id, producer_id)

            with transaction.atomic():

                # 🔥 1️⃣ Create one transaction (Batch Level)
                # txn = CertificateTransaction.objects.create(
                #     producer_id=producer_id,
                #     rvsf_id=rvsf_id,
                #     status="pending"
                # )
                
                txn = CertificateTransaction.objects.create(
                    transaction_id=txn_id,
                    producer_id=producer_id,
                    rvsf_id=rvsf_id,
                    status="pending"
                )

                for detail_id in detail_ids:

                    detail = DenominationDetail.objects.select_related(
                        "denomination_master"
                    ).get(unique_id=detail_id, rvsf_id=rvsf_id)

                    # Expiry validation
                    if detail.denomination_master.expiry_date < timezone.now().date():
                        messages.error(
                            request,
                            f"Certificate {detail.unique_id} is expired."
                        )
                        return redirect("transfer_certificate")
                    if detail.status not in ["generated", "reverted"]:
                        messages.error(
                            request,
                            f"Certificate {detail.unique_id} is not available for transfer."
                        )
                        return redirect("transfer_certificate")
                    # 🔥 2️⃣ Create transfer row linked to transaction
                    CertificateTransfer.objects.create(
                        denomination_detail=detail,
                        transaction=txn,
                        status="pending",
                        transfer_date=now()
                    )

                    # 🔥 3️⃣ Update certificate status
                    detail.status = "under_transfer"
                    detail.save(update_fields=["status"])

            messages.success(request, "Certificates transferred successfully.")
            return redirect("transfer_certificate")

        except DenominationDetail.DoesNotExist:
            messages.error(request, "Invalid certificate selected.")
            return redirect("transfer_certificate")

        except Exception as e:
            print("Transfer Error:", str(e))
            messages.error(request, "Something went wrong during transfer.")
            return redirect("transfer_certificate")
    
    
    
    # =========================
    # GET LOGIC (DASHBOARD DATA)
    # =========================

    cert_denominated_mt = (
        DenominatedCertificate.objects
        .filter(
            rvsf_id=rvsf_id,
            expiry_date__gte=today
        )
        .aggregate(total=Sum("total_certificate_value_denominated"))
        .get("total") or Decimal("0")
    )
    certDenominated = cert_denominated_mt * Decimal("1000")

    cert_denominated_details = (
        DenominatedCertificate.objects
        .filter(
            rvsf_id=rvsf_id,
            expiry_date__gte=today
        )
        )
    certTransferred = (DenominationDetail.objects.filter(rvsf_id=rvsf_id, status="transferred", denomination_master__expiry_date__gte=today)
                        .aggregate(total=Sum( ExpressionWrapper(F("denomination_kg") * F("quantity"), output_field=DecimalField())))
                        .get("total") or Decimal("0"))
    generated_certificates = (DenominationDetail.objects.select_related("denomination_master").filter(rvsf_id=rvsf_id,
                                status__in=["generated", "reverted"], denomination_master__expiry_date__gte=today).order_by("-id"))

    remainCertAvailTransferred = certDenominated - certTransferred

    
    print(producers, "2222222222222222222")
    context = {
        "certDenominated": certDenominated,
        "certTransferred": certTransferred,
        "remainCertAvailTransferred": remainCertAvailTransferred,
        "producers": producers,
        "generated_certificates" : generated_certificates,
        "rvsf_user_info" :rvsf_user_info,
        "cert_denominated_details" : cert_denominated_details
    }
    print(certTransferred,"1111111")
    return render(
        request,
        "transfer_certificate/transfer_certificate.html",
        context
    )
    


def certificate_details(request):

    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    today = now()

    # -----------------------------
    # 🔹 Subquery for DenominationDetail
    # -----------------------------
    rvsf_name_subquery_dd = RvsfRegistration.objects.filter(
        id=OuterRef("rvsf_id")
    ).values("company_name")[:1]

    certificates_generated_list = (
        DenominationDetail.objects
        .select_related("denomination_master")
        .filter(
            rvsf_id=rvsf_id,
            denomination_master__expiry_date__gte=today,
            status__in=["generated", "reverted"]
        )
        .annotate(
            rvsf_company_name=Subquery(rvsf_name_subquery_dd)
        )
        .values(
            "id",
            "unique_id",
            "denomination_kg",
            "quantity",
            "status",
            "denomination_master__id",
            "denomination_master__expiry_date",
            "denomination_master__denomination_date",
            "rvsf_company_name"
        )
    )

    # -----------------------------
    # 🔹 Subquery for CertificateTransfer
    # -----------------------------
    producer_subquery = Registration.objects.filter(
        id=OuterRef("transaction__producer_id")
    ).values("company_name")[:1]

    rvsf_name_subquery_ct = RvsfRegistration.objects.filter(
        id=OuterRef("transaction__rvsf_id")
    ).values("company_name")[:1]

    certificates_transferred_list = (
        CertificateTransfer.objects
        .select_related(
            "denomination_detail",
            "denomination_detail__denomination_master",
            "transaction"
        )
        .filter(
            transaction__rvsf_id=rvsf_id,
            transaction__status="accepted",
            denomination_detail__status="transferred"
        )
        .annotate(
            producer_company_name=Subquery(producer_subquery),
            rvsf_company_name=Subquery(rvsf_name_subquery_ct),
            total_weight=ExpressionWrapper(
                F("denomination_detail__denomination_kg") *
                F("denomination_detail__quantity"),
                output_field=DecimalField()
            )
        )
        .values(
            "id",
            "transaction__producer_id",
            "transfer_date",
            "created_at",
            "transaction__rvsf_id",

            "denomination_detail__id",
            "denomination_detail__unique_id",
            "total_weight",
            "denomination_detail__status",
            "denomination_detail__denomination_master__expiry_date",

            "producer_company_name",
            "rvsf_company_name"
        )
    )

    context = {
        "certificates_transferred_list": certificates_transferred_list,
        "certificate_details": certificates_generated_list
    }
    print(context, "11111111")
    return render(
        request,
        "certificate_details/certificate_details.html",
        context
    )

def generate_transaction_id(rvsf_id, producer_id):

    # Date format YYYYMMDD
    date_str = timezone.now().strftime("%Y%m%d")

    # Random 5 digits
    random_digits = random.randint(10000, 99999)

    # Sequence (count of today's transactions)
    today = timezone.now().date()
    seq = CertificateTransaction.objects.filter(
        created_at__date=today
    ).count() + 1

    sequence = str(seq).zfill(5)

    txn_id = f"{rvsf_id}_{date_str}_{random_digits}_{sequence}_{producer_id}"

    return txn_id
    
    