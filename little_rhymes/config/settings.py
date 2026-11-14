"""Fail-closed production configuration; see .env.example and docs/DEPLOYMENT.md."""
import os
import base64
import binascii
import hashlib
from pathlib import Path
from datetime import timedelta
from urllib.parse import urlsplit

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env', override=False)

def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ('1', 'true', 'yes')

def env_list(name, default=''):
    return [value.strip() for value in os.getenv(name, default).split(',') if value.strip()]

DEBUG = env_bool('DEBUG')
SECRET_KEY = os.getenv('SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('Set a private SECRET_KEY, or DEBUG=True for local development.')
    SECRET_KEY = 'django-insecure-local-development-only-not-for-production'
if not DEBUG and len(SECRET_KEY) == 44:
    # Render generateValue produces 32 random bytes as 44 base64 characters.
    # Domain-separated expansion retains its 256-bit entropy and satisfies
    # Django's minimum-length deployment check without exposing the raw seed.
    try:
        secret_seed = base64.b64decode(SECRET_KEY, validate=True)
    except (binascii.Error, ValueError):
        secret_seed = b''
    if len(secret_seed) == 32:
        SECRET_KEY = hashlib.sha512(b'little-rhymes:django-key:v1:' + secret_seed).hexdigest()
    del secret_seed
if not DEBUG and (len(SECRET_KEY) < 50 or SECRET_KEY.startswith('django-insecure-')):
    raise ImproperlyConfigured('Use a random SECRET_KEY of at least 50 characters, or a generated 256-bit base64 secret.')

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1' if DEBUG else '')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')
render_host = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if render_host:
    ALLOWED_HOSTS.append(render_host)
    CSRF_TRUSTED_ORIGINS.append(f'https://{render_host}')
SITE_URL = os.getenv('SITE_URL', f'https://{render_host}' if render_host else 'http://127.0.0.1:8000').rstrip('/')
if not DEBUG and (not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS or not SITE_URL.startswith('https://')):
    raise ImproperlyConfigured('Production requires explicit ALLOWED_HOSTS and an HTTPS SITE_URL.')

INSTALLED_APPS = [
    'core.admin_apps.StudioAdminConfig', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'django.contrib.sitemaps', 'rest_framework', 'storages', 'axes',
    'core.apps.CoreConfig', 'poems.apps.PoemsConfig', 'contact.apps.ContactConfig',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'core.context_processors.site_context',
    ]},
}]
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'
DATABASE_URL = os.getenv('DATABASE_URL', '')
if not DEBUG and not DATABASE_URL.startswith(('postgres://', 'postgresql://')):
    raise ImproperlyConfigured('Production requires PostgreSQL DATABASE_URL.')
DATABASES = {'default': dj_database_url.parse(
    DATABASE_URL or f'sqlite:///{BASE_DIR / "db.sqlite3"}',
    conn_max_age=600 if DATABASE_URL else 0, conn_health_checks=True,
)}
if DATABASE_URL and env_bool('DATABASE_SSL_REQUIRE', not DEBUG):
    DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}

REDIS_URL = os.getenv('REDIS_URL', '')
if not DEBUG and not REDIS_URL:
    raise ImproperlyConfigured('Production requires REDIS_URL for shared form rate limits.')
CACHES = {'default': {
    'BACKEND': 'django.core.cache.backends.redis.RedisCache' if REDIS_URL else 'django.core.cache.backends.locmem.LocMemCache',
    'LOCATION': REDIS_URL or 'little-rhymes-local', 'KEY_PREFIX': 'little-rhymes', 'TIMEOUT': 300,
}}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
AUTHENTICATION_BACKENDS = ['axes.backends.AxesStandaloneBackend', 'django.contrib.auth.backends.ModelBackend']
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_LOCKOUT_PARAMETERS = [['username', 'ip_address']]
AXES_RESET_ON_SUCCESS = True
AXES_ENABLE_ACCESS_FAILURE_LOG = False
AXES_CLIENT_IP_CALLABLE = 'core.security.client_ip'

LANGUAGE_CODE = 'en'
LANGUAGES = [('en', 'English'), ('hi', 'हिन्दी'), ('mr', 'मराठी')]
LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
USE_S3 = env_bool('USE_S3')
if not DEBUG and not USE_S3:
    raise ImproperlyConfigured('Production media must use S3-compatible persistent storage (USE_S3=True).')
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage' if DEBUG else 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
if USE_S3:
    if not os.getenv('AWS_STORAGE_BUCKET_NAME'):
        raise ImproperlyConfigured('Set AWS_STORAGE_BUCKET_NAME.')
    STORAGES['default'] = {'BACKEND': 'storages.backends.s3.S3Storage', 'OPTIONS': {
        'bucket_name': os.environ['AWS_STORAGE_BUCKET_NAME'],
        'region_name': os.getenv('AWS_S3_REGION_NAME', 'ap-south-1'),
        'endpoint_url': os.getenv('AWS_S3_ENDPOINT_URL') or None,
        'access_key': os.getenv('AWS_ACCESS_KEY_ID') or None,
        'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY') or None,
        'default_acl': None, 'file_overwrite': False,
        'querystring_auth': True, 'querystring_expire': 3600,
        'object_parameters': {'CacheControl': 'private, max-age=3600'},
    }}
# Explicit HTTPS origins, e.g. https://my-bucket.s3.ap-south-1.amazonaws.com.
MEDIA_ORIGINS = env_list('MEDIA_ORIGINS')
EXTERNAL_VIDEO_HOSTS = env_list('EXTERNAL_VIDEO_HOSTS')
if USE_S3 and not MEDIA_ORIGINS:
    raise ImproperlyConfigured('Set MEDIA_ORIGINS to the exact HTTPS storage origins so CSP permits uploaded media.')
for media_origin in MEDIA_ORIGINS:
    parsed = urlsplit(media_origin)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username or '*' in media_origin:
        raise ImproperlyConfigured('MEDIA_ORIGINS must contain exact HTTPS origins without paths, credentials or wildcards.')
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o644
CONTACT_RATE_LIMIT = 5
CONTACT_RATE_WINDOW = 900
TRUST_RENDER_PROXY = env_bool('TRUST_RENDER_PROXY')

SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('HSTS_INCLUDE_SUBDOMAINS')
SECURE_HSTS_PRELOAD = env_bool('HSTS_PRELOAD')
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'
CSRF_FAILURE_VIEW = 'core.views.csrf_failure'
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
}
LOGGING = {
    'version': 1, 'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': os.getenv('LOG_LEVEL', 'INFO')},
    'loggers': {'django.server': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False}},
}
