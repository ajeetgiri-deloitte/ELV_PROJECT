from binascii import Incomplete
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from django.db.models import Sum
from django.urls import reverse
from django.utils.http import urlencode
from datetime import timezone
from functools import wraps
import random
import string
from django.contrib import messages
from django.db.models import Subquery, OuterRef
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
import pytz
from RvsfApp.models import *
from RvsfApp.views import rvsfdetails
from SpcbApp.models import * 
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password, check_password
from registration.forms import CaptchaForm, LoginForm
from registration.models import District, State
from django.db.models import Q
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime

import os, base64, json, subprocess
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from reportlab.pdfgen import canvas
from django.shortcuts import render, redirect, get_object_or_404

import os
from django.http import Http404, FileResponse
from django.db import transaction
import threading

# utils/crypto.py or views.py

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_v1_5
from Cryptodome.Random import get_random_bytes
from utils.email_services import *
from RvsfApp.views import *
import logging

Send_Grid_Api_Key="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"
aware_now = datetime.now(timezone.utc)
logger = logging.getLogger('elv_logger')

def sendforgetpwdemail(auth_email):
    try:
        email = auth_email
        sender_email = 'cpcbepr@cpcbauditempanelment.co.in'
        sender_password = 'airtel@123'
        recipient_email = email
        resetpassword = StateUsers.objects.filter(auth_email = auth_email).first()
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
    except Exception as db_error:
        logger.exception("❌ ERROR while  endforgetpwdemail")
        logger.error(f"Exact endforgetpwdemail  Error: {str(db_error)}")
        
        logger.info(f"Exact endforgetpwdemail Error: {str(db_error)}")

import time
from django.core.cache import cache


def sendforgetpwdemail_forgotpwd(username, company_email):
    try:
        # Disable SSL warnings for development (not recommended for production)
        ssl._create_default_https_context = ssl._create_unverified_context
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        user = StateUsers.objects.filter(username=username, auth_email=company_email).first()

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
    except Exception as db_error:
        logger.exception("❌ ERROR while  endforgetpwdemail_forgotpwd")
        logger.error(f"Exact endforgetpwdemail_forgotpwd  Error: {str(db_error)}")
        
        logger.info(f"Exact endforgetpwdemail_forgotpwd Error: {str(db_error)}")

def spcbforgetpassword(request):
    # print('spcbforgets')
    form = CaptchaForm()
    return render(request , 'spcb/forget_password.html', {'form': form})
    
def spcbresetpassword(request):
    # print('yha bhi11')
    try:
        """Handle password reset requests with full validation and rate limiting."""
        form = CaptchaForm(request.POST or None)

        if request.method == 'POST':
            username = request.POST.get('username', '').strip()
            company_email = request.POST.get('company_email', '').strip()
            user_ip = get_client_ip(request)

            # === 1️⃣ Validate inputs ===
            if not username or not company_email:
                messages.error(request, "Both username and company email are required.")
                return render(request, 'spcb/forget_password.html', {'form': form})

            # === 2️⃣ Validate CAPTCHA ===
            if not form.is_valid():
                messages.error(request, "Invalid CAPTCHA. Please try again.")
                return render(request, 'spcb/forget_password.html', {'form': CaptchaForm()})

            # === 3️⃣ Rate Limiting ===
            rate_key_user_rvsf = f"reset_attempts_user_{username}_rvsf"
            rate_key_ip_rvsf = f"reset_attempts_ip_{user_ip}_rvsf"

            max_attempts_rvsf = 3
            block_time_rvsf = 10  # in minutes

            # if is_rate_limited(rate_key_user_rvsf, max_attempts_rvsf, block_time_rvsf) or \
            #    is_rate_limited(rate_key_ip_rvsf, max_attempts_rvsf, block_time_rvsf):
            #     messages.error(request, "Too many attempts. Please try again later.")
            #     return render(request, 'spcb/forget_password.html', {'form': CaptchaForm()})

            # === 4️⃣ Verify username and email ===
            # print('user check')
            # print(username,company_email)
            userin = StateUsers.objects.all()
            for i in userin:
                print(i.username,i.auth_email,'111111222222222233333333354')
            user = StateUsers.objects.filter(username=username, auth_email=company_email).first()
            # print('mil gya')
            if not user:
                messages.error(request, "Invalid username or email address.")
                return render(request, 'spcb/forget_password.html', {'form': CaptchaForm()})

            # === 5️⃣ Send password reset email ===
            # success, msg, _ = sendforgetpwdemail_forgotpwd(username, company_email)  # Use underscore to ignore third value
            # print('bhej du ')
            success, msg = sendForgetPwdEmail(username, company_email)
            if success:
                messages.success(request, msg)
                return redirect('spcb_home')
            else:
                messages.error(request, msg)
                return render(request, 'spcb/forget_password.html', {'form': CaptchaForm()})

        # GET → show form
        return render(request, 'spcb/forget_password.html', {'form': form})
    except Exception as db_error:
        logger.exception("❌ ERROR while  spcbresetpassword")
        logger.error(f"Exact spcbresetpassword  Error: {str(db_error)}")
        
        logger.info(f"Exact spcbresetpassword Error: {str(db_error)}")


def rsa_decrypt(encrypted_value: str) -> str:

    with open(settings.RSA_PRIVATE_KEY_PATH, "rb") as f:
        private_key = RSA.import_key(f.read())
        print("RSA key size:", private_key.size_in_bits())

    key_size_bytes = private_key.size_in_bytes()  # 🔥 AUTO (128 or 256)

    decoded = base64.b64decode(encrypted_value)

    # ✅ Correct validation
    if len(decoded) != key_size_bytes:
        raise ValueError(
            f"Invalid RSA payload size: {len(decoded)} bytes (expected {key_size_bytes})"
        )

    cipher = PKCS1_v1_5.new(private_key)
    sentinel = get_random_bytes(16)

    decrypted = cipher.decrypt(decoded, sentinel)

    if decrypted == sentinel:
        raise ValueError("RSA decryption failed")

    return decrypted.decode("utf-8")

def updateRole(request):
    try:
        if request.method != "POST":
            return redirect("viewroles")

        encrypted_payload = request.POST.get("hidden_id", "")

        try:
            decrypted_json = rsa_decrypt(encrypted_payload)
            data = json.loads(decrypted_json)
        except Exception as e:
            print("RSA ERROR:", e)
            messages.error(request, "Invalid encrypted payload.")
            return redirect("viewroles")

        userid = data.get("userid")
        role   = data.get("role")

        if not userid or not role:
            messages.error(request, "Invalid data.")
            return redirect("viewroles")

        spcbuser = StateUsers.objects.filter(id=userid).first()
        if not spcbuser:
            messages.error(request, "User not found.")
            return redirect("viewroles")

        spcbuser.RoleAccess = role
        spcbuser.save()

        messages.success(
            request,
            f"Role updated successfully for {spcbuser.OfficerName}."
        )
        return redirect("viewroles")
    except Exception as db_error:
        logger.exception("❌ ERROR while  updaterole")
        logger.error(f"Exact updaterole  Error: {str(db_error)}")
        
        logger.info(f"Exact updaterole Error: {str(db_error)}")

def protected_file(request, path):
    try:
        # Check for either admin or producer login
        # admin_id = request.session.get('admin_user_id')
        rvsf_id = request.session.get('user_id')
        user_role = request.session.get('user_role')
        
        # if neither producer nor admin logged in
        if  not rvsf_id:
            # Redirect based on role (default to producer login)
            if user_role == 'spcb':
                return redirect('spcb_home')  # use your producer login view name
            else:
                return redirect('custom_admin_login')

        # File access
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        if not os.path.exists(file_path):
            raise Http404("File not found")

        return FileResponse(open(file_path, 'rb'), as_attachment=False)
    except Exception as db_error:
        logger.exception("❌ ERROR while  protectedfile")
        logger.error(f"Exact protectedfile  Error: {str(db_error)}")
        
        logger.info(f"Exact protectedfile Error: {str(db_error)}")

class ChangePasswordFirstspcb(View):
    krishan_logger = logging.getLogger('elv_logger')
    print("🔹 Initializing krishan_logger")
    try:
        print("🔹 Entering try block")
        def get(self, request):
            print("🔹 Entered ChangePasswordFirst GET method")
            # print("🔹 Entered ChangePasswordFirst GET method")

            user_id = request.session.get('user_id')
            print(f"🔹 user_id from session: {user_id}")
            # print(f"🧑 Session user_id: {user_id}")

            if not user_id:
                print("🔹 user_id not found, entering if block")
                # print("❌ No user_id found in session — redirecting to login")
                messages.error(request, "Session expired. Please login again.")
                print("🔹 Added error message about session expiry")
                return redirect('spcb_home')
                print("🔹 Redirecting to spcb_home")

            user = StateUsers.objects.filter(id=user_id).first()
            print(f"🔹 User fetched from filter: {user}")
            # print(f"🔍 User fetched: {user}")

            if not user:
                print("🔹 User not found, entering if block")
                # print("❌ User not found in DB — redirecting to login")
                messages.error(request, "User not found.")
                print("🔹 Added error message about user not found")
                return redirect('spcb_home')
                print("🔹 Redirecting to spcb_home")

            # fresh_count = producerGeneralDetails.objects.filter(application_type=0, forwarded_to=user_id).count()
            # resubmit_count = producerGeneralDetails.objects.filter(application_type=1, forwarded_to=user_id).count()
            # print(f"📊 Fresh count: {fresh_count}, Resubmit count1: {resubmit_count}")

            print("🔹 Rendering change_password template")
            return render(request, 'auth/pwdchange/change_password_spcb.html',{'form': OTPForm()})
            print("🔹 Returned render response")

        def post(self, request):
            print("🔹 Entered ChangePasswordFirst POST method")
    
            user_id = request.session.get('user_id')
            print(f"🔹 user_id from session: {user_id}")
            print(f"🔹 Type of user_id: {type(user_id)}")
            
            if not user_id:
                print("🔹 user_id not found, entering if block")
                return redirect('spcb_home')
            
            # Check if user exists before decryption
            user_exists = StateUsers.objects.filter(id=user_id).exists()
            print(f"🔹 User exists in DB: {user_exists}")
            
            if not user_exists:
                print(f"🔹 No user found with id: {user_id}")
                print(f"🔹 All user ids in DB: {list(StateUsers.objects.values_list('id', flat=True))}")
                messages.error(request, "User not found. Please login again.")
                return redirect('spcb_home')
            print("🔹 Entered ChangePasswordFirst POST method")
            # print("🔹 Entered ChangePasswordFirst POST method")

            user_id = request.session.get('user_id')
            print(f"🔹 user_id from session: {user_id}")
            # print(f"🧑 Session user_id: {user_id}")

            if not user_id:
                print("🔹 user_id not found, entering if block")
                print("❌ No user_id in session")
                # messages.error(request, "Session expired. Please login again.")
                return redirect('spcb_home')
                print("🔹 Redirecting to spcb_home")
            
            enc_oldPassword = request.POST.get('old_password')
            print(f"🔹 enc_oldPassword retrieved: {enc_oldPassword}")
            enc_newPassword = request.POST.get('new_password')
            print(f"🔹 enc_newPassword retrieved: {enc_newPassword}")
            enc_confirmPassword = request.POST.get('confirm_password')
            print(f"🔹 enc_confirmPassword retrieved: {enc_confirmPassword}")

            # print(f"🔒 Encrypted old_password: {enc_oldPassword}")
            # print(f"🔒 Encrypted new_password: {enc_newPassword}")
            # print(f"🔒 Encrypted confirm_password: {enc_confirmPassword}")

            try:
                print("🔹 Entering try block for decryption")
                old_password = decrypt_aes(enc_oldPassword)
                print(f"🔹 old_password decrypted: {old_password}")
                new_password = decrypt_aes(enc_newPassword)
                print(f"🔹 new_password decrypted: {new_password}")
                confirm_password = decrypt_aes(enc_confirmPassword)
                print(f"🔹 confirm_password decrypted: {confirm_password}")
                # print(f"🔓 Decrypted old_password: {old_password}")
                # print(f"🔓 Decrypted new_password: {new_password}")
                # print(f"🔓 Decrypted confirm_password: {confirm_password}")
            except Exception as e:
                print("🔹 Entering except block for decryption error")
                # print(f"❌ Password decryption failed: {e}")
                messages.error(request, "Passwords not match")
                print("🔹 Added error message about password mismatch")
                return redirect('change-password-first-spcb')
                print("🔹 Redirecting to change-password-first-spcb")

            try:
                print("🔹 Entering try block to fetch user")
                user = StateUsers.objects.get(id=user_id)
                print(f"🔹 User fetched: {user.username}")
                # print(f"✅ User fetched: {user.username}")
            except StateUsers.DoesNotExist:
                print("🔹 Entering except block - user not found")
                # print("❌ User not found in DB")
                messages.error(request, "User not found.")
                print("🔹 Added error message about user not found")
                return redirect('change-password-first-spcb')
                print("🔹 Redirecting to change-password-first-spcb")

            # print("🔑 Checking old password...")
            print("🔹 Checking old password")
            if not check_password(old_password, user.password):
                print("🔹 Old password check failed")
                # print("❌ Old password is incorrect")
                messages.error(request, "Old password is incorrect.")
                print("🔹 Added error message about incorrect old password")
                return redirect('change-password-first-spcb')
                print("🔹 Redirecting to change-password-first-spcb")

            print("🔹 Checking if new password matches confirm password")
            if new_password != confirm_password:
                print("🔹 Password mismatch detected")
                # print("❌ New password and confirm password mismatch")
                messages.error(request, "New password and confirm password do not match.")
                print("🔹 Added error message about password mismatch")
                return redirect('change-password-first-spcb')
                print("🔹 Redirecting to change-password-first-spcb")

            # print("🧠 Validating new password strength...")
            print("🔹 Validating password strength")
            if not self.is_strong_password(new_password):
                print("🔹 Weak password detected")
                # print("❌ Weak password entered")
                messages.error(request, "Password must be at least 8 characters long and include uppercase, lowercase, digit, and special character.")
                print("🔹 Added error message about weak password")
                return redirect('change-password-first-spcb')
                print("🔹 Redirecting to change-password-first-spcb")

            # Check against last 3 passwords
            # print("📜 Checking password history...")
            print("🔹 Checking password history")
            password_history = json.loads(user.password_history or '[]')
            print(f"🔹 Password history loaded: {password_history}")
            recent_passwords = [user.password] + password_history[:2]
            print(f"🔹 Recent passwords for comparison: {recent_passwords}")

            for old_hashed in recent_passwords:
                print(f"🔹 Checking against old hashed password: {old_hashed}")
                if check_password(new_password, old_hashed):
                    print("🔹 New password matches old password")
                    # print("❌ New password matches one of the last 3 passwords")
                    messages.error(request, "New password must not match any of the last 3 passwords.")
                    print("🔹 Added error message about password history match")
                    return redirect('change-password-first-spcb')
                    print("🔹 Redirecting to change-password-first-spcb")

            # Update password
            # print("💾 Updating password...")
            print("🔹 Updating password")
            new_hashed = make_password(new_password)
            print(f"🔹 New password hashed: {new_hashed}")
            updated_history = [user.password] + password_history
            print(f"🔹 Updated history: {updated_history}")
            user.password_history = json.dumps(updated_history[:3])
            print(f"🔹 Password history saved: {user.password_history}")
            user.password = new_hashed
            print("🔹 Password field updated")
            user.first_login = 1
            print("🔹 first_login set to 1")
            user.save()
            print("🔹 User saved successfully")
            # print("✅ Password updated and saved")

            # print("📧 Sending new password email...")
            print("🔹 Sending new password email")
            # sendNewPasswordemail(user.username, user.company_email, new_password)
            sendNewPasswordEmail(user.company_name, user.username, user.company_email, new_password)
            print("🔹 Email sent")

            messages.success(request, "Password changed successfully.")
            print("🔹 Success message added")
            # print("🏁 Redirecting to rvsf_dashboard")
            print("🔹 Redirecting to rvsf_dashboard")
            return redirect('rvsf_dashboard')
            print("🔹 Returned redirect response")

        def is_strong_password(self, password):
            print(f"🔹 Entering is_strong_password method")
            print(f"🧩 Checking password strength for: {password}")
            result = (
                len(password) >= 8 and
                re.search(r'[A-Z]', password) and
                re.search(r'[a-z]', password) and
                re.search(r'\d', password) and
                re.search(r'[!@#$%^&*(),.?\":{}|<>]', password)
            )
            print(f"🔹 Password strength result: {result}")
            return result
            print(f"🔹 Returning from is_strong_password")
    except Exception as db_error:
                print("🔹 Entering outer except block for DB error")
                krishan_logger.exception("❌ ERROR while saving EquipmentEntry")
                print("🔹 Logged exception")
                krishan_logger.error(f"Exact DB Error: {str(db_error)}")
                print(f"🔹 Logged error: {db_error}")
                krishan_logger.info(f"Exact DB Error: {str(db_error)}")
                print("🔹 Logged info message")

# Create your views here.
def index(request):
    try:
        if request.method == 'POST':
            captcha_form = CaptchaForm(request.POST)

            if not captcha_form.is_valid():
                messages.error(request, 'Incorrect captcha entered')
                return redirect('spcb_home')

            try:
                enc_username = request.POST.get('username')
                enc_password = request.POST.get('password')

                if not enc_username or not enc_password:
                    raise ValueError("Missing encrypted credentials")

                username = rsa_decrypt(enc_username)
                raw_pwd = rsa_decrypt(enc_password)

                # First check if user exists
                user = StateUsers.objects.filter(username=username).first()
                if not user:
                    messages.error(request, 'Invalid credentials')
                    return redirect('spcb_home')

                # Then check if user is disabled
                if user.DisableStatus != 0:  # or user.DisableStatus == 1 depending on your model
                    messages.error(request, 'User Authentication disabled. Please contact the Administrator')
                    return redirect('spcb_home')

                if not check_password(raw_pwd, user.password):
                    messages.error(request, 'Invalid credentials')
                    return redirect('spcb_home')

                # ✅ LOGIN SUCCESS
                request.session['user_id'] = user.id
                request.session['role_id'] = user.RoleAccess
                request.session['officername'] = user.OfficerName
                request.session['user_role'] = "spcb"

                if user.first_login == 0:
                    print('yha tk hai')
                    return redirect('change-password-first-spcb')

                return redirect('dashboard')

            except Exception as e:
                print("LOGIN ERROR:", e)
                messages.error(request, 'Invalid encrypted payload')
                return redirect('spcb_home')

        else:
            request.session.flush()
            captcha_form = CaptchaForm()

        with open(settings.RSA_PUBLIC_KEY_PATH, "rb") as f:
            public_key_b64 = base64.b64encode(f.read()).decode()

        return render(request, 'auth/login.html', {
            'captcha_form': captcha_form,
            'public_key_b64': public_key_b64
        })
    except Exception as db_error:
        logger.exception("❌ ERROR while  endforgetpwdemail")
        logger.error(f"Exact endforgetpwdemail  Error: {str(db_error)}")
        
        logger.info(f"Exact endforgetpwdemail Error: {str(db_error)}")
