from django.conf import settings
from django.core.mail import EmailMultiAlternatives

# --------------------------------------------------
# SMTP CONFIG (same as nodemailer)
# --------------------------------------------------
settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

settings.EMAIL_HOST = "smtpsgwhyd.nic.in"
settings.EMAIL_PORT = 465
settings.EMAIL_USE_TLS = TRUE

settings.EMAIL_HOST_USER = "elv-epr.cpcb@gov.in"        # NIC email ID
settings.EMAIL_HOST_PASSWORD = "Elvepr@987"    # NIC password

settings.DEFAULT_FROM_EMAIL = '"CPCB Battery EPR" <noreply-ucams.cpcb@gov.in>'


# --------------------------------------------------
# Test OTP Mail
# --------------------------------------------------
def send_test_otp():
    subject = "Your UCAMS OTP Code"
    otp = "123456"

    text_content = f"Your OTP code is {otp}"
    html_content = f"<p>Your OTP code is <b>{otp}</b></p>"

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=["mahabhart.cpcb@gmail.com"],
    )

    msg.attach_alternative(html_content, "text/html")
    msg.send()

    print("✅ OTP Mail sent successfully!")


# --------------------------------------------------
# Run directly
# --------------------------------------------------
if __name__ == "__main__":
    send_test_otp()
