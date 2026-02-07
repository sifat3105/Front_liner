from pathlib import Path
from datetime import timedelta
import os
import importlib.util
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
HAS_WHITENOISE = importlib.util.find_spec("whitenoise") is not None


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def env(key: str, default=None):
    return os.getenv(key, default)

def env_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y", "on")

def env_list(key: str, default=None):
    val = os.getenv(key)
    if val is None:
        return default if default is not None else []
    return [x.strip() for x in val.split(",") if x.strip()]

def env_int(key: str, default: int = 0) -> int:
    val = os.getenv(key)
    if val is None or val == "":
        return default
    return int(val)


# ------------------------------------------------------------------------------
# Base config
# ------------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY", "change-this")
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])

# If behind Nginx/Proxy with HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True


# ------------------------------------------------------------------------------
# Apps
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    # Admin UI
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.guardian",
    "unfold.contrib.import_export",
    "admin_interface",
    "colorfield",

    # Core
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "channels",

    # Local apps
    "apps.user",
    "apps.social",
    "apps.publish",
    "apps.post",
    "apps.chat",
    "apps.voice",
    "apps.assistant",
    "apps.support",
    "apps.call",
    "apps.invoice",
    "apps.phone_number",
    "apps.transaction",
    "apps.topup",
    "apps.notification",
    "apps.settings",
    "apps.account",
    "apps.sells",
    "apps.courier",
    "apps.paymentgateway",
    "apps.vendor",
    "apps.orders",
    "apps.inventory",
    "apps.popup",
    "apps.subscription",
]

AUTH_USER_MODEL = "user.User"


# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # Your custom middlewares
    "middleware.request_log.RequestLogMiddleware",
    "middleware.jwt_auth.JWTAuthMiddleware",
]
if HAS_WHITENOISE:
    # Keep WhiteNoise right after SecurityMiddleware.
    MIDDLEWARE.insert(2, "whitenoise.middleware.WhiteNoiseMiddleware")


# ------------------------------------------------------------------------------
# URL / Templates / ASGI / WSGI
# ------------------------------------------------------------------------------
ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "project.wsgi.application"
ASGI_APPLICATION = "project.asgi.application"


# ------------------------------------------------------------------------------
# CORS & CSRF
# ------------------------------------------------------------------------------
CORS_ALLOW_CREDENTIALS = True

# In production keep False, in dev you can set True using env
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", False)
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", ["http://localhost:3000"])

CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", CORS_ALLOWED_ORIGINS)

CSRF_COOKIE_SAMESITE = env("CSRF_COOKIE_SAMESITE", "None")
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_HTTPONLY = env_bool("CSRF_COOKIE_HTTPONLY", True)

SESSION_COOKIE_SAMESITE = env("SESSION_COOKIE_SAMESITE", "None")
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
SESSION_COOKIE_HTTPONLY = env_bool("SESSION_COOKIE_HTTPONLY", True)


# ------------------------------------------------------------------------------
# Database
# ------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": env("DB_NAME", ""),
        "USER": env("DB_USER", ""),
        "PASSWORD": env("DB_PASSWORD", ""),
        "HOST": env("DB_HOST", "127.0.0.1"),
        "PORT": env("DB_PORT", "5432"),
        "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
    },
    "replica": {
        "ENGINE": env("DB_REPLICA_ENGINE", "django.db.backends.postgresql"),
        "NAME": env("DB_REPLICA_NAME", ""),
        "USER": env("DB_REPLICA_USER", ""),
        "PASSWORD": env("DB_REPLICA_PASSWORD", ""),
        "HOST": env("DB_REPLICA_HOST", "127.0.0.1"),
        "PORT": env("DB_REPLICA_PORT", "5432"),
        "CONN_MAX_AGE": env_int("DB_REPLICA_CONN_MAX_AGE", 60),
    },
}

# Optional: you can later add a DB router to send reads to replica automatically.


