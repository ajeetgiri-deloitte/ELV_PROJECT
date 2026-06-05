# ------------------------------------------------------------------------
"""
Django settings for ELV project.
Supports both development (DEBUG=True) and production (DEBUG=False).
"""
# ------------------------------------------------------------------------

from pathlib import Path
import os
import warnings
import pdfkit
import platform
from dotenv import load_dotenv
from datetime import datetime


# ------------------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

RSA_PRIVATE_KEY_PATH = BASE_DIR / "keys" / "private.pem"
RSA_PUBLIC_KEY_PATH  = BASE_DIR / "keys" / "public.pem"

load_dotenv(BASE_DIR / ".env")

# ------------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------------
TEMPLATE_DIR = str(BASE_DIR / "registration" / "templates")

# ------------------------------------------------------------------------
# General Security
# ------------------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY is not set")


CRYPTOGRAPHY_ENCRYPTION_KEY = b"HsCih6RKKPZlY55SECelx0lv3ahuPi3lERT_WI9ErqE="

DEBUG = True  # default, override for dev
ALLOWED_HOSTS = ['*']  # update for production
TRUSTED_PROXIES = ['*']



# ------------------------------------------------------------------------
# Installed Apps
# ------------------------------------------------------------------------
INSTALLED_APPS = [
    "csp",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'registration.apps.RegistrationConfig',
    'CpcbApp',
    'RvsfApp',
    'SpcbApp',
    'captcha',
    'Transfer_Certificate.apps.TransferCertificateConfig',
]

# ------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'registration.middleware.AutoLogout',
    'registration.middleware.NoCacheMiddleware',
    'registration.middleware.RemoveServerHeadersMiddleware',
    "registration.middleware.OneSessionPerUserMiddleware",
    'registration.middleware.MetadataStripMiddleware',
    "ELV.settings_security.AdditionalSecurityHeadersMiddleware",
]

# ✅ Ensure sessions are stored in the database (not lost)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ------------------------------------------------------------------------
# URLs & Templates
# ------------------------------------------------------------------------
CSRF_TRUSTED_ORIGINS = ["https://demosignergateway.emsigner.com/"]

ROOT_URLCONF = 'ELV.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'RvsfApp.context_processors.certificate_access',
            ],
        },
    },
]

WSGI_APPLICATION = 'ELV.wsgi.application'


# ------------------------------------------------------------------------
# Database (MySQL)
# ------------------------------------------------------------------------


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "OPTIONS": {"sql_mode": "STRICT_TRANS_TABLES"},
    }
}


# ------------------------------------------------------------------------
# Cache (Redis)
# ------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}


# ------------------------------------------------------------------------
# Password Validators
# ------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# ------------------------------------------------------------------------
# Internationalization
# ------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# ------------------------------------------------------------------------
# Static & Media
# ------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/ELV/documents/")


# Media access control rules
# settings.py - RECOMMENDED CONFIG
MEDIA_ACCESS_RULES = {
    'ALLOWED_DIRECTORIES': [
        # Be VERY specific about what's allowed
        'documents/public/',
        'images/avatars/',
        'uploads/temp/',
    ],
    
    'BLOCKED_DIRECTORIES': [
        # Block everything else by default
        'documents/',  # This blocks ALL documents except the specific allowed ones above
        'images/',
        'uploads/',
        'private/',
        'secret/',
        'config/',
        'documents/auth_person_pan/',  # Specifically block this folder
    ],
    
    'ALLOWED_EXTENSIONS': [
        '.pdf', '.jpg', '.jpeg', '.png', '.gif',
        '.doc', '.docx', '.txt', '.csv'
    ],
    
    'BLOCKED_EXTENSIONS': [
        '.exe', '.php', '.sh', '.bat', '.py', '.js',
        '.html', '.htm', '.css', '.sql', '.env'
    ],
    
    'REQUIRE_AUTHENTICATION': [
        'documents/auth_person_pan/',  # Or require login for this folder
        'private/',
        'user_uploads/',
    ]
}




# ------------------------------------------------------------------------
# CAPTCHA
# ------------------------------------------------------------------------
CAPTCHA_IMAGE_SIZE = (175, 50)
CAPTCHA_LENGTH = 6
CAPTCHA_FONT_SIZE = 30
CAPTCHA_NOISE_FUNCTIONS = ('captcha.helpers.noise_arcs', 'captcha.helpers.noise_dots')
CAPTCHA_BACKGROUND_COLOR = "#f0f2f5"
CAPTCHA_FOREGROUND_COLOR = "#020f2c"
CAPTCHA_CHALLENGE_FUNCT = 'registration.captcha_challenges.complex_symbol_challenge'
CAPTCHA_TIMEOUT = 5

