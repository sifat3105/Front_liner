from pathlib import Path
from datetime import timedelta
import os

# ==============================================================================
# BASE CONFIG
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-ub(l^bz2881iu&olufa$0f*d*bma_3h0f_f^6*l#jj56)b%a)k'
DEBUG = True
ALLOWED_HOSTS = ["*"]

# ==============================================================================
# CORS & CSRF CONFIG
# ==============================================================================

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Allow all only in development

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://127.0.0.1:5501",
    "https://127.0.0.1:5501",
    "http://192.168.0.100:3000",
    "http://192.168.0.101:3000",
    "http://103.98.107.22:8000",
]

CORS_ALLOW_METHODS = [
    "DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"
]

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# ==============================================================================
# APPLICATIONS
# ==============================================================================

INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'channels',

    # Local apps
    'apps.user',
    'apps.social',
    'apps.publish',
    'apps.post',
    'apps.chat',
    'apps.voice',
    'apps.assistant',
    'apps.support',
    'apps.call',
    'apps.invoice',
    'apps.phone_number',
    'apps.transaction',
    'apps.topup',
    'apps.notification',
    'apps.settings',
    'apps.account',
    'apps.sells',
    'apps.courier',
    'apps.paymentgateway',
    'apps.vendor',
    'apps.inventory',
]

AUTH_USER_MODEL = 'user.User'

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.request_log.RequestLogMiddleware',
    'middleware.jwt_auth.JWTAuthMiddleware',
]

# ==============================================================================
# URL / TEMPLATES / ASGI / WSGI
# ==============================================================================

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'
ASGI_APPLICATION = 'project.asgi.application'

# ==============================================================================
# DATABASE
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'myproject',
        'USER': 'myprojectuser',
        'PASSWORD': 'password',
        'HOST': 'db.frontliner.io',
        'PORT': '5432',
    }
}

# ==============================================================================
# REST FRAMEWORK & JWT
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'utils.authentication.CookieJWTAuthentication',
    ),
    'EXCEPTION_HANDLER': 'utils.exception_handler.custom_exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'utils.pagination.StandardPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '200/minute',
        'login': '10/minute',
        'register': '5/minute',
        'refresh': '10/minute',
        'social_post': '5/minute',
        'logout': '10/minute',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ==============================================================================
# CACHING
# ==============================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ==============================================================================
# LOGGING
# ==============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(name)s %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ==============================================================================
# STATIC & MEDIA FILES
# ==============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# THIRD-PARTY INTEGRATIONS
# ==============================================================================

FACEBOOK_APP_ID = "3184250695088317"
FACEBOOK_APP_SECRET = "b4f5267bc9facef8ed80a4d39c5cfb53"
FACEBOOK_REDIRECT_URI = "https://test.frontliner.io/api/social/facebook/callback/"
FB_VERIFY_TOKEN = "my_fb_verify_token_2025"

INSTAGRAM_APP_ID = "2060639764791245"
INSTAGRAM_APP_SECRET = "694ced5269ad277849e5923c"

TIKTOK_CLIENT_KEY = "sbaw6iwjvtlzl0dnqr"
TIKTOK_CLIENT_SECRET = "7GSGlOQYv7fHwaHj4JTGS1KOZfIpNoqa"
TIKTOK_REDIRECT_URI = "https://test.frontliner.io/api/social/tiktok/callback/"

PAYSTATION_MERCHANT_ID = "104-1653730183"
PAYSTATION_PASSWORD = "gamecoderstorepass"
PAYSTATION_BASE_URL = "https://sandbox.paystation.com.bd"
PAYSTATION_CALLBACK_URL = "https://sandbox.paystation.com.bd/initiate-payment"

# ==============================================================================
# ENV-BASED SETTINGS
# ==============================================================================

SP_USERNAME = os.environ.get('SP_USERNAME')
SP_PASSWORD = os.environ.get('SP_PASSWORD')
SP_BASE_URL = os.environ.get('SP_BASE_URL')
SP_RETURN_URL = os.environ.get('SP_RETURN_URL')
SP_CANCEL_URL = os.environ.get('SP_CANCEL_URL')
SP_LOGDIR = os.environ.get('SP_LOGDIR')
SP_PREFIX = os.environ.get('SP_PREFIX')