# ------------------------------------------------------------------------------
# Redis (Cache + Channels)
# ------------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", "redis://127.0.0.1:6379/1")
REDIS_CHANNEL_URL = env("REDIS_CHANNEL_URL", "redis://127.0.0.1:6379/2")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_CHANNEL_URL]},
    }
}


# ------------------------------------------------------------------------------
# DRF & JWT
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "utils.authentication.CookieJWTAuthentication",
    ),
    "EXCEPTION_HANDLER": "utils.exception_handler.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "utils.pagination.AutoPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/minute",
        "user": "200/minute",
        "login": "10/minute",
        "register": "5/minute",
        "refresh": "10/minute",
        "social_post": "5/minute",
        "logout": "10/minute",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_MINUTES", 1)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env_int("JWT_REFRESH_DAYS", 1)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# ------------------------------------------------------------------------------
# Static & Media
# ------------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
    if HAS_WHITENOISE
    else "django.contrib.staticfiles.storage.StaticFilesStorage"
)

MEDIA_ROOT = env("MEDIA_ROOT", "/var/www/media")
MEDIA_URL = env("MEDIA_URL", "https://media.frontliner.io/")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ------------------------------------------------------------------------------
# Internationalization
# ------------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True


# ------------------------------------------------------------------------------
# Third-party integrations (ALL FROM ENV)
# ------------------------------------------------------------------------------
CRYPTO_SECRET_KEY = env("CRYPTO_SECRET_KEY", "")

