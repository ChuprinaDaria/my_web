from decouple import config
import os
import locale
import sys
from pathlib import Path
import logging
import re
from celery.schedules import crontab

# === 🔒 SECURITY & ENCODING ===
os.environ['PYTHONIOENCODING'] = 'utf-8'
try:
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
sys.stdout.reconfigure(encoding='utf-8')

# Gettext для Windows
gettext_path = r"C:\Program Files (x86)\GnuWin32\bin"
if os.path.exists(gettext_path):
    os.environ['PATH'] = gettext_path + os.pathsep + os.environ['PATH']

# === 📁 BASE PATHS ===
BASE_DIR = Path(__file__).resolve().parent.parent

# === 🔐 CORE SECURITY ===
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# ✅ Керуємо з .env: DJANGO_ALLOWED_HOSTS, DJANGO_CSRF_TRUSTED_ORIGINS
# приклад у .env:
# DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,lazysoft.pl,www.lazysoft.pl
# DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost,https://localhost,http://127.0.0.1,https://127.0.0.1,https://lazysoft.pl,https://www.lazysoft.pl
ALLOWED_HOSTS = [h for h in config('DJANGO_ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',') if h]

_csrf_from_env = [o for o in config(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    default='http://localhost,https://localhost,http://127.0.0.1,https://127.0.0.1'
).split(',') if o]
# Якщо у .env нема доменів для CSRF — додамо їх автоматично з ALLOWED_HOSTS (http/https)
if _csrf_from_env:
    CSRF_TRUSTED_ORIGINS = _csrf_from_env
else:
    CSRF_TRUSTED_ORIGINS = [f"http://{h}" for h in ALLOWED_HOSTS] + [f"https://{h}" for h in ALLOWED_HOSTS]

# === 🔐 AUTHENTICATION ===
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Django-axes
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_LOCKOUT_TEMPLATE = 'security/lockout.html'
AXES_LOCK_OUT_AT_FAILURE = True
AXES_LOCKOUT_URL = '/control/login/'
AXES_ENABLED = True

# === 📦 INSTALLED APPS ===
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django_ckeditor_5',
    
    # Third party
    'parler',
    'ckeditor',
    'ckeditor_uploader',
    'django_filters',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_select2',
    'django_extensions',
    'axes',
    'django_celery_beat',
    
    # 2FA Security
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_email',
    
    # Your apps
    'core',
    'about',
    'blog',
    'news',
    'projects',
    'pricing',
    'services',
    'contacts.apps.ContactsConfig',
    'accounts',
    'consultant',
    'terms',
    'rag',
    'pgvector',
    'emails',
    'hr',  # 👔 HR Панель
]

SITE_ID = 1

# === 🔧 MIDDLEWARE ===
MIDDLEWARE = [
    'core.middleware.security.WWWRedirectMiddleware',  # Редірект www → non-www (ПЕРШИЙ!)
    'core.middleware.error_pages.ErrorPagesMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RequireOTPForAdminMiddleware',
    'core.middleware.security.AdminJWTMiddleware',
    'core.middleware.cookie_consent.CookieConsentMiddleware',
    'core.middleware.security.LinusSecurityMiddleware',
    'core.middleware.sitemap_robots.SitemapRobotsMiddleware',
]

ROOT_URLCONF = 'lazysoft.urls'

# === 📄 TEMPLATES ===
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core'/'templates', BASE_DIR / 'emails' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'core.context_processors.seo_settings',
                'core.context_processors.cookie_consent',
            ],
        },
    },
]

WSGI_APPLICATION = 'lazysoft.wsgi.application'

