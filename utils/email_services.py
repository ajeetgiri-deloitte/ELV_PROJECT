from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
import logging
from registration.models import Registration
from RvsfApp.models import RvsfRegistration
from SpcbApp.models import StateUsers


logger = logging.getLogger(__name__)

def sendContactEmail(subject, to_email, html_content, text_content=""):
    """Common Contact email sender"""

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content or "Please view this email in HTML format.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        return True

    except Exception as e:
        logger.error("Email failed for %s: %s", to_email, str(e), exc_info=True)
        return False

def sendOtpEmail(name, username, email, otp):
    subject = "One Time Password for End of Life Vehicle"
    
    display_name = name or "User"

    html_content = f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:30px 0;">
        <tr>
            <td align="center">

            <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;font-family:Arial,Helvetica,sans-serif;border:1px solid #e6e8ec;">
                
                <tr>
                <td style="padding:18px 24px;background:#0b5cff;color:#ffffff;font-size:18px;font-weight:bold;border-radius:8px 8px 0 0;">
                    End of Life Vehicle – OTP Verification
                </td>
                </tr>

                <tr>
                <td style="padding:24px;color:#333333;font-size:14px;line-height:1.6;">
                    
                    <p style="margin:0 0 10px;">Dear <strong>{display_name}</strong>,</p>

                    <p style="margin:0 0 16px;">
                    Your One-Time Password (OTP) for accessing the <strong>ELV EPR Portal</strong> is given below:
                    </p>

                    <div style="text-align:center;margin:22px 0;">
                    <div style="display:inline-block;padding:12px 22px;font-size:22px;font-weight:bold;border:1px dashed #0b5cff;border-radius:6px;background:#f3f7ff;">
                        {otp}
                    </div>
                    </div>

                    <p style="margin:0 0 10px;">
                    This OTP is valid for <strong>15 minutes</strong>.
                    </p>

                    <p style="margin:0 0 10px;">
                    <strong>Do not share this OTP</strong> with anyone. CPCB never asks for OTP over phone or email.
                    </p>

                    <p style="margin-top:18px;">
                    Regards,<br>
                    Central Pollution Control Board
                    </p>

                </td>
                </tr>

                <tr>
                <td style="padding:14px 24px;background:#fafbfc;border-top:1px solid #eceff3;color:#777;font-size:12px;">
                    This is an automated email. Please do not reply. If you did not request this OTP, kindly ignore this message.
                </td>
                </tr>

            </table>

            </td>
        </tr>
        </table>
        """


    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=f"Your OTP is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        return True

    except Exception as e:
        logger.error("OTP email failed for %s: %s", email, str(e), exc_info=True)
        raise RuntimeError("OTP email sending failed") from e

def sendSignupEmail(name, username, auth_email, password):
    subject = "Sign-Up Successfully Completed – EPR End of Life Vehicle"
    display_name = name or "User"

    html_content = f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:30px 0;">
        <tr>
            <td align="center">

            <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;font-family:Arial,Helvetica,sans-serif;border:1px solid #e6e8ec;">

                <tr>
                <td style="padding:18px 24px;background:#0b5cff;color:#ffffff;font-size:18px;font-weight:bold;border-radius:8px 8px 0 0;">
                    Sign-Up Successful – ELV EPR Portal
                </td>
                </tr>

                <tr>
                <td style="padding:24px;color:#333333;font-size:14px;line-height:1.6;">

                    <p style="margin:0 0 10px;">Dear <strong>{display_name}</strong>,</p>

                    <p style="margin:0 0 14px;">
                    Your sign-up on the <strong>End of Life Vehicle (ELV) EPR Portal</strong> has been completed successfully.
                    </p>

                    <p style="margin:0 0 10px;font-weight:bold;">Login Credentials</p>

                    <table cellpadding="6" cellspacing="0" style="background:#f7f9ff;border:1px solid #dbe3ff;border-radius:6px;">
                    <tr>
                        <td style="font-size:13px;">Username:</td>
                        <td style="font-size:13px;font-weight:bold;">{username}</td>
                    </tr>
                    <tr>
                        <td style="font-size:13px;">Password:</td>
                        <td style="font-size:13px;font-weight:bold;">{password}</td>
                    </tr>
                    </table>

                    <p style="margin:14px 0 10px;">
                    Please keep these credentials confidential. For security reasons, it is strongly recommended to
                    <strong>change your password on first login</strong>.
                    </p>

                    <p style="margin-top:18px;">
                    Regards,<br>
                    Central Pollution Control Board
                    </p>

                </td>
                </tr>

                <tr>
                <td style="padding:14px 24px;background:#fafbfc;border-top:1px solid #eceff3;color:#777;font-size:12px;">
                    This is an automated email. Please do not reply. If you did not create this account, please contact the portal support team.
                </td>
                </tr>

            </table>

            </td>
        </tr>
        </table>
        """


    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body="Your signup has been successfully completed.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[auth_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        return True

    except Exception as e:
        logger.error(
            "Signup email failed for %s: %s",
            auth_email,
            str(e),
            exc_info=True
        )
        raise RuntimeError("Signup email sending failed") from e