# ------------------------------------------------------------------------
# Email
# ------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ------------------------------------------------------------------------
# Session / Auth
# ------------------------------------------------------------------------
# AUTH_USER_MODEL = 'CpcbApp.User'

SESSION_COOKIE_PATH = '/'
CSRF_COOKIE_PATH = '/'
SESSION_COOKIE_AGE = 30 * 60  # 30 min
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Custom auto logout settings
SESSION_EXPIRE_SECONDS = 1800
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_TIMEOUT_REDIRECT = "/login/"
LOGIN_URL = "/login/"
RATELIMIT_IP_META_KEY = 'HTTP_X_FORWARDED_FOR'

SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False


# ------------------------------------------------------------------------
# Whatapp API Auth Token
# ------------------------------------------------------------------------
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")


# ------------------------------------------------------------------------
# Billdesk Payment Gateway Production
# ------------------------------------------------------------------------
BILLDESK_MERCHANT_ID = os.environ.get("BILLDESK_MERCHANT_ID")
BILLDESK_CLIENT_ID = os.environ.get("BILLDESK_CLIENT_ID")
BILLDESK_KEY_ID = os.environ.get("BILLDESK_KEY_ID")
BILLDESK_SIGNING_KEY = os.environ.get("BILLDESK_SIGNING_KEY")
BILLDESK_ENCRYPTION_KEY = os.environ.get("BILLDESK_ENCRYPTION_KEY")
BILLDESK_API_ENDPOINT = os.environ.get("BILLDESK_API_ENDPOINT")
BILLDESK_RETRIEVE_PAYMENT_API_ENDPOINT = os.environ.get("BILLDESK_RETRIEVE_PAYMENT_API_ENDPOINT")



# BILLDESK_MERCHANT_ID = 'XBCEFCPELV'   # Production
# BILLDESK_CLIENT_ID = 'xbcefcpelv'    # Production
# BILLDESK_KEY_ID = 'hv5hosPFNY4nx6URKMG1d0ctwxUROIKw'  # Production
# BILLDESK_API_ENDPOINT = 'https://api.billdesk.com/payments/ve1_2/ecomorders/create'    #Production



# ------------------------------------------------------------------------
# wkhtmltopdf
# ------------------------------------------------------------------------
WKHTMLTOPDF_CMD = (
    r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    if platform.system() == "Windows"
    else "/usr/local/bin/wkhtmltopdf"
)

if not os.path.exists(WKHTMLTOPDF_CMD):
    WKHTMLTOPDF_CMD = "wkhtmltopdf"

PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_CMD)


# ------------------------------------------------------------------------
# Em-Signer
# ------------------------------------------------------------------------

ESIGNER_AUTHTOKEN = os.environ.get("ESIGNER_AUTHTOKEN")



# ------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------
# LOGGING = {
#     'version':1,
#     'loggers':{
#         'django':{'handlers':['console'],'level':'DEBUG',}
#     },
#     'handlers':{
#         'console':{'level':'INFO','class':'logging.StreamHandler','formatter':'simpleRe',}
#     },
#     'formatters':{
#         'simpleRe':{'format':'{levelname} {asctime} {module} {process:d} {thread:d} {message}','style':'{',}
#     }
# }
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'elv_logger': {
            'handlers': ['elv_file'],
            'level': 'INFO',
            'propagate': False,
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simpleRe',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'debug.log'),
            'formatter': 'simpleRe',
        },
        'elv_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'elv.log'),
            'formatter': 'simpleRe',
        }
    },
    'formatters': {
        'simpleRe': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        }
    }
}

# ------------------------------------------------------------------------
# Warnings
# ------------------------------------------------------------------------
warnings.filterwarnings('ignore', message='Model .* was already registered', category=RuntimeWarning)


# ------------------------------------------------------------------------
# Import environment-specific security settings
# ------------------------------------------------------------------------
if DEBUG:
    try:
        from .settings_security_dev import *
    except ImportError:
        warnings.warn("settings_security_dev.py not found! Dev security not applied.")
else:
    try:
        from .settings_security import *
    except ImportError:
        warnings.warn("settings_security.py not found! Production security not applied.")
        
        