# === 🗄️ DATABASE ===
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# === 🧠 RAG SETTINGS ===
RAG_SETTINGS = {
    "PROVIDER": "openai",
    "EMBEDDING_MODELS": {
        "gemini": {
            "name": "models/embedding-001",
            "dim": 768,
        },
        "openai": {
            "name": "text-embedding-3-small",
            "dim": 1536,
        },
    },
    "SIMILARITY_THRESHOLD": 0.2,
    "MAX_SEARCH_RESULTS": 10,
    "MAX_CONTEXT_LENGTH": 4000,
    "AUTO_GENERATE_EMBEDDINGS": False,
    "REINDEX_INTERVAL_HOURS": 24,
    "INDEXABLE_MODELS": [
        "services.ServiceCategory",
        "projects.Project",
        "services.FAQ",
        "rag.KnowledgeSource",
        "pricing.ServicePricing",
        "contacts.Contact",
        "about.About",
    ],
    "SUPPORTED_LANGUAGES": ["uk", "en", "pl"],
    "CONSULTANT_NAME": "Julie",
    "CONSULTANT_PERSONALITY": "Дружелюбна IT-експертка, яка допомагає з технічними рішеннями",
    "DEFAULT_LANGUAGE": "uk",
    "CONSULTATION_CALENDAR_URL": "https://calendly.com/dchuprina-lazysoft/free-consultation-1h",
    "CONSULTATION_URL": "https://calendly.com/dchuprina-lazysoft/free-consultation-1h",
}

# === 📦 CELERY ===
CELERY_BROKER_URL = config('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Warsaw'

CELERY_TASK_ROUTES = {
    'news.process_single_article': {'queue': 'news_processing'},
    'news.process_rss_source': {'queue': 'news_parsing'},
    'news.run_all_rss_sources_processing': {'queue': 'news_parsing'},
    'news.post_top_news_to_telegram': {'queue': 'social'},
    'news.run_full_daily_pipeline': {'queue': 'news_parsing'},
    'rag.*': {'queue': 'rag'},
}

CELERY_BEAT_SCHEDULE = {
    'hourly-telegram-post': {
        'task': 'news.post_top_news_to_telegram',
        'schedule': crontab(hour='8-23', minute=0),
    },
    'daily-full-news-pipeline': {
        'task': 'news.run_full_daily_pipeline',
        'schedule': crontab(hour=18, minute=10),
    },
    'daily-conversation-analysis': {
        'task': 'rag.analyze_conversations',
        'schedule': crontab(hour=6, minute=0),
        'kwargs': {'days': 1, 'auto_approve': False}
    },
    'weekly-pattern-analysis': {
        'task': 'rag.analyze_conversations',
        'schedule': crontab(day_of_week=1, hour=7, minute=0),
        'kwargs': {'days': 7, 'auto_approve': False}
    },
    'monthly-cleanup': {
        'task': 'rag.cleanup_old_patterns',
        'schedule': crontab(day_of_month=1, hour=2, minute=0),
        'kwargs': {'days_old': 60}
    },
    'daily-reindex-approved': {
        'task': 'rag.reindex_approved_patterns',
        'schedule': crontab(hour=8, minute=30),
    }
}

RAG_LEARNING_SETTINGS = {
    'AUTO_ANALYSIS_ENABLED': True,
    'DAILY_ANALYSIS_DAYS': 1,
    'WEEKLY_ANALYSIS_DAYS': 7,
    'MIN_FREQUENCY_FOR_QUALITY': 3,
    'MIN_SUCCESS_RATE_FOR_QUALITY': 0.8,
    'MIN_MESSAGE_LENGTH': 10,
    'NOTIFY_NEW_PATTERNS': True,
    'ADMIN_EMAIL': 'your-email@domain.com',
    'SLACK_WEBHOOK': None,
}

# === 🌐 INTERNATIONALIZATION ===
LANGUAGES = [
    ('en', 'English'),
    ('uk', 'Українська'),
    ('pl', 'Polski'),
]

LANGUAGE_CODE = 'en'
USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = 'Europe/Warsaw'

LOCALE_PATHS = [BASE_DIR / 'locale']

# === 🎨 PARLER (Multi-language) ===
PARLER_LANGUAGES = {
    None: (
        {'code': 'en'},
        {'code': 'uk'},
        {'code': 'pl'},
    ),
    'default': {
        'fallbacks': ['en', 'uk'],
        'hide_untranslated': False,
    }
}

# === 📁 STATIC & MEDIA ===
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Для production збірки
STATICFILES_DIRS = [BASE_DIR / 'static']  # Для розробки

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# === ✏️ CKEDITOR ===
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Full',
        'height': 300,
        'width': '100%',
        'tabSpaces': 4,
        'extraPlugins': ','.join(['codesnippet']),
    },
}

