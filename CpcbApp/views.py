import os, base64, json, subprocess, re, time, uuid, pdfkit, urllib3, hashlib, openpyxl, logging, string, requests, random, secrets, imaplib, smtplib
from .forms import *
from .models import *

from SpcbApp.models import *
from django.views import View
from registration.views import *

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
import logging
# User = get_user_model()
from django.db.models import Count, Q, Sum, Max
from collections import defaultdict
# logger = logging.getLogger(__name__)

from jose.exceptions import JWTError
from jose import jwt
import django.utils.timezone as dj_timezone
from django.contrib.auth.hashers import check_password as django_check_password
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse

from registration.session_utils import set_active_session

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
MOBILE_REGEX = r'^[6-9]\d{9}$'
MAX_OTP_REQUESTS = 5      # Max OTP requests per period
OTP_REQUEST_PERIOD = 3600 # 1 hour in seconds
MAX_OTP_ATTEMPTS = 5      # Max verification attempts per OTP
OTP_EXPIRY = 900

from django.contrib.auth.decorators import login_required
from registration.session_utils import set_active_session, mask_email, mask_phone
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
from registration.validators import validate_uploaded_file, secure_filename
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

from ELV.whatsapp_api import WhatsAppService
logger = logging.getLogger("elv_logger")

def frwd_application(mobile_no, from_name, to_name):
    whatsapp = WhatsAppService()

    response = whatsapp.send_template(
        number=mobile_no,
        template_name="fwd_app_verify",
        components=[
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": to_name},
                    {"type": "text", "text": from_name}
                ]
            }
        ]
    )

    return JsonResponse(response)

# ----------------------------------------------------------- Admin Section --------------------------------------------------#


def admin_logout(request):
    try:    
        session_key = request.session.session_key
        admin_id = request.session.get('admin_user_id')

        # Clear Django session
        # request.session.flush()

        # Delete session cookie
        response = redirect('custom_admin_login')
        # response.delete_cookie('sessionid')

        # Remove ActiveSession entry for admin
        if admin_id and session_key:
            ActiveSession.objects.filter(user_id=admin_id, session_key=session_key, user_type='admin').delete()


        return response
    except Exception as e:
        logger.info(
            f"Error occurred in admin_logout | admin_id={request.session.get('admin_user_id')} | error={str(e)}"
        )
        return redirect('admin_dashboard')