def sendNewPasswordEmail(name, username, auth_email, password):
    subject = "Password Changed Successfully – EPR End of Life Vehicle"
    display_name = name or "User"

    html_content = f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:30px 0;">
        <tr>
            <td align="center">

            <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;font-family:Arial,Helvetica,sans-serif;border:1px solid #e6e8ec;">

                <tr>
                <td style="padding:18px 24px;background:#0b5cff;color:#ffffff;font-size:18px;font-weight:bold;border-radius:8px 8px 0 0;">
                    Password Changed Successfully – ELV EPR Portal
                </td>
                </tr>

                <tr>
                <td style="padding:24px;color:#333333;font-size:14px;line-height:1.6;">

                    <p style="margin:0 0 10px;">Dear <strong>{display_name}</strong>,</p>

                    <p style="margin:0 0 14px;">
                    Your password for the <strong>End of Life Vehicle (ELV) EPR Portal</strong> has been changed successfully.
                    </p>

                    <p style="margin:0 0 6px;font-weight:bold;">Account Details</p>

                    <table cellpadding="6" cellspacing="0" style="background:#f7f9ff;border:1px solid #dbe3ff;border-radius:6px;">
                    <tr>
                        <td style="font-size:13px;">Username:</td>
                        <td style="font-size:13px;font-weight:bold;">{username}</td>
                    </tr>
                    <tr>
                        <td style="font-size:13px;">New Password:</td>
                        <td style="font-size:13px;font-weight:bold;">{password}</td>
                    </tr>
                    </table>

                    <p style="margin:14px 0 8px;">
                    If you did **not** initiate this change, please reset your password immediately and contact support.
                    </p>

                    <p style="margin:0 0 8px;">
                    For your security, avoid sharing your password and consider changing it regularly.
                    </p>

                    <p style="margin-top:18px;">
                    Regards,<br>
                    Central Pollution Control Board
                    </p>

                </td>
                </tr>

                <tr>
                <td style="padding:14px 24px;background:#fafbfc;border-top:1px solid #eceff3;color:#777;font-size:12px;">
                    This is an automated message. Please do not reply. If you didn’t request a password change, report it immediately through the portal helpdesk.
                </td>
                </tr>

            </table>

            </td>
        </tr>
        </table>
        """


    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body="Your password has been changed successfully.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[auth_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        return True

    except Exception as e:
        logger.error(
            "Password change email failed for %s: %s",
            auth_email,
            str(e),
            exc_info=True
        )
        raise RuntimeError("Password email sending failed") from e


def sendForgetPwdEmail(username, company_email):

    producer = Registration.objects.filter(
        username=username,
        company_email=company_email
    ).first()
    print(producer,'prod')

    rvsf = RvsfRegistration.objects.filter(
        username=username,
        company_email=company_email
    ).first()
    print(producer,'rvsf')

    spcb = StateUsers.objects.filter(
        username=username,
        auth_email=company_email
    ).first()
    print(producer,'spcb')

    # ---- CONDITION HANDLING ----
    if not producer and not rvsf and not spcb:
        return False, "Invalid Username or Email."

    # Determine which user object to reset
    if producer:
        user = producer
        user_type = "Producer"
    elif rvsf:
        user = rvsf
        user_type = "RVSF User"
    else:
        user = spcb
        user_type = "SPCB User"

    # ---- GENERATE NEW PASSWORD ----
    new_password = get_random_string(
        length=8,
        allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    )

    # ---- UPDATE PASSWORD ----
    user.password = make_password(new_password)
    user.first_login = 0

    subject = "Password Reset – EPR End of Life Vehicle"

    html_content = f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:30px 0;">
        <tr>
            <td align="center">

            <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;font-family:Arial,Helvetica,sans-serif;border:1px solid #e6e8ec;">

                <tr>
                <td style="padding:18px 24px;background:#0b5cff;color:#ffffff;font-size:18px;font-weight:bold;border-radius:8px 8px 0 0;">
                    Password Reset – ELV EPR Portal
                </td>
                </tr>

                <tr>
                <td style="padding:24px;color:#333333;font-size:14px;line-height:1.6;">

                    <p style="margin:0 0 10px;">Dear User,</p>

                    <p style="margin:0 0 14px;">
                    Your password for the <strong>End of Life Vehicle (ELV) EPR Portal</strong> has been reset successfully.
                    </p>

                    <p style="margin:0 0 8px;font-weight:bold;">Account Credentials</p>

                    <table cellpadding="6" cellspacing="0" style="background:#f7f9ff;border:1px solid #dbe3ff;border-radius:6px;">
                    <tr>
                        <td style="font-size:13px;">Username:</td>
                        <td style="font-size:13px;font-weight:bold;">{username}</td>
                    </tr>
                    <tr>
                        <td style="font-size:13px;">Temporary Password:</td>
                        <td style="font-size:13px;font-weight:bold;">{new_password}</td>
                    </tr>
                    </table>

                    <p style="margin:14px 0 8px;">
                    Please log in using this temporary password and
                    <strong>change your password immediately</strong>.
                    </p>

                    <p style="margin:0 0 8px;">
                    Do not share your password with anyone. CPCB will never ask for your password.
                    </p>

                    <p style="margin-top:18px;">
                    Regards,<br>
                    Central Pollution Control Board
                    </p>

                </td>
                </tr>

                <tr>
                <td style="padding:14px 24px;background:#fafbfc;border-top:1px solid #eceff3;color:#777;font-size:12px;">
                    This is an automated email. Please do not reply. If you did not request a password reset, contact the portal helpdesk immediately.
                </td>
                </tr>

            </table>

            </td>
        </tr>
        </table>
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
            company_email, str(e),
            exc_info=True
        )
        return False, "Unable to send email at the moment. Please try again later."


# def sendForgetPwdEmail(username, company_email):
#     producer = Registration.objects.filter(
#         username=username,
#         company_email=company_email
#     ).first()
    
#     rvsf = RvsfRegistration.objects.filter(
#         username=username,
#         company_email=company_email
#     ).first()

#     if not producer or rvsf:
#         return False, "Invalid Username or Email."

#     # Generate new password
#     new_password = get_random_string(
#         length=8,
#         allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
#     )

#     # Save hashed password
#     user.password = make_password(new_password)
#     user.first_login = 0

#     subject = "Password Reset – EPR End of Life Vehicle"

#     html_content = f"""
#         <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
#             <p>Dear User,</p>

#             <p>Your password has been reset for the
#             <strong>EPR End of Life Vehicle</strong> portal.</p>

#             <div style="background-color: #f5f7fa; border: 1px solid #ddd;
#                         border-radius: 6px; padding: 12px; margin: 15px 0;">
#                 <p><strong>Username:</strong> {username}</p>
#                 <p><strong>New Password:</strong> {new_password}</p>
#             </div>

#             <p>Please log in and change your password immediately.</p>

#             <p>Regards,<br>
#             Central Pollution Control Board (CPCB)</p>
#         </div>
#     """

#     try:
#         msg = EmailMultiAlternatives(
#             subject=subject,
#             body="Your password has been reset successfully.",
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[company_email],
#         )
#         msg.attach_alternative(html_content, "text/html")
#         msg.send(fail_silently=False)

#         user.save()
#         return True, "New password has been sent to your registered company email."

#     except Exception as e:
#         logger.error(
#             "Forgot password email failed for %s: %s",
#             company_email,
#             str(e),
#             exc_info=True
#         )
#         return False, "Unable to send email at the moment. Please try again later."