# === 🔄 FIVEFILTERS ===
FIVEFILTERS_ENABLED = config('FIVEFILTERS_ENABLED', default=True, cast=bool)
FIVEFILTERS_BASE_URL = config('FIVEFILTERS_BASE_URL', default='http://localhost:8082')
FIVEFILTERS_TIMEOUT = config('FIVEFILTERS_TIMEOUT', default=30, cast=int)
FIVEFILTERS_MAX_RETRIES = config('FIVEFILTERS_MAX_RETRIES', default=2, cast=int)

# === 🖼️ STOCK IMAGES ===
UNSPLASH_ACCESS_KEY = config('UNSPLASH_ACCESS_KEY', default=None)
PEXELS_API_KEY = config('PEXELS_API_KEY', default=None)
PIXABAY_API_KEY = config('PIXABAY_API_KEY', default=None)
STOCK_IMAGE_CACHE_TIMEOUT = config('STOCK_IMAGE_CACHE_TIMEOUT', default=2592000, cast=int)

# === 🤖 AI CONFIGURATION ===
GEMINI_API_KEY = config('GEMINI_API_KEY', default=None)
OPENAI_API_KEY = config('OPENAI_API_KEY', default=None)
OPENAI_ORG_ID = config("OPENAI_ORG_ID", default="")
OPENAI_PROJECT_ID = config("OPENAI_PROJECT_ID", default="")

AI_PREFERRED_MODEL = config('AI_PREFERRED_MODEL', default='openai')
AI_BACKUP_MODEL = config('AI_BACKUP_MODEL', default='openai')
AI_MAX_TOKENS = config('AI_MAX_TOKENS', default=2000, cast=int)
AI_TEMPERATURE = config('AI_TEMPERATURE', default=0.7, cast=float)
AI_GEMINI_GENERATIVE_MODEL = config('AI_GEMINI_GENERATIVE_MODEL', default='gemini-1.5-flash')
AI_OPENAI_GENERATIVE_MODEL = config('AI_OPENAI_GENERATIVE_MODEL', default='gpt-4o')
AI_OPENAI_GENERATIVE_MODEL_FALLBACK = config('AI_OPENAI_GENERATIVE_MODEL_FALLBACK', default='gpt-4o-mini')

# === 📱 SOCIAL MEDIA ===
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default=None)
TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID", default=None)
TELEGRAM_ADMIN_CHAT_ID = config('TELEGRAM_ADMIN_CHAT_ID', default=None)

FACEBOOK_ACCESS_TOKEN = config('FACEBOOK_ACCESS_TOKEN', default=None)
FACEBOOK_PAGE_EN = config('FACEBOOK_PAGE_EN', default=None)
FACEBOOK_PAGE_PL = config('FACEBOOK_PAGE_PL', default=None)

LINKEDIN_ACCESS_TOKEN = config('LINKEDIN_ACCESS_TOKEN', default=None)

# === 📰 NEWS SYSTEM ===
NEWS_AUTO_PUBLISH = config('NEWS_AUTO_PUBLISH', default=False, cast=bool)
NEWS_MAX_DAILY_ARTICLES = config('NEWS_MAX_DAILY_ARTICLES', default=20, cast=int)
NEWS_DEFAULT_LANGUAGE = config('NEWS_DEFAULT_LANGUAGE', default='uk')