# def index(request):
#     print(f"DEBUG: Request method = {request.method}")
    
#     if request.method == 'POST':
#         # DEBUG: Check if form is being received
#         print("DEBUG: POST request detected")
#         form = LoginForm(request.POST)  
#         print(f"DEBUG: Form created with data: {request.POST}")

#         if form.is_valid():  
#             # DEBUG: Form validation passed
#             print("DEBUG: Form is valid")
#             username = form.cleaned_data.get('username')
#             input_password = form.cleaned_data.get('password')
#             print(f"DEBUG: Username = {username}, Password = [HIDDEN]")
            
#             # DEBUG: Query database for user
#             user = StateUsers.objects.filter(username=username).first()
#             print(f"DEBUG: User query result = {user}")
            
#             if user is not None:  # check if user exists
#                 # DEBUG: User exists, check password
#                 print(f"DEBUG: User found: {user.username}")
#                 print(f"DEBUG: Stored password hash: {user.password}")
                
#                 if check_password(input_password, user.password):
#                     # DEBUG: Password matches
#                     print("DEBUG: Password check PASSED")
#                     request.session['user_id'] = user.id
#                     request.session['user_role'] = "spcb"
#                     print(f"DEBUG: Session set - user_id: {user.id}, user_role: spcb")
                    
#                     # DEBUG: Check session function
#                     # set_active_session("user", user.id, request)
#                     # print("DEBUG: Active session set")
                    
#                     # DEBUG: Check first login status
#                     print(f"DEBUG: user.first_login = {user.first_login}")
#                     if user.first_login == 0:
#                         print("DEBUG: Redirecting to change-password-first")
#                         # return redirect('change-password-first')
#                     else:
#                         print("DEBUG: Redirecting to spcb_dashboard")
#                         return redirect('dashboard')
#                 else:
#                     # DEBUG: Password doesn't match
#                     print("DEBUG: Password check FAILED")
#                     messages.error(request, "Invalid username or password.")
#                     print("DEBUG: Error message set - Invalid credentials")
#                     return redirect('spcb_home')
#             else:
#                 # DEBUG: User doesn't exist
#                 print("DEBUG: User not found in database")
#                 messages.error(request, "User Not Found.")
#                 print("DEBUG: Error message set - User not found")
#                 return redirect('spcb_home')

#         else:
#             # DEBUG: Form validation failed
#             print("DEBUG: Form is INVALID")
#             print(f"DEBUG: Form errors: {form.errors}")
#             messages.error(request, "Invalid captcha.")
#             print("DEBUG: Error message set - Invalid captcha")
#             return render(request, 'auth/login.html', {'form': form})
#     else:
#         # DEBUG: GET request
#         print("DEBUG: GET request detected")
#         form = LoginForm()
#         print("DEBUG: Empty form created")
    
#     # DEBUG: Final render for GET requests
#     print("DEBUG: Rendering login page with form")
#     with open(settings.RSA_PUBLIC_KEY_PATH, "rb") as f:
#             public_key_b64 = base64.b64encode(f.read()).decode()
#     return render(request, 'auth/login.html', {'form': form,"public_key_b64": public_key_b64})
#     # if request.method == 'POST':
#     #      captcha_form = CaptchaForm(request.POST or None)
#     #      print(captcha_form)
#     #      if  captcha_form.is_valid():
#     #         print('errorrrrrrr')
#     #         username = request.POST.get('username')
#     #         raw_pwd = request.POST.get('password')
#     #         disablestatus = StateUsers.objects.filter(username = username).first()
#     #         disable = disablestatus.DisableStatus

#     #         if disable == 1:
#     #             messages.error(request, 'Username is Disabled please contact CPCB Admin')
#     #             return redirect('spcb_home')
            

#     #         try:
#     #             user = StateUsers.objects.get(username=username)
#     #             if check_password(raw_pwd, user.password):
#     #                 request.session['user_id'] = user.id
#     #                 request.session['role_id'] = user.RoleAccess
#     #                 request.session['officername'] = user.OfficerName
#     #                 request.session['user_role'] = "spcb"
#     #                 return redirect('dashboard')
#     #             else:
#     #                 messages.error(request, 'Invalid credentials')
#     #                 return redirect('spcb_home')
#     #         except StateUsers.DoesNotExist:
#     #             messages.error(request, 'Invalid credentials')
#     #      else:
#     #         # If captcha errors
#     #         print('arjun uprit')
#     #         messages.error(request, 'Incorrect captcha entered')
#     #         return redirect('spcb_home')
#     # else:
#     #     request.session.flush()
#     #     captcha_form = CaptchaForm()
#     # request.session.flush()
#     # return render(request, 'auth/login.html', {
#     #     'captcha_form': captcha_form,
#     # })

# def index(request):
#     print(f"DEBUG: Request method = {request.method}")

#     # Always load public key for page
#     with open(settings.RSA_PUBLIC_KEY_PATH, "rb") as f:
#         public_key_b64 = base64.b64encode(f.read()).decode()

#     if request.method == "POST":
#         print("DEBUG: POST request detected")

#         # Captcha form validation FIRST
#         form = LoginForm(request.POST)
#         if not form.is_valid():
#             print("DEBUG: Captcha validation failed")
#             messages.error(request, "Invalid captcha.")
#             return render(
#                 request,
#                 "auth/login.html",
#                 {"form": form, "public_key_b64": public_key_b64},
#             )

#         # Read encrypted fields
#         encrypted_username = request.POST.get("username")
#         encrypted_password = request.POST.get("password")

#         if not encrypted_username or not encrypted_password:
#             print("DEBUG: Missing encrypted fields")
#             messages.error(request, "Invalid request.")
#             return redirect("spcb_home")

#         # RSA Decryption
#         try:
#             username = rsa_decrypt(encrypted_username).strip()
#             password = rsa_decrypt(encrypted_password).replace("\x00", "").strip()

#             print("DEBUG: RSA decryption successful")
#             print(f"DEBUG: Username = {username}")

#         except Exception as e:
#             print("RSA ERROR:", e)
#             messages.error(request, "Decryption failed.")
#             return redirect("spcb_home")

#         # User lookup
#         user = StateUsers.objects.filter(username=username).first()
#         if not user:
#             print("DEBUG: User not found")
#             messages.error(request, "Invalid username or password.")
#             return redirect("spcb_home")

#         # Password check
#         if not check_password(password, user.password):
#             print("DEBUG: Password mismatch")
#             messages.error(request, "Invalid username or password.")
#             return redirect("spcb_home")

#         # Login success
#         print("DEBUG: Login successful")

#         request.session["user_id"] = user.id
#         request.session["user_role"] = "spcb"

#         # Optional first-login logic
#         if getattr(user, "first_login", 1) == 0:
#             return redirect("change-password-first")

#         return redirect("dashboard")

#     # GET request
#     print("DEBUG: GET request detected")
#     form = LoginForm()

#     return render(
#         request,
#         "auth/login.html",
#         {"form": form, "public_key_b64": public_key_b64},
#     )


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('spcb_home')
        return view_func(request, *args, **kwargs)
    return wrapper        


 
@login_required
def Dashboard(request):
    try:
        userid = request.session.get('user_id')
        # print(userid)
        userdata = StateUsers.objects.filter(id = userid).first()
        if userdata.first_login == 0:
            messages.warning(request, "Please change your password to continue.")
            return redirect('change-password-first-spcb') 
        # print(userdata)
        submitted = ConfirmApplication.objects.filter(state_id = userdata.State_id).count()
        scrutiny1 = ConfirmApplication.objects.filter(state_id = userdata.State_id , appstatus__in=[2,3,5],incomplete=0).count()
        # print(scrutiny1,'dgs')
        countapproving = ConfirmApplication.objects.filter(state_id = userdata.State_id , role_id = '1',incomplete=0).count()
        countreporting = ConfirmApplication.objects.filter(state_id = userdata.State_id , role_id = '2',incomplete=0).count()
        countverifying = ConfirmApplication.objects.filter(state_id = userdata.State_id , role_id = '3',incomplete=0).count()
        # print(countapproving)
        application = {}

        submitted_apps = ConfirmApplication.objects.filter(paymentModeStatus='Completed',state_id=userdata.State_id).count()
        new_application = ConfirmApplication.objects.filter(paymentModeStatus='Completed',appstatus='1',state_id=userdata.State_id).count()
        scrutiny = ConfirmApplication.objects.filter(paymentModeStatus='Completed', appstatus__in=[2, 3, 5], state_id=userdata.State_id).count()
        forapproval = ConfirmApplication.objects.filter(paymentModeStatus='Completed',appstatus='8',state_id=userdata.State_id).count()
        approved = ConfirmApplication.objects.filter(paymentModeStatus='Completed',appstatus='4',state_id=userdata.State_id,incomplete=0).count()
        rejected = ConfirmApplication.objects.filter(paymentModeStatus='Completed',appstatus='7',state_id=userdata.State_id).count()
        certified = ConfirmApplication.objects.filter(paymentModeStatus='Completed',appstatus='9',state_id=userdata.State_id).count()
        inspection = ConfirmApplication.objects.filter(paymentModeStatus='Completed',state_id=userdata.State_id,incomplete=1).count()
        verifiers=StateUsers.objects.filter(State_id=userdata.State_id,RoleAccess=3).count()
        print(verifiers,'count')
        # success_count1 = Payment.objects.filter(status='success').count()

        # print('count', success_count)

        application['completed_application'] = submitted_apps
        application['newapplications'] = new_application
        application['undclarification_required'] = scrutiny1
        application['forapproval'] = forapproval
        application['approved'] = approved
        application['rejected'] = rejected
        application['certified'] = certified
        application['inspection'] = inspection

        # print('application dict:', application)

        return render(request , 'dashboard.html' , {'userdata': userdata ,
                                                    'submitted': submitted,
                                                    'scrutiny' : scrutiny,
                                                    'approving' : countapproving,
                                                    'reporting': countreporting,
                                                    'verifying' : countverifying,
                                                    'application':application,
                                                    'verifiers':verifiers
                                                    })
    except Exception as db_error:
        logger.exception("❌ ERROR while  dashboard")
        logger.error(f"Exact dashboard  Error: {str(db_error)}")
        
        logger.info(f"Exact dashboard Error: {str(db_error)}")
# def generate_username_from_email(email):
#     # base = email.split('@')[0]
#     # while True:
#     #     suffix = ''.join(random.choices(string.digits, k=4))
#     #     username = f"{base}{suffix}"
#     #     if not StateUsers.objects.filter(username=username).exists():
#     #         return username
#     year_suffix = datetime.now().strftime('%y')
#     sequence_file = 'sequence_spcb.txt'

#     # Load last used sequence
#     if os.path.exists(sequence_file):
#         with open(sequence_file, 'r') as f:
#             last_seq = int(f.read().strip())
#     else:
#         last_seq = 0

#     # Increment and save new sequence
#     new_seq = last_seq + 1
#     with open(sequence_file, 'w') as f:
#         f.write(str(new_seq))

#     sequence_str = str(new_seq).zfill(2)  
#     return f'SPCB{year_suffix}{sequence_str}'



def generate_username_from_email(OfficerName):

    # base = email.split('@')[0]
    # while True:
    #     suffix = ''.join(random.choices(string.digits, k=4))
    #     username = f"{base}{suffix}"
    #     if not StateUsers.objects.filter(username=username).exists():
    #         return username
    year_suffix = datetime.now().strftime('%y')
    # sequence_file = 'sequence_spcb.txt'

    # # Load last used sequence
    # if os.path.exists(sequence_file):
    #     with open(sequence_file, 'r') as f:
    #         last_seq = int(f.read().strip())
    # else:
    #     last_seq = 0

    # # Increment and save new sequence
    # new_seq = last_seq + 1
    # with open(sequence_file, 'w') as f:
    #     f.write(str(new_seq))

    # sequence_str = str(new_seq).zfill(2)  
    return f'SPCB{year_suffix}{OfficerName}'


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


@login_required
def addspcbuser(request):
    try:
        userid = request.session.get('user_id')
        userdata = StateUsers.objects.filter(id = userid).first()
        # print(userdata.RoleAccess,'sfsfsf')
        if userdata.RoleAccess != '2':
            return redirect('dashboard')


        statename = State.objects.filter(state_id = userdata.State_id).first()
        districts = District.objects.filter(state_id=userdata.State_id).values('city_id', 'city_name')

        if request.method == 'POST':
            userid = request.session.get('user_id')
            OfficerName = request.POST.get('OfficerName')
            auth_email = request.POST.get('auth_email')
            # username = generate_username_from_email(auth_email)
            username = generate_username_from_email(OfficerName)
            auth_mobile = request.POST.get('auth_mobile')
            # officerDesignation = request.POST.get('officerDesignation')

            spcb_user_fields = {
                'OfficerName': OfficerName,
                
                'username': username,
                'auth_mobile': auth_mobile
            }
            for field, value in spcb_user_fields.items():
                print(f"Validating field {field} => {value}")

                if value:
                    value = value.strip()
                    print(f"Stripped value for {field}: {value}")

                    
                    # Validate that TIN, CIN, IEC don't have special characters
                    # (excluding spaces since your regex allows spaces)
                    if field in ['OfficerName', 'username','auth_mobile']:
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
                            return redirect('addspcbuser')
            # password = request.POST.get('password')
            # confirmpwd = request.POST.get('confirmpassword')

            user_exists = StateUsers.objects.filter(Q(auth_email=auth_email) | Q(auth_mobile=auth_mobile)).exists()
            # print(user_exists)

            if user_exists:
                messages.error(request, "User Already Exists")
                return redirect('addspcbuser')


            if not auth_mobile.isdigit() or len(auth_mobile) != 10:
                messages.error(request, "Invalid mobile number. It must be 10 digits.")
                return redirect("addspcbuser")

            # if password != confirmpwd:
            #     messages.error(request, "Password and Confirm Password do not match.")
            #     return redirect("addspcbuser")  # reload form

            # ✅ (Optional) Validate password strength
            # if len(password) < 8:
            #     messages.error(request, "Password must be at least 8 characters long.")
            #     return redirect("addspcbuser")
            
            password = generate_password()
            hashpwd = make_password(password)
            # print(password)
            # print(username)
            # password_hashed = make_password(password)
            
            State_id = userdata.State_id
            District_id = request.POST.get('District_id')
            StateUsers.objects.create(
                OfficerName = OfficerName,
                auth_email = auth_email,
                auth_mobile = auth_mobile,
                officerDesignation = 'Reviewing Officer',
                State_id = State_id,
                District_id = District_id,
                RoleAccess = '3',
                username = username,
                password  = hashpwd          
            )
            sendSignupEmail(OfficerName, username, auth_email, password)

            return redirect('dashboard')
        
        return render(request ,'usermanagement/adduser.html' , {'userdata': userdata , 'districts' : districts , 'statename':statename})
    except Exception as db_error:
        logger.exception("❌ ERROR while  addspcbuser")
        logger.error(f"Exact addspcbuser  Error: {str(db_error)}")
        
        logger.info(f"Exact addspcbuser Error: {str(db_error)}")

@login_required   
def viewusers(request):
    try:
        userid = request.session.get('user_id')
        # userdata = StateUsers.objects.exclude(RoleAccess__in=[1, 2])
        masteruser = StateUsers.objects.filter(id = userid).first()
        userdata = StateUsers.objects.filter(~Q(RoleAccess__in=[1, 2]),State_id=masteruser.State_id )
        if masteruser.RoleAccess != '2':
            return redirect('dashboard')
        district_map = {d.city_id: d.city_name for d in District.objects.all()}

        for user in userdata:
            user.district_name = district_map.get(user.District_id, 'Unknown')
        return render(request , 'usermanagement/listusers.html' , {
            'data': userdata,
            'userdata': masteruser
        })
    except Exception as db_error:
        logger.exception("❌ ERROR while  viewusers")
        logger.error(f"Exact viewusers  Error: {str(db_error)}")
        
        logger.info(f"Exact viewusers Error: {str(db_error)}")


def toggle_user_status(request, user_id):
    user = StateUsers.objects.filter(id=user_id).first()
    if user:
        user.DisableStatus = 1 if user.DisableStatus == 0 else 0
        user.save()
    return redirect('viewusers')



def get_user_applications(request, user_id):
    try:

        # Get state of deleting user
        user = StateUsers.objects.only('State_id').get(id=user_id)

        # Subquery to get username from RvsfRegistration
        username_subquery = RvsfRegistration.objects.filter(
            id=OuterRef('userid')
        ).values('username')[:1]

        applications = ConfirmApplication.objects.filter(
            marked_to_id=user_id
        ).annotate(
            username=Subquery(username_subquery)
        )

        # Verifiers (RoleAccess = '3')
        verifiers = StateUsers.objects.filter(
            RoleAccess='3',
            State_id=user.State_id
        )

        return JsonResponse({
            'applications': list(applications.values(
                'id',
                'username',
                'appstatus',
                'created_at'
            )),
            'verifiers': list(verifiers.values(
                'id',
                'OfficerName'
            ))
        })
    except Exception as db_error:
        logger.exception("❌ ERROR while  getuserapp")
        logger.error(f"Exact getuserapp  Error: {str(db_error)}")
        
        logger.info(f"Exact getuserapp Error: {str(db_error)}")
    
def delete_user(request, user_id):
    if request.method == "POST":
        new_user_id = request.POST.get('new_user_id')

        # Reassign applications
        ConfirmApplication.objects.filter(
            marked_to_id=user_id
        ).update(marked_to_id=new_user_id)

        # Delete user
        StateUsers.objects.filter(id=user_id).delete()

        return redirect('viewusers')

@login_required
def viewroles(request):
    try:
        userdata = StateUsers.objects.exclude(RoleAccess = 1)
        userid = request.session.get('user_id')
        masteruser = StateUsers.objects.filter(id = userid).first()
        if masteruser.RoleAccess != '2':
            return redirect('dashboard')
        district_map = {d.city_id: d.city_name for d in District.objects.all()}

        for user in userdata:
            user.district_name = district_map.get(user.District_id, 'Unknown')

        with open(settings.RSA_PUBLIC_KEY_PATH, "rb") as f:
                public_key_b64 = base64.b64encode(f.read()).decode()
        return render(request , 'usermanagement/AddNewRole.html' , {
            'data': userdata,
            'userdata': masteruser,
            "public_key_b64": public_key_b64
        })
    except Exception as db_error:
        logger.exception("❌ ERROR while  viewroles")
        logger.error(f"Exact viewroles  Error: {str(db_error)}")
        
        logger.info(f"Exact viewroles Error: {str(db_error)}")

