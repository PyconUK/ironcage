from .base import *  # flake8: noqa

ALLOWED_HOSTS = ['hq.pyconuk.org']

# A custom setting for creating full URLs in links in emails
DOMAIN = f'https://{ALLOWED_HOSTS[0]}'

# SSL
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Misc. security settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Email address to send mail from
SERVER_EMAIL = f'PyCon UK 2017 <noreply@{ALLOWED_HOSTS[0]}>'
EMAIL_FROM_ADDR = f'PyCon UK 2017 <noreply@{ALLOWED_HOSTS[0]}>'
EMAIL_REPLY_TO_ADDR = 'PyCon UK 2017 <pyconuk-committee@uk.python.org>'

# Last orders...
bst = timezone(timedelta(hours=1))
CFP_CLOSE_AT = datetime(2017, 8, 11, 0, 0, tzinfo=bst)
GRANT_APPLICATIONS_CLOSE_AT = datetime(2017, 8, 11, 0, 0, tzinfo=bst)