RSS_PARSER_USER_AGENT = 'LAZYSOFT-NewsBot/1.0'
RSS_FETCH_TIMEOUT = config('RSS_FETCH_TIMEOUT', default=30, cast=int)
RSS_MAX_ARTICLES_PER_SOURCE = config('RSS_MAX_ARTICLES_PER_SOURCE', default=50, cast=int)

NEWS_ARTICLES_PER_PAGE = 12
NEWS_RELATED_ARTICLES = 3

# === 🎯 SEO ===
SITE_URL = config('SITE_URL')  # БЕЗ default - обов'язково в .env
SITE_NAME = config('SITE_NAME', default='LAZYSOFT')

GOOGLE_ANALYTICS_ID = config('GOOGLE_ANALYTICS_ID', default=None)
GOOGLE_SITE_VERIFICATION = config('GOOGLE_SITE_VERIFICATION', default=None)
BING_SITE_VERIFICATION = config('BING_SITE_VERIFICATION', default=None)
YAHOO_SITE_VERIFICATION = config('YAHOO_SITE_VERIFICATION', default=None)
DISABLE_GOOGLE_INDEXING = config('DISABLE_GOOGLE_INDEXING', default=False, cast=bool)

# === 💾 CACHING ===
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'lazysoft-cache',
        'TIMEOUT': 900,
        'OPTIONS': {'MAX_ENTRIES': 1000}
    }
}

CACHE_TIMEOUT_NEWS = config('CACHE_TIMEOUT_NEWS', default=900, cast=int)
CACHE_TIMEOUT_WIDGETS = config('CACHE_TIMEOUT_WIDGETS', default=300, cast=int)