@login_required
# def viewapplication(request):
#     if request.method == 'POST':
#         userid = request.POST.get('userid')  
#         print(userid)
   
#     entity = RvsfRegistration.objects.filter(id = userid).first()
#     generaldata = GeneralDetails.objects.filter(userid=userid).first()
#     statename = State.objects.filter(state_id=entity.state).first()
#     districtname = District.objects.filter(city_id=entity.district).first()
    
#     equipmentdata = EquipmentType.objects.all().order_by('id')
#     data = EquipmentEntry.objects.filter(userid = userid)
#     facilitydata = RvsfFacility.objects.filter(user_id = userid).first()
#     vehicleTypeData = VehicleType.objects.filter(userid=userid)
#     capacityPlant = PlantCapacity.objects.filter(userid =  userid).first()
#     pollutiondetails = PollutionDevice.objects.filter(userid = userid)
#     wasterecycled = WasteRecycled.objects.filter(userid = userid)
     

#     return render(request,'processing/viewapplication.html', {'entity' : entity ,
#      'general' : generaldata , 'statename': statename, 'districtname':districtname,
#       'equipmentdata': equipmentdata, 'data':data, 'facilitydata': facilitydata,
#       'VechileType': vehicleTypeData, 'capacitydata':capacityPlant,'pollutiondetails':pollutiondetails,'wasterecycled':wasterecycled                                          
#     })

# def viewapplication(request):
#     print(request.POST)
#     if request.method == 'POST':
#         userid = request.POST.get('userid')
#     else:
#         userid = request.GET.get('userid')

#     cache_key = f"viewapp_user_{userid}"
#     cached_context = cache.get(cache_key)
#     if cached_context:
#         return render(request, 'processing/viewapplication.html', cached_context)

#     print(userid)
#     entities = RvsfRegistration.objects.filter(id=userid).first()
#     generaldatainfo = GeneralDetails.objects.filter(userid=userid).first()
#     rvsfdatainfo = RvsfDetails.objects.filter(userid=userid).first()
#     print(entities,'gjkh')
#     print(rvsfdatainfo,('ffeefefeef'))
#     # ... other queries ...

#     context = {
#         'entity': entities,
#         'general': generaldatainfo,
#         'rvsf': rvsfdatainfo,
#         'statename': State.objects.filter(state_id=entities.state).first(),
#         'districtname': District.objects.filter(city_id=entities.district).first(),
#         'equipmentdata': EquipmentType.objects.all().order_by('id'),
#         'data': EquipmentEntry.objects.filter(userid=userid),
#         'facilitydata': RvsfFacility.objects.filter(user_id=userid).first(),
#         'VechileType': VehicleType.objects.filter(userid=userid),
#         'capacitydata': PlantCapacity.objects.filter(userid=userid).first(),
#         'pollutiondetails': PollutionDevice.objects.filter(userid=userid),
#         'wasterecycled': WasteRecycled.objects.filter(userid=userid),
#     }

#     cache.set(cache_key, context, 60 * 5)  # cache for 5 minutes
#     return render(request, 'processing/viewapplication.html', context)
    

@require_POST
def viewapplication(request):
    try:
        # print(request.POST)

        userid = request.POST.get('userid')

        if not userid or not userid.isdigit():
            return redirect('dashboard')

        userid = int(userid)

        cache_key = f"viewapp_user_{userid}"
        cached_context = cache.get(cache_key)
        if cached_context:
            return render(request, 'processing/viewapplication.html', cached_context)

        entities = RvsfRegistration.objects.filter(id=userid).first()
        if not entities:
            return redirect('dashboard')

        generaldatainfo = GeneralDetails.objects.filter(userid=userid).first()
        rvsfdatainfo = RvsfDetails.objects.filter(userid=userid).first()

        context = {
            'entity': entities,
            'general': generaldatainfo,
            'rvsf': rvsfdatainfo,
            'statename': State.objects.filter(state_id=entities.state).first(),
            'districtname': District.objects.filter(city_id=entities.district).first(),
            'equipmentdata': EquipmentType.objects.all().order_by('id'),
            'data': EquipmentEntry.objects.filter(userid=userid),
            'facilitydata': RvsfFacility.objects.filter(user_id=userid).first(),
            'VechileType': VehicleType.objects.filter(userid=userid),
            'capacitydata': PlantCapacity.objects.filter(userid=userid).first(),
            'pollutiondetails': PollutionDevice.objects.filter(userid=userid),
            'wasterecycled': WasteRecycled.objects.filter(userid=userid),
        }

        cache.set(cache_key, context, 60 * 5)
        return render(request, 'processing/viewapplication.html', context)
    except Exception as db_error:
        logger.exception("❌ ERROR while  viewapp")
        logger.error(f"Exact viewapp  Error: {str(db_error)}")
        
        logger.info(f"Exact viewapp Error: {str(db_error)}")

def decrypt_aes(encrypted_text):
    key = b"16charSecretKey!"  # same as client
    iv = b"16charSecretIV!!"   # same as client
    encrypted_bytes = base64.b64decode(encrypted_text)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
    pad_len = decrypted_padded[-1]
    return decrypted_padded[:-pad_len].decode('utf-8')


@login_required
# def updateRole(request):
#     if request.method != "POST":
#         messages.error(request, "Invalid request.")
#         return redirect("viewusers")

#     encrypted_payload = request.POST.get("hidden_id")

#     if len(encrypted_payload) < 300:
#         messages.error(request, "Invalid encrypted payload.")
#         return redirect("viewroles")

#     if not encrypted_payload:
#         messages.error(request, "Missing payload.")
#         return redirect("viewusers")

#     try:
#         # 🔐 RSA decrypt (SAME as login)
#         decrypted_json = rsa_decrypt(encrypted_payload)
#         data = json.loads(decrypted_json)

#         userid = int(data.get("userid"))
#         role   = int(data.get("role"))

#     except Exception as e:
#         print("RSA ERROR:", e)
#         messages.error(request, "Invalid encrypted data.")
#         return redirect("viewusers")

#     # ✅ Validate role
#     if role not in (2, 3):
#         messages.error(request, "Invalid role selected.")
#         return redirect("viewusers")

#     spcbuser = StateUsers.objects.filter(id=userid).first()
#     if not spcbuser:
#         messages.error(request, "User not found.")
#         return redirect("viewusers")

#     spcbuser.RoleAccess = role
#     spcbuser.save()

#     messages.success(
#         request,
#         f"Role updated successfully for {spcbuser.OfficerName}."
#     )

#     return redirect("viewusers")


# def updateRole(request):
#     if request.method == 'POST':
#         encrypted_payload = request.POST.get('hidden_id')

#         data = json.loads(decrypt_aes(request.POST["hidden_id"]))
#         userid = data["userid"]
#         # role = data["role"]

#         spcbuser = StateUsers.objects.filter(id=userid).first()
#         # spcbuser.RoleAccess = role
#         spcbuser.RoleAccess = 3
#         spcbuser.save()

#         messages.success(request, f"Role updated successfully for {spcbuser.OfficerName}.") 
#         return redirect('viewusers')
# # def updateRole(request):
#     if request.method == 'POST':
#         userid = request.POST.get('hidden_id')
#         roletype = request.POST.get('roleassign')
#         spcbuser = StateUsers.objects.filter(id = userid).first()
#         spcbuser.RoleAccess = roletype
#         spcbuser.save()
#         messages.success(request, f"Role updated successfully for {spcbuser.OfficerName}.") 
#         return redirect('viewusers')
    

@login_required
def rvsf_applications(request):
    try:
        session_id = request.session.get('user_id')
        resubmit = 0
        userinfo = StateUsers.objects.filter(id=session_id).first()
        
        if not userinfo:
            # Handle case where userinfo is None
            return redirect('login')  # or appropriate error handling
        
        # print('rvsf_apps', session_id, userinfo.RoleAccess)

        # Read resubmit only if POST
        if request.method == 'POST':
            resubmit = int(request.POST.get('resubmit', 0))
            # print("Resubmit:", resubmit)

        # ROLE BASED SETTINGS
        if userinfo.RoleAccess == '1':
            Roles = {'2': 'Recommending Authority', '3': 'Verification Authority'}
            fetchappstage = ApplicationStatus.objects.filter(
                DisableStatus=0, RoleAccess__in=[3, 1]
            )

        elif userinfo.RoleAccess == '2':
            Roles = {'1': 'Approving Authority', '3': 'Verification Authority'}
            fetchappstage = ApplicationStatus.objects.filter(
                DisableStatus=0, RoleAccess__in=[3, 2]
            )

        elif userinfo.RoleAccess == '3':
            Roles = {'2': 'Recommending Authority'}
            fetchappstage = ApplicationStatus.objects.filter(
                DisableStatus=0, RoleAccess__in=[3, 2]
            )

        # FILTER CONDITION BASED ON RESUBMIT
        response_filter = 1 if resubmit == 1 else 0
        
        # CORRECTED CONDITION
        if userinfo.RoleAccess in ['1', '2']: 
            # print('yha pe check kr rha hu') # Check if RoleAccess is 1 OR 2
            applications = ConfirmApplication.objects.filter(
                state_id=userinfo.State_id,
                role_id=userinfo.RoleAccess,
                incomplete=0,
                paymentstatus=1,
                response=response_filter
            ).exclude(appstatus=7).annotate(
                company_name=Subquery(
                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
                ),
                username=Subquery(
        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('username')[:1]
    ),
                registered_address=Subquery(
                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
                ),
                company_email=Subquery(
                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
                ),
                unit_pan=Subquery(
                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
                ),
                pin_code=Subquery(
                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
                )
            )
        else:  # Role 3
            # print('nhi yha hu',userinfo.RoleAccess)
            applications = ConfirmApplication.objects.filter(
                state_id=userinfo.State_id,
                marked_to_id=session_id,
                role_id=userinfo.RoleAccess,
                incomplete=0,
                paymentstatus=1,
                response=response_filter
            ).exclude(appstatus=7).annotate(
                company_name=Subquery(
                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
                ),
                username=Subquery(
        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('username')[:1]
    ),
                registered_address=Subquery(
                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
                ),
                company_email=Subquery(
                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
                ),
                unit_pan=Subquery(
                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
                ),
                pin_code=Subquery(
                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
                )
            )

        # print(applications)

        return render(request, 'processing/rvsfapplications.html', {
            'data': applications,
            'userinfo': userinfo,
            'fetchappstage': fetchappstage,
            'Roles': Roles
        })
    except Exception as db_error:
        logger.exception("❌ ERROR while  rvsfapp")
        logger.error(f"Exact rvsfapp  Error: {str(db_error)}")
        
        logger.info(f"Exact rvsfapp Error: {str(db_error)}")


import re
@login_required
def mark_application(request):
    try:
        if request.method != 'POST':
            return redirect('dashboard')

        # -----------------------------
        # Fetch POST + SESSION data
        # -----------------------------
        user_ses_id = request.session.get('user_id')

        userid = request.POST.get('userid')
        appno = request.POST.get('appno')
        marked_to_role = request.POST.get('marked_to_role')  # string
        comment = request.POST.get('comment')
        appstatus1 = request.POST.get('appstatus1')
        appstat = request.POST.get('appstatus')              # string
        marked_to_verifying = request.POST.get('marked_to_verifying')

        # -----------------------------
        # Validation: comment
        # -----------------------------
        if not comment:
            messages.error(request, 'Remarks Are Required Before Assigning It !')
            base_url = reverse('checklist')
            params = urlencode({'userid': userid, 'appno': appno})
            return redirect(f"{base_url}?{params}")

        comment = comment.strip()

        if re.search(r'[^a-zA-Z0-9\s.]', comment):
            messages.error(request, "Comment should not contain special characters.")
            return redirect('dashboard')

        # -----------------------------
        # Normalize status values
        # -----------------------------
        appstatus = '5' if appstatus1 == '5' else appstat

        try:
            marked_to_role_int = int(marked_to_role)
            appstat_int = int(appstat)
            marked_to_verifying = int(marked_to_verifying) if marked_to_verifying else None
        except (TypeError, ValueError):
            messages.error(request, "Invalid data received.")
            return redirect('dashboard')

        # -----------------------------
        # Auto-assign role when appstatus == 4
        # -----------------------------
        if appstat_int == 4:
            marked_to_role_int = 2

        # -----------------------------
        # Fetch logged-in SPCB user
        # -----------------------------
        spcbuser = StateUsers.objects.filter(id=user_ses_id).first()
        if not spcbuser:
            messages.error(request, "Invalid session user.")
            return redirect('dashboard')

        marked_by_role = spcbuser.RoleAccess
        stateid = spcbuser.State_id

        # =====================================================
        # CASE 1 : ROLE 1 or 2
        # =====================================================
        if marked_to_role_int in (1, 2):

            fetchmarkedDetails = StateUsers.objects.filter(
                RoleAccess=marked_to_role_int,
                State_id=stateid
            ).first()

            if not fetchmarkedDetails:
                messages.error(request, "User to mark not found.")
                return redirect('dashboard')

            ApplicationTrail.objects.create(
                AppNo=appno,
                stateid=stateid,
                marked_to_designation=fetchmarkedDetails.officerDesignation,
                marked_by_designation=spcbuser.officerDesignation,
                marked_to_role=marked_to_role_int,
                marked_by_role=marked_by_role,
                comment=comment,
                added_by_userid=spcbuser.id,
                added_by_person=spcbuser.OfficerName,
                added_to_person=fetchmarkedDetails.OfficerName,
                added_to_userid=fetchmarkedDetails.id,
                industry_user_id=userid
            )

            updateunit = ConfirmApplication.objects.filter(appno=appno).first()
            if updateunit:
                if marked_to_role == '1':
                    # print('ujghlskhgvkj')
                    updateunit.role_id = marked_to_role_int
                    # print(marked_to_role,'625655465651')
                    updateunit.appstatus = 8
                    updateunit.marked_to_id = fetchmarkedDetails.id
                    updateunit.marked_by_id = spcbuser.id
                    updateunit.save()
                else:
                    updateunit.role_id = marked_to_role_int
                    # print(marked_to_role,'625655465651')
                    updateunit.appstatus = appstatus
                    updateunit.marked_to_id = fetchmarkedDetails.id
                    updateunit.marked_by_id = spcbuser.id
                    updateunit.save()

        # =====================================================
        # CASE 2 : ROLE 3 (Verifier)
        # =====================================================
        elif marked_to_role_int == 3:

            if not marked_to_verifying:
                messages.error(request, "Verifying officer not selected.")
                return redirect('dashboard')

            markedtoofficer = StateUsers.objects.filter(id=marked_to_verifying).first()
            if not markedtoofficer:
                messages.error(request, "Verifying officer not found.")
                return redirect('dashboard')

            ApplicationTrail.objects.create(
                AppNo=appno,
                stateid=stateid,
                marked_to_designation=markedtoofficer.officerDesignation,
                marked_by_designation=spcbuser.officerDesignation,
                marked_to_role=3,
                marked_by_role=marked_by_role,
                comment=comment,
                added_by_userid=spcbuser.id,
                added_by_person=spcbuser.OfficerName,
                added_to_person=markedtoofficer.OfficerName,
                added_to_userid=markedtoofficer.id,
                industry_user_id=userid
            )

            updateunit = ConfirmApplication.objects.filter(appno=appno).first()
            if updateunit:
                updateunit.role_id = 3
                updateunit.appstatus = appstatus
                updateunit.marked_to_id = markedtoofficer.id
                updateunit.marked_by_id = spcbuser.id
                updateunit.save()

        else:
            messages.error(request, "Invalid role selected.")
            return redirect('dashboard')

        messages.success(request, 'Application successfully marked.')
        return redirect('dashboard')
    except Exception as db_error:
        logger.exception("❌ ERROR while  mark app")
        logger.error(f"Exact mark app  Error: {str(db_error)}")
        
        logger.info(f"Exact mark app Error: {str(db_error)}")

    
     
@login_required
def get_trails(request):
    # print("entered")
    appno = request.GET.get('appno')
    # print(appno)
    # trails1 = ApplicationTrail.objects.filter(id=56).order_by('-created_at')
    # for trail in trails1:
    #     print(vars(trail))
    try:
        trails = ApplicationTrail.objects.filter(AppNo=appno).order_by('-created_at')
        # print(trails)
        trail_data = [{
            'user': trail.added_by_person,
            'designation': trail.marked_by_designation,
            # 'date': trail.created_at.strftime("%d-%m-%Y %H:%M"),
            'date': timezone.localtime(trail.created_at).strftime("%d-%m-%Y %H:%M"),
            'comment': trail.comment,
            'marked_to_role': trail.marked_to_role,
        } for trail in trails]


        # print(trail_data)
        return JsonResponse({'trails': trail_data})
    
    except Exception as e:
        print("Error:", str(e))
        return JsonResponse({'error': str(e)}, status=500)

def upload_attested_certificate(request):
    try:
        if request.method == 'POST' and request.FILES.get('attested_certificate'):
            from django.conf import settings
            print(f"MEDIA_ROOT from settings: {settings.MEDIA_ROOT}")
            print(f"BASE_DIR from settings: {settings.BASE_DIR}")
            try:
                userid = request.POST.get('userid')
                appno = request.POST.get('appno')
                certificate_file = request.FILES['attested_certificate']
                
                # Validate file size (max 2MB)
                if certificate_file.size > 2 * 1024 * 1024:
                    return JsonResponse({
                        'success': False,
                        'message': 'File size must be less than 2MB.'
                    })
                
                # Validate file extension
                allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
                file_ext = os.path.splitext(certificate_file.name)[1].lower()
                if file_ext not in allowed_extensions:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid file format. Allowed formats: PDF, DOC, DOCX, JPG, JPEG, PNG.'
                    })
                
                # Get the RvsfRegistration instance
                rvsf_reg = RvsfRegistration.objects.filter(id=userid).first()
                if not rvsf_reg:
                    return JsonResponse({
                        'success': False,
                        'message': 'User not found.'
                    })
                
                # Delete old certificate if exists
                if rvsf_reg.attested_certificate:
                    # Delete the file from storage
                    rvsf_reg.attested_certificate.delete(save=False)
                
                # Save the file directly to the FileField (like EquipmentEntry does)
                # The upload_to function in the model will handle the path
                rvsf_reg.attested_certificate.save(certificate_file.name, certificate_file, save=False)
                rvsf_reg.attested_certificate_uploaded_at = timezone.now()
                rvsf_reg.save()
                
                # Also update the ConfirmApplication if needed
                confirm_app = ConfirmApplication.objects.filter(userid=userid, appno=appno).first()
                confirm_app.certificateattested=1
                confirm_app.save()
                if confirm_app:
                    # You can add a field to track this in ConfirmApplication too if needed
                    pass
                
                return JsonResponse({
                    'success': True,
                    'message': 'Certificate uploaded successfully!',
                    'certificate_url': rvsf_reg.attested_certificate.url,
                    'uploaded_at': rvsf_reg.attested_certificate_uploaded_at.strftime('%Y-%m-%d %H:%M')
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error uploading certificate: {str(e)}'
                })
        
        return JsonResponse({
            'success': False,
            'message': 'Invalid request.'
        })
    except Exception as db_error:
        logger.exception("❌ ERROR while  upload attest")
        logger.error(f"Exact upload attest  Error: {str(db_error)}")
        
        logger.info(f"Exact upload attest Error: {str(db_error)}")


