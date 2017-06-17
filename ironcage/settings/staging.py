from .base import *  # flake8: noqa

ALLOWED_HOSTS = ['ironcage-dev.herokuapp.com']

# A custom setting for creating full URLs in links in emails
DOMAIN = f'https://{ALLOWED_HOSTS[0]}'