OPENAI_API_KEY = env("OPENAI_API_KEY", "")
GOOGLE_API_KEY = env("GOOGLE_API_KEY", "")
GROQ_API_KEY = env("GROQ_API_KEY", "")
AZURE_SPEECH_KEY = env("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = env("AZURE_SPEECH_REGION", "")

FACEBOOK_APP_ID = env("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = env("FACEBOOK_APP_SECRET", "")
FACEBOOK_REDIRECT_URI = env("FACEBOOK_REDIRECT_URI", "")
FB_VERIFY_TOKEN = env("FB_VERIFY_TOKEN", "")

INSTAGRAM_APP_ID = env("INSTAGRAM_APP_ID", "")
INSTAGRAM_APP_SECRET = env("INSTAGRAM_APP_SECRET", "")
INSTAGRAM_REDIRECT_URI = env("INSTAGRAM_REDIRECT_URI", "")

WHATSAPP_SYSTEM_TOKEN = env("WHATSAPP_SYSTEM_TOKEN", "")
WHATSAPP_REDIRECT_URI = env("WHATSAPP_REDIRECT_URI", "")

TIKTOK_CLIENT_KEY = env("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = env("TIKTOK_CLIENT_SECRET", "")
TIKTOK_REDIRECT_URI = env("TIKTOK_REDIRECT_URI", "")
TIKTOK_VERIFY_TOKEN = env("TIKTOK_VERIFY_TOKEN", "")

PLATFORM_CONFIG = {
    "facebook": {
        "auth_url": "https://www.facebook.com/v19.0/dialog/oauth",
        "client_id": FACEBOOK_APP_ID,
        "redirect_uri": FACEBOOK_REDIRECT_URI,
        "scope": [
            "public_profile",
            "pages_show_list",
            "pages_read_engagement",
            "pages_manage_posts",
            "pages_manage_engagement",
            "pages_manage_metadata",
            "pages_messaging",
        ],
        "state_prefix": "facebook_oauth_",
    },
    "instagram": {
        "auth_url": "https://www.facebook.com/v19.0/dialog/oauth",
        "client_id": FACEBOOK_APP_ID,  # Instagram uses Facebook app in your setup
        "redirect_uri": INSTAGRAM_REDIRECT_URI,
        "scope": [
            "instagram_basic",
            "instagram_content_publish",
            "instagram_manage_comments",
            "instagram_manage_messages",
            "instagram_manage_insights",
            "pages_show_list",
            "pages_read_engagement",
            "pages_manage_metadata",
            "business_management",
        ],
        "state_prefix": "instagram_oauth_",
    },
    "whatsapp": {
        "auth_url": "https://www.facebook.com/v19.0/dialog/oauth",
        "client_id": FACEBOOK_APP_ID,
        "redirect_uri": WHATSAPP_REDIRECT_URI,
        "scope": [
            "business_management",
            "whatsapp_business_management",
            "whatsapp_business_messaging",
        ],
        "state_prefix": "whatsapp_oauth_",
    },
    "tiktok": {
        "auth_url": "https://www.tiktok.com/v2/auth/authorize/",
        "client_id": TIKTOK_CLIENT_KEY,
        "redirect_uri": TIKTOK_REDIRECT_URI,
        "scope": [
            "user.info.basic",
            "video.list",
            "video.upload",
            "video.publish",
        ],
        "state_prefix": "tiktok_oauth_",
    },
}


# ------------------------------------------------------------------------------
# Paystation (ENV)
# ------------------------------------------------------------------------------
PAYSTATION_MERCHANT_ID = env("PAYSTATION_MERCHANT_ID", "")
PAYSTATION_PASSWORD = env("PAYSTATION_PASSWORD", "")
PAYSTATION_BASE_URL = env("PAYSTATION_BASE_URL", "")
PAYSTATION_CALLBACK_URL = env("PAYSTATION_CALLBACK_URL", "")


# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


# ------------------------------------------------------------------------------
# Production security hardening (optional but recommended)
# ------------------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = env("SECURE_REFERRER_POLICY", "same-origin")


# ------------------------------------------------------------------------------
# Unfold (Admin UI)
# ------------------------------------------------------------------------------
UNFOLD = {
    "SITE_TITLE": "Care On Admin",
    "SITE_HEADER": "Care On Administration",
    "DASHBOARD_CALLBACK": "project.admin_dashboard.dashboard_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "User Management",
                "collapsible": True,
                "items": [
                    {"title": "Users", 
                    "link": "/admin/user/user/"
                    },
                    {"title": "UserAccounts", 
                    "link": "/admin/user/account/"
                    },
                    {
                        "title": "User Subscriptions",
                        "link": "/admin/subscription/usersubscription/"
                    },
                    {
                        "title": "Subscription Plans",
                        "link": "/admin/subscription/subscriptionplan/"
                    }
                ],
            },
            {
                "title": "Accounts & Profits",
                "collapsible": True,
                "items": [
                    {"title": "Incomes", "link": "/admin/account/income/"},
                    {"title": "Payments", "link": "/admin/account/payment/"},
                    {"title": "Sells", "link": "/admin/account/sell/"},
                    {"title": "Refunds", "link": "/admin/account/refund/"},
                    {"title": "Debit Credit", "link": "/admin/account/debitcredit/"},
                    {"title": "Profit & Loss Reports", "link": "/admin/account/profitlossreport/"},
                    {"title": "Receivers", "link": "/admin/account/receiver/"},
                    {"title": "Products", "link": "/admin/account/product/"},
                    {"title": "Invoices", "link": "/admin/account/invoice/"},
                    {"title": "Payment Gateway", "link": "/admin/account/paymentgateway/"},
                ],
            },
            {
                "title": "Assistant & Agents",
                "collapsible": True,
                "items": [
                    {"title": "Assistants", "link": "/admin/assistant/assistant/"},
                    {"title": "Assistant Files", "link": "/admin/assistant/assistantfile/"},
                    {"title": "Transcripts", "link": "/admin/assistant/transcript/"},
                    {"title": "Transcript Chunks", "link": "/admin/assistant/transcriptchunk/"},
                    {"title": "Assistant Memories", "link": "/admin/assistant/assistantmemory/"},
                ],
            },
            {
                "title": "Calls & Logs",
                "collapsible": True,
                "items": [
                    {"title": "Call Logs", "link": "/admin/call/calllog/"},
                    {"title": "Call Campaigns", "link": "/admin/call/callcampaign/"},
                ],
            },
            {
                "title": "Chat & Conversations",
                "collapsible": True,
                "items": [
                    {"title": "Conversations", "link": "/admin/chat/conversation/"},
                    {"title": "Messages", "link": "/admin/chat/message/"},
                ],
            },
            {
                "title": "Courier",
                "collapsible": True,
                "items": [
                    {"title": "Courier List", "link": "/admin/courier/courierlist/"},
                    {"title": "User Couriers", "link": "/admin/courier/usercourier/"},
                ],
            },
            {
                "title": "Invoice",
                "collapsible": True,
                "items": [
                    {"title": "Admin Invoices", "link": "/admin/invoice/admininvoice/"},
                    {"title": "User Invoices", "link": "/admin/invoice/invoice/"},
                ],
            },
            {
                "title": "Vendor",
                "collapsible": True,
                "items": [
                    {"title": "Vendors", "link": "/admin/vendor/vendor/"},
                    {"title": "Vendor Invoices", "link": "/admin/vendor/vendorinvoice/"},
                    {"title": "Vendor Payments", "link": "/admin/vendor/vendorpayment/"},
                ],
            },
            {
                "title": "Notifications",
                "collapsible": True,
                "items": [
                    {"title": "Notifications", "link": "/admin/notification/notification/"},
                ],
            },
            {
                "title": "Orders",
                "collapsible": True,
                "items": [
                    {"title": "Orders", "link": "/admin/orders/order/"},
                    {"title": "Order Items", "link": "/admin/orders/orderitem/"},
                ],
            },
            {
                "title": "Payment Gateway",
                "collapsible": True,
                "items": [
                    {"title": "Payments", "link": "/admin/paymentgateway/payment/"},
                ],
            },
            {
                "title": "Phone Numbers",
                "collapsible": True,
                "items": [
                    {"title": "Phone Numbers", "link": "/admin/phone_number/phonenumber/"},
                ],
            },
            {
                "title": "Invoices & Billing",
                "collapsible": True,
                "items": [
                    {"title": "Admin invoices", "link": "/admin/invoice/admininvoice/"},
                    {"title": "User invoices", "link": "/admin/invoice/invoice/"},
                ],
            },
            {
                "title": "Posts",
                "collapsible": True,
                "items": [
                    {"title": "Generated Captions", "link": "/admin/post/generatedcaption/"},
                ],
            },
            {
                "title": "Publish",
                "collapsible": True,
                "items": [
                    {"title": "Social Posts", "link": "/admin/publish/socialpost/"},
                    {"title": "Post Media Files", "link": "/admin/publish/postmediafile/"},
                    {"title": "Social Media Drafts", "link": "/admin/publish/mediadraft/"},
                ],
            },
            {
                "title": "Sales",
                "collapsible": True,
                "items": [
                    {"title": "Customers", "link": "/admin/sales/customer/"},
                    {"title": "Locations", "link": "/admin/sales/location/"},
                    {"title": "Contacts", "link": "/admin/sales/contact/"},
                    {"title": "Products", "link": "/admin/sales/product/"},
                ],
            },
            {
                "title": "Social Media",
                "collapsible": True,
                "items": [
                    {"title": "Social Platforms", "link": "/admin/social/socialplatform/"},
                    {"title": "Social Accounts", "link": "/admin/social/socialaccount/"},
                    {"title": "Facebook Pages", "link": "/admin/social/facebookpage/"},
                    {"title": "Instagram Accounts", "link": "/admin/social/instagramaccount/"},
                ],
            },
            {
                "title": "Support",
                "collapsible": True,
                "items": [
                    {"title": "Support Tickets", "link": "/admin/support/ticket/"},
                ],
            },
            {
                "title": "Transactions",
                "collapsible": True,
                "items": [
                    {"title": "Transactions", "link": "/admin/transaction/transaction/"},
                ],
            },
            {
                "title": "Settings & Pricing",
                "collapsible": True,
                "items": [
                    {"title": "Agent Pricing", "link": "/admin/settings/agentpricepermonth/"},
                    {"title": "Minimum Topup", "link": "/admin/settings/minimumtopup/"},
                    {"title": "Call Cost Per Minute", "link": "/admin/settings/callcostperminute/"},
                ],
            },
        ],
    },
}