def get_certificate_info(request):
    try:
        userid = request.GET.get('userid')

        if not userid:
            return JsonResponse({
                'success': False,
                'message': 'User ID is required'
            })

        rvsf_reg = RvsfRegistration.objects.filter(id=userid).first()

        if rvsf_reg and rvsf_reg.attested_certificate:
            return JsonResponse({
                'success': True,
                'certificate_url': reverse(
                    'protected_file_spcb',
                    kwargs={'path': rvsf_reg.attested_certificate.name}
                ),
                'uploaded_at': (
                    rvsf_reg.attested_certificate_uploaded_at.strftime('%Y-%m-%d %H:%M')
                    if rvsf_reg.attested_certificate_uploaded_at else ''
                )
            })

        return JsonResponse({
            'success': False,
            'message': 'No certificate found'
        })
    except Exception as db_error:
        logger.exception("❌ ERROR while  get certificate info")
        logger.error(f"Exact get certificate info  Error: {str(db_error)}")
        
        logger.info(f"Exact get certificate info Error: {str(db_error)}")

def debug_upload_test(request):
    """Test file upload directly"""
    try:
        if request.method == 'POST' and request.FILES.get('test_file'):
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            import os
            
            test_file = request.FILES['test_file']
            
            # Test 1: Direct storage save
            test_path = f"RVSFDocs/test_{os.urandom(4).hex()}.txt"
            try:
                saved_path = default_storage.save(test_path, ContentFile(b'test content'))
                result1 = f"Direct storage save SUCCESS: {saved_path}"
                
                # Clean up
                default_storage.delete(saved_path)
            except Exception as e:
                result1 = f"Direct storage save FAILED: {str(e)}"
            
            # Test 2: Model save
            try:
                userid = request.POST.get('userid', 53)  # Use the ID from your logs
                rvsf_reg = RvsfRegistration.objects.filter(id=userid).first()
                if rvsf_reg:
                    # Reset file pointer
                    test_file.seek(0)
                    
                    # Save using model
                    rvsf_reg.attested_certificate.save(test_file.name, test_file, save=False)
                    rvsf_reg.save()
                    
                    result2 = f"Model save SUCCESS: {rvsf_reg.attested_certificate.path}"
                    
                    # Clean up
                    if rvsf_reg.attested_certificate:
                        rvsf_reg.attested_certificate.delete(save=False)
                else:
                    result2 = "User not found"
            except Exception as e:
                result2 = f"Model save FAILED: {str(e)}"
            
            return JsonResponse({
                'direct_storage': result1,
                'model_save': result2,
                'file_name': test_file.name,
                'file_size': test_file.size,
                'file_content_type': test_file.content_type
            })
        
        return JsonResponse({'error': 'No file provided'})
    except Exception as db_error:
        logger.exception("❌ ERROR while  debug upload test")
        logger.error(f"Exact debug upload test  Error: {str(db_error)}")
        
        logger.info(f"Exact debug upload test Error: {str(db_error)}")

def check_media_permissions(request):
    try:
        """Check media directory permissions"""
        import os
        import stat
        from django.conf import settings
        
        media_root = settings.MEDIA_ROOT
        target_dir = os.path.join(media_root, 'RVSFDocs/attested_certificates')
        
        # Create directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        permissions = {
            'media_root': {
                'path': media_root,
                'exists': os.path.exists(media_root),
                'is_dir': os.path.isdir(media_root),
                'permissions': oct(os.stat(media_root).st_mode)[-3:] if os.path.exists(media_root) else 'N/A',
                'writable': os.access(media_root, os.W_OK) if os.path.exists(media_root) else False
            },
            'target_dir': {
                'path': target_dir,
                'exists': os.path.exists(target_dir),
                'is_dir': os.path.isdir(target_dir),
                'permissions': oct(os.stat(target_dir).st_mode)[-3:] if os.path.exists(target_dir) else 'N/A',
                'writable': os.access(target_dir, os.W_OK) if os.path.exists(target_dir) else False
            }
        }
        
        # Try to create a test file
        test_file = os.path.join(target_dir, 'test_write.txt')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            permissions['can_write'] = True
            os.remove(test_file)
        except Exception as e:
            permissions['can_write'] = False
            permissions['write_error'] = str(e)
        
        return JsonResponse(permissions)
    except Exception as db_error:
        logger.exception("❌ ERROR while  check media permission")
        logger.error(f"Exact check media permission  Error: {str(db_error)}")
        
        logger.info(f"Exact check media permission Error: {str(db_error)}")

# def list_rvsf(request):
#     applications = []
#     if request.method == 'POST':
#         # No, this is not correct. You cannot use an empty subscript like request.POST[].
#         # If you want to print all POST data:
#         print(request.POST)
#         userid = request.session.get('user_id')
#         user = StateUsers.objects.filter(id=userid).first()
#         if user:
#             print('444')
#             # print(f"ID: {user.id}, Username: {user.username}")
#             # print(userid, 'fghhfh')
#             # print(user, 'fghhfh')
#             status = request.POST.get('status')
#             incomplete = request.POST.get('incomplete')
#             print(incomplete)
#             if status == '-1':
#                 print('000')
#                 print(status)
#                 applications = ConfirmApplication.objects.filter(state_id=user.State_id,paymentModeStatus='Completed').annotate(
#                     company_name=Subquery(
#                         RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
#                     ),
#                     registered_address=Subquery(
#                         RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
#                     ),
#                     company_email=Subquery(
#                         RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
#                     ),
#                     unit_pan=Subquery(
#                         RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
#                     ),
#                     pin_code=Subquery(
#                         RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
#                     )
#                 )
#             else:
#                 if incomplete=='1':
#                     print('111')
#                     applications = ConfirmApplication.objects.filter(state_id=user.State_id,incomplete=1).annotate(
#                         company_name=Subquery(
#                             RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
#                         ),
#                         registered_address=Subquery(
#                             RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
#                         ),
#                         company_email=Subquery(
#                             RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
#                         ),
#                         unit_pan=Subquery(
#                             RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
#                         ),
#                         pin_code=Subquery(
#                             RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
#                         )
#                     )
                    
#                 else:
#                     print('222')
#                     if status == '2':
#                         applications = ConfirmApplication.objects.filter(appstatus__in=[2,3,5], state_id=user.State_id, paymentModeStatus='Completed',incomplete=0).annotate(
#                             company_name=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
#                             ),
#                             registered_address=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
#                             ),
#                             company_email=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
#                             ),
#                             unit_pan=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
#                             ),
#                             pin_code=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
#                             )
#                         )
#                     elif status == '4':
#                         applications = ConfirmApplication.objects.filter(appstatus__in=[4,9], state_id=user.State_id,paymentModeStatus='Completed',incomplete=0).annotate(
#                             company_name=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
#                             ),
#                             registered_address=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
#                             ),
#                             company_email=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
#                             ),
#                             unit_pan=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
#                             ),
#                             pin_code=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
#                             )
#                         )
#                     else:
#                         applications = ConfirmApplication.objects.filter(appstatus=status, state_id=user.State_id,paymentModeStatus='Completed').annotate(
#                             company_name=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
#                             ),
#                             registered_address=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
#                             ),
#                             company_email=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
#                             ),
#                             unit_pan=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
#                             ),
#                             pin_code=Subquery(
#                                 RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
#                             )
#                         )
#     return render(request, 'processing/listapplications.html', {'data': applications})


def list_rvsf(request):
    try:
        applications = []
        if request.method == 'POST':
            # print(request.POST)
            userid = request.session.get('user_id')
            user = StateUsers.objects.filter(id=userid).first()
            if user:
                # print('444')
                status = request.POST.get('status')
                incomplete = request.POST.get('incomplete')
                # print(incomplete)
                
                if status == '-1':
                    # print('000')
                    # print(status)
                    applications = ConfirmApplication.objects.filter(
                        state_id=user.State_id, 
                        paymentModeStatus='Completed'
                    ).annotate(
                        company_name=Subquery(
                            RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
                        ),
                        username=Subquery(
        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('username')[:1]
    ),
                        registered_address=Subquery(
                            RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
                        ),
                        company_email=Subquery(
                            RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
                        ),
                        unit_pan=Subquery(
                            RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
                        ),
                        pin_code=Subquery(
                            RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
                        ),
                        attested_certificate=Subquery(
                            RvsfRegistration.objects.filter(id=OuterRef('userid')).values('attested_certificate')[:1]
                        ),
                        attested_certificate_uploaded_at=Subquery(
                            RvsfRegistration.objects.filter(id=OuterRef('userid')).values('attested_certificate_uploaded_at')[:1]
                        )
                    )
                else:
                    if incomplete == '1':
                        # print('111')
                        applications = ConfirmApplication.objects.filter(
                            state_id=user.State_id, 
                            incomplete=1
                        ).annotate(
                            company_name=Subquery(
                                RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
                            ),
                            username=Subquery(
        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('username')[:1]
    ),
                            registered_address=Subquery(
                                RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
                            ),
                            company_email=Subquery(
                                RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
                            ),
                            unit_pan=Subquery(
                                RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
                            ),
                            pin_code=Subquery(
                                RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
                            ),
                            attested_certificate=Subquery(
                                RvsfRegistration.objects.filter(id=OuterRef('userid')).values('attested_certificate')[:1]
                            ),
                            attested_certificate_uploaded_at=Subquery(
                                RvsfRegistration.objects.filter(id=OuterRef('userid')).values('attested_certificate_uploaded_at')[:1]
                            )
                        )
                    else:
                        # print('222')
                        if status == '2':
                            applications = ConfirmApplication.objects.filter(
                                appstatus__in=[2, 3, 5], 
                                state_id=user.State_id, 
                                paymentModeStatus='Completed', 
                                incomplete=0
                            ).annotate(
                                company_name=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
                                ),
                                username=Subquery(
        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('username')[:1]
    ),
                                registered_address=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
                                ),
                                company_email=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
                                ),
                                unit_pan=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
                                ),
                                pin_code=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
                                ),
                                attested_certificate=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('attested_certificate')[:1]
                                ),
                                attested_certificate_uploaded_at=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('attested_certificate_uploaded_at')[:1]
                                )
                            )
                        elif status == '4':
                            applications = ConfirmApplication.objects.filter(
                                appstatus__in=[4, 9], 
                                state_id=user.State_id, 
                                paymentModeStatus='Completed', 
                                incomplete=0
                            ).annotate(
                                company_name=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
                                ),
                                username=Subquery(
        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('username')[:1]
    ),
                                registered_address=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
                                ),
                                company_email=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
                                ),
                                unit_pan=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
                                ),
                                pin_code=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
                                ),
                                attested_certificate=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('attested_certificate')[:1]
                                ),
                                attested_certificate_uploaded_at=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('attested_certificate_uploaded_at')[:1]
                                )
                            )
                        else:
                            applications = ConfirmApplication.objects.filter(
                                appstatus=status, 
                                state_id=user.State_id, 
                                paymentModeStatus='Completed'
                            ).annotate(
                                company_name=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
                                ),
                                username=Subquery(
        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('username')[:1]
    ),
                                registered_address=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
                                ),
                                company_email=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
                                ),
                                unit_pan=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
                                ),
                                pin_code=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
                                ),
                                attested_certificate=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('attested_certificate')[:1]
                                ),
                                attested_certificate_uploaded_at=Subquery(
                                    RvsfRegistration.objects.filter(id=OuterRef('userid')).values('attested_certificate_uploaded_at')[:1]
                                )
                            )
        
        # For GET requests, you might want to handle differently
        # Here's an example if you want to show all applications on initial load:
        else:
            userid = request.session.get('user_id')
            user = StateUsers.objects.filter(id=userid).first()
            if user:
                applications = ConfirmApplication.objects.filter(
                    state_id=user.State_id
                ).annotate(
                    company_name=Subquery(
                        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
                    ),
                    registered_address=Subquery(
                        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
                    ),
                    username=Subquery(
        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('username')[:1]
    ),
                    company_email=Subquery(
                        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
                    ),
                    unit_pan=Subquery(
                        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
                    ),
                    pin_code=Subquery(
                        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
                    ),
                    attested_certificate=Subquery(
                        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('attested_certificate')[:1]
                    ),
                    attested_certificate_uploaded_at=Subquery(
                        RvsfRegistration.objects.filter(id=OuterRef('userid')).values('attested_certificate_uploaded_at')[:1]
                    )
                )
                print(applications,'vdhh')
                print(user,'fsdjhfd')
        
        return render(request, 'processing/listapplications.html', {'data': applications,'userinfo':user})
    except Exception as db_error:
        logger.exception("❌ ERROR while  list rvsf")
        logger.error(f"Exact list rvsf  Error: {str(db_error)}")
        
        logger.info(f"Exact list rvsf Error: {str(db_error)}")

# @login_required
# def checklist(request):
#     appno = request.POST.get('appno')
#     industryid = int(request.POST.get('userid', 0))
#     fectchsignup = SignupChecklist.objects.filter(industryid = industryid).first()
#     fetchgeneral = GeneralChecklist.objects.filter(Industryid = industryid).first()
#     fetchequipment = EquipmentChecklist.objects.filter(industryid = industryid).first()
#     fetchfacility = FacilityChecklist.objects.filter(industryid = industryid).first()
#     fetchcapacity = CapacityChecklist.objects.filter(industryid = industryid).first()
#     fetchpollution = PollutionChecklist.objects.filter(industryid = industryid).first()
#     fetchwasterec = WasteRecycleChecklist.objects.filter(industryid = industryid).first()
#     fetchpayment = PaymentChecklist.objects.filter(industryid = industryid).first()
#     confirmapp = ConfirmApplication.objects.filter(userid = industryid).first()     

#     return render(request , 'processing/checklist.html' , {'AppNo': appno , 'IndustryId': industryid , 'signup': fectchsignup , 'general' : fetchgeneral , 'equipment': fetchequipment ,
#                                                            'facility':fetchfacility , 'capacity': fetchcapacity , 'pollution': fetchpollution, 'recycle': fetchwasterec, 'payment': fetchpayment ,
#                                                            'confirmapp': confirmapp
#                                                            })   
from django.utils import timezone
import pytz
@login_required
def checklist(request):
    try:
        india_tz = pytz.timezone('Asia/Kolkata')
        # Get current time directly in IST
        ist_now = timezone.now().astimezone(india_tz)
        
        # print(india_tz, '111')
        # print(ist_now, '333') 
        

    # Get current UTC time
        # utc_time = timezone.now()  # 2026-01-09 11:57:30.134816+00:00

        # # Convert to local time (if TIME_ZONE is set in settings)
        # local_time = timezone.localtime(utc_time)
        # print(local_time)
        session_id = request.session.get('user_id')
        userinfo = StateUsers.objects.filter(id=session_id).first()

        if not userinfo:
            messages.error(request, "Invalid session or user not found.")
            return redirect('login')

        # 🔥 Accept both POST and GET
        userid = request.POST.get('userid') or request.GET.get('userid')
        appno = request.POST.get('appno') or request.GET.get('appno')

        if not userid or not appno:
            messages.error(request, "Missing parameters.")
            return redirect('rvsf_applications')

        # ROLE BASED SETTINGS
        if userinfo.RoleAccess == '1':
            Roles = {'2': 'Recommending officer'}
            fetchappstage = ApplicationStatus.objects.filter(
                DisableStatus=0, RoleAccess__in=[3, 1]
            )
        elif userinfo.RoleAccess == '2':
            Roles = {
                '1': 'Approving officer',
                '3': 'Verifying officer',
                '4': 'Sent Back to User'
            }
            fetchappstage = ApplicationStatus.objects.filter(
                DisableStatus=0, RoleAccess__in=[3, 2]
            )
        else:
            Roles = {'2': 'Recommending officer'}
            fetchappstage = ApplicationStatus.objects.filter(
                DisableStatus=0, RoleAccess__in=[3, 2]
            )

        # Fetch the application
        application = ConfirmApplication.objects.filter(
            userid=userid,
            appno=appno,
            state_id=userinfo.State_id,
            role_id=userinfo.RoleAccess,
            incomplete=0
        ).annotate(
            company_name=Subquery(
                RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
            ),
            registered_address=Subquery(
                RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
            ),
            company_email=Subquery(
                RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
            ),
            unit_pan=Subquery(
                RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
            ),
            pin_code=Subquery(
                RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
            )
        ).first()

        if not application:
            messages.error(request, "Application not found.")
            return redirect('rvsf_applications')

        industryid = application.userid

        # Fetch all checklist data
        fectchsignup = SignupChecklist.objects.filter(industryid=industryid).first()
        fetchgeneral = GeneralChecklist.objects.filter(Industryid=industryid).first()
        fetchequipment = EquipmentChecklist.objects.filter(industryid=industryid).first()
        fetchfacility = FacilityChecklist.objects.filter(industryid=industryid).first()
        fetchcapacity = CapacityChecklist.objects.filter(industryid=industryid).first()
        fetchpollution = PollutionChecklist.objects.filter(industryid=industryid).first()
        fetchwasterec = WasteRecycleChecklist.objects.filter(industryid=industryid).first()
        fetchpayment = PaymentChecklist.objects.filter(industryid=industryid).first()
        confirmapp = ConfirmApplication.objects.filter(
            userid=industryid, appno=appno
        ).first()

        verifyingofficers = StateUsers.objects.filter(
            RoleAccess=3, State_id=userinfo.State_id
        )
        entities = RvsfRegistration.objects.filter(id=userid).first()
        generaldatainfo = GeneralDetails.objects.filter(userid=userid).first()
        rvsfdatainfo = RvsfDetails.objects.filter(userid=userid).first()
        # print(rvsfdatainfo,('ffeefefeef'))
        # Prepare payment info for checklist table as per checklist.html (1370-1381)
        payinf=Payment.objects.filter(owner_id=userid, status='success').values(
            'txn_id', 'amount_initiated', 'txn_date','status')
        total_amount = Payment.objects.filter(owner_id=userid, status='success') \
                                .aggregate(total=Sum('amount_initiated'))['total'] or 0
        # ... other queries ...
        # print(payinf,('ffeefefeef'))

        context = {
            'entity': entities,
            'general': generaldatainfo,
            'rvsf': rvsfdatainfo,
            'statename': State.objects.filter(state_id=entities.state).first(),
            'districtname': District.objects.filter(city_id=entities.district).first(),
            'equipmentdata': EquipmentType.objects.all().order_by('id'),
            'data': EquipmentEntry.objects.filter(userid=userid),
            'facilitydata': RvsfFacility.objects.filter(user_id=userid).first(),
            'VechileType': VehicleType.objects.filter(userid=userid),
            'capacitydata': PlantCapacity.objects.filter(userid=userid).first(),
            'pollutiondetails': PollutionDevice.objects.filter(userid=userid),
            'wasterecycled': WasteRecycled.objects.filter(userid=userid),
            # 'paymentinfo':Payment.objects.filter(owner_id=userid,status='success')
            'paymentinfo':Payment.objects.filter(owner_id=userid, status='success').values(
            'txn_id', 'amount_initiated', 'txn_date','status'
            
        ),'total_amount': total_amount,
        }
        # print(context)

        return render(request, 'processing/checklist.html', {
            'AppNo': appno,
            'IndustryId': industryid,
            'userinfo': userinfo,
            'Roles': Roles,
            'fetchappstage': fetchappstage,
            'signup': fectchsignup,
            'general': fetchgeneral,
            'equipment': fetchequipment,
            'facility': fetchfacility,
            'capacity': fetchcapacity,
            'pollution': fetchpollution,
            'recycle': fetchwasterec,
            'payment': fetchpayment,
            'confirmapp': confirmapp,
            'verifyingofficers': verifyingofficers,
            'current_user_role': userinfo.RoleAccess,
            'postuser': {'id': industryid},
            'context':context,
        })
    except Exception as db_error:
        logger.exception("❌ ERROR while  checklist")
        logger.error(f"Exact checklist  Error: {str(db_error)}")
        
        logger.info(f"Exact checklist Error: {str(db_error)}")