def sendforgetpwdemailcpcb(username, company_email):
    user = CpcbUser.objects.filter(
        username=username,
        company_email=company_email
    ).first()

    if not user:
        return False, "Invalid Username or Email."

    # Generate new password
    new_password = get_random_string(
        length=8,
        allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    )

    # Save hashed password
    user.password = make_password(new_password)
    user.first_login = 0

    subject = "Password Reset – EPR End of Life Vehicle"

    html_content = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>Dear User,</p>

            <p>Your password has been reset for the
            <strong>EPR End of Life Vehicle</strong> portal.</p>

            <div style="background-color: #f5f7fa; border: 1px solid #ddd;
                        border-radius: 6px; padding: 12px; margin: 15px 0;">
                <p><strong>Username:</strong> {username}</p>
                <p><strong>New Password:</strong> {new_password}</p>
            </div>

            <p>Please log in and change your password immediately.</p>

            <p>Regards,<br>
            Central Pollution Control Board (CPCB)</p>
        </div>
    """

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body="Your password has been reset successfully.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[company_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        user.save()
        return True, "New password has been sent to your registered company email."

    except Exception as e:
        logger.error(
            "Forgot password email failed for %s: %s",
            company_email,
            str(e),
            exc_info=True
        )
        return False, "Unable to send email at the moment. Please try again later."


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


def cpcb_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_id = request.session.get('admin_user_id')
        if not user_id:
            return redirect('custom_admin_login')
        try:
            user = CpcbUser.objects.get(id=user_id)
            if not user.is_active:
                return redirect('custom_admin_login')
            request.user = user  # attach user to request
        except CpcbUser.DoesNotExist:
            return redirect('custom_admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def generate_admin_username():
    # year_suffix = datetime.datetime.now().strftime('%y')  # '25' for 2025
    year_suffix = datetime.now().strftime('%y')
    sequence_file = 'sequence.txt'

    # Load last used sequence
    if os.path.exists(sequence_file):
        with open(sequence_file, 'r') as f:
            last_seq = int(f.read().strip())
    else:
        last_seq = 0

    # Increment and save new sequence
    new_seq = last_seq + 1
    with open(sequence_file, 'w') as f:
        f.write(str(new_seq))

    sequence_str = str(new_seq).zfill(2)  
    return f'CPCB{year_suffix}{sequence_str}'


@cpcb_admin_required
def create_user(request):
    try:
        officer = request.user

        # ✅ Replace is_superuser check with custom flag
        if not officer.is_admin:
            raise PermissionDenied("You are not allowed to create users.")

        # Fetch dashboard counts
        fresh_count = producerGeneralDetails.objects.filter(
            application_type=0, forwarded_to=officer.id
        ).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()

        resubmit_count = producerGeneralDetails.objects.filter(
            application_type=1, forwarded_to=officer.id
        ).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()

        # Handle user creation
        if request.method == 'POST':
            form = CpcbUserForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)

                try:
                    validate_email(user.email)
                except ValidationError:
                    return JsonResponse({'success': False, 'message': 'Invalid email format.'})

                username = generate_admin_username()
                password = generate_password()

                user.username = username
                user.password = make_password(password)  # ✅ hash manually
                user.is_active = True
                user.is_admin = False  # new users are not admins unless explicitly set
                user.save()

                # Send email with credentials
                try:
                    sendSignupEmail(user.first_name, username, user.email, password)
                    messages.success(
                        request,
                        f"Account created successfully! Credentials have been sent to {user.first_name}'s email."
                    )
                except Exception as e:
                    messages.warning(request, f"Account created, but email not sent: {e}")

                return redirect('create_user')
        else:
            form = CpcbUserForm()

        role = RoleType.objects.all()
        return render(request, 'admin/create_user.html', {
            'form': form,
            'roles': role,
            'fresh_count': fresh_count,
            'resubmit_count': resubmit_count,
        })
    except Exception as e:
        logger.info(f"Unexpected error in create_user | user_id={request.user.id} | error={str(e)}")
        return redirect('admin_dashboard')    


@cpcb_admin_required
def view_user(request):
    try:
        officer = request.user

        # ✅ Use your own `is_admin` flag instead of `is_superuser`
        if officer.is_admin:
            users = CpcbUser.objects.all()
        else:
            users = CpcbUser.objects.filter(division=officer.division)

        role = RoleType.objects.all()

        fresh_count = producerGeneralDetails.objects.filter(
            application_type=0, forwarded_to=officer.id
        ).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()

        resubmit_count = producerGeneralDetails.objects.filter(
            application_type=1, forwarded_to=officer.id
        ).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()

        approved_count = rejected_count = 0
        if officer.division == '1':
            approved_count = producerGeneralDetails.objects.filter(
                forwarded_to=officer.id, status='5'
            ).count()
            rejected_count = producerGeneralDetails.objects.filter(
                forwarded_to=officer.id, status='7'
            ).count()

        return render(request, 'admin/admin_users.html', {
            'users': users,
            'roles': role,
            'fresh_count': fresh_count,
            'resubmit_count': resubmit_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
        })
    except Exception as e:
        logger.info(
            f"Error in view_user | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")
    
    
@cpcb_admin_required
def toggle_user_status(request):
    logger.info("Entering toggle_user_status function")
    try:
        logger.info("Starting try block")
        user_id = request.POST.get("user_id")
        logger.info(f"User ID retrieved from POST: {user_id}")
        
        logger.info(f"Checking if user is admin: {request.user.is_admin if request.user else None}")
        if not request.user.is_admin:
            logger.info("User is not admin - access denied")
            messages.error(request, "Only superadmins can change user status.")
            logger.info("Redirecting to view_user")
            return redirect('view_user')
        logger.info("User is admin - proceeding")

        logger.info(f"Attempting to fetch CpcbUser with id: {user_id}")
        user = get_object_or_404(CpcbUser, id=user_id)
        logger.info(f"User found: {user.username} (ID: {user.id}), current is_active status: {user.is_active}")
        
        logger.info("Toggling user status")
        user.is_active = not user.is_active  # Toggle status
        logger.info(f"New is_active status: {user.is_active}")
        
        logger.info("Saving user changes")
        user.save()
        logger.info("User saved successfully")

        if user.is_active:
            logger.info(f"User {user.username} has been enabled")
            messages.success(request, f"{user.username} has been enabled.")
        else:
            logger.info(f"User {user.username} has been disabled")
            messages.warning(request, f"{user.username} has been disabled.")

        logger.info("Redirecting to view_user")
        return redirect('view_user')
        
    except Exception as e:
        logger.info(f"Error in toggle_user_status | performed_by={request.user.id if request.user else 'anonymous'} | target_user_id={request.POST.get('user_id')} | error={str(e)}")
        logger.info("Redirecting to admin_dashboard due to exception")
        return redirect("admin_dashboard")
# def toggle_user_status(request):
#     try:
#         user_id = request.POST.get("user_id")
#         if not request.user.is_admin:
#             messages.error(request, "Only superadmins can change user status.")
#             return redirect('view_user')

#         user = get_object_or_404(CpcbUser, id=user_id)
#         user.is_active = not user.is_active  # Toggle status
#         user.save()

#         if user.is_active:
#             messages.success(request, f"{user.username} has been enabled.")
#         else:
#             messages.warning(request, f"{user.username} has been disabled.")

#         return redirect('view_user')
#     except Exception as e:
#         logger.info(
#             f"Error in toggle_user_status | performed_by={request.user.id if request.user else 'anonymous'} | target_user_id={request.POST.get('user_id')} | error={str(e)}"
#         )
#         return redirect("admin_dashboard")


@cpcb_admin_required
def cpcb_profile(request):
    try:
        # print("Method:", request.method)        # GET or POST
        # print("GET params:", request.GET)        # Query string
        # print("POST data:", request.POST)        # Form data
        # print("FILES:", request.FILES)           # Uploaded files
        # print("Headers:", request.headers)       # Request headers
        # print("Body:", request.body)
        if request.method == 'POST':
            hid_id = request.POST.get('hidden_id')

            try:
                officer_user = CpcbUser.objects.get(id=hid_id)
            except CpcbUser.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('view_user')

            fresh_count = producerGeneralDetails.objects.filter(
                application_type=0, forwarded_to=request.user.id
            ).count()
            resubmit_count = producerGeneralDetails.objects.filter(
                application_type=1, forwarded_to=request.user.id
            ).count()

            roles = RoleType.objects.all()
            form = CaptchaForm()

            return render(request, 'admin/cpcbprofile.html', {
                'fresh_count': fresh_count,
                'resubmit_count': resubmit_count,
                'roles': roles,
                'form': form,
                'officer_user': officer_user,  # Pass user data to template
            })
    except Exception as e:
        logger.info(
            f"Error in cpcb_profile | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")

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
    
@cpcb_admin_required
def updatecpcbprofile(request):
    try:
        if request.method == 'POST':
            form = CaptchaForm(request.POST)
            if form.is_valid():
                hid_id = request.POST.get('hid_id')

                try:
                    officer = CpcbUser.objects.get(id=hid_id)
                except CpcbUser.DoesNotExist:
                    messages.error(request, "User not found.")
                    return redirect('view_user')

                email = request.POST.get('email')
                mobile = request.POST.get('mobile_no')

                # CHECK EMAIL DUPLICATE (exclude current user)
                if CpcbUser.objects.filter(email=email).exclude(id=hid_id).exists():
                    messages.error(request, "Email already exists.")
                    return redirect('updatecpcbprofile')

                # CHECK MOBILE DUPLICATE (exclude current user)
                if CpcbUser.objects.filter(mobile_no=mobile).exclude(id=hid_id).exists():
                    messages.error(request, "Mobile number already exists.")
                    return redirect('updatecpcbprofile')
                
                officer.first_name = request.POST.get('first_name')
                officer.last_name = request.POST.get('last_name')
                officer.email = request.POST.get('email')
                officer.division = request.POST.get('division')
                officer.mobile_no = request.POST.get('mobile_no')

                officer.save()
                password = generate_password()
                try:
                    sendSignupEmail(officer.first_name, officer.username, request.POST.get('email'), password)
                    officercpcb = CpcbUser.objects.get(id=hid_id)
                    send_signup_sms(officer.mobile_no)
                    messages.success(
                        request,
                        f"Account details updated successfully! Credentials have been sent to {officercpcb.first_name}'s email."
                    )
                except Exception as e:
                    messages.warning(request, f"Account created, but email not sent: {e}")
                messages.success(request, "Officer profile updated successfully.")
            else:
                messages.error(request, "Captcha validation failed.")
                logger.info('wrong captcha')

        return redirect('view_user')
    except Exception as e:
        logger.info(
            f"Error in updatecpcbprofile | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")
# def updatecpcbprofile(request):
#     try:
#         if request.method == 'POST':
#             form = CaptchaForm(request.POST)
#             if form.is_valid():
#                 hid_id = request.POST.get('hid_id')

#                 try:
#                     officer = CpcbUser.objects.get(id=hid_id)
#                 except CpcbUser.DoesNotExist:
#                     messages.error(request, "User not found.")
#                     return redirect('view_user')

#                 officer.first_name = request.POST.get('first_name')
#                 officer.last_name = request.POST.get('last_name')
#                 officer.email = request.POST.get('email')
#                 officer.division = request.POST.get('division')
#                 officer.mobile_no = request.POST.get('mobile_no')

#                 officer.save()
#                 password = generate_password()
#                 try:
#                     sendSignupEmail(officer.first_name, officer.username, request.POST.get('email'), password)
#                     officercpcb = CpcbUser.objects.get(id=hid_id)
#                     send_signup_sms(officer.mobile_no)
#                     messages.success(
#                         request,
#                         f"Account details updated successfully! Credentials have been sent to {officercpcb.first_name}'s email."
#                     )
#                 except Exception as e:
#                     messages.warning(request, f"Account created, but email not sent: {e}")
#                 messages.success(request, "Officer profile updated successfully.")
#             else:
#                 messages.error(request, "Captcha validation failed.")
#                 logger.info('wrong captcha')

#         return redirect('view_user')
#     except Exception as e:
#         logger.info(
#             f"Error in updatecpcbprofile | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
#         )
#         return redirect("admin_dashboard")


def custom_admin_login(request):
    logger.info("Entering custom_admin_login function")
    
    try:
        logger.info("Starting try block")

        # Step 2: OTP verification
        logger.info("Checking if request method is POST and contains 'otp'")
        if request.method == 'POST' and 'otp' in request.POST:
            logger.info("Processing OTP verification step")
            form = ProducerOTPForm(request.POST)
            logger.info("OTP form created")
            
            if form.is_valid():
                logger.info("OTP form is valid")
                enc_otp = request.POST.get('enc_otp')
                logger.info(f"Encrypted OTP retrieved: {enc_otp}")
                
                if not enc_otp:
                    logger.info("No encrypted OTP found")
                    messages.error(request, "Missing encrypted OTP.")
                    logger.info("Rendering admin_otp_verify.html with form")
                    return render(request, 'admin/admin_otp_verify.html', {'form': form})

                logger.info("Decrypting OTP")
                entered_otp = decrypt_aes(enc_otp)
                logger.info(f"Decrypted OTP: {entered_otp}")
                
                if not entered_otp:
                    logger.info("OTP decryption failed")
                    messages.error(request, "OTP decryption failed.")
                    logger.info("Rendering admin_otp_verify.html with form")
                    return render(request, 'admin/admin_otp_verify.html', {'form': form})

                logger.info("Retrieving OTP and user_id from session")
                otp = request.session.get('admin_otp')
                user_id = request.session.get('admin_user_id')
                logger.info(f"Session OTP: {otp}, Session user_id: {user_id}")

                if not otp or not user_id:
                    logger.info("Session expired - missing OTP or user_id")
                    messages.error(request, "Session expired. Please login again.")
                    logger.info("Redirecting to custom_admin_login")
                    return redirect('custom_admin_login')

                logger.info("Comparing entered OTP with session OTP")
                if entered_otp == otp:
                    logger.info("OTP matches successfully")
                    try:
                        logger.info(f"Attempting to fetch CpcbUser with id: {user_id}")
                        user = CpcbUser.objects.get(id=user_id)
                        logger.info(f"User found: {user.username}")
                        
                        # Log the user in using your custom backend
                        # login(request, user, backend='CpcbApp.backends.CpcbUserBackend')
                        #login(request, user)
                        # set_active_session("admin", user.id, request)

                        logger.info("Setting admin user_id and role in session")
                        request.session['admin_user_id'] = user_id
                        request.session['user_role'] = "admin"
                        logger.info("Calling set_active_session")
                        set_active_session("admin", user_id, request)

                        # Clean up OTP session values
                        logger.info("Cleaning up OTP session values")
                        request.session.pop('admin_otp', None)
                        request.session.pop('admin_otp_created_at', None)

                        logger.info(f"Checking user first_login status: {user.first_login}")
                        if user.first_login == 0:
                            logger.info("First login detected - redirecting to change_admin_password_first")
                            return redirect('change_admin_password_first')
                        else:
                            logger.info("Not first login - redirecting to admin_dashboard")
                            return redirect('admin_dashboard')

                    except CpcbUser.DoesNotExist:
                        logger.info("CpcbUser.DoesNotExist exception - user not found")
                        messages.error(request, "Session expired. Please login again.")
                        logger.info("Redirecting to custom_admin_login")
                        return redirect('custom_admin_login')
                else:
                    logger.info(f"OTP mismatch - entered: {entered_otp}, expected: {otp}")
                    messages.error(request, "Invalid OTP.")
                    logger.info("Rendering admin_otp_verify.html with form")
                    return render(request, 'admin/admin_otp_verify.html', {'form': form})
            else:
                logger.info("OTP form is invalid")
                messages.error(request, "Invalid Captcha.")
                logger.info("Rendering admin_otp_verify.html with form")
                return render(request, 'admin/admin_otp_verify.html', {'form': form})

        # Step 1: Username/Password form
        elif request.method == 'POST':
            logger.info("Processing username/password login step")
            form = LoginForm(request.POST)
            logger.info("Login form created")
            
            if form.is_valid():
                logger.info("Login form is valid")
                
                enc_username = request.POST.get('username')
                enc_password = request.POST.get('password')
                logger.info(f"Encrypted username and password retrieved")

                try:
                    logger.info("Decrypting username and password")
                    username = decrypt_aes(enc_username)
                    password = decrypt_aes(enc_password)
                    logger.info(f"Decrypted username: {username}")
                except Exception:
                    logger.info("Exception occurred during decryption")
                    messages.error(request, "Invalid Credentials.")
                    logger.info("Rendering admin_login.html with form")
                    return render(request, 'admin/admin_login.html', {'form': form})

                try:
                    logger.info(f"Attempting to fetch CpcbUser with username: {username}")
                    user = CpcbUser.objects.get(username=username)
                    logger.info(f"User found: {user.username}")
                except CpcbUser.DoesNotExist:
                    logger.info("CpcbUser.DoesNotExist exception - user not found")
                    user = None

                if not user or not user.is_active:
                    logger.info(f"User validation failed - user exists: {bool(user)}, is_active: {user.is_active if user else None}")
                    messages.error(request, "Invalid username or password / account disabled.")
                    logger.info("Rendering admin_login.html with form")
                    return render(request, 'admin/admin_login.html', {'form': form})

                # Check password
                logger.info("Checking password")
                if check_password(password, user.password):
                    logger.info("Password is valid")
                    # Generate OTP
                    logger.info("Setting admin user_id and role in session")
                    request.session['admin_user_id'] = user.id
                    request.session['user_role'] = "admin"
                    
                    logger.info("Generating OTP")
                    otp = str(random.randint(100000, 999999))
                    # otp="123456"
                    logger.info(f"Generated OTP: {otp}")
                    
                    logger.info("Setting OTP in session")
                    request.session['admin_otp'] = otp
                    request.session['admin_otp_created_at'] = datetime.now().isoformat()
                    print(otp)
                    
                    # Send OTP via email and SMS
                    logger.info("Sending OTP email")
                    # sendtitanemail(user.first_name, username, user.email, otp)
                    sendOtpEmail(user.first_name, username, user.email, otp)
                    logger.info("Sending OTP SMS")
                    send_login_otp_sms(user.mobile_no, otp)
                    logger.info("OTP sent successfully")

                    logger.info("Rendering admin_otp_verify.html with ProducerOTPForm")
                    return render(request, 'admin/admin_otp_verify.html', {'form': ProducerOTPForm()})

                else:
                    logger.info("Password validation failed")
                    messages.error(request, "Invalid username or password.")
                    logger.info("Rendering admin_login.html with form")
                    return render(request, 'admin/admin_login.html', {'form': form})

            else:
                logger.info("Login form is invalid")
                messages.error(request, "Invalid Captcha.")
                logger.info("Rendering admin_login.html with form")
                return render(request, 'admin/admin_login.html', {'form': form})

        else:
            logger.info("GET request - displaying login form")
            form = LoginForm()
            logger.info("Rendering admin_login.html with empty form")
            return render(request, 'admin/admin_login.html', {'form': form})
            
    except Exception as e:
        logger.info(f"Error in custom_admin_login | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}")
        logger.info("Redirecting to custom_admin_login due to exception")
        return redirect("custom_admin_login")

# def custom_admin_login(request):
#     try:

#         # Step 2: OTP verification
#         if request.method == 'POST' and 'otp' in request.POST:
#             form = ProducerOTPForm(request.POST)
#             if form.is_valid():
#                 enc_otp = request.POST.get('enc_otp')
#                 if not enc_otp:
#                     messages.error(request, "Missing encrypted OTP.")
#                     return render(request, 'admin/admin_otp_verify.html', {'form': form})

#                 entered_otp = decrypt_aes(enc_otp)
#                 if not entered_otp:
#                     messages.error(request, "OTP decryption failed.")
#                     return render(request, 'admin/admin_otp_verify.html', {'form': form})

#                 otp = request.session.get('admin_otp')
#                 user_id = request.session.get('admin_user_id')

#                 if not otp or not user_id:
#                     messages.error(request, "Session expired. Please login again.")
#                     return redirect('custom_admin_login')

#                 if entered_otp == otp:
#                     try:
#                         user = CpcbUser.objects.get(id=user_id)
                        
#                         # Log the user in using your custom backend
#                         # login(request, user, backend='CpcbApp.backends.CpcbUserBackend')
#                         #login(request, user)
#                         # set_active_session("admin", user.id, request)

#                         request.session['admin_user_id'] = user_id
#                         request.session['user_role'] = "admin"
#                         set_active_session("admin", user_id, request)

#                         # Clean up OTP session values
#                         request.session.pop('admin_otp', None)
#                         request.session.pop('admin_otp_created_at', None)

#                         if user.first_login == 0:
#                             return redirect('change_admin_password_first')
#                         else:
#                             return redirect('admin_dashboard')

#                     except CpcbUser.DoesNotExist:
#                         messages.error(request, "Session expired. Please login again.")
#                         return redirect('custom_admin_login')
#                 else:
#                     messages.error(request, "Invalid OTP.")
#                     return render(request, 'admin/admin_otp_verify.html', {'form': form})
#             else:
#                 messages.error(request, "Invalid Captcha.")
#                 return render(request, 'admin/admin_otp_verify.html', {'form': form})

#         # Step 1: Username/Password form
#         elif request.method == 'POST':
#             form = LoginForm(request.POST)
#             if form.is_valid():

#                 enc_username = request.POST.get('username')
#                 enc_password = request.POST.get('password')

#                 try:
#                     username = decrypt_aes(enc_username)
#                     password = decrypt_aes(enc_password)
#                 except Exception:
#                     messages.error(request, "Invalid Credentials.")
#                     return render(request, 'admin/admin_login.html', {'form': form})

#                 try:
#                     user = CpcbUser.objects.get(username=username)
#                 except CpcbUser.DoesNotExist:
#                     user = None

#                 if not user or not user.is_active:
#                     messages.error(request, "Invalid username or password / account disabled.")
#                     return render(request, 'admin/admin_login.html', {'form': form})

#                 # Check password
#                 if check_password(password, user.password):
#                     # Generate OTP
#                     request.session['admin_user_id'] = user.id
#                     request.session['user_role'] = "admin"
#                     otp = str(random.randint(100000, 999999))
#                     # otp="123456"
#                     request.session['admin_otp'] = otp
#                     request.session['admin_otp_created_at'] = datetime.now().isoformat()
#                     print(otp)
#                     # Send OTP via email and SMS
#                     # sendtitanemail(user.first_name, username, user.email, otp)
#                     sendOtpEmail(user.first_name, username, user.email, otp)
#                     send_login_otp_sms(user.mobile_no, otp)

#                     return render(request, 'admin/admin_otp_verify.html', {'form': ProducerOTPForm()})

#                 else:
#                     messages.error(request, "Invalid username or password.")
#                     return render(request, 'admin/admin_login.html', {'form': form})

#             else:
#                 messages.error(request, "Invalid Captcha.")
#                 return render(request, 'admin/admin_login.html', {'form': form})

#         else:
#             form = LoginForm()
#             return render(request, 'admin/admin_login.html', {'form': form})
#     except Exception as e:
#         logger.info(
#             f"Error in custom_admin_login | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
#         )
#         return redirect("custom_admin_login")


def forget_cpcb_password(request):
    try:
        form = CaptchaForm()  # load captcha for GET
        return render(request, 'admin/forget_cpcb_password.html', {'form': form})
    except Exception as e:
        logger.info(
            f"Error in forget_cpcb_password | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("custom_admin_login")
    

def reset_cpcb_password(request):
    logger.info("Entering reset_cpcb_password function")
    try:
        logger.info("Starting try block")
        """Handle password reset requests with full validation and rate limiting."""
        logger.info("Creating CaptchaForm instance")
        form = CaptchaForm(request.POST or None)
        logger.info(f"Form created with data: {request.POST if request.POST else 'None'}")

        logger.info(f"Checking request method: {request.method}")
        if request.method == 'POST':
            logger.info("Processing POST request")
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            user_ip = get_client_ip(request)
            logger.info(f"Username: {username}, Email: {email}, User IP: {user_ip}")

            # === 1️⃣ Validate inputs ===
            logger.info("Validating inputs")
            if not username or not email:
                logger.info("Username or email missing")
                messages.error(request, "Both username and company email are required.")
                logger.info("Rendering forget_cpcb_password.html with form")
                return render(request, 'admin/forget_cpcb_password.html', {'form': form})

            # === 2️⃣ Validate CAPTCHA ===
            logger.info("Validating CAPTCHA")
            if not form.is_valid():
                logger.info("CAPTCHA validation failed")
                messages.error(request, "Invalid CAPTCHA. Please try again.")
                logger.info("Rendering forget_cpcb_password.html with new CaptchaForm")
                return render(request, 'admin/forget_cpcb_password.html', {'form': CaptchaForm()})
            logger.info("CAPTCHA validation successful")

            # === 3️⃣ Rate Limiting ===
            logger.info("Setting up rate limiting")
            rate_key_user = f"reset_attempts_user_{username}"
            rate_key_ip = f"reset_attempts_ip_{user_ip}"
            logger.info(f"Rate limit keys - User: {rate_key_user}, IP: {rate_key_ip}")

            max_attempts = 3
            block_time = 10  # in minutes
            logger.info(f"Max attempts: {max_attempts}, Block time: {block_time} minutes")

            logger.info("Checking rate limits")
            if is_rate_limited(rate_key_user, max_attempts, block_time) or \
                is_rate_limited(rate_key_ip, max_attempts, block_time):
                logger.info("Rate limit exceeded for user or IP")
                messages.error(request, "Too many attempts. Please try again later.")
                logger.info("Rendering forget_cpcb_password.html with CaptchaForm")
                return render(request, 'admin/forget_cpcb_password.html', {'form': CaptchaForm()})
            logger.info("Rate limits not exceeded")

            # === 4️⃣ Verify username and email ===
            logger.info(f"Verifying username and email: {username}, {email}")
            user = CpcbUser.objects.filter(username=username, email=email).first()
            logger.info(f"User found: {user}")

            if not user:
                logger.info("No user found with provided username and email")
                messages.error(request, "Invalid username or email address.")
                logger.info("Rendering forget_cpcb_password.html with CaptchaForm")
                return render(request, 'admin/forget_cpcb_password.html', {'form': CaptchaForm()})
            logger.info("User verified successfully")

            # === 5️⃣ Send password reset email ===
            logger.info("Sending password reset email")
            success, msg = sendforgetpwdemailcpcb(username, email)
            logger.info(f"Email sending result - Success: {success}, Message: {msg}")
            
            if success:
                logger.info("Password reset email sent successfully")
                messages.success(request, msg)
                logger.info("Redirecting to custom_admin_login")
                return redirect('custom_admin_login')
            else:
                logger.info("Failed to send password reset email")
                messages.error(request, msg)
                logger.info("Rendering forget_cpcb_password.html with CaptchaForm")
                return render(request, 'admin/forget_cpcb_password.html', {'form': CaptchaForm()})

        # GET → show form
        logger.info("GET request - displaying password reset form")
        logger.info("Rendering forget_cpcb_password.html with form")
        return render(request, 'admin/forget_cpcb_password.html', {'form': form})
        
    except Exception as e:
        logger.info(f"Error in reset_cpcb_password | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}")
        logger.info("Redirecting to custom_admin_login due to exception")
        return redirect("custom_admin_login")
# def reset_cpcb_password(request):
#     try:
#         """Handle password reset requests with full validation and rate limiting."""
#         form = CaptchaForm(request.POST or None)

#         if request.method == 'POST':
#             username = request.POST.get('username', '').strip()
#             email = request.POST.get('email', '').strip()
#             user_ip = get_client_ip(request)

#             # === 1️⃣ Validate inputs ===
#             if not username or not email:
#                 messages.error(request, "Both username and company email are required.")
#                 return render(request, 'admin/forget_cpcb_password.html', {'form': form})

#             # === 2️⃣ Validate CAPTCHA ===
#             if not form.is_valid():
#                 messages.error(request, "Invalid CAPTCHA. Please try again.")
#                 return render(request, 'admin/forget_cpcb_password.html', {'form': CaptchaForm()})

#             # === 3️⃣ Rate Limiting ===
#             rate_key_user = f"reset_attempts_user_{username}"
#             rate_key_ip = f"reset_attempts_ip_{user_ip}"

#             max_attempts = 3
#             block_time = 10  # in minutes

#             if is_rate_limited(rate_key_user, max_attempts, block_time) or \
#                 is_rate_limited(rate_key_ip, max_attempts, block_time):
#                 messages.error(request, "Too many attempts. Please try again later.")
#                 return render(request, 'admin/forget_cpcb_password.html', {'form': CaptchaForm()})

#             # === 4️⃣ Verify username and email ===
#             user = CpcbUser.objects.filter(username=username, email=email).first()

#             if not user:
#                 messages.error(request, "Invalid username or email address.")
#                 return render(request, 'admin/forget_cpcb_password.html', {'form': CaptchaForm()})

#             # === 5️⃣ Send password reset email ===
#             success, msg = sendforgetpwdemailcpcb(username, email)
#             if success:
#                 messages.success(request, msg)
#                 return redirect('custom_admin_login')
#             else:
#                 messages.error(request, msg)
#                 return render(request, 'admin/forget_cpcb_password.html', {'form': CaptchaForm()})

#         # GET → show form
#         return render(request, 'admin/forget_cpcb_password.html', {'form': form})
#     except Exception as e:
#         logger.info(
#             f"Error in reset_cpcb_password | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
#         )
#         return redirect("custom_admin_login")
    
@cpcb_admin_required
def admin_profile(request):
    try:
        officer = request.user
        print(officer)
        officer_id = officer.id
        
        if not officer_id:
            return redirect('home')

        userdata = CpcbUser.objects.filter(id=officer_id).first()
        roles = RoleType.objects.all()
        # Build a dictionary: {id: role_name}
        role_dict = {role.id: role.name for role in roles}
        
        fresh_count = producerGeneralDetails.objects.filter(application_type=0, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()
        resubmit_count = producerGeneralDetails.objects.filter(application_type=1, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()

        approved_count=0
        rejected_count=0
        if officer.division=='1':
            approved_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id, status='5').count()
            rejected_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id, status='7').count()

        forwarded_counts = producerGeneralDetails.objects.values('forwarded_to') \
            .annotate(count=Count('id')) \
            .order_by()

        # Convert to a dictionary: {user_id: count}
        forwarded_count_dict = {item['forwarded_to']: item['count'] for item in forwarded_counts}

        return render(request,"admin/admin_profile.html",{'user': userdata, 'fresh_count': fresh_count,
            'resubmit_count': resubmit_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'forwarded_count_dict': forwarded_count_dict,
            'role_dict': role_dict,})
    except Exception as e:
        logger.info(
            f"Error in admin_profile | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")


@cpcb_admin_required
def admin_dashboard(request):
    try:
        officer = request.user  # Comes from our session-based login system
        

        # Fetch all related data
        applicants = Registration.objects.all()
        producers = producerGeneralDetails.objects.all()
        roles = RoleType.objects.all()
        users = CpcbUser.objects.all().order_by('division')

        # Build role dictionary
        role_dict = {role.id: role.name for role in roles}

        # Aggregate producer counts by status
        producer_counts = producerGeneralDetails.objects.aggregate(
            total_active = Count('id', filter=Q(status__gt=0)),
            new_application = Count('id', filter=Q(status=1)),
            under_review = Count('id', filter=Q(status=2)),
            incomplete_application = Count('id', filter=Q(status=3)),
            for_approval = Count('id', filter=Q(status=4)),
            approved_application = Count('id', filter=Q(status=5)),
            granted_application = Count('id', filter=Q(status=6)),
            rejected_application = Count('id', filter=Q(status=7)),
        )

        # Total fees collected
        total_fees = Transaction.objects.filter(was_success=True).aggregate(
            total=Sum('amount_initiated')
        )['total']

        fees_data = Transaction.objects.filter(was_success=True).select_related('owner')

        # Counts for fresh and resubmitted applications
        fresh_count = producerGeneralDetails.objects.filter(
            application_type=0, forwarded_to=request.user.id
        ).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()

        resubmit_count = producerGeneralDetails.objects.filter(
            application_type=1, forwarded_to=request.user.id
        ).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()

        # Approved / Rejected counts for division = 1
        approved_count = rejected_count = 0
        if officer.division == '1':
            approved_count = producerGeneralDetails.objects.filter(
                forwarded_to=request.user.id, status='5'
            ).count()
            rejected_count = producerGeneralDetails.objects.filter(
                forwarded_to=request.user.id, status='7'
            ).count()

        # Forwarded application counts
        forwarded_counts = producerGeneralDetails.objects.values('forwarded_to') \
            .annotate(count=Count('id'))
        forwarded_count_dict = {item['forwarded_to']: item['count'] for item in forwarded_counts}

        # Noting comments grouped by producer
        all_notings = Noting.objects.select_related('producer').order_by('-forwarded_at')
        noting_dict = defaultdict(list)
        for note in all_notings:
            noting_dict[str(note.producer_id)].append(note)

        # Build user dictionary
        user_dict = {}
        for u in users:
            try:
                division_id = int(u.division)
            except (TypeError, ValueError):
                division_id = None

            role_name = role_dict.get(division_id, "User")

            # Safely build name (avoid get_full_name)
            name = f"{(u.first_name or '').strip()} {(u.last_name or '').strip()}".strip()
            if not name:
                name = u.username

            user_dict[u.id] = {
                'name': name,
                'division': u.division,
                'role_name': role_name,
            }
            
        all_transactions=[]
        
        # All successful transactions for the admin dashboard
        all_transactions = Transaction.objects.filter(
            was_success=True
        ).select_related('owner').order_by('-ru_date')

        # Render dashboard
        return render(request, 'admin/admin_dashboard.html', {
            'officer': officer,
            'applicant': applicants,
            'producers': producers,
            'users': users,
            'role_dict': role_dict,
            'fresh_count': fresh_count,
            'resubmit_count': resubmit_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'forwarded_count_dict': forwarded_count_dict,
            'producers_total_active_count': producer_counts['total_active'],
            'producers_new_application_count': producer_counts['new_application'],
            'producers_under_review_count': producer_counts['under_review'],
            'producers_incomplete_application_count': producer_counts['incomplete_application'],
            'producers_for_approval_count': producer_counts['for_approval'],
            'producers_approved_application_count': producer_counts['approved_application'],
            'producers_granted_application_count': producer_counts['granted_application'],
            'producers_rejected_application_count': producer_counts['rejected_application'],
            'noting_dict': dict(noting_dict),
            'user_dict': user_dict,
            'total_fees': total_fees,
            'fees_data': fees_data,
            'all_transactions': all_transactions,
        })
    except Exception as e:
        logger.info(
            f"Error in admin_dashboard | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("custom_admin_login")


@cpcb_admin_required
def all_users(request):
    try:
        users = Registration.objects.all()
        return render(request, 'admin/allusers.html', {'users':users})
    except Exception as e:
        logger.info(
            f"Error in all_users | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("custom_admin_login")
    
@cpcb_admin_required
def admin_producer(request):
    try:
        officer = request.user
        app_type = request.GET.get('type')  
        roles = RoleType.objects.all()
        users = CpcbUser.objects.all()
        
        users = sorted(users, key=lambda officer: officer.division)
        
        role_dict = {role.id: role.name for role in roles}
        # print(request.user.id)
        if app_type == 'resubmit':
            producers = producerGeneralDetails.objects.filter(application_type=1, forwarded_to=request.user.id)
        elif app_type == 'fresh':
            producers = producerGeneralDetails.objects.filter(application_type=0, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).all()
        elif app_type == 'approved':
            noting = producerGeneralDetails.objects.filter(status__in=['5','6']).all()
            producer_ids = noting.values_list('id', flat=True)
            producers = producerGeneralDetails.objects.filter(id__in=producer_ids)
        elif app_type == 'rejected':
            noting = producerGeneralDetails.objects.filter(status='7').all()
            producer_ids = noting.values_list('id', flat=True)
            producers = producerGeneralDetails.objects.filter(id__in=producer_ids)
        elif app_type == 'forwarded':
            noting = Noting.objects.filter(forwarded_from=request.user.id).exclude(forwarded_to = 0).all()
            producer_ids = noting.values_list('producer_id', flat=True)
            producers = producerGeneralDetails.objects.filter(id__in=producer_ids)
        elif app_type == 'sent_back':
            noting = Noting.objects.filter(forwarded_from=request.user.id, forwarded_to=0).all()
            producer_ids = noting.values_list('producer_id', flat=True)
            producers = producerGeneralDetails.objects.filter(id__in=producer_ids)
        
        fresh_count = producerGeneralDetails.objects.filter(application_type=0, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()
        resubmit_count = producerGeneralDetails.objects.filter(application_type=1, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()

        approved_count=0
        rejected_count=0# approved_count=0
        if officer.division=='1':
            approved_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id, status='5').count()
            rejected_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id, status='7').count()
        
        
        all_notings = Noting.objects.select_related('producer').order_by('-forwarded_at')
        noting_dict = defaultdict(list)
        print(noting_dict,'jgsjddjsg')
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
            
        total_fees = Transaction.objects.filter(was_success=True).aggregate(Sum('amount_initiated'))['amount_initiated__sum']
        fees_data = Transaction.objects.filter(was_success=True).select_related('owner')
        
        return render(request, 'admin/all_producers.html', {
            'producers': producers,
            'fresh_count': fresh_count,
            'resubmit_count': resubmit_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'app_type': app_type,
            'officer': officer,
            'noting_dict': noting_dict,
            'user_dict': user_dict,
            'total_fees': total_fees,
            'fees_data' : fees_data,
        })
    except Exception as e:
        logger.info(
            f"Error in admin_producer | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")
    
    
@cpcb_admin_required
def producer_detail(request):
    logger.info("Entering producer_detail function")
    try:
        logger.info("Starting try block")
        officer = request.user
        logger.info(f"Officer assigned: {officer}")
        # producer_id = request.POST.get("producer_id")
        encrypted_id = request.POST.get("producer_id")
        logger.info(f"Encrypted ID retrieved: {encrypted_id}")
        # print(encrypted_id)

        try:
            logger.info("Attempting to decrypt producer_id")
            producer_id = signing.loads(encrypted_id)
            logger.info(f"Successfully decrypted producer_id: {producer_id}")
        except signing.BadSignature:
            logger.info("BadSignature exception caught - invalid or tampered producer ID")
            return HttpResponseBadRequest("Invalid or tampered producer ID")
        
        logger.info("Counting fresh applications")
        fresh_count = producerGeneralDetails.objects.filter(application_type=0, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()
        logger.info(f"Fresh count: {fresh_count}")
        
        logger.info("Counting resubmit applications")
        resubmit_count = producerGeneralDetails.objects.filter(application_type=1, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()
        logger.info(f"Resubmit count: {resubmit_count}")

        approved_count=0
        rejected_count=0
        logger.info(f"Initialized approved_count={approved_count}, rejected_count={rejected_count}")
        
        logger.info(f"Checking officer division: {officer.division}")
        if officer.division=='1':
            logger.info("Officer division is 1, counting approved and rejected")
            approved_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id, status='5').count()
            rejected_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id, status='7').count()
            logger.info(f"Approved count: {approved_count}, Rejected count: {rejected_count}")
        
        section_fields = {
            'sign_up_details': [
                'producer_name_address', 'company_email', 'upload_gst_certificate', 'year_of_incorporation',
                'pan_card_uploaded','tin_certificate_uploaded', 'cin_certificate_uploaded', 'iec_certificate_uploaded',
                'authorized_person_details', 'authorized_person_pan_details'
            ],
            'manufacturing_facility': [
                'nature_of_business', 'name_address_facility', 'activity_type', 'capacity_of_facility'
            ],
            'transport_vehicles': [
                'data_transport', 'fy_data_transport', 'vehicle_data_transport', 'manufactured_data_transport',
                'open_market_sales_data_transport', 'other_producer_sales_data_transport', 'cobranding_sales_data_transport',
                'uploaded_excel_other_producer_standard_format_transport', 'self_use_transport', 'exported_vehicles_transport',
                'uploaded_ca_certificates_each_fy_transport'
            ],
            'non_transport_vehicles': [
                'data_non_transport', 'fy_data_non_transport', 'vehicle_data_non_transport', 'manufactured_data_non_transport',
                'open_market_sales_data_non_transport', 'other_producer_sales_data_non_transport', 'cobranding_sales_data_non_transport',
                'uploaded_excel_standard_format_non_transport', 'self_use_non_transport', 'exported_vehicles_non_transport',
                'uploaded_ca_certificates_each_fy_non_transport'
            ],
            'annual_turnover': [
                'provided_annual_turnover_both_fy', 'uploaded_ca_certificate_each_fy', 'uploaded_undertaking'
                
            ],
            'registration_fee': [
                'reg_fee',
                
            ]
        }
        logger.info("Section fields defined")

        logger.info(f"Fetching general details for producer_id: {producer_id}")
        general_details = get_object_or_404(producerGeneralDetails, id=producer_id)
        logger.info(f"General details retrieved for GST: {general_details.gst_no}")
        
        logger.info(f"Fetching Registration data for GST: {general_details.gst_no}")
        userdata = Registration.objects.get(gst_no=general_details.gst_no)
        logger.info(f"Registration data retrieved for user: {userdata}")
        
        state_name = ''
        district_name = ''
        logger.info(f"Initialized state_name='{state_name}', district_name='{district_name}'")

        logger.info("Processing state and district information")
        if userdata:
            logger.info("userdata exists")
            if userdata.state:
                logger.info(f"Fetching state for state_id: {userdata.state}")
                state_obj = State.objects.filter(state_id=userdata.state).first()
                if state_obj:
                    state_name = state_obj.state_name
                    logger.info(f"State name found: {state_name}")
                else:
                    logger.info("No state object found")
            else:
                logger.info("userdata.state is None or empty")

            if userdata.district:
                logger.info(f"Fetching district for district_id: {userdata.district}")
                district_obj = District.objects.filter(city_id=userdata.district).first()
                if district_obj:
                    district_name = district_obj.city_name
                    logger.info(f"District name found: {district_name}")
                else:
                    logger.info("No district object found")
            else:
                logger.info("userdata.district is None or empty")
        else:
            logger.info("userdata is None")
        # print(general_details.gst_no)
        
        logger.info("Fetching manufacturing details")
        # Use .filter().first() to avoid exceptions if no record found
        manufacturing_details = ManufacturingDetails.objects.filter(producer_id=producer_id).first()
        logger.info(f"Manufacturing details retrieved: {manufacturing_details}")
        
        logger.info("Processing nature_selected")
        # Handle nature_selected safely
        nature_selected = []
        if manufacturing_details and manufacturing_details.nature_of_business:
            nature_selected = manufacturing_details.nature_of_business.split(",")
            logger.info(f"Nature selected: {nature_selected}")
        else:
            logger.info("No nature_of_business found")
        
        logger.info("Fetching manufacturing facility details")
        facilities = ManufacturingFacilityDetails.objects.filter(producer_id=producer_id)
        logger.info(f"Found {facilities.count()} facilities")
        
        for facility in facilities:
            logger.info(f"Processing facility - fetching state for state_id: {facility.state}")
            state_obj = State.objects.filter(state_id=facility.state).first()
            facility.state_name = state_obj.state_name if state_obj else ''
            logger.info(f"Facility state_name set to: {facility.state_name}")
        
        logger.info("Fetching vehicle data")
        vehicle_data = ProducerSalesData.objects.filter(producer_id=producer_id)
        logger.info(f"Vehicle data count: {vehicle_data.count()}")
        
        logger.info("Fetching vehicle financial year data")
        vehicle_fy_data = ProducerSalesSummary.objects.filter(producer_id=producer_id)
        logger.info(f"Vehicle FY data count: {vehicle_fy_data.count()}")

        logger.info("Initializing grouped_data and metadata structures")
        grouped_data = {
            'non_transport': defaultdict(lambda: defaultdict(list)),
            'transport': defaultdict(lambda: defaultdict(list)),
        }
        
        # Store extra metadata like epr_target and ca_certificate
        metadata = {
            'non_transport': defaultdict(dict),
            'transport': defaultdict(dict),
        }
        logger.info("Starting to process vehicle_fy_data")
        
        for fy_item in vehicle_fy_data:
            logger.info(f"Processing FY item: {fy_item}")
            categories = fy_item.category.split(',') if isinstance(fy_item.category, str) else fy_item.category
            year = fy_item.financial_year  # assuming field is named financial_year
            epr_target = fy_item.total_epr_target
            ca_certificate = fy_item.ca_certificate
            logger.info(f"Categories: {categories}, Year: {year}, EPR Target: {epr_target}")
            
            for cat in categories:
                cat = cat.strip()
                logger.info(f"Processing category: {cat}")
                if cat in grouped_data:
                    logger.info(f"Category {cat} found in grouped_data")
                    # Save epr_target and ca_certificate once per category + year
                    metadata[cat][year] = {
                        'epr_target': epr_target,
                        'ca_certificate': ca_certificate
                    }
                    logger.info(f"Metadata saved for {cat} - {year}")
                    # Filter vehicle_data by matching category and financial year
                    matching_vehicles = vehicle_data.filter(category=cat, financial_year=year.split('-')[0].strip())
                    logger.info(f"Found {matching_vehicles.count()} matching vehicles")

                    for vehicle in matching_vehicles:
                        vehicle_type = vehicle.vehicle_type
                        logger.info(f"Processing vehicle type: {vehicle_type}")
                        grouped_data[cat][year][vehicle_type].append({
                            # 'vehicle_type': vehicle.vehicle_type,
                            'no_of_vehicles_manufactured': vehicle.no_of_vehicles_manufactured,
                            'no_of_vehicles_imported': vehicle.no_of_vehicles_imported,
                            'no_of_vehicles_procurred_domestically': vehicle.no_of_vehicles_procurred_domestically,
                            'open_market_vehicles': vehicle.open_market_vehicles,
                            'open_market_vehicle_weight': vehicle.open_market_vehicle_weight,
                            'open_market_steel_weight': vehicle.open_market_steel_weight,
                            'open_market_brand_name': vehicle.open_market_brand_name,
                            'producer_vehicles': vehicle.producer_vehicles,
                            'producer_vehicle_weight': vehicle.producer_vehicle_weight,
                            'producer_steel_weight': vehicle.producer_steel_weight,
                            'producer_sale_file': vehicle.producer_sale_file,
                            'cobranded_vehicles': vehicle.cobranded_vehicles,
                            'cobranded_vehicle_weight': vehicle.cobranded_vehicle_weight,
                            'cobranded_steel_weight': vehicle.cobranded_steel_weight,
                            'cobranded_brand_name': vehicle.cobranded_brand_name,
                            'cobranded_partner_file': vehicle.cobranded_partner_file,
                            'selfuse_vehicles': vehicle.selfuse_vehicles,
                            'selfuse_vehicle_weight': vehicle.selfuse_vehicle_weight,
                            'selfuse_steel_weight': vehicle.selfuse_steel_weight,
                            'export_vehicles': vehicle.export_vehicles,
                            'vehicle_number_qty': vehicle.vehicle_number_qty,
                            'vehicle_weight_qty': vehicle.vehicle_weight_qty,
                            'epr_qty': vehicle.epr_qty,
                            'epr_target': vehicle.epr_target,
                            # 'category': vehicle.category,
                            # 'financial_year': vehicle.financial_year,
                            # 'producer_id': vehicle.producer_id,
                        })
                        logger.info(f"Vehicle data appended for {vehicle_type}")
                else:
                    logger.info(f"Category {cat} not found in grouped_data")
        
        logger.info("Converting defaultdict to dict for grouped_data")
        grouped_data['non_transport'] = convert_defaultdict_to_dict(grouped_data['non_transport'])
        grouped_data['transport'] = convert_defaultdict_to_dict(grouped_data['transport'])
        metadata['non_transport'] = convert_defaultdict_to_dict(metadata['non_transport'])
        metadata['transport'] = convert_defaultdict_to_dict(metadata['transport'])
        logger.info("Conversion completed")
        
        # print(json.dumps(grouped_data, indent=4, default=lambda o: dict(o)))
        logger.info("Fetching ProducerDeclaration")
        declaration = ProducerDeclaration.objects.filter(producer_id=producer_id).first()
        logger.info(f"Declaration retrieved: {declaration}")
        
        logger.info("Fetching reporting officers")
        reporting_officers = CpcbUser.objects.filter(division__in=[2, 4, 5],is_active=1)
        reporting_officers = sorted(reporting_officers, key=lambda officer: officer.division)
        logger.info(f"Reporting officers count: {len(reporting_officers)}")
        
        logger.info("Fetching RoleType objects")
        roles = RoleType.objects.all()
        role_dict = {role.id: role.name for role in roles}
        logger.info(f"Role dictionary created with {len(role_dict)} entries")
        
        logger.info("Fetching noting comments")
        # Fetch and group noting comments by producer_id
        all_notings = Noting.objects.select_related('producer').order_by('-forwarded_at')
        noting_dict = defaultdict(list)
        for note in all_notings:
            # noting_dict[note.producer_id].append(note)
            noting_dict[str(note.producer_id)].append(note)
        logger.info(f"Noting dictionary created with {len(noting_dict)} entries")
        
        logger.info("Fetching all CPCB users")
        users = CpcbUser.objects.all()
        # users = CpcbUser.objects.exclude(division_isnull=True).exclude(division_exact='')
        # Sort by division field, assuming division is an integer or string
        users = sorted(users, key=lambda officer: officer.division)
        logger.info(f"Total users found: {len(users)}")
        
        user_dict = {}
        for u in users:
            logger.info(f"Processing user: {u.id}")
            logger.info(type(u.division))
            try:
                division_id = int(u.division)
                logger.info(f"User division ID: {division_id}")
            except (TypeError, ValueError):
                division_id = None
                logger.info(f"Error converting division for user {u.id}")

            role_name = role_dict.get(u.division, "User")
            logger.info(f"Role name for user {u.id}: {role_name}")

            # user_dict[u.id] = {
            #     'name': u.get_full_name() or u.username,
            #     'division': u.division,
            #     'role_name': role_name,
            # }
            
            name = f"{(u.first_name or '').strip()} {(u.last_name or '').strip()}".strip()
            if not name:
                name = u.username
                logger.info(f"Using username for user {u.id}")
            else:
                logger.info(f"Using full name for user {u.id}: {name}")

            user_dict[u.id] = {
                'name': name,
                'division': u.division,
                'role_name': role_name,
            }
            logger.info(f"User {u.id} added to user_dict")
        
        logger.info("Creating ChecklistForm and NotingForm instances")
        form = ChecklistForm()
        noting_form = NotingForm()
        logger.info("Forms created")
        
        logger.info(f"Fetching Checklist for producer_id: {producer_id}")
        checklist_obj = Checklist.objects.filter(producer_id=producer_id).first()
        checklist_data = {}
        logger.info(f"Checklist object found: {checklist_obj}")

        if checklist_obj:
            logger.info("Processing existing checklist object")
            for field in checklist_obj._meta.fields:
                field_name = field.name
                if field_name.startswith('remarks_') or field_name in section_fields.get('sign_up_details', []) + \
                    section_fields.get('manufacturing_facility', []) + \
                    section_fields.get('transport_vehicles', []) + \
                    section_fields.get('non_transport_vehicles', []) + \
                    section_fields.get('annual_turnover', []) + \
                    section_fields.get('registration_fee', []):

                    checklist_data[field_name] = getattr(checklist_obj, field_name)
                    logger.info(f"Added field {field_name} to checklist_data")
        else:
            logger.info("No existing checklist object found")
        
        logger.info(f"Checking request method: {request.method}")
        if request.method == 'POST':
            logger.info("Processing POST request")
            if 'save_checklist' in request.POST:
                logger.info("Processing save_checklist action")
                # -------- Handle Save Checklist --------
                form = ChecklistForm(request.POST)
                if form.is_valid():
                    logger.info("ChecklistForm is valid")
                    data = form.cleaned_data
                    data['producer'] = producer_id
                    save_form = SaveChecklistForm(data)
                    if save_form.is_valid():
                        logger.info("SaveChecklistForm is valid")
                        checklist_data = save_form.cleaned_data
                        Checklist.objects.update_or_create(
                            producer_id=producer_id,
                            defaults=checklist_data
                        )
                        logger.info("Checklist saved/updated from Save button")
                        print("Checklist saved/updated from Save button")
                    else:
                        logger.info(f"Save form errors: {save_form.errors}")
                        print("Save form errors:", save_form.errors)
                else:
                    logger.info(f"Checklist form errors: {form.errors}")
                    print("Checklist form errors:", form.errors)

            elif 'submit_noting' in request.POST:
                logger.info("Processing submit_noting action")
                
                form = ChecklistForm(request.POST)
                checklist = Checklist.objects.filter(producer_id=producer_id).first()
                logger.info(f"Checklist found: {checklist}")

                # Save checklist only if not already saved
                # if form.is_valid():
                if not checklist and form.is_valid():
                    logger.info("No checklist found and form is valid - creating new checklist")
                    data = form.cleaned_data
                    data['producer'] = producer_id
                    save_form = SaveChecklistForm(data)
                    if save_form.is_valid():
                        logger.info("SaveChecklistForm is valid")
                        print("save")
                        checklist_data = save_form.cleaned_data
                        checklist, _ = Checklist.objects.update_or_create(
                            producer_id=producer_id,
                            defaults=checklist_data
                        )
                        logger.info(f"Checklist created/updated with ID: {checklist.id if checklist else None}")
                    else:
                        logger.info(f"Save form errors: {save_form.errors}")
                        print("Save form errors:", save_form.errors)
                else:
                    if checklist:
                        logger.info("Checklist already exists")
                    else:
                        logger.info(f"Checklist form errors: {form.errors}")
                    print("Checklist form errors:", form.errors)
                # Handle noting submit
                noting_form = NotingForm(request.POST)
                if noting_form.is_valid():
                    logger.info("NotingForm is valid")
                    
                    noting = noting_form.save(commit=False)
                    noting.producer_id = producer_id
                    noting.last_updated_by = request.user.id
                    noting.forwarded_from = request.user.id  # or some logic to determine origin
                    logger.info(f"Noting object prepared: forwarded_from={noting.forwarded_from}")

                    # Process forwarded_to
                    forwarded_to = request.POST.get('forwarded_to')
                    logger.info(f"Forwarded to value: {forwarded_to}")
                    if forwarded_to == 'officers':
                        officer_id = request.POST.get('division')
                        logger.info(f"Forwarding to officer with ID: {officer_id}")
                        if officer_id:
                            noting.forwarded_to = officer_id
                            general_details.forwarded_to = officer_id
                            general_details.status = 2
                            logger.info(f"Updated general_details: forwarded_to={officer_id}, status=2")
                            
                    elif forwarded_to == 'user':
                        logger.info("Forwarding to user")
                        noting.forwarded_to = 0  # or set to appropriate user/group
                        # general_details.forwarded_to = producer_id
                        general_details.forwarded_to = 0
                        general_details.status = 3
                        userdata.status = 3
                        logger.info("Sending query SMS")
                        send_query_sms(general_details.authorized_person_mobile)
                        logger.info(f"Updated: general_details forwarded_to=0 status=3, userdata status=3")
                        
                    elif forwarded_to == 'dh':
                        logger.info("Forwarding to DH")
                        dh_id = CpcbUser.objects.filter(division='2').first()
                        noting.forwarded_to = dh_id.id  # or set to appropriate user/group
                        general_details.forwarded_to = dh_id.id
                        logger.info(f"Forwarded to DH ID: {dh_id.id if dh_id else None}")

                        
                    elif forwarded_to == 'ms_cpcb':
                        logger.info("Forwarding to MS CPCB")
                        ms_id = CpcbUser.objects.filter(division='1').first()
                        noting.forwarded_to = ms_id.id  # or set to appropriate user/group
                        general_details.forwarded_to = ms_id.id
                        general_details.status = 4
                        # userdata.status = 4
                        logger.info(f"Forwarded to MS ID: {ms_id.id if ms_id else None}, status set to 4")

        
                    # checklist = Checklist.objects.filter(producer_id=producer_id).first()
                    if not checklist:
                        logger.info("No checklist found - creating new one")
                        # Create new Checklist if not found
                        checklist = Checklist.objects.create(producer_id=producer_id)
                        logger.info(f"New checklist created with ID: {checklist.id}")

                    # Link checklist to noting and save
                    noting.checklist_id = checklist.id
                    noting.save()
                    logger.info(f"Noting saved with ID: {noting.id}")
                    
                    general_details.save()
                    logger.info("General details saved")
                    
                    userdata.save()
                    logger.info("Userdata saved")
                    
                    # whatsapp api send message through whatsapp
                    logger.info("Preparing WhatsApp message")
                    from_name = CpcbUser.objects.filter(id=noting.forwarded_from).first()
                    to_name = CpcbUser.objects.filter(id=noting.forwarded_to).first()
                    logger.info(f"From: {from_name.first_name if from_name else None}, To: {to_name.first_name if to_name else None}")
                    # print(from_name)
                    # print(from_name.first_name)
                    
                    # frwd_application(to_name.mobile_no,from_name.first_name, to_name.first_name)
                    logger.info("WhatsApp message sent")
                    
                    logger.info("Redirecting to admin_dashboard")
                    return redirect('admin_dashboard')
                else:
                    logger.info(f"Noting form errors: {noting_form.errors}")
                    print("Noting form errors:", noting_form.errors)


            elif 'approved' in request.POST:
                logger.info("Processing approved action")
                print("ok")
                general_details.status = 5  # Approved
                # userdata.status = 5
                general_details.save()
                logger.info(f"General details status updated to 5 (Approved)")
                userdata.save()
                logger.info("Userdata saved")
                logger.info("Redirecting to admin_dashboard")
                return redirect('admin_dashboard')

            elif 'rejected' in request.POST:
                logger.info("Processing rejected action")
                print("notok")
                general_details.status = 7  # Rejected
                userdata.status = 7
                general_details.save()
                logger.info(f"General details status updated to 7 (Rejected)")
                userdata.save()
                logger.info("Userdata saved")
                logger.info("Redirecting to admin_dashboard")
                return redirect('admin_dashboard')
        
        logger.info("Calculating registration fee")
        registration_fee = 0
        
        try:
            logger.info("Processing declaration for fee calculation")
            if declaration:
                logger.info("Declaration exists")
                turnover_23_24 = declaration.turnover_23_24 if declaration.turnover_23_24 else 0
                turnover_24_25 = declaration.turnover_24_25 if declaration.turnover_24_25 else 0
                logger.info(f"Turnover 23-24: {turnover_23_24}, Turnover 24-25: {turnover_24_25}")

                # print(turnover_23_24)
                # print(turnover_24_25)

                total_turnover = turnover_23_24 + turnover_24_25
                logger.info(f"Total turnover: {total_turnover}")
                # print(total_turnover)

                average_turnover = total_turnover / 2
                logger.info(f"Average turnover: {average_turnover}")

                # Find the matching fee slab
                fee_record = ProducerRegistrationFee.objects.filter(
                    models.Q(min_turnover__lte=average_turnover) | models.Q(min_turnover__isnull=True)
                ).filter(
                    models.Q(max_turnover__gte=average_turnover) | models.Q(max_turnover__isnull=True)
                ).first()
                logger.info(f"Fee record found: {fee_record}")

                if fee_record:
                    registration_fee = fee_record.registration_fee
                    logger.info(f"Registration fee set to: {registration_fee}")
                else:
                    registration_fee = 0  # fallback if no matching fee slab found
                    logger.info("No matching fee record found - registration fee set to 0")

            else:
                # Handle case when declaration is None
                logger.info("No declaration found")
                print("No declaration found")
                turnover_23_24 = 0
                turnover_24_25 = 0
                total_turnover = 0
                average_turnover = 0
                registration_fee = 0
                logger.info("All turnover values set to 0")

        except Exception as e:
            logger.info(f"Error while processing declaration: {e}")
            print(f"Error while processing declaration: {e}")
            turnover_23_24 = turnover_24_25 = total_turnover = average_turnover = registration_fee = 0
            logger.info("All values reset to 0 due to exception")

        # producer_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id).count
        logger.info("Fetching producer fees and RVSF fees")
        producer_fees = ProducerRegistrationFee.objects.all()
        rvsf_fees = RVSFRegistrationFee.objects.all()
        logger.info(f"Producer fees count: {producer_fees.count()}, RVSF fees count: {rvsf_fees.count()}")
        
        all_transactions=[]
        logger.info("Fetching transactions")
        
        all_transactions = Transaction.objects.filter(
                    owner_id=producer_id, 
                    status="success"
                ).order_by('-ru_date')
        logger.info(f"Transactions found: {all_transactions.count()}")
        
        logger.info("Rendering admin_producer.html template")
        return render(
            request,
            'admin/admin_producer.html',
            {
                'officer': officer,
                'user': userdata,
                'state_name': state_name,
                'district_name': district_name,
                'general': general_details,
                'manufacturing_details': manufacturing_details,
                'facilities': facilities,
                'nature_selected': nature_selected,
                'reporting_officers': reporting_officers,
                'role_dict': role_dict,
                'form': form,
                'noting_form': noting_form,
                'vehicle_data': vehicle_data,
                'grouped_data': grouped_data,
                'metadata': metadata,
                'declaration': declaration,
                'total_turnover': total_turnover,
                'average_turnover' : average_turnover,
                'registration_fee': registration_fee,
                'producer_fees': producer_fees,
                'rvsf_fees': rvsf_fees,
                'section_fields': section_fields,
                'checklist': checklist_data,
                'fresh_count': fresh_count,
                'resubmit_count': resubmit_count,
                'approved_count': approved_count,
                'rejected_count': rejected_count,
                'noting_dict': dict(noting_dict),
                'user_dict': user_dict,
                'all_transactions': all_transactions,
                # 'producer_count': producer_count,
            }
        )
        logger.info("Template rendered successfully")
    except Exception as e:
        logger.info(f"Error in producer_detail | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}")
        logger.info("Redirecting to admin_dashboard due to exception")
        return redirect("admin_dashboard")
# def producer_detail(request):
#     try:
#         officer = request.user
#         # producer_id = request.POST.get("producer_id")
#         encrypted_id = request.POST.get("producer_id")
#         # print(encrypted_id)

#         try:
#             producer_id = signing.loads(encrypted_id)
#         except signing.BadSignature:
#             return HttpResponseBadRequest("Invalid or tampered producer ID")
        
#         fresh_count = producerGeneralDetails.objects.filter(application_type=0, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()
#         resubmit_count = producerGeneralDetails.objects.filter(application_type=1, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()

#         approved_count=0
#         rejected_count=0
#         if officer.division=='1':
#             approved_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id, status='5').count()
#             rejected_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id, status='7').count()
        
#         section_fields = {
#             'sign_up_details': [
#                 'producer_name_address', 'company_email', 'upload_gst_certificate', 'year_of_incorporation',
#                 'pan_card_uploaded','tin_certificate_uploaded', 'cin_certificate_uploaded', 'iec_certificate_uploaded',
#                 'authorized_person_details', 'authorized_person_pan_details'
#             ],
#             'manufacturing_facility': [
#                 'nature_of_business', 'name_address_facility', 'activity_type', 'capacity_of_facility'
#             ],
#             'transport_vehicles': [
#                 'data_transport', 'fy_data_transport', 'vehicle_data_transport', 'manufactured_data_transport',
#                 'open_market_sales_data_transport', 'other_producer_sales_data_transport', 'cobranding_sales_data_transport',
#                 'uploaded_excel_other_producer_standard_format_transport', 'self_use_transport', 'exported_vehicles_transport',
#                 'uploaded_ca_certificates_each_fy_transport'
#             ],
#             'non_transport_vehicles': [
#                 'data_non_transport', 'fy_data_non_transport', 'vehicle_data_non_transport', 'manufactured_data_non_transport',
#                 'open_market_sales_data_non_transport', 'other_producer_sales_data_non_transport', 'cobranding_sales_data_non_transport',
#                 'uploaded_excel_standard_format_non_transport', 'self_use_non_transport', 'exported_vehicles_non_transport',
#                 'uploaded_ca_certificates_each_fy_non_transport'
#             ],
#             'annual_turnover': [
#                 'provided_annual_turnover_both_fy', 'uploaded_ca_certificate_each_fy', 'uploaded_undertaking'
                
#             ],
#             'registration_fee': [
#                 'reg_fee',
                
#             ]
#         }

#         general_details = get_object_or_404(producerGeneralDetails, id=producer_id)
#         userdata = Registration.objects.get(gst_no=general_details.gst_no)
#         state_name = ''
#         district_name = ''

#         if userdata:
#             if userdata.state:
#                 state_obj = State.objects.filter(state_id=userdata.state).first()
#                 if state_obj:
#                     state_name = state_obj.state_name

#             if userdata.district:
#                 district_obj = District.objects.filter(city_id=userdata.district).first()
#                 if district_obj:
#                     district_name = district_obj.city_name
#         # print(general_details.gst_no)
        
#         # Use .filter().first() to avoid exceptions if no record found
#         manufacturing_details = ManufacturingDetails.objects.filter(producer_id=producer_id).first()
        
#         # Handle nature_selected safely
#         nature_selected = []
#         if manufacturing_details and manufacturing_details.nature_of_business:
#             nature_selected = manufacturing_details.nature_of_business.split(",")
        
#         facilities = ManufacturingFacilityDetails.objects.filter(producer_id=producer_id)
#         for facility in facilities:
#             state_obj = State.objects.filter(state_id=facility.state).first()
#             facility.state_name = state_obj.state_name if state_obj else ''
        
        
#         vehicle_data = ProducerSalesData.objects.filter(producer_id=producer_id)
#         vehicle_fy_data = ProducerSalesSummary.objects.filter(producer_id=producer_id)

#         grouped_data = {
#             'non_transport': defaultdict(lambda: defaultdict(list)),
#             'transport': defaultdict(lambda: defaultdict(list)),
#         }
        
#         # Store extra metadata like epr_target and ca_certificate
#         metadata = {
#             'non_transport': defaultdict(dict),
#             'transport': defaultdict(dict),
#         }

#         for fy_item in vehicle_fy_data:
            
#             categories = fy_item.category.split(',') if isinstance(fy_item.category, str) else fy_item.category
#             year = fy_item.financial_year  # assuming field is named financial_year
#             epr_target = fy_item.total_epr_target
#             ca_certificate = fy_item.ca_certificate
            
#             for cat in categories:
#                 cat = cat.strip()
#                 if cat in grouped_data:
#                     # Save epr_target and ca_certificate once per category + year
#                     metadata[cat][year] = {
#                         'epr_target': epr_target,
#                         'ca_certificate': ca_certificate
#                     }
#                     # Filter vehicle_data by matching category and financial year
#                     matching_vehicles = vehicle_data.filter(category=cat, financial_year=year.split('-')[0].strip())

#                     for vehicle in matching_vehicles:
#                         vehicle_type = vehicle.vehicle_type
#                         grouped_data[cat][year][vehicle_type].append({
#                             # 'vehicle_type': vehicle.vehicle_type,
#                             'no_of_vehicles_manufactured': vehicle.no_of_vehicles_manufactured,
#                             'no_of_vehicles_imported': vehicle.no_of_vehicles_imported,
#                             'no_of_vehicles_procurred_domestically': vehicle.no_of_vehicles_procurred_domestically,
#                             'open_market_vehicles': vehicle.open_market_vehicles,
#                             'open_market_vehicle_weight': vehicle.open_market_vehicle_weight,
#                             'open_market_steel_weight': vehicle.open_market_steel_weight,
#                             'open_market_brand_name': vehicle.open_market_brand_name,
#                             'producer_vehicles': vehicle.producer_vehicles,
#                             'producer_vehicle_weight': vehicle.producer_vehicle_weight,
#                             'producer_steel_weight': vehicle.producer_steel_weight,
#                             'producer_sale_file': vehicle.producer_sale_file,
#                             'cobranded_vehicles': vehicle.cobranded_vehicles,
#                             'cobranded_vehicle_weight': vehicle.cobranded_vehicle_weight,
#                             'cobranded_steel_weight': vehicle.cobranded_steel_weight,
#                             'cobranded_brand_name': vehicle.cobranded_brand_name,
#                             'cobranded_partner_file': vehicle.cobranded_partner_file,
#                             'selfuse_vehicles': vehicle.selfuse_vehicles,
#                             'selfuse_vehicle_weight': vehicle.selfuse_vehicle_weight,
#                             'selfuse_steel_weight': vehicle.selfuse_steel_weight,
#                             'export_vehicles': vehicle.export_vehicles,
#                             'vehicle_number_qty': vehicle.vehicle_number_qty,
#                             'vehicle_weight_qty': vehicle.vehicle_weight_qty,
#                             'epr_qty': vehicle.epr_qty,
#                             'epr_target': vehicle.epr_target,
#                             # 'category': vehicle.category,
#                             # 'financial_year': vehicle.financial_year,
#                             # 'producer_id': vehicle.producer_id,
#                         })
        
#         grouped_data['non_transport'] = convert_defaultdict_to_dict(grouped_data['non_transport'])
#         grouped_data['transport'] = convert_defaultdict_to_dict(grouped_data['transport'])
#         metadata['non_transport'] = convert_defaultdict_to_dict(metadata['non_transport'])
#         metadata['transport'] = convert_defaultdict_to_dict(metadata['transport'])
        
#         # print(json.dumps(grouped_data, indent=4, default=lambda o: dict(o)))
#         declaration = ProducerDeclaration.objects.filter(producer_id=producer_id).first()
        
        
        
#         reporting_officers = CpcbUser.objects.filter(division__in=[2, 4, 5],is_active=1)
#         reporting_officers = sorted(reporting_officers, key=lambda officer: officer.division)
        
        
#         roles = RoleType.objects.all()
#         role_dict = {role.id: role.name for role in roles}
        
        
#         # Fetch and group noting comments by producer_id
#         all_notings = Noting.objects.select_related('producer').order_by('-forwarded_at')
#         noting_dict = defaultdict(list)
#         for note in all_notings:
#             # noting_dict[note.producer_id].append(note)
#             noting_dict[str(note.producer_id)].append(note)
            
#         users = CpcbUser.objects.all()
#         # Sort by division field, assuming division is an integer or string
#         users = sorted(users, key=lambda officer: officer.division)
        
#         user_dict = {}
#         for u in users:
#             try:
#                 division_id = int(u.division)
#             except (TypeError, ValueError):
#                 division_id = None

#             role_name = role_dict.get(division_id, "User")

#             # user_dict[u.id] = {
#             #     'name': u.get_full_name() or u.username,
#             #     'division': u.division,
#             #     'role_name': role_name,
#             # }
            
#             name = f"{(u.first_name or '').strip()} {(u.last_name or '').strip()}".strip()
#             if not name:
#                 name = u.username

#             user_dict[u.id] = {
#                 'name': name,
#                 'division': u.division,
#                 'role_name': role_name,
#             }
        
        
#         form = ChecklistForm()
#         noting_form = NotingForm()
        
#         checklist_obj = Checklist.objects.filter(producer_id=producer_id).first()
#         checklist_data = {}

#         if checklist_obj:
#             for field in checklist_obj._meta.fields:
#                 field_name = field.name
#                 if field_name.startswith('remarks_') or field_name in section_fields.get('sign_up_details', []) + \
#                     section_fields.get('manufacturing_facility', []) + \
#                     section_fields.get('transport_vehicles', []) + \
#                     section_fields.get('non_transport_vehicles', []) + \
#                     section_fields.get('annual_turnover', []) + \
#                     section_fields.get('registration_fee', []):

#                     checklist_data[field_name] = getattr(checklist_obj, field_name)

        
#         if request.method == 'POST':
#             if 'save_checklist' in request.POST:
#                 # -------- Handle Save Checklist --------
#                 form = ChecklistForm(request.POST)
#                 if form.is_valid():
#                     data = form.cleaned_data
#                     data['producer'] = producer_id
#                     save_form = SaveChecklistForm(data)
#                     if save_form.is_valid():
#                         checklist_data = save_form.cleaned_data
#                         Checklist.objects.update_or_create(
#                             producer_id=producer_id,
#                             defaults=checklist_data
#                         )
#                         print("Checklist saved/updated from Save button")
#                     else:
#                         print("Save form errors:", save_form.errors)
#                 else:
#                     print("Checklist form errors:", form.errors)

#             elif 'submit_noting' in request.POST:
                
#                 form = ChecklistForm(request.POST)
#                 checklist = Checklist.objects.filter(producer_id=producer_id).first()

#                 # Save checklist only if not already saved
#                 # if form.is_valid():
#                 if not checklist and form.is_valid():
#                     data = form.cleaned_data
#                     data['producer'] = producer_id
#                     save_form = SaveChecklistForm(data)
#                     if save_form.is_valid():
#                         print("save")
#                         checklist_data = save_form.cleaned_data
#                         checklist, _ = Checklist.objects.update_or_create(
#                             producer_id=producer_id,
#                             defaults=checklist_data
#                         )
#                     else:
#                         print("Save form errors:", save_form.errors)
#                 else:
#                     print("Checklist form errors:", form.errors)
#                 # Handle noting submit
#                 noting_form = NotingForm(request.POST)
#                 if noting_form.is_valid():
                    
#                     noting = noting_form.save(commit=False)
#                     noting.producer_id = producer_id
#                     noting.last_updated_by = request.user.id
#                     noting.forwarded_from = request.user.id  # or some logic to determine origin

#                     # Process forwarded_to
#                     forwarded_to = request.POST.get('forwarded_to')
#                     if forwarded_to == 'officers':
#                         officer_id = request.POST.get('division')
#                         if officer_id:
#                             noting.forwarded_to = officer_id
#                             general_details.forwarded_to = officer_id
#                             general_details.status = 2
                            
#                     elif forwarded_to == 'user':
#                         noting.forwarded_to = 0  # or set to appropriate user/group
#                         # general_details.forwarded_to = producer_id
#                         general_details.forwarded_to = 0
#                         general_details.status = 3
#                         userdata.status = 3
#                         send_query_sms(general_details.authorized_person_mobile)
                        
#                     elif forwarded_to == 'dh':
#                         dh_id = CpcbUser.objects.filter(division='2').first()
#                         noting.forwarded_to = dh_id.id  # or set to appropriate user/group
#                         general_details.forwarded_to = dh_id.id

                        
#                     elif forwarded_to == 'ms_cpcb':
#                         ms_id = CpcbUser.objects.filter(division='1').first()
#                         noting.forwarded_to = ms_id.id  # or set to appropriate user/group
#                         general_details.forwarded_to = ms_id.id
#                         general_details.status = 4
#                         # userdata.status = 4

        
#                     # checklist = Checklist.objects.filter(producer_id=producer_id).first()
#                     if not checklist:
#                         # Create new Checklist if not found
#                         checklist = Checklist.objects.create(producer_id=producer_id)

#                     # Link checklist to noting and save
#                     noting.checklist_id = checklist.id
#                     noting.save()
#                     general_details.save()
#                     userdata.save()
                    
#                     # whatsapp api send message through whatsapp
#                     from_name = CpcbUser.objects.filter(id=noting.forwarded_from).first()
#                     to_name = CpcbUser.objects.filter(id=noting.forwarded_to).first()
#                     # print(from_name)
#                     # print(from_name.first_name)
                    
#                     frwd_application(to_name.mobile_no,from_name.first_name, to_name.first_name)
                    
#                     return redirect('admin_dashboard')
#                 else:
#                     print("Noting form errors:", noting_form.errors)


#             elif 'approved' in request.POST:
#                 print("ok")
#                 general_details.status = 5  # Approved
#                 # userdata.status = 5
#                 general_details.save()
#                 userdata.save()
#                 return redirect('admin_dashboard')

#             elif 'rejected' in request.POST:
#                 print("notok")
#                 general_details.status = 7  # Rejected
#                 userdata.status = 7
#                 general_details.save()
#                 userdata.save()
#                 return redirect('admin_dashboard')
        
        
        
#         registration_fee = 0
        
#         try:
#             if declaration:
#                 turnover_23_24 = declaration.turnover_23_24 if declaration.turnover_23_24 else 0
#                 turnover_24_25 = declaration.turnover_24_25 if declaration.turnover_24_25 else 0

#                 # print(turnover_23_24)
#                 # print(turnover_24_25)

#                 total_turnover = turnover_23_24 + turnover_24_25
#                 # print(total_turnover)

#                 average_turnover = total_turnover / 2

#                 # Find the matching fee slab
#                 fee_record = ProducerRegistrationFee.objects.filter(
#                     models.Q(min_turnover__lte=average_turnover) | models.Q(min_turnover__isnull=True)
#                 ).filter(
#                     models.Q(max_turnover__gte=average_turnover) | models.Q(max_turnover__isnull=True)
#                 ).first()

#                 if fee_record:
#                     registration_fee = fee_record.registration_fee
#                 else:
#                     registration_fee = 0  # fallback if no matching fee slab found

#             else:
#                 # Handle case when declaration is None
#                 print("No declaration found")
#                 turnover_23_24 = 0
#                 turnover_24_25 = 0
#                 total_turnover = 0
#                 average_turnover = 0
#                 registration_fee = 0

#         except Exception as e:
#             print(f"Error while processing declaration: {e}")
#             turnover_23_24 = turnover_24_25 = total_turnover = average_turnover = registration_fee = 0

#         # producer_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id).count
#         producer_fees = ProducerRegistrationFee.objects.all()
#         rvsf_fees = RVSFRegistrationFee.objects.all()
        
#         all_transactions=[]
        
#         all_transactions = Transaction.objects.filter(
#                     owner_id=producer_id, 
#                     status="success"
#                 ).order_by('-ru_date')
        
#         return render(
#             request,
#             'admin/admin_producer.html',
#             {
#                 'officer': officer,
#                 'user': userdata,
#                 'state_name': state_name,
#                 'district_name': district_name,
#                 'general': general_details,
#                 'manufacturing_details': manufacturing_details,
#                 'facilities': facilities,
#                 'nature_selected': nature_selected,
#                 'reporting_officers': reporting_officers,
#                 'role_dict': role_dict,
#                 'form': form,
#                 'noting_form': noting_form,
#                 'vehicle_data': vehicle_data,
#                 'grouped_data': grouped_data,
#                 'metadata': metadata,
#                 'declaration': declaration,
#                 'total_turnover': total_turnover,
#                 'average_turnover' : average_turnover,
#                 'registration_fee': registration_fee,
#                 'producer_fees': producer_fees,
#                 'rvsf_fees': rvsf_fees,
#                 'section_fields': section_fields,
#                 'checklist': checklist_data,
#                 'fresh_count': fresh_count,
#                 'resubmit_count': resubmit_count,
#                 'approved_count': approved_count,
#                 'rejected_count': rejected_count,
#                 'noting_dict': dict(noting_dict),
#                 'user_dict': user_dict,
#                 'all_transactions': all_transactions,
#                 # 'producer_count': producer_count,
#             }
#         )
#     except Exception as e:
#         logger.info(
#             f"Error in producer_detail | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
#         )
#         return redirect("admin_dashboard")
    
    

# def producer_details(request):
#     try:
#         logger.info(f"producer_details called | user_id={request.user.id if request.user else 'anonymous'}")
        
#         # Get encrypted_id from POST
#         encrypted_id = request.POST.get("producer_id")
#         logger.info(f"Encrypted ID received: {encrypted_id}")
#         print(encrypted_id)

#         # Decrypt the producer_id
#         try:
#             producer_id = signing.loads(encrypted_id)
#             logger.info(f"Successfully decrypted producer_id: {producer_id}")
#         except signing.BadSignature as e:
#             logger.error(f"BadSignature error while decrypting producer_id: {str(e)}")
#             return HttpResponseBadRequest("Invalid or tampered producer ID")
        
#         # Fetch producer general details
#         logger.info(f"Fetching producerGeneralDetails for id: {producer_id}")
#         general_details = get_object_or_404(producerGeneralDetails, id=producer_id)
#         logger.info(f"Found producerGeneralDetails: company_name={general_details.company_name}, gst_no={general_details.gst_no}, status={general_details.status}")
        
#         # Fetch user registration data
#         logger.info(f"Fetching Registration for gst_no: {general_details.gst_no}")
#         userdata = Registration.objects.get(gst_no=general_details.gst_no)
#         logger.info(f"Found Registration: company_name={userdata.company_name}, status={userdata.status}")
        
#         # Fetch officer with division '2'
#         logger.info(f"Fetching CpcbUser with division='2'")
#         officer = CpcbUser.objects.get(division='2')
#         logger.info(f"Found officer: id={officer.id}, username={officer.username}, division={officer.division}")
        
#         # Check and update status if needed
#         print(officer.id,'gsdfsjgfj')
#         logger.info(f"Checking general_details.status: {general_details.status}")
#         if general_details.status == 1:
#             logger.info(f"Status is 1, updating to 2 and setting forwarded_to to officer.id={officer.id}")
#             general_details.status = 2
#             general_details.forwarded_to = officer.id
#             logger.info(f"userdata.status before update: {userdata.status}")
#             userdata.status = 1
#             logger.info(f"userdata.status after update: {userdata.status}")
            
#             general_details.save()
#             logger.info(f"general_details saved successfully")
#             userdata.save()
#             logger.info(f"userdata saved successfully")
#         else:
#             logger.info(f"Status is {general_details.status}, no update needed")
        
#         logger.info(f"Calling producer_detail function")
#         return producer_detail(request)
        
#     except CpcbUser.MultipleObjectsReturned as e:
#         logger.error(f"MultipleObjectsReturned error: {str(e)} | division='2' returned multiple users")
#         logger.error(f"All users with division='2': {list(CpcbUser.objects.filter(division='2').values('id', 'username', 'first_name'))}")
#         return redirect("admin_dashboard")
        
#     except CpcbUser.DoesNotExist as e:
#         logger.error(f"DoesNotExist error: {str(e)} | No user found with division='2'")
#         return redirect("admin_dashboard")
        
#     except Registration.DoesNotExist as e:
#         logger.error(f"Registration.DoesNotExist error: {str(e)} | gst_no={general_details.gst_no if 'general_details' in locals() else 'unknown'}")
#         return redirect("admin_dashboard")
        
#     except Exception as e:
#         logger.error(f"Unexpected error in producer_details | user_id={request.user.id if request.user else 'anonymous'} | error_type={type(e).__name__} | error={str(e)}", exc_info=True)
#         return redirect("admin_dashboard")
@cpcb_admin_required
def producer_details(request):
    try:
        # producer_id = request.POST.get("producer_id")
        encrypted_id = request.POST.get("producer_id")
        print(encrypted_id)

        try:
            producer_id = signing.loads(encrypted_id)
        except signing.BadSignature:
            return HttpResponseBadRequest("Invalid or tampered producer ID")
        
        general_details = get_object_or_404(producerGeneralDetails, id=producer_id)
        userdata = Registration.objects.get(gst_no=general_details.gst_no)
        officer = CpcbUser.objects.get(division = '2')
        
        if general_details.status == 1:
            general_details.status = 2
            general_details.forwarded_to = officer.id
            # userdata.status = 2
            userdata.status = 1
            general_details.save()
            userdata.save()
        
        return producer_detail(request)
    except Exception as e:
        logger.info(
            f"Error in producer_details | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")
    
class ChangeAdminPasswordFirst(View):

    def get(self, request):
        try:
            user_id = request.session.get('admin_user_id')
            if not user_id:
                messages.error(request, "Session expired. Please login again.")
                return redirect('custom_admin_login')

            user = CpcbUser.objects.filter(id=user_id).first()
            if not user:
                messages.error(request, "User not found.")
                return redirect('custom_admin_login')

            return render(request, 'admin/change_admin_password.html', {
                'url': 'login/change-password',
                'form': ProducerOTPForm(),
            })
        except Exception as e:
            logger.info(f"Error in GET ChangeAdminPasswordFirst | error={str(e)}")
            return redirect("custom_admin_login")
        
    def post(self, request):
        try:
            user_id = request.session.get('admin_user_id')
            if not user_id:
                messages.error(request, "Session expired. Please login again.")
                return redirect('custom_admin_login')
            
            form = CaptchaForm(request.POST)
            if not form.is_valid():
                messages.error(request, "Invalid captcha. Please try again.")
                return redirect('change_admin_password_first')
            
            old_password = new_password = confirm_password = None
            
            enc_oldPassword = request.POST.get('old_password')
            enc_newPassword = request.POST.get('new_password')
            enc_confirmPassword = request.POST.get('confirm_password')
            
            # print(enc_oldPassword)
            # print(enc_newPassword)
            # print(enc_confirmPassword)
            

            try:
                old_password = decrypt_aes(enc_oldPassword)
                new_password = decrypt_aes(enc_newPassword)
                confirm_password = decrypt_aes(enc_confirmPassword)
                
            except Exception:
                messages.error(request, "Passwords not match")
                return redirect('change_admin_password_first')

            # old_password = request.POST.get('old_password')
            # new_password = request.POST.get('new_password')
            # confirm_password = request.POST.get('confirm_password')

            try:
                user = CpcbUser.objects.get(id=user_id)
            except CpcbUser.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('change_admin_password_first')

            if not check_password(old_password, user.password):
                messages.error(request, "Old password is incorrect.")
                return redirect('change_admin_password_first')

            if new_password != confirm_password:
                messages.error(request, "New password and confirm password do not match.")
                return redirect('change_admin_password_first')

            if not self.is_strong_password(new_password):
                messages.error(request, "Password must be at least 8 characters long and include uppercase, lowercase, digit, and special character.")
                return redirect('change_admin_password_first')

            # Check against last 3 passwords
            password_history = json.loads(user.password_history or '[]')
            recent_passwords = [user.password] + password_history[:2]  # current + last 2

            for old_hashed in recent_passwords:
                if check_password(new_password, old_hashed):
                    messages.error(request, "New password must not match any of the last 3 passwords.")
                    return redirect('change_admin_password_first')

            # Update password
            new_hashed = make_password(new_password)
            updated_history = [user.password] + password_history
            user.password_history = json.dumps(updated_history[:3])
            user.password = new_hashed
            user.first_login=1
            user.save()
            
            # sendNewPasswordemail(user.first_name, user.username, user.email, new_password)
            sendNewPasswordEmail(user.first_name, user.username, user.email, new_password)
            
            
            # Re-login the admin after password change
            login(request, user)

            # Optional: reset the session to keep admin info
            request.session['admin_user_id'] = user.id
            request.session['user_role'] = "admin"
            set_active_session("admin", user.id, request)

            messages.success(request, "Password changed successfully.")
            return redirect('admin_dashboard')
        except Exception as e:
            logger.info(f"Error in POST ChangeAdminPasswordFirst | error={str(e)}")
            return redirect("custom_admin_login")
        
    def is_strong_password(self, password):
        return (
            len(password) >= 8 and
            re.search(r'[A-Z]', password) and
            re.search(r'[a-z]', password) and
            re.search(r'\d', password) and
            re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
        )



def payment_receipt_admin(request):
    try:
        # producer_id = request.POST.get("producer_id")
        encrypted_id = request.POST.get("producer_id")
        # print(encrypted_id)

        try:
            producer_id = signing.loads(encrypted_id)
        except signing.BadSignature:
            return HttpResponseBadRequest("Invalid or tampered producer ID")
        # print(producer_id) 
        
        producer = producerGeneralDetails.objects.filter(id=producer_id).first()
        user = Registration.objects.filter(gst_no=producer.gst_no).first()
        # transaction = Transaction.objects.filter(owner_id=producer.id, status="success").order_by('-ru_date').first()
        
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
        
        return redirect('admin_dashboard')
        
        
        # if transaction:
        #     producer = producerGeneralDetails.objects.filter(id=producer_id).first()
        #     status = transaction.status
        #     order_id=transaction.order_id
        #     transaction_id =transaction.txn_id
        #     transaction_date=transaction.ru_date
        #     amount=transaction.amount_initiated
        #     producer = producerGeneralDetails.objects.filter(gst_no=user.gst_no).first()
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
        
        # messages.error(request, "No successful transaction found.")
        # return redirect('admin_dashboard') 
    except Exception as e:
        logger.info(
            f"Error in payment_receipt_admin | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")


#--------------------------------------------------- Functions For Registering SPCBs ---------------------------------------------#


def generate_spcb_username():
    # year_suffix = datetime.datetime.now().strftime('%y')  # '25' for 2025
    year_suffix = datetime.now().strftime('%y')
    sequence_file = 'spcb_sequence.txt'

    # Load last used sequence
    if os.path.exists(sequence_file):
        with open(sequence_file, 'r') as f:
            last_seq = int(f.read().strip())
    else:
        last_seq = 0

    # Increment and save new sequence
    new_seq = last_seq + 1
    with open(sequence_file, 'w') as f:
        f.write(str(new_seq))

    sequence_str = str(new_seq).zfill(2)  
    return f'SPCB{year_suffix}{sequence_str}'


@cpcb_admin_required
def register_spcbs(request):
    try:
        officer = request.user
        # print(officer)
        fresh_count = producerGeneralDetails.objects.filter(application_type=0, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()
        resubmit_count = producerGeneralDetails.objects.filter(application_type=1, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()

        approved_count=0
        rejected_count=0# approved_count=0
        if officer.division=='1':
            approved_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id, status='5').count()
            rejected_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id, status='7').count()
        states = State.objects.all()
        
        # roles = StateRoles.objects.all()
        roles = StateRoles.objects.all().exclude(id=3)
        # print(roles)

        if request.method == 'POST':
            form = CaptchaForm(request.POST)
            if form.is_valid():
                email = request.POST.get('auth_email')
                mobile = request.POST.get('auth_mobile')
                # raw_password = request.POST.get('password')
                OfficerName = request.POST.get('OfficerName')
                stateId = request.POST.get('State_id')
                RoleAccess = request.POST.get('RoleAccess')
                
                try:
                    validate_email(email)
                except ValidationError:
                    return JsonResponse({'success': False, 'message': 'Invalid email format.'})
                
                # ✅ Check disposable email
                if is_disposable_email(email):
                    messages.error(request, f"Disposable or fake email '{email}' is not allowed.")
                    return render(request, 'spcbregister/createuser.html', {
                        'form': CaptchaForm(),  # refresh captcha
                        'states': states,
                        'roles': roles,
                        'fresh_count': fresh_count,
                        'resubmit_count': resubmit_count,
                        'approved_count': approved_count,
                        'rejected_count': rejected_count,
                    })
                
                username = generate_spcb_username()
                raw_password = generate_password()
                
                # Get all accounts for this state
                state_users = StateUsers.objects.filter(State_id=stateId, RoleAccess=RoleAccess)

                if state_users.exists():
                    # Check if ANY user is active (DisableStatus=False)
                    active_exists = state_users.filter(DisableStatus=False).exists()

                    if active_exists:
                        messages.error(request, "This Role is already exists for this State. Please disable the existing active account before creating a new one.")
                        return redirect('register_spcbs')
                
                if StateUsers.objects.filter(auth_email=email).exists():
                    messages.error(request, "Email already registered.")
                    return redirect('register_spcbs')

                if StateUsers.objects.filter(auth_mobile=mobile).exists():
                    messages.error(request, "Mobile number already registered.")
                    return redirect('register_spcbs')

                # Create new user
                new_user = StateUsers(
                    username=username,
                    password=make_password(raw_password),
                    auth_mobile=mobile,
                    auth_email=email,
                    OfficerName=OfficerName,
                    officerDesignation=request.POST.get('officerDesignation'),
                    RoleAccess=RoleAccess,
                    State_id=stateId,
                    District_id=request.POST.get('District_id'),
                    # Assuming new users are disabled by default
                )
                new_user.save()
                
                try:
                    sendSignupEmail(OfficerName, username, email, raw_password)
                    messages.success(
                        request,
                        f"Account created successfully! Credentials have been sent to {OfficerName}'s email."
                    )

                except Exception as e:
                    messages.warning(request, f"Account details saved, but failed to send email: {e}")

                # messages.success(request, "User created successfully!")
                # return redirect('register_spcbs')
            else:
                messages.error(request, "Invalid Captcha !")
        else:
            form = CaptchaForm()
        
        return render(request, 'spcbregister/createuser.html', {
            'form': form,
            'states': states,
            'roles': roles,
            'fresh_count': fresh_count,
            'resubmit_count': resubmit_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
        })
    except Exception as e:
        logger.info(
            f"Error in register_spcbs | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")
    

@cpcb_admin_required
def spcb_users(request):
    try:
        officer = request.user
        users = StateUsers.objects.all()
        fresh_count = producerGeneralDetails.objects.filter(application_type=0, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()
        resubmit_count = producerGeneralDetails.objects.filter(application_type=1, forwarded_to=request.user.id).exclude(Q(status='5') | Q(status='6') | Q(status='7')).count()

        approved_count=0
        rejected_count=0# approved_count=0
        if officer.division=='1':
            approved_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id, status='5').count()
            rejected_count = producerGeneralDetails.objects.filter(forwarded_to=request.user.id, status='7').count()

        user_data = []
        for user in users:
            state_name = ''
            district_name = ''
            role_name = ''

            if user.State_id:
                state_obj = State.objects.filter(state_id=user.State_id).first()
                if state_obj:
                    state_name = state_obj.state_name

            if user.District_id:
                district_obj = District.objects.filter(city_id=user.District_id).first()
                if district_obj:
                    district_name = district_obj.city_name
                    
            if user.RoleAccess:
                role_obj = StateRoles.objects.filter(id=user.RoleAccess).first()
                if role_obj:
                    role_name = role_obj.Rolename


            user_data.append({
                'user': user,
                'state_name': state_name,
                'district_name': district_name,
                'role_name': role_name,
            })

        return render(request, 'spcbregister/viewusers.html', {
            'users': user_data,
            'fresh_count': fresh_count,
            'resubmit_count': resubmit_count
        })
    except Exception as e:
        logger.info(
            f"Error in spcb_users | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")
    

@cpcb_admin_required
def toggle_spcb_user_status(request):
    try:
        user_id = request.POST.get("user_id")

        if not request.user.is_admin:
            messages.error(request, "Only superadmins can change user status.")
            return redirect('spcb_users')

        user = get_object_or_404(StateUsers, id=user_id)
        user.DisableStatus = not user.DisableStatus  # Toggle status
        user.save()

        if user.DisableStatus:
            messages.warning(request, f"{user.username} has been disabled.")
        else:
            messages.success(request, f"{user.username} has been enabled.")

        return redirect('spcb_users')
    except Exception as e:
        logger.info(
            f"Error in toggle_spcb_user_status | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")

@cpcb_admin_required
def spcb_profile(request):
    try:
        officer = request.user

        # Common counts for header/dashboard
        fresh_count = producerGeneralDetails.objects.filter(application_type=0, forwarded_to=officer.id).count()
        resubmit_count = producerGeneralDetails.objects.filter(application_type=1, forwarded_to=officer.id).count()
        # roles = StateRoles.objects.all()
        # roles = StateRoles.objects.filter(id = 2)
        form = CaptchaForm()

        # Handle POST (e.g., coming from a form)
        if request.method == 'POST':
            hid_id = request.POST.get('hidden_id')
            getdetails = StateUsers.objects.filter(id=hid_id).first()

            if not getdetails:
                messages.error(request, "User not found.")
                return redirect('spcb_users')

        else:
            # Handle GET (normal page open)
            # Use logged-in officer details by default
            getdetails = StateUsers.objects.filter(id=officer.id).first()

        if not getdetails:
            # messages.error(request, "Profile not found.")
            return redirect('spcb_users')

        # Get related state/district names
        statename = State.objects.filter(state_id=getdetails.State_id).first()
        districtname = District.objects.filter(city_id=getdetails.District_id).first()
        roles = StateRoles.objects.all()
        spcb_role = StateRoles.objects.filter(id=getdetails.RoleAccess).first()
        # Prepare context for template
        context = {
            'profile': getdetails,
            'fresh_count': fresh_count,
            'resubmit_count': resubmit_count,
            'roles': roles,
            'form': form,
            'spcb_role': spcb_role,
            'statename': statename.state_name if statename else '',
            'districtname': districtname.city_name if districtname else '',
        }
        print(context['profile'].__dict__)

        return render(request, 'spcbregister/spcbprofile.html', context)
    except Exception as e:
        logger.info(
            f"Error in spcb_profile | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")
    
        
def is_current_password_correct(user: StateUsers, raw_password: str) -> bool:
    """
    Securely checks if the provided raw_password matches the user's stored password hash.
    Returns True if correct, False otherwise.
    """
    return django_check_password(raw_password, user.password)   

@cpcb_admin_required
def updatespcbprofile(request):
    try:
        if request.method == 'POST':
            form = CaptchaForm(request.POST)
            hid_id = request.POST.get('hid_id')
            stateupdate = StateUsers.objects.filter(id=hid_id).first()

            if not stateupdate:
                messages.error(request, "User not found.")
                return redirect('spcb_users')

            # Prepare state/district/role for re-render
            statename = State.objects.filter(state_id=stateupdate.State_id).first()
            districtname = District.objects.filter(city_id=stateupdate.District_id).first()
            roles = StateRoles.objects.all()

            if form.is_valid():
                auth_email = request.POST.get('auth_email')
                auth_mobile = request.POST.get('auth_mobile')
                OfficerName = request.POST.get('OfficerName')
                officerDesignation = request.POST.get('officerDesignation')
                RoleAccess = request.POST.get('RoleAccess')
                username = request.POST.get('username')

            # ✅ Check disposable email properly
                if is_disposable_email(auth_email):
                    messages.error(request, f"The email domain of '{auth_email}' is not allowed (disposable).")
                    return render(request, 'spcbregister/spcbprofile.html', {
                        'form': CaptchaForm(),  # new captcha
                        'profile': stateupdate,
                        'roles': roles,
                        'statename': statename.state_name if statename else '',
                        'districtname': districtname.city_name if districtname else '',
                    })
                    
                # ✅ Save profile
                stateupdate.auth_email = auth_email
                stateupdate.username = username
                stateupdate.officerDesignation = officerDesignation
                stateupdate.OfficerName = OfficerName
                stateupdate.RoleAccess = RoleAccess
                stateupdate.auth_mobile = auth_mobile
                stateupdate.save()

                messages.success(request, "Profile updated successfully!")
                return redirect('ViewSpcbProfile')  # success redirect
            else:
                messages.error(request, "Invalid Captcha. Please try again.")
                return render(request, 'spcbregister/spcbprofile.html', {
                    'form': CaptchaForm(),  # new captcha after error
                    'profile': stateupdate,
                    'roles': roles,
                    'statename': statename.state_name if statename else '',
                    'districtname': districtname.city_name if districtname else '',
                })

        return redirect('spcb_users')
    except Exception as e:
        logger.info(
            f"Error in updatespcbprofile | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")



# -------------------------------------------------------- EmSigner ---------------------------------------------------------------- #
@csrf_exempt
def esign_cancel(request):
    # optional: log or read POST here
    return redirect('/cpcb/allproducers/?type=approved')  # or whatever you need

def create_file(file_path, content):
    with open(file_path, "w") as f:
        f.write(content)

def read_file_content(file_path):
    with open(file_path, "r") as f:
        return f.read()
    

@cpcb_admin_required
def generate_certificate(request):
    try:
        # producer_id = request.POST.get("producer_id")
        encrypted_id = request.POST.get("producer_id")
        # print(encrypted_id)

        try:
            producer_id = signing.loads(encrypted_id)
        except signing.BadSignature:
            return HttpResponseBadRequest("Invalid or tampered producer ID")

        try:
            html_content = create_pdf(request)
            cert_dir = os.path.join(settings.BASE_DIR, 'certificates')
            os.makedirs(cert_dir, exist_ok=True)
            cert_no = f"CERT_{producer_id}"
        
            pdf_path = os.path.join(cert_dir, f"{cert_no}.pdf")

            config = settings.PDFKIT_CONFIG

            # Options to prevent printer popup & allow static files
            options = {
                "enable-local-file-access": "",  # allow local file:// access
                "no-print-media-type": None,
                "enable-smart-shrinking": "",
                "quiet": "",  # suppress extra logs
                'encoding': 'UTF-8',
                'quiet': '',
                'margin-top': '0.5in',
                'margin-right': '0.5in',
                'margin-bottom': '0.5in',
                'margin-left': '0.5in',
                'page-size': 'A4',
                'debug-javascript': '',  # Bypass printer checks
                'javascript-delay': '10',  # Milliseconds (reduce if needed)
                'no-stop-slow-scripts': '',
            }

            # Replace relative static URLs with absolute file paths
            html_content = html_content.replace(
                '/static/',
                f'file:///{os.path.join(settings.BASE_DIR, "static")}/'
            )

            # Generate PDF
            pdfkit.from_string(html_content, pdf_path, configuration=config, options=options)

            # 5. Now read the PDF, encode and proceed with eSigner as before
            with open(pdf_path, "rb") as f:
                b64_pdf = base64.b64encode(f.read()).decode()

            user_id = request.user.id
            reference_no = f"{cert_no}-{user_id}"
            # redirect_url = request.build_absolute_uri('/cpcb/view-certs/')
            view_url = reverse('view_producer_certs')
            redirect_url = request.build_absolute_uri(f"{view_url}?producer_id={producer_id}")
            cancel_url = request.build_absolute_uri(reverse("esign_cancel"))

            unique_reference_no = uuid.uuid4().hex[:17]
            
            # Aadhaar last 4 digits collected from user
            aadhaar_last4 = "5307"   # TODO: take from form input

            # Build JSON
            aadhaar_json = {
                "userAadhaarLast4Digit": aadhaar_last4
            }

            # Convert to JSON string
            aadhaar_json_str = json.dumps(aadhaar_json)

            # Base64 encode
            aadhaar_base64 = base64.b64encode(aadhaar_json_str.encode()).decode()
            

            # print(b64_pdf)
            json_data = {
                "Name": "Deepti Kapil",
                "FileType": "PDF",
                "SignatureMode": 12,
                "SelectPage": "ALL",
                # "SelectPage": "SPECIFIC",
                # "SelectPage": "LAST",
                "SignaturePosition": "Bottom-Right",
                "AuthToken": settings.ESIGNER_AUTHTOKEN, 
                "File": b64_pdf,
                "PageNumber": "",
                "Noofpages": 0,
                "PreviewRequired": True,
                "SUrl": redirect_url,
                "FUrl": cancel_url,
                "CUrl": cancel_url,
                "ReferenceNumber": unique_reference_no,
                "IsCompressed": False,
                "IsCosign": False,
                "IsCustomized": True,
                "eSignGatewayCustomUI": aadhaar_base64,
                "eMudhraV2SignatureType": 2
                
            }
            # print(json_data)
            
            
            
            data_dir = unique_reference_no
            signed_dir = os.path.join(settings.BASE_DIR, "certificates", "config_files",unique_reference_no)

            arg1 = "Encrypt"
            arg2 = os.path.normpath(os.path.join(signed_dir, "Json_Data.txt"))
            arg3 = os.path.join(signed_dir, "session_key.txt")
            arg4 = os.path.join(signed_dir, "encrypted_session_key.txt")
            arg5 = os.path.join(signed_dir, "encrypted_json_data.txt")
            arg6 = os.path.join(signed_dir, "encrypted_hash_of_json_data.txt")
            arg7 = os.path.join(settings.BASE_DIR, "certificate.cer")
            
            # logger.debug(f"Check if the directory exists : {data_dir}")
            if not os.path.exists(signed_dir):
                # os.makedirs(data_dir, exist_ok=False)
            # logger.debug("Data dir created successfully")
                os.makedirs(signed_dir, exist_ok=True)
            # signed_pdf_path = os.path.join(signed_dir, f"{cert_no}.pdf")

            empty_txt = ''
            # Creating the Files to store Encrypted Data
            create_file(file_path=arg3, content=empty_txt)
            create_file(file_path=arg4, content=empty_txt)
            create_file(file_path=arg5, content=empty_txt)
            create_file(file_path=arg6, content=empty_txt)
            
            jar_path = os.path.join(settings.BASE_DIR, "SG_Final_Jar_PHP", "Final_ED_Both.jar")

            with open(arg2, "w") as outfile:
                json.dump(json_data, outfile)

            try:
                logger.info("Executing JAR now ..")
                command = f'java -jar "{jar_path}" {arg1} "{arg2}" "{arg3}" "{arg4}" "{arg5}" "{arg6}" "{arg7}"'
                # print(command)
                subprocess.getoutput(command)
            except Exception as je:
                logger.error(f"DSign JAR Execution error : {str(je)}")
                raise Exception("DSign JAR Execution error")


            encrypted_session_key = read_file_content(file_path=arg4).strip()
            encrypted_json_data = read_file_content(file_path=arg5).strip()
            encrypted_hash_of_json_data = read_file_content(file_path=arg6).strip()

            parametersData = {
                "Parameter1": encrypted_session_key,
                "Parameter2": encrypted_json_data,
                "Parameter3": encrypted_hash_of_json_data
            }
            
            # print(parametersData)
            return render(request, "admin/esign/call_gateway.html", {"parametersData": parametersData})

        except subprocess.CalledProcessError as e:
            return HttpResponse(f"Java execution failed: {e}")
        except FileNotFoundError as e:
            return HttpResponse(f"File not found: {e}")
        except Exception as e:
            return HttpResponse(f"Unexpected error: {e}")
    except Exception as e:
        logger.info(
            f"Error in generate_certificate | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")
    
    
@csrf_exempt
@xframe_options_exempt
def view_certs(request):
    try:
        
        # reference = request.POST.get("ReferenceNumber") or request.POST.get("Referencenumber")
        # status = request.POST.get("ReturnStatus")
        # return_value = request.POST.get("Returnvalue")
        reference = (
            request.POST.get("ReferenceNumber")
            or request.POST.get("Referencenumber")
            or request.GET.get("ReferenceNumber")
            or request.GET.get("Referencenumber")
        )

        status = (
            request.POST.get("ReturnStatus")
            or request.GET.get("ReturnStatus")
            or request.POST.get("status")
            or request.GET.get("status")
        )

        return_value = (
            request.POST.get("Returnvalue")
            or request.POST.get("ReturnValue")
            or request.GET.get("Returnvalue")
            or request.GET.get("ReturnValue")
        )
        
        producer_id = request.GET.get('producer_id')


        if not reference:
            return HttpResponse("Missing reference number")

        # cert_no = reference
        cert_no = f"CERT_{producer_id}"
        data_dir = os.path.join(settings.BASE_DIR, "certificates", "config_files", reference)
        # data_dir = os.path.join(settings.BASE_DIR, cert_no)  # Full path to cert_no directory

        # Paths
        encrypted_file = os.path.join(data_dir, "Encrypted_Signed_Data.txt")
        session_key_file = os.path.join(data_dir, "session_key.txt")
        decrypted_file = os.path.join(data_dir, "Decrypted_Signed_Data.txt")
        jar_path = os.path.join(settings.BASE_DIR, "SG_Final_Jar_PHP", "Final_ED_Both.jar")

        # Ensure signed_files directory exists
        signed_dir = os.path.join(settings.BASE_DIR, "certificates", "signed_files")
        os.makedirs(signed_dir, exist_ok=True)
        signed_pdf_path = os.path.join(signed_dir, f"{cert_no}.pdf")

        if status == "Success" and return_value:
            try:
                # Step 1: Save the encrypted data
                create_file(file_path=encrypted_file, content=return_value)
                
                # Step 2: Run decryption (this should create Decrypted_Signed_Data.txt)
                cmd = ['java', '-jar', jar_path, 'Decrypt', encrypted_file, session_key_file, decrypted_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Decryption failed: {result.stderr}")
                    return HttpResponse("Decryption process failed")
                
                # Step 3: Read the decrypted base64 content
                decrypted_content = read_file_content(decrypted_file).strip()
                if not decrypted_content:
                    logger.error("Decrypted content is empty")
                    return HttpResponse("Decrypted content is empty")
                
                # Step 4: Decode base64 to PDF
                try:
                    pdf_bytes = base64.b64decode(decrypted_content)
                except Exception as e:
                    logger.error(f"Base64 decoding failed: {str(e)}")
                    return HttpResponse("Invalid base64 content")
                
                # Step 5: Verify it's a PDF
                if not pdf_bytes.startswith(b'%PDF'):
                    logger.error("Decrypted content is not a valid PDF")
                    return HttpResponse("Decrypted content is not a valid PDF")
                
                # Step 6: Save the PDF
                with open(signed_pdf_path, 'wb') as f:
                    f.write(pdf_bytes)
                
                logger.info(f"Successfully saved signed PDF to {signed_pdf_path}")
                
                producer = producerGeneralDetails.objects.filter(id=producer_id).first()
                user = Registration.objects.filter(gst_no=producer.gst_no).first()
                
                producer.status = 6
                producer.forwarded_to = 0
                user.status = 6
                
                producer.save()
                user.save()
                
                # return FileResponse(open(signed_pdf_path, 'rb'), content_type='application/pdf')
                
                url = reverse("admin_producers") + "?type=approved"
                return redirect(url)
                
                # return redirect('admin_dashboard')
                # return HttpResponse("Signature process completed successfully")
                
            except Exception as e:
                logger.error(f"Error in signature process: {str(e)}")
                return HttpResponse(f"Error processing signature: {str(e)}")

        return HttpResponse("Signature process failed - invalid status or return value")
    except Exception as e:
        logger.info(
            f"Error in view_certs | user_id={request.user.id if request.user else 'anonymous'} | error={str(e)}"
        )
        return redirect("admin_dashboard")

