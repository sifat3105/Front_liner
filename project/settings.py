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
    "https://barta-bahok.vercel.app",
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
    "unfold",
    "unfold.contrib.filters",   
    "unfold.contrib.forms", 
    "unfold.contrib.inlines",
    "unfold.contrib.guardian",  
    "unfold.contrib.import_export",
    'admin_interface',
    'colorfield',
    "daphne",
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
    'apps.orders',
    'apps.inventory',
    'apps.popup',
    'apps.subscription',

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
# CHANNEL LAYERS (WebSocket)
# ==============================================================================
REDIS_CHANNEL_URL = os.getenv(
    "REDIS_CHANNEL_URL",
    os.getenv("REDIS_URL", "redis://127.0.0.1:6379/2"),
)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_CHANNEL_URL]},
    }
}

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
    'DEFAULT_PAGINATION_CLASS': 'utils.pagination.AutoPagination',
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
    "BACKEND": "django_redis.cache.RedisCache",
    "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
    "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
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

MEDIA_ROOT = "/var/www/media"
MEDIA_URL = "https://media.frontliner.io/"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATICFILES_DIRS = [
    BASE_DIR / "static"
]

# ==============================================================================
# THIRD-PARTY INTEGRATIONS
# ==============================================================================

FACEBOOK_APP_ID = "3184250695088317"
FACEBOOK_APP_SECRET = "b4f5267bc9facef8ed80a4d39c5cfb53"
FACEBOOK_REDIRECT_URI = "https://test.frontliner.io/api/social/facebook/callback/"
FB_VERIFY_TOKEN = "my_fb_verify_token_2025"
WHATSAPP_SYSTEM_TOKEN="EAAtQDyOOeL0BQafpvWiLOpb85aaWVdSN1BCiNTouWk0uKJyZCyeqDU4cPc3RNbXsSGTsw0XTNXcrRLllNZCSklnXFlm4bkZB2L6G2ZBjaZB7CWAB8tyQMKckItFIgZCyPXZABGr2FjkQONTu6Y1IfkupezLc8qcvF5MCOqpI21169OiObVIjx9n6qynO28wYG6TBgZDZD"

INSTAGRAM_APP_ID = "2060639764791245"
INSTAGRAM_APP_SECRET = "694ced5269ad277849e5923c"
INSTAGRAM_REDIRECT_URI = "https://test.frontliner.io/api/social/instagram/callback/"

TIKTOK_CLIENT_KEY = "sbaw6iwjvtlzl0dnqr"
TIKTOK_CLIENT_SECRET = "7GSGlOQYv7fHwaHj4JTGS1KOZfIpNoqa"
TIKTOK_REDIRECT_URI = "https://test.frontliner.io/api/social/tiktok/callback/"
TIKTOK_VERIFY_TOKEN = os.environ.get("TIKTOK_VERIFY_TOKEN", "my_tiktok_verify_token_2026")
WHATSAPP_REDIRECT_URI = "https://test.frontliner.io/api/social/whatsapp/callback/"

PLATFORM_CONFIG = {
        "facebook": {
            "auth_url": "https://www.facebook.com/v19.0/dialog/oauth",
            "client_id": FACEBOOK_APP_ID,
            "redirect_uri":FACEBOOK_REDIRECT_URI,
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
            "client_id": FACEBOOK_APP_ID,
            "redirect_uri": INSTAGRAM_REDIRECT_URI,
            # "force_reauth": True,
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
        # Future-ready
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


#===============================================================================
# PAYSTATION
#===============================================================================

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