# def checklist(request):
#     session_id = request.session.get('user_id')
#     userinfo = StateUsers.objects.filter(id=session_id).first()
#     current_user_role = userinfo.RoleAccess if userinfo else None
    
#     if not userinfo:
#         messages.error(request, "Invalid session or user not found.")
#         return redirect('login')

#     # Get the specific application from POST data
#     if request.method == 'POST':
#         userid = request.POST.get('userid')
#         appno = request.POST.get('appno')
#     else:
#         # If not POST, redirect back or handle appropriately
#         messages.error(request, "Invalid request.")
#         return redirect('rvsf_applications')

#     # ROLE BASED SETTINGS
#     if userinfo.RoleAccess == '1':
#         Roles = {'2': 'Recommending officer'}
#         fetchappstage = ApplicationStatus.objects.filter(DisableStatus=0, RoleAccess__in=[3, 1])
#     elif userinfo.RoleAccess == '2':
#         Roles = {'1': 'Approving officer', '3': 'Reviewing officer', '4': 'Sent Back to User'}
#         fetchappstage = ApplicationStatus.objects.filter(DisableStatus=0, RoleAccess__in=[3, 2])
#     else:
#         Roles = {'2': 'Recommending officer'}
#         fetchappstage = ApplicationStatus.objects.filter(DisableStatus=0, RoleAccess__in=[3, 2])

#     # Get the SPECIFIC application that was clicked
#     application = ConfirmApplication.objects.filter(
#         userid=userid,  # Filter by the specific userid from POST
#         appno=appno,    # Filter by the specific appno from POST
#         state_id=userinfo.State_id, 
#         role_id=userinfo.RoleAccess, 
#         incomplete=0
#     ).annotate(
#         company_name=Subquery(RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]),
#         registered_address=Subquery(RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]),
#         company_email=Subquery(RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]),
#         unit_pan=Subquery(RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]),
#         pin_code=Subquery(RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1])
#     ).first()  # This will now get the specific application

#     if not application:
#         messages.error(request, "Application not found.")
#         return redirect('rvsf_applications')

#     appno = application.appno
#     industryid = application.userid

#     # Fetch all related checklist data for THIS SPECIFIC application
#     fectchsignup = SignupChecklist.objects.filter(industryid=industryid).first()
#     fetchgeneral = GeneralChecklist.objects.filter(Industryid=industryid).first()
#     fetchequipment = EquipmentChecklist.objects.filter(industryid=industryid).first()
#     fetchfacility = FacilityChecklist.objects.filter(industryid=industryid).first()
#     fetchcapacity = CapacityChecklist.objects.filter(industryid=industryid).first()
#     fetchpollution = PollutionChecklist.objects.filter(industryid=industryid).first()
#     fetchwasterec = WasteRecycleChecklist.objects.filter(industryid=industryid).first()
#     fetchpayment = PaymentChecklist.objects.filter(industryid=industryid).first()
#     confirmapp = ConfirmApplication.objects.filter(userid=industryid, appno=appno).first()
#     verifyingofficers = StateUsers.objects.filter(RoleAccess=3,State_id=userinfo.State_id)

#     return render(request, 'processing/checklist.html', {
#         'AppNo': appno,
#         'IndustryId': industryid,
#         'userinfo': userinfo, 
#         'Roles': Roles,
#         'fetchappstage': fetchappstage,
#         'signup': fectchsignup,
#         'general': fetchgeneral,
#         'equipment': fetchequipment,
#         'facility': fetchfacility,
#         'capacity': fetchcapacity,
#         'pollution': fetchpollution,
#         'recycle': fetchwasterec,
#         'payment': fetchpayment,
#         'confirmapp': confirmapp,
#         'verifyingofficers': verifyingofficers,
#         'current_user_role': current_user_role,
#         'postuser': {'id': industryid},  # Use the actual industryid
#     })
# def checklist(request):
   
#     session_id = request.session.get('user_id')
#     postuser = {'id': 49}
#     print(postuser['id'])
#     postid = None
    
#     print('20 hvjhdv')
#     userinfo = StateUsers.objects.filter(id=session_id).first()
#     if not userinfo:
#         messages.error(request, "Invalid session or user not found.")
#         return redirect('login')

#     if userinfo.RoleAccess == '1':
#         # Roles = {'2': 'Recommending Authority', '3': 'Verification Authority'}
#         Roles = {'2': 'Recommending officer'}
#         # Roles = {'2': 'Recommending officer','4':'Sent Back to User'}
#         fetchappstage = ApplicationStatus.objects.filter(DisableStatus=0, RoleAccess__in=[3, 1])
#     elif userinfo.RoleAccess == '2':
#         Roles = {'1': 'Approving officer', '3': 'Reviewing officer','4':'Sent Back to User'}
#         fetchappstage = ApplicationStatus.objects.filter(DisableStatus=0, RoleAccess__in=[3, 2])
#     else:
#         # Roles = {'1': 'Approving officer', '2': 'Recommending officer'}
#         Roles = {'2': 'Recommending officer'}
#         fetchappstage = ApplicationStatus.objects.filter(DisableStatus=0, RoleAccess__in=[3, 2])


  
    
#     print(userinfo,session_id)
#     applications = ConfirmApplication.objects.filter(state_id = userinfo.State_id , role_id = userinfo.RoleAccess , incomplete = 0).annotate(
#         company_name=Subquery(
#             RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]
#         ),
#         registered_address=Subquery(
#             RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]
#         ),
#         company_email=Subquery(
#             RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]
#         ),
#         unit_pan=Subquery(
#             RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]
#         ),
#         pin_code=Subquery(
#             RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1]
#         )
#     )

#     application = ConfirmApplication.objects.filter(
#         state_id=userinfo.State_id, role_id=userinfo.RoleAccess, incomplete=0
#     ).annotate(
#         company_name=Subquery(RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_name')[:1]),
#         registered_address=Subquery(RvsfRegistration.objects.filter(id=OuterRef('userid')).values('registered_address')[:1]),
#         company_email=Subquery(RvsfRegistration.objects.filter(id=OuterRef('userid')).values('company_email')[:1]),
#         unit_pan=Subquery(RvsfRegistration.objects.filter(id=OuterRef('userid')).values('auth_pan')[:1]),
#         pin_code=Subquery(RvsfRegistration.objects.filter(id=OuterRef('userid')).values('pin_code')[:1])
#     ).first()

#     appno = application.appno if application else None
#     industryid = application.userid if application else None

#     # print(appno)
#     # print(industryid)

#     fectchsignup = SignupChecklist.objects.filter(industryid=industryid).first()
#     fetchgeneral = GeneralChecklist.objects.filter(Industryid=industryid).first()
#     fetchequipment = EquipmentChecklist.objects.filter(industryid=industryid).first()
#     fetchfacility = FacilityChecklist.objects.filter(industryid=industryid).first()
#     fetchcapacity = CapacityChecklist.objects.filter(industryid=industryid).first()
#     fetchpollution = PollutionChecklist.objects.filter(industryid=industryid).first()
#     fetchwasterec = WasteRecycleChecklist.objects.filter(industryid=industryid).first()
#     fetchpayment = PaymentChecklist.objects.filter(industryid=industryid).first()
#     confirmapp = ConfirmApplication.objects.filter(userid=industryid).first()
#     verifyingofficers=StateUsers.objects.filter(RoleAccess=3)

#     return render(request, 'processing/checklist.html', {
#         'AppNo': appno,
#         'data': applications,
#         'IndustryId': industryid,
#         'userinfo':userinfo , 
#         'Roles':Roles,
#         'fetchappstage':fetchappstage ,
#         'signup': fectchsignup,
#         'general': fetchgeneral,
#         'equipment': fetchequipment,
#         'facility': fetchfacility,
#         'capacity': fetchcapacity,
#         'pollution': fetchpollution,
#         'recycle': fetchwasterec,
#         'payment': fetchpayment,
#         'confirmapp': confirmapp,
#         'verifyingofficers':verifyingofficers,
#         'postuser':postuser,
#     })
    
@login_required
def signupchecklist(request):
    try:
        # print('casghcas')
        if request.method == 'POST':
            userid = request.session.get('user_id')
            industryid = request.POST.get('industryid')
            AppNo = request.POST.get('appno')
            name_address = request.POST.get('name_address')
            remarks_name_address = request.POST.get('remarks_name_address')
            company_email = request.POST.get('company_email')
            remarks_company_email = request.POST.get('remarks_company_email')
            gst_certificate = request.POST.get('gst_certificate')
            remarks_gst_certificate = request.POST.get('remarks_gst_certificate')
            company_pan_card = request.POST.get('company_pan_card')
            remarks_company_pan_card = request.POST.get('remarks_company_pan_card')
            company_tin = request.POST.get('company_tin')
            remarks_company_tin = request.POST.get('remarks_company_tin')
            company_cin = request.POST.get('company_cin')
            remarks_company_cin = request.POST.get('remarks_company_cin')
            company_iec = request.POST.get('company_iec')
            remarks_company_iec = request.POST.get('remarks_company_iec')
            auth_person_details = request.POST.get('auth_person_details')
            remarks_auth_person_details = request.POST.get('remarks_auth_person_details')

            signup_fields = {
                'name_address': name_address,
                'remarks_name_address': remarks_name_address,
                'company_email': company_email,
                'remarks_company_email': remarks_company_email,
                'gst_certificate': gst_certificate,
                'remarks_gst_certificate': remarks_gst_certificate,
                'company_pan_card': company_pan_card,
                'remarks_company_pan_card': remarks_company_pan_card,
                'company_tin': company_tin,
                'remarks_company_tin': remarks_company_tin,
                'company_cin': company_cin,
                'remarks_company_cin': remarks_company_cin,
                'company_iec': company_iec,
                'remarks_company_iec': remarks_company_iec,
                'auth_person_details': auth_person_details,
                'remarks_auth_person_details': remarks_auth_person_details,
            }
            for field, value in signup_fields.items():
                # print(f"Validating field {field} => {value}")

                if value:
                    value = value.strip()
                    # print(f"Stripped value for {field}: {value}")

                    
                    # Validate that TIN, CIN, IEC don't have special characters
                    # (excluding spaces since your regex allows spaces)
                    if field in ['remarks_auth_person_details', 'auth_person_details', 'remarks_company_iec','company_iec','remarks_company_cin','company_cin','remarks_company_tin','company_tin','remarks_company_pan_card','company_pan_card','remarks_company_email','remarks_gst_certificate','gst_certificate','company_email','remarks_name_address','name_address']:
                        # Check if has special characters (excluding allowed ones)
                        # We'll use a simpler check
                        import re
                        # Allow alphanumeric and spaces only
                        if re.search(r'[^a-zA-Z0-9\s]', value):
                            # print(f"Special characters found in {field}")
                            messages.error(
                                request,
                                f"{field.replace('_', ' ').title()} should not contain special characters."
                            )
                            # return redirect('pollutiondetails')
                            base_url = reverse('checklist')  # path: viewchecklist
                            params = urlencode({'userid': industryid, 'appno': AppNo})
                            return redirect(f"{base_url}?{params}")

            checkSignupData = SignupChecklist.objects.filter(AppNo = AppNo).first()
            if checkSignupData:
                checkSignupData.name_address = name_address
                checkSignupData.remarks_name_address = remarks_name_address
                checkSignupData.company_email = company_email
                checkSignupData.remarks_company_email = remarks_company_email
                checkSignupData.gst_certificate = gst_certificate
                checkSignupData.remarks_gst_certificate = remarks_gst_certificate
                checkSignupData.company_pan_card = company_pan_card
                checkSignupData.remarks_company_pan_card = remarks_company_pan_card
                checkSignupData.company_tin = company_tin
                checkSignupData.remarks_company_tin = remarks_company_tin
                checkSignupData.company_cin = company_cin
                checkSignupData.remarks_company_cin = remarks_company_cin
                checkSignupData.company_iec = company_iec
                checkSignupData.remarks_company_iec = remarks_company_iec
                checkSignupData.auth_person_details = auth_person_details
                checkSignupData.remarks_auth_person_details = remarks_auth_person_details
                checkSignupData.added_by = userid
                checkSignupData.save()

                messages.success(request, "Signup Checklist updated successfully.")
                base_url = reverse('checklist')  # path: viewchecklist
                params = urlencode({'userid': industryid, 'appno': AppNo})
                return redirect(f"{base_url}?{params}")
                
            else:
                SignupChecklist.objects.create(
                    AppNo=AppNo,
                    industryid= industryid,
                    name_address=name_address,
                    remarks_name_address=remarks_name_address,
                    company_email=company_email,
                    remarks_company_email=remarks_company_email,
                    gst_certificate=gst_certificate,
                    remarks_gst_certificate=remarks_gst_certificate,
                    company_pan_card=company_pan_card,
                    remarks_company_pan_card=remarks_company_pan_card,
                    company_tin=company_tin,
                    remarks_company_tin=remarks_company_tin,
                    company_cin=company_cin,
                    remarks_company_cin=remarks_company_cin,
                    company_iec=company_iec,
                    remarks_company_iec=remarks_company_iec,
                    auth_person_details=auth_person_details,
                    remarks_auth_person_details=remarks_auth_person_details,
                    added_by=userid
                )
            messages.success(request, "Signup Checklist updated successfully.")
            base_url = reverse('checklist')  # path: viewchecklist
            params = urlencode({'userid': industryid, 'appno': AppNo})
            return redirect(f"{base_url}?{params}")
            # return redirect('rvsf_applications')
    except Exception as db_error:
        logger.exception("❌ ERROR while  signup checklist")
        logger.error(f"Exact signup checklist  Error: {str(db_error)}")
        
        logger.info(f"Exact signup checklist Error: {str(db_error)}")
    
@login_required
def insert_or_update_general_checklist(request):
    try:
        if request.method == 'POST':
            appno = request.POST.get('appno')
            industryid = request.POST.get('industryid')

            if not appno:
                return HttpResponse("AppNo is required", status=400)

            import re
            from django.urls import reverse
            from urllib.parse import urlencode
            
            general_remarks_fields = {
                'remarks_rvsf_address': request.POST.get('remarks_rvsf_address'),
                'remarks_gps_location': request.POST.get('remarks_gps_location'),
                'remarks_rvsf_state': request.POST.get('remarks_rvsf_state'),
                'remarks_cto_certificate': request.POST.get('remarks_cto_certificate'),
                'remarks_cto_validity': request.POST.get('remarks_cto_validity'),
                'remarks_howm_certificate': request.POST.get('remarks_howm_certificate'),
                'remarks_dic_certificate': request.POST.get('remarks_dic_certificate'),
                'remarks_rvsf_certificate': request.POST.get('remarks_rvsf_certificate'),
                'remarks_rvsf_certificate_validity': request.POST.get('remarks_rvsf_certificate_validity'),
                'remarks_process_flow': request.POST.get('remarks_process_flow'),
                'remarks_material_balance_sheet': request.POST.get('remarks_material_balance_sheet'),
                'remarks_annual_return': request.POST.get('remarks_annual_return'),
            }

            # Validate each remarks field for special characters
            for field_name, field_value in general_remarks_fields.items():
                if field_value:
                    field_value = field_value.strip()
                    
                    # Check for special characters (allow only alphanumeric and spaces)
                    if re.search(r'[^a-zA-Z0-9\s]', field_value):
                        # print(f"Special characters found in {field_name}")
                        
                        # Create a user-friendly field name for the error message
                        friendly_name = field_name.replace('remarks_', '').replace('_', ' ').title()
                        
                        messages.error(
                            request,
                            f"{friendly_name} remarks should not contain special characters."
                        )
                        
                        # Redirect back with parameters
                        base_url = reverse('checklist')
                        params = urlencode({'userid': industryid, 'appno': appno})
                        return redirect(f"{base_url}?{params}")

            # Fetch or create the checklist entry
            checklist, created = GeneralChecklist.objects.get_or_create(AppNo=appno)

            checklist.Industryid = request.POST.get('industryid')
            checklist.rvsf_address = request.POST.get('rvsf_address')
            checklist.remarks_rvsf_address = request.POST.get('remarks_rvsf_address')
            checklist.gps_location = request.POST.get('gps_location')
            checklist.remarks_gps_location = request.POST.get('remarks_gps_location')
            checklist.rvsf_state = request.POST.get('rvsf_state')
            checklist.remarks_rvsf_state = request.POST.get('remarks_rvsf_state')
            checklist.cto_certificate = request.POST.get('cto_certificate')
            checklist.remarks_cto_certificate = request.POST.get('remarks_cto_certificate')
            checklist.cto_validity = request.POST.get('cto_validity')
            checklist.remarks_cto_validity = request.POST.get('remarks_cto_validity')
            checklist.howm_certificate = request.POST.get('howm_certificate')
            checklist.remarks_howm_certificate = request.POST.get('remarks_howm_certificate')
            checklist.dic_certificate = request.POST.get('dic_certificate')
            checklist.remarks_dic_certificate = request.POST.get('remarks_dic_certificate')
            checklist.rvsf_certificate = request.POST.get('rvsf_certificate')
            checklist.remarks_rvsf_certificate = request.POST.get('remarks_rvsf_certificate')
            checklist.rvsf_certificate_validity = request.POST.get('rvsf_certificate_validity')
            checklist.remarks_rvsf_certificate_validity = request.POST.get('remarks_rvsf_certificate_validity')
            checklist.process_flow = request.POST.get('process_flow')
            checklist.remarks_process_flow = request.POST.get('remarks_process_flow')
            checklist.material_balance_sheet = request.POST.get('material_balance_sheet')
            checklist.remarks_material_balance_sheet = request.POST.get('remarks_material_balance_sheet')
            checklist.annual_return = request.POST.get('annual_return')
            checklist.remarks_annual_return = request.POST.get('remarks_annual_return')
            checklist.added_by = request.session.get('user_id')

            checklist.save()

            messages.success(request, f"Checklist {'created' if created else 'updated'} successfully.")
            # return redirect('rvsf_applications')
            # messages.success(request, "Signup Checklist updated successfully.")
            base_url = reverse('checklist')  # path: viewchecklist
            params = urlencode({'userid': industryid, 'appno': appno})
            return redirect(f"{base_url}?{params}")

        return HttpResponse("Invalid request method", status=405)
    except Exception as db_error:
        logger.exception("❌ ERROR while  update general checklist")
        logger.error(f"Exact update general checklist  Error: {str(db_error)}")
        
        logger.info(f"Exact update general checklist Error: {str(db_error)}")

