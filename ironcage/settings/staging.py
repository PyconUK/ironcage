from .base import *  # flake8: noqa

ALLOWED_HOSTS = ['hq-staging.pyconuk.org']

# A custom setting for creating full URLs in links in emails
DOMAIN = f'https://{ALLOWED_HOSTS[0]}'

# SSL
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Slack
SLACK_USERNAME = 'ironcage-log-bot-staging'

# Email address to send error mails from
SERVER_EMAIL = f'noreply@{ALLOWED_HOSTS[0]'
