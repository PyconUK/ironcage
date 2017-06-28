from .base import *  # flake8: noqa

ALLOWED_HOSTS = ['hq-staging.pyconuk.org']

# A custom setting for creating full URLs in links in emails
DOMAIN = f'https://{ALLOWED_HOSTS[0]}'