@login_required
def save_equipment_checklist(request):
    try:
        if request.method == 'POST':
            app_no = request.POST.get('appno')
            industry_id = request.POST.get('industryid')

            # print("Industry ID received:", industry_id)  # Debug

            if not industry_id:
                messages.error(request, "Industry ID is missing. Please contact admin.")
                return redirect('rvsf_applications')

            # Ensure industry_id is saved as an integer
            try:
                industry_id = int(industry_id)
            except ValueError:
                messages.error(request, "Invalid Industry ID format.")
                return redirect('rvsf_applications')

            import re
            from django.urls import reverse
            from urllib.parse import urlencode
            
            equipment_remarks_fields = {
                'remarks_dismantling_equipment': request.POST.get('remarks_dismantling_equipment'),
                'remarks_depollution_equipment': request.POST.get('remarks_depollution_equipment'),
                'remarks_bailing_equipment': request.POST.get('remarks_bailing_equipment'),
                'remarks_shredding_equipment': request.POST.get('remarks_shredding_equipment'),
                'remarks_storage_equipment': request.POST.get('remarks_storage_equipment'),
                'remarks_classifier_equipment': request.POST.get('remarks_classifier_equipment'),
                'remarks_other_equipment': request.POST.get('remarks_other_equipment'),
            }

            # Validate each remarks field for special characters
            for field_name, field_value in equipment_remarks_fields.items():
                if field_value:
                    field_value = field_value.strip()
                    
                    # Check for special characters (allow only alphanumeric and spaces)
                    if re.search(r'[^a-zA-Z0-9\s]', field_value):
                        # print(f"Special characters found in {field_name}")
                        
                        # Create a user-friendly field name for the error message
                        friendly_name = field_name.replace('remarks_', '').replace('_', ' ').title()
                        
                        messages.error(
                            request,
                            f"{friendly_name} remarks should not contain special characters."
                        )
                        
                        # Redirect back with parameters
                        base_url = reverse('checklist')
                        params = urlencode({'userid': industry_id, 'appno': app_no})
                        return redirect(f"{base_url}?{params}")


            checklist, created = EquipmentChecklist.objects.get_or_create(AppNo=app_no)
            checklist.industryid = industry_id

            checklist.dismantling_equipment = request.POST.get('dismantling_equipment') == 'Yes'
            checklist.remarks_dismantling_equipment = request.POST.get('remarks_dismantling_equipment')

            checklist.depollution_equipment = request.POST.get('depollution_equipment') == 'Yes'
            checklist.remarks_depollution_equipment = request.POST.get('remarks_depollution_equipment')

            checklist.bailing_equipment = request.POST.get('bailing_equipment') == 'Yes'
            checklist.remarks_bailing_equipment = request.POST.get('remarks_bailing_equipment')

            checklist.shredding_equipment = request.POST.get('shredding_equipment') == 'Yes'
            checklist.remarks_shredding_equipment = request.POST.get('remarks_shredding_equipment')

            checklist.storage_equipment = request.POST.get('storage_equipment') == 'Yes'
            checklist.remarks_storage_equipment = request.POST.get('remarks_storage_equipment')

            checklist.classifier_equipment = request.POST.get('classifier_equipment') == 'Yes'
            checklist.remarks_classifier_equipment = request.POST.get('remarks_classifier_equipment')

            checklist.other_equipment = request.POST.get('other_equipment') == 'Yes'
            checklist.remarks_other_equipment = request.POST.get('remarks_other_equipment')

            # Ensure session user ID is valid
            user_id = request.session.get('user_id')
            if user_id:
                checklist.added_by_id = user_id

            checklist.save()

            messages.success(request, f"Checklist {'created' if created else 'updated'} successfully.")
            # return redirect('rvsf_applications')
            base_url = reverse('checklist')  # path: viewchecklist
            params = urlencode({'userid': industry_id, 'appno': app_no})
            return redirect(f"{base_url}?{params}")

        return HttpResponse("Invalid request")
    except Exception as db_error:
        logger.exception("❌ ERROR while  save equipment checklist")
        logger.error(f"Exact save equipment checklist  Error: {str(db_error)}")
        
        logger.info(f"Exact save equipment checklist Error: {str(db_error)}")

@login_required
# def PostFacilityCheckList(request):
#     if request.method == 'POST':
#         appno = request.POST.get("appno")
#         industryid = request.POST.get("industryid")
#         added_by = request.session.get("user_id")

#         # Either get the existing checklist or create a new one
#         checklist, created = FacilityChecklist.objects.get_or_create(AppNo=appno)

#         checklist.industryid = industryid or 0
#         checklist.geo_tagged_video = request.POST.get("geo_tagged_video") == "Yes"
#         checklist.remarks_geo_tagged_video = request.POST.get("remarks_geo_tagged_video")

#         checklist.total_rvsf_area = request.POST.get("total_rvsf_area") == "Yes"
#         checklist.remarks_total_rvsf_area = request.POST.get("remarks_total_rvsf_area")

#         checklist.shift_number = request.POST.get("shift_number") == "Yes"
#         checklist.remarks_shift_number = request.POST.get("remarks_shift_number")

#         # checklist.shift_number = request.POST.get("sectioned_power") == "Yes"
#         # checklist.remarks_shift_number = request.POST.get("remarks_sectioned_power")

#         checklist.employees_number = request.POST.get("employees_number") == "Yes"
#         checklist.remarks_employees_number = request.POST.get("remarks_employees_number")

#         checklist.sectioned_power = request.POST.get("sectioned_power") == "Yes"
      
#         checklist.remarks_sectioned_power = request.POST.get("remarks_sectioned_power")
        

#         checklist.added_by = added_by

#         checklist.save()

#         messages.success(request, f"Checklist {'created' if created else 'updated'} successfully.")
#         return redirect('rvsf_applications')  # Replace with your desired URL

#     else:
#         messages.error(request, "Invalid request method.")
#         return redirect('rvsf_applications')  # Redirect even on GET (or customize as needed)
        


@login_required
@login_required
def PostFacilityCheckList(request):
    try:
        if request.method == 'POST':
            appno = request.POST.get("appno")
            industryid = request.POST.get("industryid")
            added_by = request.session.get("user_id")

            import re
            from django.urls import reverse
            from urllib.parse import urlencode
            
            facility_remarks_fields = {
                'remarks_geo_tagged_video': request.POST.get("remarks_geo_tagged_video"),
                'remarks_total_rvsf_area': request.POST.get("remarks_total_rvsf_area"),
                'remarks_shift_number': request.POST.get("remarks_shift_number"),
                'remarks_employees_number': request.POST.get("remarks_employees_number"),
                'remarks_sectioned_power': request.POST.get("remarks_sectioned_power"),
            }

            # Validate each remarks field for special characters
            for field_name, field_value in facility_remarks_fields.items():
                if field_value:
                    field_value = field_value.strip()
                    
                    # Check for special characters (allow only alphanumeric and spaces)
                    if re.search(r'[^a-zA-Z0-9\s]', field_value):
                        # print(f"Special characters found in {field_name}")
                        
                        # Create a user-friendly field name for the error message
                        friendly_name = field_name.replace('remarks_', '').replace('_', ' ').title()
                        
                        messages.error(
                            request,
                            f"{friendly_name} remarks should not contain special characters."
                        )
                        
                        # Redirect back with parameters
                        base_url = reverse('checklist')
                        params = urlencode({'userid': industryid, 'appno': appno})
                        return redirect(f"{base_url}?{params}")

            # Get or create checklist
            checklist, created = FacilityChecklist.objects.get_or_create(AppNo=appno)

            checklist.industryid = industryid or 0
            checklist.geo_tagged_video = request.POST.get("geo_tagged_video") == "Yes"
            checklist.remarks_geo_tagged_video = request.POST.get("remarks_geo_tagged_video")

            checklist.total_rvsf_area = request.POST.get("total_rvsf_area") == "Yes"
            checklist.remarks_total_rvsf_area = request.POST.get("remarks_total_rvsf_area")

            checklist.shift_number = request.POST.get("shift_number") == "Yes"
            checklist.remarks_shift_number = request.POST.get("remarks_shift_number")

            checklist.employees_number = request.POST.get("employees_number") == "Yes"
            checklist.remarks_employees_number = request.POST.get("remarks_employees_number")

            checklist.sectioned_power = request.POST.get("sectioned_power") == "Yes"
            checklist.remarks_sectioned_power = request.POST.get("remarks_sectioned_power")

            checklist.added_by = added_by
            checklist.save()

            messages.success(request, "Checklist saved successfully.")

            # 🔥 Redirect to checklist page with GET parameters
            base_url = reverse('checklist')  # path: viewchecklist
            params = urlencode({'userid': industryid, 'appno': appno})
            return redirect(f"{base_url}?{params}")

        # Invalid request
        messages.error(request, "Invalid request method.")
        return redirect('rvsf_applications')
    except Exception as db_error:
        logger.exception("❌ ERROR while  post facilty checklist")
        logger.error(f"Exact post facilty checklist  Error: {str(db_error)}")
        
        logger.info(f"Exact post facilty checklist Error: {str(db_error)}")
          
            
@login_required
def CapacityChecklistView(request):
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            appno = request.POST.get('appno')

            import re
            from django.urls import reverse
            from urllib.parse import urlencode
            
            capacity_remarks_fields = {
                'remarks_vehicle_category': request.POST.get('remarks_vehicle_category'),
                'remarks_vehicle_installed_capacity': request.POST.get('remarks_vehicle_installed_capacity'),
                'remarks_steel_installed_capacity': request.POST.get('remarks_steel_installed_capacity'),
                'remarks_vehicle_operating_capacity': request.POST.get('remarks_vehicle_operating_capacity'),
                'remarks_steel_operating_capacity': request.POST.get('remarks_steel_operating_capacity'),
            }

            # Validate each remarks field for special characters
            for field_name, field_value in capacity_remarks_fields.items():
                if field_value:
                    field_value = field_value.strip()
                    
                    # Check for special characters (allow only alphanumeric and spaces)
                    if re.search(r'[^a-zA-Z0-9\s]', field_value):
                        # print(f"Special characters found in {field_name}")
                        
                        # Create a user-friendly field name for the error message
                        friendly_name = field_name.replace('remarks_', '').replace('_', ' ').title()
                        
                        messages.error(
                            request,
                            f"{friendly_name} remarks should not contain special characters."
                        )
                        
                        # Redirect back with parameters
                        base_url = reverse('checklist')
                        params = urlencode({'userid': industryid, 'appno': appno})
                        return redirect(f"{base_url}?{params}")

            # Convert Yes/No to Boolean
            def to_bool(value):
                return True if value == 'Yes' else False

            data = {
                'vehicle_category': to_bool(request.POST.get('vehicle_category')),
                'remarks_vehicle_category': request.POST.get('remarks_vehicle_category'),

                'vehicle_installed_capacity': to_bool(request.POST.get('vehicle_installed_capacity')),
                'remarks_vehicle_installed_capacity': request.POST.get('remarks_vehicle_installed_capacity'),

                'steel_installed_capacity': to_bool(request.POST.get('steel_installed_capacity')),
                'remarks_steel_installed_capacity': request.POST.get('remarks_steel_installed_capacity'),

                'vehicle_operating_capacity': to_bool(request.POST.get('vehicle_operating_capacity')),
                'remarks_vehicle_operating_capacity': request.POST.get('remarks_vehicle_operating_capacity'),

                'steel_operating_capacity': to_bool(request.POST.get('steel_operating_capacity')),
                'remarks_steel_operating_capacity': request.POST.get('remarks_steel_operating_capacity'),

                'industryid': industryid,
                'AppNo': appno,
                'added_by': request.session.get('user_id') or 0
            }

            checklist, created = CapacityChecklist.objects.update_or_create(
                AppNo=appno,
                defaults=data
            )
            messages.success(request, f"Checklist {'created' if created else 'updated'} successfully.")
            base_url = reverse('checklist')  # path: viewchecklist
            params = urlencode({'userid': industryid, 'appno': appno})
            return redirect(f"{base_url}?{params}")
            # return redirect('rvsf_applications')

        return redirect('rvsf_applications')
    except Exception as db_error:
        logger.exception("❌ ERROR while  capacity checklist")
        logger.error(f"Exact capacity checklist  Error: {str(db_error)}")
        
        logger.info(f"Exact capacity checklist Error: {str(db_error)}")

@login_required
def SavePollutionChecklist(request):
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            appno = request.POST.get('appno')
            added_by = request.session.get('user_id')  # Adjust as needed

            import re
            from django.urls import reverse
            from urllib.parse import urlencode
            
            pollution_remarks_fields = {
                'remarks_air_pollution': request.POST.get('remarks_air_pollution'),
                'remarks_water_pollution': request.POST.get('remarks_water_pollution'),
                'remarks_noise_pollution': request.POST.get('remarks_noise_pollution'),
            }

            # Validate each remarks field for special characters
            for field_name, field_value in pollution_remarks_fields.items():
                if field_value:
                    field_value = field_value.strip()
                    
                    # Check for special characters (allow only alphanumeric and spaces)
                    if re.search(r'[^a-zA-Z0-9\s]', field_value):
                        # print(f"Special characters found in {field_name}")
                        
                        # Create a user-friendly field name for the error message
                        friendly_name = field_name.replace('remarks_', '').replace('_', ' ').title()
                        
                        messages.error(
                            request,
                            f"{friendly_name} remarks should not contain special characters."
                        )
                        
                        # Redirect back with parameters
                        base_url = reverse('checklist')
                        params = urlencode({'userid': industryid, 'appno': appno})
                        return redirect(f"{base_url}?{params}")

            # Convert "Yes"/"No" to boolean
            def to_bool(val):
                return val == "Yes"

            # Retrieve existing or create new
            checklist, created = PollutionChecklist.objects.get_or_create(AppNo=appno)

            checklist.industryid = industryid
            checklist.air_pollution = to_bool(request.POST.get('air_pollution'))
            checklist.remarks_air_pollution = request.POST.get('remarks_air_pollution')
            checklist.water_pollution = to_bool(request.POST.get('water_pollution'))
            checklist.remarks_water_pollution = request.POST.get('remarks_water_pollution')
            checklist.noise_pollution = to_bool(request.POST.get('noise_pollution'))
            checklist.remarks_noise_pollution = request.POST.get('remarks_noise_pollution')
            checklist.added_by = added_by

            checklist.save()

            messages.success(request, "Pollution Checklist saved successfully.")
            # return redirect('rvsf_applications')  # Replace with your actual redirect
            base_url = reverse('checklist')  # path: viewchecklist
            params = urlencode({'userid': industryid, 'appno': appno})
            return redirect(f"{base_url}?{params}")

        return redirect('rvsf_applications')  # If handling GET
    except Exception as db_error:
        logger.exception("❌ ERROR while  savepollution checklist")
        logger.error(f"Exact savepollution checklist  Error: {str(db_error)}")
        
        logger.info(f"Exact savepollution checklist Error: {str(db_error)}")



