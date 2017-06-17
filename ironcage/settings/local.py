from .base import *  # flake8: noqa

DEBUG = bool(os.environ.get('DEBUG'))

# A custom setting for creating full URLs in links in emails
DOMAIN = 'http://localhost:8000'

# Password validators are a pain when testing locally
AUTH_PASSWORD_VALIDATORS = []

# Write emails to the console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
