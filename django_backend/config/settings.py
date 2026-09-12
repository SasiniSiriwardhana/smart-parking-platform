"""
Django settings for the Smart Parking Availability Platform (Day 1 Foundation).

Generated for a clean, modular architecture supporting:
- Django ORM with Oracle Database (python-oracledb)
- Django REST Framework
- Tailwind CSS
- Spring Boot Recommendation Engine integration
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-smart-parking-availability-platform-fallback-key-day-1'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
    if host.strip()
] + ['testserver']

# Application definition
INSTALLED_APPS = [
    # Core platform commands & health checks
    'apps.core',

    # Core Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party packages
    'rest_framework',
    'corsheaders',

    # Smart Parking Platform Apps
    'apps.accounts',        # User profiles, auth, driver preferences
    'apps.parking',         # Parking lots, spots, rate matrices
    'apps.reservations',    # Parking slot booking and hold lifecycle
    'apps.sessions',        # Active parking sessions & duration tracking (label: parking_sessions)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ==============================================================================
# Database Configuration - Oracle Database via python-oracledb
# ==============================================================================
# Modern python-oracledb runs in Thin mode by default (no Oracle Instant Client required).
# Compatibility alias ensures Django's backend connects seamlessly.
try:
    import oracledb
    sys.modules.setdefault('cx_Oracle', oracledb)
except ImportError:
    pass

ORACLE_DB_NAME = os.getenv('ORACLE_DB_NAME', 'FREEPDB1')
ORACLE_USER = os.getenv('ORACLE_USER', 'smart_parking_user')
ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD', '')
ORACLE_HOST = os.getenv('ORACLE_HOST', 'localhost')
ORACLE_PORT = os.getenv('ORACLE_PORT', '1521')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': ORACLE_DB_NAME,
        'USER': ORACLE_USER,
        'PASSWORD': ORACLE_PASSWORD,
        'HOST': ORACLE_HOST,
        'PORT': ORACLE_PORT,
    }
}

# ==============================================================================
# Django REST Framework Configuration
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# ==============================================================================
# CORS Configuration
# ==============================================================================
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://127.0.0.1:3000,http://localhost:8081'
    ).split(',')
    if origin.strip()
]

# ==============================================================================
# External Services Configuration
# ==============================================================================
RECOMMENDATION_SERVICE_URL = os.getenv(
    'RECOMMENDATION_SERVICE_URL',
    'http://localhost:8081/api/recommendation'
)

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