def SaveWasteRecycleChecklist(request):
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            appno = request.POST.get('appno')
            added_by = request.session.get('user_id')

            import re
            from django.urls import reverse
            from urllib.parse import urlencode
            
            waste_remarks_fields = {
                'remarks_used_oil': request.POST.get('remarks_used_oil'),
                'remarks_plastic_waste': request.POST.get('remarks_plastic_waste'),
                'remarks_battery_waste': request.POST.get('remarks_battery_waste'),
                'remarks_tyre_waste': request.POST.get('remarks_tyre_waste'),
                'remarks_e_waste': request.POST.get('remarks_e_waste'),
                'remarks_steel_scrap': request.POST.get('remarks_steel_scrap'),
            }

            # Validate each remarks field for special characters
            for field_name, field_value in waste_remarks_fields.items():
                if field_value:
                    field_value = field_value.strip()
                    
                    # Check for special characters (allow only alphanumeric and spaces)
                    if re.search(r'[^a-zA-Z0-9\s]', field_value):
                        # print(f"Special characters found in {field_name}")
                        
                        # Create a user-friendly field name for the error message
                        friendly_name = field_name.replace('remarks_', '').replace('_', ' ').title()
                        
                        messages.error(
                            request,
                            f"{friendly_name} remarks should not contain special characters."
                        )
                        
                        # Redirect back with parameters
                        base_url = reverse('checklist')
                        params = urlencode({'userid': industryid, 'appno': appno})
                        return redirect(f"{base_url}?{params}")

            used_oil = request.POST.get('used_oil') == 'Yes'
            remarks_used_oil = request.POST.get('remarks_used_oil')

            plastic_waste = request.POST.get('plastic_waste') == 'Yes'
            remarks_plastic_waste = request.POST.get('remarks_plastic_waste')

            battery_waste = request.POST.get('battery_waste') == 'Yes'
            remarks_battery_waste = request.POST.get('remarks_battery_waste')

            tyre_waste = request.POST.get('tyre_waste') == 'Yes'
            remarks_tyre_waste = request.POST.get('remarks_tyre_waste')

            e_waste = request.POST.get('e_waste') == 'Yes'
            remarks_e_waste = request.POST.get('remarks_e_waste')

            steel_scrap = request.POST.get('steel_scrap') == 'Yes'
            remarks_steel_scrap = request.POST.get('remarks_steel_scrap')


            obj, created = WasteRecycleChecklist.objects.update_or_create(
                AppNo=appno,
                defaults={
                    'industryid': industryid,
                    'used_oil': used_oil,
                    'remarks_used_oil': remarks_used_oil,
                    'plastic_waste': plastic_waste,
                    'remarks_plastic_waste': remarks_plastic_waste,
                    'battery_waste': battery_waste,
                    'remarks_battery_waste': remarks_battery_waste,
                    'tyre_waste': tyre_waste,
                    'remarks_tyre_waste': remarks_tyre_waste,
                    'e_waste': e_waste,
                    'remarks_e_waste': remarks_e_waste,
                    'steel_scrap': steel_scrap,
                    'remarks_steel_scrap': remarks_steel_scrap,
                    'added_by': added_by,
                }
            )

            if created:
                messages.success(request, 'Waste Recycle Checklist created successfully.')
                base_url = reverse('checklist')  # path: viewchecklist
                params = urlencode({'userid': industryid, 'appno': appno})
                return redirect(f"{base_url}?{params}")
            else:
                messages.success(request, 'Waste Recycle Checklist updated successfully.')
                base_url = reverse('checklist')  # path: viewchecklist
                params = urlencode({'userid': industryid, 'appno': appno})
                return redirect(f"{base_url}?{params}")
            

            # return redirect('rvsf_applications')  # Replace with your actual URL name
            base_url = reverse('checklist')  # path: viewchecklist
            params = urlencode({'userid': industryid, 'appno': appno})
            return redirect(f"{base_url}?{params}")
        

        messages.error(request, 'Invalid request method.')
        return redirect('rvsf_applications')
    except Exception as db_error:
        logger.exception("❌ ERROR while  save waste recycle checklist")
        logger.error(f"Exact save waste recycle checklist  Error: {str(db_error)}")
        
        logger.info(f"Exact save waste recycle checklist Error: {str(db_error)}")

@login_required
def SaveDeclarationChecklist(request):
    try:
        if request.method == 'POST':
            appno = request.POST.get('appno')
            industryid = request.POST.get('industryid')
            added_by = request.session.get('user_id')
            declaration = request.POST.get('declaration') == 'Yes'

            import re
            from django.urls import reverse
            from urllib.parse import urlencode
            
            declaration_remarks_fields = {
                'remarks_declaration': request.POST.get('remarks_declaration', '').strip(),
                'remarks_registration_fee_details': request.POST.get('remarks_registration_fee_details', '').strip(),
            }

            # Validate each remarks field for special characters
            for field_name, field_value in declaration_remarks_fields.items():
                if field_value:
                    field_value = field_value.strip()
                    
                    # Check for special characters (allow only alphanumeric and spaces)
                    if re.search(r'[^a-zA-Z0-9\s]', field_value):
                        # print(f"Special characters found in {field_name}")
                        
                        # Create a user-friendly field name for the error message
                        friendly_name = field_name.replace('remarks_', '').replace('_', ' ').title()
                        
                        messages.error(
                            request,
                            f"{friendly_name} remarks should not contain special characters."
                        )
                        
                        # Redirect back with parameters
                        base_url = reverse('checklist')
                        params = urlencode({'userid': industryid, 'appno': appno})
                        return redirect(f"{base_url}?{params}")

            remarks_declaration = request.POST.get('remarks_declaration', '').strip()
            registration_fee_details = request.POST.get('registration_fee_details') == 'Yes'
            remarks_registration_fee_details = request.POST.get('remarks_registration_fee_details', '').strip()

            try:
                checklist, created = PaymentChecklist.objects.update_or_create(
                    AppNo=appno,
                    defaults={
                        'industryid': industryid,
                        'declaration': declaration,
                        'remarks_declaration': remarks_declaration,
                        'registration_fee_details': registration_fee_details,
                        'remarks_registration_fee_details': remarks_registration_fee_details,
                        'added_by': added_by,
                    }
                )
                if created:
                    messages.success(request, "Declaration checklist saved successfully.")
                    base_url = reverse('checklist')  # path: viewchecklist
                    params = urlencode({'userid': industryid, 'appno': appno})
                    return redirect(f"{base_url}?{params}")
            
                    # return redirect('rvsf_applications')  # Replace with your actual URL name
                else:
                    messages.success(request, "Declaration checklist updated successfully.")
                    base_url = reverse('checklist')  # path: viewchecklist
                    params = urlencode({'userid': industryid, 'appno': appno})
                    return redirect(f"{base_url}?{params}")
            
                    # return redirect('rvsf_applications')  # Replace with your actual URL name
            except Exception as e:
                print(e)
                messages.error(request, "Something went wrong while saving declaration checklist.")

            return redirect(request.META.get('HTTP_REFERER', '/'))

        else:
            messages.warning(request, "Invalid request method.")
            return redirect('/')    
    except Exception as db_error:
        logger.exception("❌ ERROR while  save declaration checklist")
        logger.error(f"Exact save declaration checklist  Error: {str(db_error)}")
        
        logger.info(f"Exact save declaration checklist Error: {str(db_error)}")

@login_required
def mark_back_to_applicant(request):
    if request.method == 'POST':
        pass
def ViewGeneralDetails(request):
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            AppNo = request.POST.get('appno')
            data = RvsfRegistration.objects.filter(id=industryid).first()
            generaldata = GeneralDetails.objects.filter(userid=industryid).first()
            statename =  State.objects.filter(state_id=data.state).first()
            districtname = District.objects.filter(city_id=data.district).first()
            FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
            commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 1).first()
            commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 1).count()  
            # print(commentcount)
            return render(request, 'Application/generaldetails.html', {
            'statename': statename,
            'districtname': districtname,
            'general': generaldata,
            'fetchapp' : FetchApp,
            'comment':commentgiven,
            'commentcount': commentcount
        })
    except Exception as db_error:
        logger.exception("❌ ERROR while  view general checklist")
        logger.error(f"Exact view general checklist  Error: {str(db_error)}")
        
        logger.info(f"Exact view general checklist Error: {str(db_error)}")
        
def ViewEquipmentDetails(request):
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            AppNo = request.POST.get('appno')
            data = RvsfRegistration.objects.filter(id=industryid).first()
            equipmentdata = EquipmentEntry.objects.filter(userid=industryid).first()
            statename =  State.objects.filter(state_id=data.state).first()
            districtname = District.objects.filter(city_id=data.district).first()
            FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
            commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 2).first()
            commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 2).count()  
            # print(commentcount)
            return render(request, 'Application/equipmentdetails.html', {
            'statename': statename,
            'districtname': districtname,
            'equipmentdata': equipmentdata,
            'fetchapp' : FetchApp,
            'comment':commentgiven,
            'commentcount': commentcount

        })
    except Exception as db_error:
        logger.exception("❌ ERROR while  view equipment details")
        logger.error(f"Exact view equipment details  Error: {str(db_error)}")
        
        logger.info(f"Exact view equipment details Error: {str(db_error)}")
        
def ViewFacilityDetails(request):
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            AppNo = request.POST.get('appno')
            data = RvsfRegistration.objects.filter(id=industryid).first()
            facilitydata = RvsfFacility.objects.filter(user_id=industryid)
            statename =  State.objects.filter(state_id=data.state).first()
            districtname = District.objects.filter(city_id=data.district).first()
            FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
            commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 3).first()
            commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 3).count()  
            # print(commentcount)
            return render(request, 'Application/facilitydetails.html', {
            'statename': statename,
            'districtname': districtname,
            'facilitydata': facilitydata,
            'fetchapp' : FetchApp,
            'comment':commentgiven,
            'commentcount': commentcount
        })
    
    except Exception as db_error:
        logger.exception("❌ ERROR while  viewfacility details")
        logger.error(f"Exact viewfacility details  Error: {str(db_error)}")
        
        logger.info(f"Exact viewfacility details Error: {str(db_error)}")
        
def ViewRvsfCapacityDetails(request):
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            AppNo = request.POST.get('appno')
            data = RvsfRegistration.objects.filter(id=industryid).first()
            rvsfCapacitydata = PlantCapacity.objects.filter(userid=industryid).first()
            statename =  State.objects.filter(state_id=data.state).first()
            districtname = District.objects.filter(city_id=data.district).first()
            FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
            commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 4).first()
            commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 4).count()  
            # print(commentcount)
            return render(request, 'Application/rvsfcapacitydetails.html', {
            'statename': statename,
            'districtname': districtname,
            'rvsfCapacitydata': rvsfCapacitydata,
            'fetchapp' : FetchApp,
            'comment':commentgiven,
            'commentcount': commentcount
        })
    except Exception as db_error:
        logger.exception("❌ ERROR while  view rvsf capcity details")
        logger.error(f"Exact view rvsf capcity details  Error: {str(db_error)}")
        
        logger.info(f"Exact view rvsf capcity details Error: {str(db_error)}")
        
def ViewPollutionDetails(request):
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            
            AppNo = request.POST.get('appno')
            data = RvsfRegistration.objects.filter(id=industryid).first()
            pollutiondata = PollutionDevice.objects.filter(userid=industryid)
            statename =  State.objects.filter(state_id=data.state).first()
            districtname = District.objects.filter(city_id=data.district).first()
            FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
            commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 5).first()
            commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 5).count()  
            # print(commentcount)
            return render(request, 'Application/pollutiondetails.html', {
            'statename': statename,
            'districtname': districtname,
            'pollutiondata': pollutiondata,
            'fetchapp' : FetchApp,
            'comment':commentgiven,
            'commentcount': commentcount
        })
    
    except Exception as db_error:
        logger.exception("❌ ERROR while  view pollution details")
        logger.error(f"Exact view pollution details  Error: {str(db_error)}")
        
        logger.info(f"Exact view pollution details Error: {str(db_error)}")
        
def ViewWasteRecycleDetails(request):
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            AppNo = request.POST.get('appno')
            data = RvsfRegistration.objects.filter(id=industryid).first()
            wasteRecycledata = WasteRecycled.objects.filter(userid=industryid)
            statename =  State.objects.filter(state_id=data.state).first()
            districtname = District.objects.filter(city_id=data.district).first()
            FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
            commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 6).first()
            commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 6).count()  
            # print(commentcount)
            return render(request, 'Application/wasterecycledetails.html', {
            'statename': statename,
            'districtname': districtname,
            'wasteRecycledata': wasteRecycledata,
            'fetchapp' : FetchApp,
            'comment':commentgiven,
            'commentcount': commentcount
        })
    
    except Exception as db_error:
        logger.exception("❌ ERROR while  view waste details")
        logger.error(f"Exact view waste details  Error: {str(db_error)}")
        
        logger.info(f"Exact view waste details Error: {str(db_error)}")
        
def ViewDeclarationDetails(request):
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            AppNo = request.POST.get('appno')
            data = RvsfRegistration.objects.filter(id=industryid).first()
            generaldata = GeneralDetails.objects.filter(userid=industryid).first()
            statename =  State.objects.filter(state_id=data.state).first()
            districtname = District.objects.filter(city_id=data.district).first()
            FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
            commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 7).first()
            commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 7).count()  
            # print(commentcount)
            return render(request, 'Application/declarationdetails.html', {
            'statename': statename,
            'districtname': districtname,
            'general': generaldata,
            'fetchapp' : FetchApp,
            'comment':commentgiven,
            'commentcount': commentcount
        })
    
    except Exception as db_error:
        logger.exception("❌ ERROR while  view declaration checklist")
        logger.error(f"Exact view declaration checklist  Error: {str(db_error)}")
        
        logger.info(f"Exact view declaration checklist Error: {str(db_error)}")


def save_general_trail(request):
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            # print(industryid)
            AppNo = request.POST.get('appno')
            stateid = request.POST.get('stateid', 0)
            officerid = request.session.get('user_id')
            EditMode = request.POST.get('editmode')
            SPCBComments = request.POST.get('SPCBComments', '').strip()

            india_timezone = pytz.timezone('Asia/Kolkata')
            india_time = timezone.now().astimezone(india_timezone)
            
            # Prevent duplicate AppNo entry
            if UntTrails.objects.filter(AppNo=AppNo , EditMode = EditMode).exists():
                return HttpResponse("Error: Record with this AppNo already exists.", status=400)

            # Create new record
            trail = UntTrails(
                industryid=industryid,
                AppNo=AppNo,
                stateid=stateid,
                officerid=officerid,
                SPCBComments=SPCBComments,
                SPCBCommentDate = india_time if SPCBComments else None,
                EditMode=EditMode
            )

            trail.save()
            if EditMode == '1':
                industryid = industryid
                AppNo = AppNo
                data = RvsfRegistration.objects.filter(id=industryid).first()
                generaldata = GeneralDetails.objects.filter(userid=industryid).first()
                statename =  State.objects.filter(state_id=data.state).first()
                districtname = District.objects.filter(city_id=data.district).first()
                FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
                commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 1).first()
                commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 1).count()  
                #  print(commentcount)
        
                return render(request, 'Application/generaldetails.html', {
                'statename': statename,
                'districtname': districtname,
                'general': generaldata,
                'fetchapp' : FetchApp,
                'comment':commentgiven,
                'commentcount': commentcount
                })
            elif EditMode == '2':
                industryid = industryid
                AppNo = AppNo
                data = RvsfRegistration.objects.filter(id=industryid).first()
                equipmentdata = EquipmentEntry.objects.filter(userid=industryid).first()
                statename =  State.objects.filter(state_id=data.state).first()
                districtname = District.objects.filter(city_id=data.district).first()
                FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
                commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 2).first()
                commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 2).count()  
                # print(commentcount)
                return render(request, 'Application/equipmentdetails.html', {
                'statename': statename,
                'districtname': districtname,
                'equipmentdata': equipmentdata,
                'fetchapp' : FetchApp,
                'comment':commentgiven,
                'commentcount': commentcount
                })
            elif EditMode == '3':
                industryid = industryid
                AppNo = AppNo
                data = RvsfRegistration.objects.filter(id=industryid).first()
                facilitydata = RvsfFacility.objects.filter(user_id=industryid)
                statename =  State.objects.filter(state_id=data.state).first()
                districtname = District.objects.filter(city_id=data.district).first()
                FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
                commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 3).first()
                commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 3).count()  
                # print(commentcount)
                return render(request, 'Application/facilitydetails.html', {
                'statename': statename,
                'districtname': districtname,
                'facilitydata': facilitydata,
                'fetchapp' : FetchApp,
                'comment':commentgiven,
                'commentcount': commentcount
                })
            elif EditMode == '4':
                industryid = industryid
                AppNo = AppNo
                data = RvsfRegistration.objects.filter(id=industryid).first()
                rvsfCapacitydata = PlantCapacity.objects.filter(userid=industryid).first()
                statename =  State.objects.filter(state_id=data.state).first()
                districtname = District.objects.filter(city_id=data.district).first()
                FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
                commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 4).first()
                commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 4).count()  
                # print(commentcount)
                return render(request, 'Application/rvsfcapacitydetails.html', {
                'statename': statename,
                'districtname': districtname,
                'rvsfCapacitydata': rvsfCapacitydata,
                'fetchapp' : FetchApp,
                'comment':commentgiven,
                'commentcount': commentcount
                })
            elif EditMode == '5':
                industryid = industryid
                AppNo = AppNo
                data = RvsfRegistration.objects.filter(id=industryid).first()
                pollutiondata = PollutionDevice.objects.filter(userid=industryid)
                statename =  State.objects.filter(state_id=data.state).first()
                districtname = District.objects.filter(city_id=data.district).first()
                FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
                commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 5).first()
                commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 5).count()  
                # print(commentcount)
                return render(request, 'Application/pollutiondetails.html', {
                'statename': statename,
                'districtname': districtname,
                'pollutiondata': pollutiondata,
                'fetchapp' : FetchApp,
                'comment':commentgiven,
                'commentcount': commentcount
            })
            elif EditMode == '6':
                industryid = industryid
                AppNo = AppNo
                data = RvsfRegistration.objects.filter(id=industryid).first()
                wasteRecycledata = WasteRecycled.objects.filter(userid=industryid)
                statename =  State.objects.filter(state_id=data.state).first()
                districtname = District.objects.filter(city_id=data.district).first()
                FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
                commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 6).first()
                commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 6).count()  
            # print(commentcount)
                return render(request, 'Application/wasterecycledetails.html', {
                'statename': statename,
                'districtname': districtname,
                'wasteRecycledata': wasteRecycledata,
                'fetchapp' : FetchApp,
                'comment':commentgiven,
                'commentcount': commentcount
                })
            elif EditMode == '7':
                industryid = industryid
                AppNo = AppNo
                data = RvsfRegistration.objects.filter(id=industryid).first()
                generaldata = GeneralDetails.objects.filter(userid=industryid).first()
                statename =  State.objects.filter(state_id=data.state).first()
                districtname = District.objects.filter(city_id=data.district).first()
                FetchApp = ConfirmApplication.objects.filter(userid = industryid).first()
                commentgiven = UntTrails.objects.filter(industryid = industryid , EditMode = 7).first()
                commentcount = UntTrails.objects.filter(industryid = industryid , EditMode = 7).count()  
            # print(commentcount)
                return render(request, 'Application/declarationdetails.html', {
                'statename': statename,
                'districtname': districtname,
                'general': generaldata,
                'fetchapp' : FetchApp,
                'comment':commentgiven,
                'commentcount': commentcount
                })




            
        else:
            return HttpResponse("Invalid request method.", status=405)
    
    except Exception as db_error:
        logger.exception("❌ ERROR while  save general trail")
        logger.error(f"Exact save general trail  Error: {str(db_error)}")
        
        logger.info(f"Exact save general trail Error: {str(db_error)}")