# === 📊 LOGGING ===
class StripEmojiFilter(logging.Filter):
    _EMOJI_RE = re.compile(r'[\U00010000-\U0010FFFF]|\uFE0F|[\u2600-\u26FF]')
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._EMOJI_RE.sub('', record.msg)
        return True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'strip_emoji': {'()': StripEmojiFilter},
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'news.log',
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'ai_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'ai_processing.log',
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['strip_emoji'],
        },
    },
    'loggers': {
        'news': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'news.services.ai_processor': {
            'handlers': ['ai_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'news.services.rss_parser': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'security': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'rag': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# === 📈 ROI ===
ROI_HOURLY_RATE_CONTENT_MANAGER = config('ROI_HOURLY_RATE_CONTENT_MANAGER', default=15, cast=float)
ROI_HOURLY_RATE_SMM_SPECIALIST = config('ROI_HOURLY_RATE_SMM_SPECIALIST', default=12, cast=float)
ROI_HOURLY_RATE_COPYWRITER = config('ROI_HOURLY_RATE_COPYWRITER', default=20, cast=float)
AI_MANUAL_COST_PER_ARTICLE = float(config("AI_MANUAL_COST_PER_ARTICLE", default=19))

# === 🔐 SECURITY HEADERS ===
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'", "'unsafe-inline'", "'unsafe-eval'",
    "https://www.googletagmanager.com",
    "https://www.google-analytics.com",
    "https://unpkg.com",
    "https://cdn.jsdelivr.net"
)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC = (
    "'self'", "data:", "blob:",
    "https://images.unsplash.com",
    "https://cdn.pixabay.com",
    "https://images.pexels.com"
)
CSP_CONNECT_SRC = (
    "'self'",
    "https://www.google-analytics.com",
    "https://analytics.google.com"
)
CSP_REQUIRE_TRUSTED_TYPES_FOR = "'script'"
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# === 📧 EMAIL ===
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'serwer2555348.home.pl'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_AUTHENTICATION = True
EMAIL_HOST_USER = 'info@lazysoft.pl'
EMAIL_HOST_PASSWORD = config('EMAIL_PASSWORD', default='')
DEFAULT_FROM_EMAIL = 'info@lazysoft.pl'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# === 🖕 LINUS SECURITY SYSTEM ===
LINUS_SECURITY_ENABLED = True
LINUS_TELEGRAM_ALERTS = True
LINUS_LOG_ALL_ATTACKS = True

# === ☁️ CLOUDFLARE / REVERSE PROXY ===
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CLOUDFLARE_IPS = [
    '173.245.48.0/20', '103.21.244.0/22', '103.22.200.0/22', '103.31.4.0/22',
    '141.101.64.0/18', '108.162.192.0/18', '190.93.240.0/20', '188.114.96.0/20',
    '197.234.240.0/22', '198.41.128.0/17', '162.158.0.0/15', '104.16.0.0/13',
    '104.24.0.0/14', '172.64.0.0/13', '131.0.72.0/22',
]

CLOUDFLARE_API_TOKEN = config('CLOUDFLARE_API_TOKEN', default=None)
CLOUDFLARE_ZONE_ID = config('CLOUDFLARE_ZONE_ID', default=None)
CLOUDFLARE_EMAIL = config('CLOUDFLARE_EMAIL', default=None)

# === 📋 ASANA ===
ASANA_TOKEN = config('ASANA_TOKEN', default=None)
ASANA_WORKSPACE_ID = config('ASANA_WORKSPACE_ID', default=None)
ASANA_PROJECT_ID = config('ASANA_PROJECT_ID', default=None)

# === 🎯 CRM ===
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
SELECT2_CACHE_BACKEND = "default"

# === 🔐 LOGIN ===
LOGIN_URL = 'admin_2fa_login'
LOGIN_REDIRECT_URL = '/control/'

# === 🔐 2FA ===
OTP_TOTP_ISSUER = 'LAZYSOFT Admin'
OTP_TOTP_TOLERANCE = 1
OTP_EMAIL_SENDER = 'noreply@lazysoft.com.ua'
OTP_EMAIL_SUBJECT = 'LAZYSOFT Admin - 2FA Code'
OTP_STATIC_THROTTLE_FACTOR = 2

CSRF_FAILURE_VIEW = 'core.views.csrf_failure'

# === 🔐 ADMIN JWT ===
ADMIN_JWT_SECRET = config('ADMIN_JWT_SECRET', default=SECRET_KEY)
ADMIN_JWT_ALG = 'HS256'
ADMIN_JWT_TTL_MIN = 30
ADMIN_JWT_COOKIE_NAME = 'admin_jwt'
ADMIN_JWT_COOKIE_SECURE = not DEBUG
ADMIN_JWT_COOKIE_SAMESITE = 'Lax'

# === 🌐 PRODUCTION SECURITY ===
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIREC = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_BROWSER_XSS_FILTER = True
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMАINS = False
    SECURE_HSTS_PRELOAD = False

# === 📁 CREATE DIRECTORIES ===
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(BASE_DIR / 'media', exist_ok=True)
os.makedirs(BASE_DIR / 'staticfiles', exist_ok=True)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# === 👥 HR Settings ===
CRYPTOGRAPHY_KEY = config('CRYPTOGRAPHY_KEY', default='Ih3AYPpozACFlZqUlTTly0z2gBmMEBwIvsCJSKIJ19w=')
CRYPTOGRAPHY_SALT = config('CRYPTOGRAPHY_SALT', default='hr-encryption-salt')

# Папка для підпису
HR_SIGNATURE_PATH = os.path.join(MEDIA_ROOT, 'hr', 'signature.png')

# Папка для згенерованих договорів
HR_CONTRACTS_PATH = os.path.join(MEDIA_ROOT, 'hr', 'contracts')

# Створюємо директорії для HR
os.makedirs(HR_CONTRACTS_PATH, exist_ok=True)
os.makedirs(os.path.dirname(HR_SIGNATURE_PATH), exist_ok=True)
