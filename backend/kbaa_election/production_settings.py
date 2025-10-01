from .settings import *
import os

DEBUG = False
ALLOWED_HOSTS = ['abedintechemail.com', 'www.abedintechemail.com', '*']

# Use environment variable for SECRET_KEY
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)  # Falls back to settings.py

# Database - already using SQLite (no password needed)

# Security
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django_errors.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}