def MarkIncomplete(request):
    try:
        if request.method == 'POST':
            industryid = request.POST.get('industryid')
            finalremark = request.POST.get('final_remark')
            # currentofficerid=request.session.get()
            currentofficerid = request.session.get('user_id')
            appno = request.POST.get('appno')

            # signup_details=SignupChecklist.objects.filter(industryid=industryid).exists()
            # general_details=GeneralChecklist.objects.filter(industryid=industryid).exists()
            # equipment_details=EquipmentChecklist.objects.filter(industryid=industryid).exists()
            # facility_details=FacilityChecklist.objects.filter(industryid=industryid).exists()
            # capacity_details=CapacityChecklist.objects.filter(industryid=industryid).exists()
            # pollution_details=PollutionChecklist.objects.filter(industryid=industryid).exists()
            # waste_details=WasteRecycleChecklist.objects.filter(industryid=industryid).exists()
            # payment_details=PaymentChecklist.objects.filter(industryid=industryid).exists()
            checklists_status = {
                'signup': SignupChecklist.objects.filter(industryid=industryid).exists(),
                'general': GeneralChecklist.objects.filter(Industryid=industryid).exists(),
                'equipment': EquipmentChecklist.objects.filter(industryid=industryid).exists(),
                'facility': FacilityChecklist.objects.filter(industryid=industryid).exists(),
                'capacity': CapacityChecklist.objects.filter(industryid=industryid).exists(),
                'pollution': PollutionChecklist.objects.filter(industryid=industryid).exists(),
                'waste': WasteRecycleChecklist.objects.filter(industryid=industryid).exists(),
                'payment': PaymentChecklist.objects.filter(industryid=industryid).exists(),
            }
            
            # Check if all checklists are completed
            all_completed = all(checklists_status.values())
            
            if not all_completed:
                # Create a user-friendly message with missing checklist names
                checklist_names = {
                    'signup': 'Signup Checklist',
                    'general': 'General Checklist', 
                    'equipment': 'Equipment Checklist',
                    'facility': 'Facility Checklist',
                    'capacity': 'Capacity Checklist',
                    'pollution': 'Pollution Checklist',
                    'waste': 'Waste & Recycle Checklist',
                    'payment': 'Payment Checklist'
                }
                
                missing = [checklist_names[key] for key, exists in checklists_status.items() if not exists]
                
                if len(missing) == 1:
                    message = f"Please complete the {missing[0]} first."
                else:
                    message = f"Please complete the following checklists first: {', '.join(missing)}"
                
                messages.error(request, message)
                # return redirect('rvsf_applications')
                base_url = reverse('checklist')  # path: viewchecklist
                params = urlencode({'userid': industryid, 'appno': appno})
                return redirect(f"{base_url}?{params}")

            import re
            
            if finalremark:
                finalremark = finalremark.strip()
                
                # Check for special characters (allow only alphanumeric and spaces)
                if re.search(r'[^a-zA-Z0-9\s]', finalremark):
                    messages.error(
                        request,
                        "Final remark should not contain special characters."
                    )
                    return redirect('rvsf_applications')
            # print(finalremark,'scscsc')
            # print(industryid,'scscsc')
            checklistcount = UntTrails.objects.filter(industryid = currentofficerid).count()
            spcbuser = StateUsers.objects.filter(id=currentofficerid).first()
            marked_by_role = spcbuser.RoleAccess

            fetchmarkedDetails = StateUsers.objects.filter(
                State_id=spcbuser.State_id
            ).first()

            if not fetchmarkedDetails:
                messages.error(request, "User to mark not found.")
                return redirect('dashboard')

            marked_by_designation = spcbuser.officerDesignation

            added_by_userid = spcbuser.id
            added_by_person = spcbuser.OfficerName
            added_to_userid = fetchmarkedDetails.id

            # industry_user_id = userid
            stateid = spcbuser.State_id
            
            if checklistcount >= 0 :
                ApplicationTrail.objects.create(
                    AppNo=appno,
                    stateid=stateid,
                    marked_to_designation='User',
                    marked_by_designation=marked_by_designation,
                    marked_to_role=0,
                    marked_by_role=marked_by_role,
                    comment=finalremark,
                    added_by_userid=added_by_userid,
                    added_by_person=added_by_person,
                    added_to_person='User',
                    added_to_userid=added_to_userid,
                    industry_user_id=industryid
                )
                updateunitapp = ConfirmApplication.objects.filter(userid = industryid).first()
                updateunitapp.incomplete = 1
                updateunitapp.incompleteRemark = finalremark
                updateunitapp.appstatus = 5
                updateunitapp.save()
            messages.success(request, "Application Send to Industry.")
            return redirect('rvsf_applications')  # Replace with your actual URL name
    
    except Exception as db_error:
        logger.exception("❌ ERROR while  mark in complete")
        logger.error(f"Exact mark in complete  Error: {str(db_error)}")
        
        logger.info(f"Exact mark in complete Error: {str(db_error)}")


def generate_rvsf_reg_no(gst_number):
    # 1. Fixed prefix
    prefix = ""

    # 2. Year - Full 4-digit year
    year = datetime.now().strftime("%Y")

    # 3. Last 2 characters of GST number
    gst_suffix = gst_number[-2:] if gst_number else "XX"

    # 4. Build base for filtering existing records
    base_code = f"{prefix}{year}{gst_suffix}"


    new_seq = "0001"

    # 7. Final registration number
    return f"{base_code}{new_seq}"


import requests
from django.http import HttpResponse, HttpResponseBadRequest

def image_proxy(request):
    url = request.GET.get("url")
    if not url:
        return HttpResponseBadRequest("Missing image url")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": url,
    }

    try:
        r = requests.get(
            url,
            headers=headers,
            timeout=10,
            verify=True
        )

        if r.status_code != 200:
            return HttpResponseBadRequest(f"Fetch failed: {r.status_code}")

        return HttpResponse(
            r.content,
            content_type=r.headers.get("Content-Type", "image/jpeg")
        )

    except requests.RequestException as e:
        return HttpResponseBadRequest(str(e))

counter_lock = threading.Lock()

def get_next_global_certificate_number():
    """Get next GLOBAL certificate number (001, 002, 003 for all certificates)"""
    counter_file = os.path.join(settings.BASE_DIR, 'certificate_counter.json')
    
    with counter_lock:  # Thread safety
        # Create file if it doesn't exist
        if not os.path.exists(counter_file):
            with open(counter_file, 'w') as f:
                json.dump({"global_counter": 1}, f)
        
        # Read and update counter
        with open(counter_file, 'r+') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"global_counter": 1}
            
            # Get current counter
            current_number = data.get("global_counter", 1)
            
            # Increment for next time
            data["global_counter"] = current_number + 1
            
            # Write back
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
            
            return current_number

@login_required
def GenerateCertificate(request):
    try:
        industryid = request.POST.get('industryid')
        
        with transaction.atomic():
            appstatus = ConfirmApplication.objects.select_for_update().filter(
                userid=industryid
            ).first()
            
            if not appstatus:
                return HttpResponse("Application not found")
            
            profiledata = RvsfRegistration.objects.filter(id=industryid).first()
            if not profiledata or not profiledata.gst_no:
                return HttpResponse("Profile data or GST number not found")
            
            appstatus.appstatus = 9
            
            if appstatus.certificateno in [None, '', 'None']:
                # Extract last 4 digits of GST number
                year = datetime.now().strftime("%Y") 
                gst_last_4 = profiledata.gst_no[-2:]
                state_id = appstatus.state_id
                # Get next GLOBAL sequence number
                next_seq = get_next_global_certificate_number()
                
                # Format as CERT+GST_LAST_4+3_DIGIT_GLOBAL_SEQUENCE
                appstatus.certificateno = f"{state_id}{year}{gst_last_4}{next_seq:03d}"
            
            appstatus.save()
        
        # Fetch data for the certificate template
        appdata = ConfirmApplication.objects.filter(userid=industryid).first()
        vecType = VehicleType.objects.filter(userid=industryid).values()
        capacityPlant = PlantCapacity.objects.filter(userid=industryid).first()
        stateurl = State.objects.filter(state_id=appdata.state_id).first()
        
        vehcarr = list(
        VehicleType.objects
        .filter(userid=industryid)
        .values_list('vehicle_type', flat=True)
    )

        vehcarr_string = ",".join(vehcarr)

        # print(vehcarr)
        # print(vecType,'fsdfsjbfhjb')
        # print(industryid,'fsdfsj32423bfhjb')
        
        # print(capacityPlant,'fsdfsasdd2342jbfhjb')
        
        context = {
            "issue_date": datetime.now().strftime("%d-%m-%Y"),
            'data': appdata,
            'profile': profiledata,
            # 'vecType': vehcarr,
            'vecType': vehcarr_string,
            'capacitydata': capacityPlant,
            'statelogo': stateurl.state_url if stateurl else '',
            'application_date': timezone.localtime(appdata.created_at).strftime("%d-%m-%Y ") if appdata and appdata.created_at else '',
        }
        
        return render(request, 'processing/rvsf_certificate.html', context)
    except Exception as db_error:
        logger.exception("❌ ERROR while  geenrate certificate")
        logger.error(f"Exact geenrate certificate  Error: {str(db_error)}")
        
        logger.info(f"Exact geenrate certificate Error: {str(db_error)}")

# def GenerateCertificate(request):

#     # Generate a registration number
#     # registration_no = generate_rvsf_reg_no(user.gst_no)
#     certificate_status = 9
#     # if certificate_status == 9:
#     industryid = request.POST.get('industryid')
#     a=1
#     appstatus = ConfirmApplication.objects.filter(userid = industryid).first()
#     appstatus.appstatus = 9
#     if(appstatus.certificateno == 'None'):
#         appstatus.certificateno=a
#         a+=1
#     appstatus.save()

#     appdata = ConfirmApplication.objects.filter(userid = industryid).first()
#     profiledata = RvsfRegistration.objects.filter(id = industryid).first()
#     vecType = VehicleType.objects.filter(userid = industryid).values()
#     capacityPlant = PlantCapacity.objects.filter(userid =  industryid).first()
#     stateurl = State.objects.filter(state_id = appdata.state_id).first()
#     print(stateurl.state_url,'dhhh')
    

#     context = {
#         "issue_date": datetime.now().strftime("%d-%m-%Y"),
#         'data':appdata,
#         'profile':profiledata,
#         'vecType':vecType,
#         'capacitydata':capacityPlant,
#         'statelogo':stateurl.state_url,
#         'application_date': timezone.localtime(appdata.created_at).strftime("%d-%m-%Y "),
#         # "registration_number": registration_no,
#     }
#     print(context['statelogo'])
#     return render(request, 'processing/rvsf_certificate.html', context)


@login_required
def create_pdf(request, user_id):
    
    try:
        
        html_content = GenerateCertificate(request, user_id)

        
        cert_dir = os.path.join(settings.BASE_DIR, 'certificates')
        os.makedirs(cert_dir, exist_ok=True)
        cert_no = f"CERT-{user_id}"
        pdf_path = os.path.join(cert_dir, f"{cert_no}.pdf")
        

        # 4. Convert HTML to PDF using pdfkit
        # config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
        # pdfkit.from_string(html_content, pdf_path, configuration=config)

        # 5. Now read the PDF, encode and proceed with eSigner as before
        with open(pdf_path, "rb") as f:
            b64_pdf = base64.b64encode(f.read()).decode()

        user_id = request.user.id
        reference_no = f"{cert_no}-{user_id}"
        redirect_url = request.build_absolute_uri('/elv/admin/view-certs/')

        json_data = {
            "Name": "Deepti Kapil",
            "FileType": "PDF",
            "SignatureType": 1,
            "SelectPage": "ALL",
            "SignaturePosition": "Bottom-Right",
            "AuthToken": "33b71185-f46d-4fcd-b8ed-fafb6644e31c",  # Replace in prod
            "File": b64_pdf,
            "PageNumber": "",
            "Noofpages": 0,
            "PreviewRequired": True,
            "SUrl": redirect_url,
            "FUrl": "/Error",
            "CUrl": "/Cancel",
            "ReferenceNumber": reference_no,
            "IsCompressed": False,
            "IsCosign": False,
            "IsCustomized": False
        }

        encrypt_dir = os.path.join(settings.BASE_DIR, 'Encrypt_Jar')
        os.makedirs(encrypt_dir, exist_ok=True)
        json_path = os.path.join(encrypt_dir, 'Json_Data.txt')
        with open(json_path, 'w') as f:
            json.dump(json_data, f)

        jar_path = os.path.join(settings.BASE_DIR, "SG_Final_Jar_PHP", "Final_ED_Both.jar")
        java_path = r"C:\Program Files\Java\jdk-24\bin\java.exe"

        args = [
            java_path, "-jar", jar_path,
            "Encrypt",
            json_path,
            os.path.join(encrypt_dir, "session_key.txt"),
            os.path.join(encrypt_dir, "encrypted_sessionkey.txt"),
            os.path.join(encrypt_dir, "encrypted_json_data.txt"),
            os.path.join(encrypt_dir, "encrypted_hashof_json_data.txt"),
            os.path.join(encrypt_dir, "certificate.cer")
        ]

        subprocess.run(args, check=True)

        with open(os.path.join(encrypt_dir, "encrypted_sessionkey.txt")) as f:
            encsession = f.read()
        with open(os.path.join(encrypt_dir, "encrypted_json_data.txt")) as f:
            encjson = f.read()
        with open(os.path.join(encrypt_dir, "encrypted_hashof_json_data.txt")) as f:
            enchashof = f.read()


        return render(request, "processing/esign/call_gateway.html",{
            "encsession": encsession,
            "encjson": encjson,
            "enchashof": enchashof,
        })

    except subprocess.CalledProcessError as e:
        logger.exception("❌ ERROR while  create pdf")
        logger.error(f"Exact create pdf  Error: {str(db_error)}")
        
        logger.info(f"Exact create pdf Error: {str(db_error)}")
        return HttpResponse(f"Java execution failed: {e}")
        
    except FileNotFoundError as e:
        logger.exception("❌ ERROR while  create pdf")
        logger.error(f"Exact create pdf  Error: {str(db_error)}")
        
        logger.info(f"Exact create pdf Error: {str(db_error)}")
        return HttpResponse(f"File not found: {e}")
    except Exception as e:
        logger.exception("❌ ERROR while  create pdf")
        logger.error(f"Exact create pdf  Error: {str(db_error)}")
        
        logger.info(f"Exact create pdf Error: {str(db_error)}")
        return HttpResponse(f"Unexpected error: {e}")

    
def view_certs(request):
    try:
        reference = request.GET.get("Referencenumber")
        status = request.GET.get("ReturnStatus")
        return_value = request.GET.get("Returnvalue")

        if not reference:
            return HttpResponse("Missing reference number")

        cert_no, user_id = reference.split("-")

        if status == "Success" and return_value:
            enc_path = os.path.join(settings.BASE_DIR, "Encrypt_Jar/decrypt/Encrypted_Signed_Data.txt")
            dec_path = os.path.join(settings.BASE_DIR, "Encrypt_Jar/decrypt/Decrypted_Signed_Data.txt")

            with open(enc_path, "w") as f:
                f.write(return_value)

            subprocess.run([
                "java", "-jar", os.path.join(settings.BASE_DIR, "SG_Final_Jar_PHP", "Final_ED_Both.jar"),
                "Decrypt",
                enc_path,
                os.path.join(settings.BASE_DIR, "Encrypt_Jar/session_key.txt"),
                dec_path
            ])

            with open(dec_path) as f:
                b64_signed = f.read()
            binary_pdf = base64.b64decode(b64_signed)

            output_pdf_path = os.path.join(settings.BASE_DIR, f"certificates/signed_files/{cert_no}.pdf")
            with open(output_pdf_path, "wb") as f:
                f.write(binary_pdf)

            return HttpResponse("Certificate signed and saved.")
        else:
            return HttpResponse(f"Error: {request.GET.get('ErrorMessage', 'Unknown')}")
    except Exception as db_error:
        logger.exception("❌ ERROR while  view cert")
        logger.error(f"Exact view cert  Error: {str(db_error)}")
        
        logger.info(f"Exact view cert Error: {str(db_error)}")


@login_required
def ViewIndustryTrails(request):
    pass

def logoutspcb(request):
    request.session.flush()  # Clears all session data
    return redirect('spcb_home')


# --------------------------------------- Logics from Producer ----------------------------------#


def rvsf_detail(request):
    try:
        # rvsfId = request.POST.get('rvsf_id')
        # rvsfid = request.POST.get('rvsf_id')
        sessionuserid = request.session.get('user_id')
        # user = StateUsers.objects.filter(id=sessionuserid).first()
        # print("showing this", sessionuserid)
        # if user:
        #     print(user.RoleAccess)
        # else:
        #     print("No user found with id", sessionuserid)
        # print(userid.RoleAccess)
        rvsfid = 48
        

        entity = RvsfRegistration.objects.filter(id=rvsfid).first()
        generaldata = GeneralDetails.objects.filter(userid=rvsfid).first()
        rvsfdata = RvsfDetails.objects.filter(userid=rvsfid).first()
        payments = Payment.objects.filter(owner_id=rvsfid, status='success')
        # for p in payments:
        #     print(p.order_id)
        # print(payments)
        # print(rvsfid,('ffeefefeef'))
        # ... other queries ...

        context = {
            'entity': entity,
            'general': generaldata,
            'rvsf': rvsfdata,
            'statename': State.objects.filter(state_id=entity.state).first(),
            'districtname': District.objects.filter(city_id=entity.district).first(),
            'equipmentdata': EquipmentType.objects.all().order_by('id'),
            'data': EquipmentEntry.objects.filter(userid=rvsfid),
            'facilitydata': RvsfFacility.objects.filter(user_id=rvsfid).first(),
            'VechileType': VehicleType.objects.filter(userid=rvsfid),
            'capacitydata': PlantCapacity.objects.filter(userid=rvsfid).first(),
            'pollutiondetails': PollutionDevice.objects.filter(userid=rvsfid),
            'wasterecycled': WasteRecycled.objects.filter(userid=rvsfid),
            'payment': Payment.objects.filter(owner_id=rvsfid, status='success'),
            'rvsfuser': StateUsers.objects.filter(id=sessionuserid).first(),
        }
        # rvsf_details = get_object_or_404(rvsfdetails, id=rvsfId)
        return render(
            request,
            'spcb/spcb_rvsf.html',
            {
                'rvsf_details': context
            }
        )
    except Exception as db_error:
        logger.exception("❌ ERROR while  rvsf details spcb")
        logger.error(f"Exact rvsf details spcb  Error: {str(db_error)}")
        
        logger.info(f"Exact rvsf details spcb Error: {str(db_error)}")    
